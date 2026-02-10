import streamlit as st
import pandas as pd
import requests
import altair as alt

# 1. CONFIGURACIÓ
st.set_page_config(page_title="Monitor 2026", page_icon="📊", layout="wide")

st.title("📊 Monitor de Contractació Pública 2026")
st.markdown("Dades oficials de la Generalitat de Catalunya (Dataset: ybgg-dgi6).")

# Variables per facilitar canvis de columnes
COL_DINERS = 'import_adjudicacio_amb_iva'
COL_EMPRESA = 'adjudicatari'
COL_DATA = 'data_adjudicacio_contracte'

# 2. CÀRREGA DE DADES PER AL DASHBOARD (SENSE CERCA)
@st.cache_data(ttl=3600)
def carregar_dades_2026():
    url = "https://analisi.transparenciacatalunya.cat/resource/ybgg-dgi6.json"
    # Filtrem contractes des de l'1 de gener de 2026
    query = f"?$where={COL_DATA} >= '2026-01-01T00:00:00.000'&$limit=5000"
    
    try:
        r = requests.get(url + query)
        if r.status_code == 200:
            df = pd.DataFrame(r.json())
            if COL_DINERS in df.columns:
                df[COL_DINERS] = pd.to_numeric(df[COL_DINERS], errors='coerce').fillna(0)
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# 3. FUNCIÓ PER A LA CERCA ESPECÍFICA
def cercar_empresa_api(text):
    url = "https://analisi.transparenciacatalunya.cat/resource/ybgg-dgi6.json"
    params = {"$q": text, "$limit": 100}
    try:
        r = requests.get(url, params=params)
        return pd.DataFrame(r.json()) if r.status_code == 200 else pd.DataFrame()
    except:
        return pd.DataFrame()

# --- INTERFÍCIE ---

# A. CERCADOR (A dalt, però no busca res fins que s'escriu)
cerca_usuari = st.text_input("🔍 Investiga una empresa o servei:", placeholder="Escriu aquí (Ex: Indra, Neteja, Sòl...)")

# B. DASHBOARD GENERAL (Sempre visible a sota)
st.divider()
with st.spinner("Actualitzant dades del 2026..."):
    df_any = carregar_dades_2026()

if not df_any.empty:
    # 1. TOTAL GASTAT
    total_2026 = df_any[COL_DINERS].sum()
    st.markdown(f"### 💰 Total invertit a Catalunya el 2026: <span style='color:#1E88E5'>{total_2026:,.2f} €</span>", unsafe_allow_html=True)
    
    # 2. GRÀFIC TOP 5
    if COL_EMPRESA in df_any.columns:
        top5 = df_any.groupby(COL_EMPRESA)[COL_DINERS].sum().reset_index()
        top5 = top5.sort_values(by=COL_DINERS, ascending=False).head(5)
        
        st.write("🏆 **Empreses amb més volum d'adjudicació enguany:**")
        
        grafic = alt.Chart(top5).mark_bar(cornerRadiusEnd=4).encode(
            x=alt.X(f'{COL_DINERS}:Q', title='Euros (€)'),
            y=alt.Y(f'{COL_EMPRESA}:N', sort='-x', title=None),
            tooltip=[COL_EMPRESA, alt.Tooltip(COL_DINERS, format=',.2f')]
        ).properties(height=300)
        
        st.altair_chart(grafic, use_container_width=True)

# C. RESULTATS DE LA CERCA (S'activa només si l'usuari posa un nom)
if cerca_usuari:
    st.divider()
    st.subheader(f"📂 Resultats de la cerca: '{cerca_usuari}'")
    
    with st.spinner("Rastrejant contractes específics..."):
        df_res = cercar_empresa_api(cerca_usuari)
        
        if not df_res.empty:
            if COL_DINERS in df_res.columns:
                df_res[COL_DINERS] = pd.to_numeric(df_res[COL_DINERS], errors='coerce')
            
            # Columnes que volem ensenyar
            cols_ok = [c for c in [COL_DATA, 'denominacio', COL_EMPRESA, COL_DINERS] if c in df_res.columns]
            
            st.dataframe(
                df_res[cols_ok],
                use_container_width=True,
                hide_index=True,
                column_config={COL_DINERS: st.column_config.NumberColumn("Import", format="%.2f €")}
            )
        else:
            st.info("No s'han trobat contractes per aquesta cerca.")
