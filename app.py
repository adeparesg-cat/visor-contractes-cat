import streamlit as st
import pandas as pd
import requests
import altair as alt

# 1. CONFIGURACIÓ
st.set_page_config(page_title="Monitor 2026", page_icon="📊", layout="wide")

st.title("📊 Monitor de Contractació Pública 2026")
st.markdown("Dades oficials de la Generalitat de Catalunya (Dataset: ybgg-dgi6).")

# 2. FUNCIÓ PER ARREGLAR ELS ENLLAÇOS TRENCATS
def netejar_enllac(valor):
    """
    Aquesta funció arregla el problema dels enllaços de Socrata.
    Si l'enllaç ve com un diccionari {'url': '...', 'html': '...'}, es queda només amb la URL.
    """
    if isinstance(valor, dict):
        return valor.get('url', '')
    return str(valor) if pd.notna(valor) else ''

# 3. CÀRREGA DE DADES
@st.cache_data(ttl=3600)
def carregar_dades_2026():
    url = "https://analisi.transparenciacatalunya.cat/resource/ybgg-dgi6.json"
    # Filtrem contractes del 2026
    query = "?$where=data_adjudicacio_contracte >= '2026-01-01T00:00:00.000'&$limit=5000"
    try:
        r = requests.get(url + query, timeout=15)
        if r.status_code == 200:
            return pd.DataFrame(r.json())
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# 4. INTERFÍCIE PRINCIPAL
cerca_usuari = st.text_input("🔍 Investiga una empresa:", placeholder="Escriu aquí el nom de l'empresa...")

st.divider()

with st.spinner("Actualitzant dades del 2026..."):
    df_any = carregar_dades_2026()

if not df_any.empty:
    # --- DETECTOR DE COLUMNES CLAU ---
    
    # 1. Diners
    col_diners = next((c for c in df_any.columns if "import_adjudicacio_amb_iva" in c), None)
    
    # 2. Enllaç (AQUÍ ESTÀ LA CORRECCIÓ)
    # Busquem la columna correcta (normalment és 'enllac_publicacio')
    col_link = 'enllac_publicacio' if 'enllac_publicacio' in df_any.columns else next((c for c in df_any.columns if "enlla" in c or "url" in c), None)
    
    # 3. Empresa
    col_empresa = None
    for opcio in ['adjudicatari', 'nom_adjudicatari', 'identificacio_adjudicatari']:
        if opcio in df_any.columns:
            col_empresa = opcio
            break

    # --- NETEJA DE L'ENLLAÇ (EL PAS CLAU) ---
    if col_link:
        # Apliquem la funció de neteja a tota la columna per treure els diccionaris
        df_any[col_link] = df_any[col_link].apply(netejar_enllac)

    # --- VISUALITZACIÓ DEL DASHBOARD (TOTAL I GRÀFIC) ---
    if col_diners:
        df_any[col_diners] = pd.to_numeric(df_any[col_diners], errors='coerce').fillna(0)
        total_2026 = df_any[col_diners].sum()
        st.markdown(f"### 💰 Total invertit el 2026: <span style='color:#1E88E5'>{total_2026:,.2f} €</span>", unsafe_allow_html=True)

    if col_empresa and col_diners:
        # Neteja del nom per al gràfic
        df_any['empresa_neta'] = df_any[col_empresa].astype(str).apply(lambda x: x.split('||')[0][:40])
        top5 = df_any.groupby('empresa_neta')[col_diners].sum().reset_index()
        top5 = top5[top5['empresa_neta'] != 'nan'].sort_values(by=col_diners, ascending=False).head(5)
        
        if not top5.empty:
            st.write("🏆 **Top 5 Empreses amb més adjudicacions (2026):**")
            grafic = alt.Chart(top5).mark_bar(color='#1E88E5', cornerRadiusEnd=4).encode(
                x=alt.X(col_diners, title='Euros (€)'),
                y=alt.Y('empresa_neta', sort='-x', title=None),
                tooltip=['empresa_neta', alt.Tooltip(col_diners, format=',.2f')]
            ).properties(height=300)
            st.altair_chart(grafic, use_container_width=True)

    # --- RESULTATS DE LA CERCA AMB ENLLAÇ DIRECTE ---
    if cerca_usuari:
        st.divider()
        mask = df_any.astype(str).apply(lambda x: x.str.contains(cerca_usuari, case=False)).any(axis=1)
        df_res = df_any[mask].copy()
        
        if not df_res.empty:
            st.subheader(f"📂 Contractes trobats per: '{cerca_usuari}'")
            
            # Preparem la taula per ensenyar
            mapa_columnes = {
                'data_adjudicacio_contracte': 'Data',
                'denominacio': 'Títol del Contracte',
                col_empresa: 'Empresa',
                col_diners: 'Import',
                col_link: 'Enllaç Oficial' # Aquesta és la clau
            }
            
            cols_finals = [c for c in mapa_columnes.keys() if c in df_res.columns and c is not None]
            df_display = df_res[cols_finals].rename(columns=mapa_columnes)
            
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Import": st.column_config.NumberColumn(format="%.2f €"),
                    "Data": st.column_config.DateColumn(format="DD/MM/YYYY"),
                    "Enllaç Oficial": st.column_config.LinkColumn(
                        "Documentació", 
                        display_text="Obrir 🔗", 
                        help="Clica per anar a la font oficial"
                    )
                }
            )
        else:
            st.warning("No s'han trobat coincidències.")
else:
    st.error("No s'han pogut carregar les dades. Revisa la connexió.")
