import streamlit as st
import pandas as pd
import requests
import altair as alt

# 1. CONFIGURACIÓ
st.set_page_config(page_title="Monitor 2026", page_icon="📊", layout="wide")

st.title("📊 Monitor de Contractació Pública 2026")
st.markdown("Dades oficials de la Generalitat de Catalunya (Dataset: ybgg-dgi6).")

# 2. CÀRREGA DE DADES
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

# 3. INTERFÍCIE DE CERCA
cerca_usuari = st.text_input("🔍 Investiga una empresa:", placeholder="Escriu aquí el nom de l'empresa...")

st.divider()
with st.spinner("Actualitzant dades del 2026..."):
    df_any = carregar_dades_2026()

if not df_any.empty:
    # --- DETECTOR DE COLUMNES ---
    col_diners = next((c for c in df_any.columns if "import_adjudicacio_amb_iva" in c), None)
    
    # Busquem la columna de l'enllaç (sol ser 'enlla_publicaci')
    col_link = next((c for c in df_any.columns if "enlla" in c or "url" in c), None)
    
    col_empresa = None
    for opcio in ['adjudicatari', 'nom_adjudicatari', 'identificacio_adjudicatari']:
        if opcio in df_any.columns:
            col_empresa = opcio
            break

    # 1. MOSTRAR EL TOTAL
    if col_diners:
        df_any[col_diners] = pd.to_numeric(df_any[col_diners], errors='coerce').fillna(0)
        total_2026 = df_any[col_diners].sum()
        st.markdown(f"### 💰 Total invertit el 2026: <span style='color:#1E88E5'>{total_2026:,.2f} €</span>", unsafe_allow_html=True)

    # 2. GENERACIÓ DEL GRÀFIC TOP 5
    if col_empresa and col_diners:
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

# 4. RESULTATS DE LA CERCA AMB ENLLAÇ DIRECTE
if cerca_usuari:
    st.divider()
    mask = df_any.astype(str).apply(lambda x: x.str.contains(cerca_usuari, case=False)).any(axis=1)
    df_res = df_any[mask].copy()
    
    if not df_res.empty:
        st.subheader(f"📂 Contractes trobats per: '{cerca_usuari}'")
        
        # Definim quines columnes volem i els noms que veurà l'usuari
        columnes_mostrar = {
            'data_adjudicacio_contracte': 'Data',
            'denominacio': 'Títol del Contracte',
            col_empresa: 'Empresa',
            col_diners: 'Import',
            col_link: 'Enllaç Oficial'
        }
        
        # Filtrem i canviem noms
        res_display = df_res[[c for c in columnes_mostrar.keys() if c in df_res.columns]].copy()
        res_display = res_display.rename(columns=columnes_mostrar)
        
        # Mostrem la taula amb configuració especial per a l'enllaç
        st.dataframe(
            res_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Import": st.column_config.NumberColumn(format="%.2f €"),
                "Enllaç Oficial": st.column_config.LinkColumn("Veure Contracte", display_text="Obrir 🔗"),
                "Data": st.column_config.DateColumn(format="DD/MM/YYYY")
            }
        )
    else:
        st.warning("No s'han trobat coincidències.")
