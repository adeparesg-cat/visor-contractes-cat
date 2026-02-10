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
    # Filtrem contractes del 2026 (Límit de 5000 per no saturar)
    query = "?$where=data_adjudicacio_contracte >= '2026-01-01T00:00:00.000'&$limit=5000"
    try:
        r = requests.get(url + query)
        if r.status_code == 200:
            return pd.DataFrame(r.json())
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# 3. INTERFÍCIE
cerca_usuari = st.text_input("🔍 Investiga una empresa o servei:", placeholder="Ex: Indra, Neteja, Sòl...")

st.divider()
with st.spinner("Actualitzant dades del 2026..."):
    df_any = carregar_dades_2026()

if not df_any.empty:
    # --- NETEJA DE COLUMNES ---
    # Busquem la columna de diners
    col_diners = next((c for c in df_any.columns if "import_adjudicacio_amb_iva" in c), None)
    if col_diners:
        df_any[col_diners] = pd.to_numeric(df_any[col_diners], errors='coerce').fillna(0)
        total_2026 = df_any[col_diners].sum()
        st.markdown(f"### 💰 Total invertit el 2026: <span style='color:#1E88E5'>{total_2026:,.2f} €</span>", unsafe_allow_html=True)

    # Busquem la columna de l'empresa (Adjudicatari)
    col_empresa = next((c for c in df_any.columns if "adjudicatari" in c or "nom_adjudicatari" in c), None)

    # --- GENERACIÓ DEL GRÀFIC ---
    if col_empresa and col_diners:
        # Preparem dades pel Top 5
        top5 = df_any.groupby(col_empresa)[col_diners].sum().reset_index()
        top5 = top5[top5[col_empresa] != 'None'] # Traiem valors buits
        top5 = top5.sort_values(by=col_diners, ascending=False).head(5)
        
        if not top5.empty:
            st.write("🏆 **Empreses amb més volum d'adjudicació enguany:**")
            try:
                # Intentem el gràfic bonic (Altair)
                grafic = alt.Chart(top5).mark_bar(color='#1E88E5', cornerRadiusEnd=4).encode(
                    x=alt.X(col_diners, title='Euros (€)'),
                    y=alt.Y(col_empresa, sort='-x', title=None),
                    tooltip=[col_empresa, alt.Tooltip(col_diners, format=',.2f')]
                ).properties(height=300)
                st.altair_chart(grafic, use_container_width=True)
            except:
                # Si falla Altair, pla B: gràfic senzill de Streamlit
                st.bar_chart(data=top5.set_index(col_empresa))
        else:
            st.info("No hi ha prou dades d'adjudicataris per generar el gràfic.")
    else:
        st.warning("No s'ha trobat la columna de l'empresa o de l'import.")

# 4. RESULTATS DE LA CERCA
if cerca_usuari:
    st.divider()
    # Aquí busquem a totes les columnes de la mostra carregada per anar ràpid
    mask = df_any.astype(str).apply(lambda x: x.str.contains(cerca_usuari, case=False)).any(axis=1)
    df_res = df_any[mask]
    
    if not df_res.empty:
        st.subheader(f"📂 Resultats per: '{cerca_usuari}'")
        cols_ok = [c for c in ['data_adjudicacio_contracte', 'denominacio', col_empresa, col_diners] if c in df_res.columns]
        st.dataframe(df_res[cols_ok], use_container_width=True, hide_index=True)
