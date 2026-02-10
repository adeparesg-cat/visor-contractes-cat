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
    # --- NETEJA DE COLUMNES INTEL·LIGENT ---
    # Identifiquem les columnes correctes
    col_diners = 'import_adjudicacio_amb_iva'
    # PRIORITAT: Busquem el camp del NOM, no el de l'ID (NIF)
    col_empresa = 'nom_adjudicatari' if 'nom_adjudicatari' in df_any.columns else 'adjudicatari'
    
    # Convertim diners a números
    df_any[col_diners] = pd.to_numeric(df_any[col_diners], errors='coerce').fillna(0)
    
    # 1. TOTAL GASTAT
    total_2026 = df_any[col_diners].sum()
    st.markdown(f"### 💰 Total invertit el 2026: <span style='color:#1E88E5'>{total_2026:,.2f} €</span>", unsafe_allow_html=True)

    # 2. GRÀFIC TOP 5 (AMB NOMS NETS)
    if col_empresa in df_any.columns:
        # Agrupem i sumem
        top5 = df_any.groupby(col_empresa)[col_diners].sum().reset_index()
        
        # EL TRUC: Filtrem noms que semblen codis (més de 30 caràcters o que contenen ||)
        # Això farà que el gràfic sigui MOLT més net
        top5 = top5[~top5[col_empresa].str.contains(r'\|\|', na=False)]
        top5 = top5[top5[col_empresa].str.len() < 60] # Retallem noms gegants
        
        top5 = top5.sort_values(by=col_diners, ascending=False).head(5)
        
        if not top5.empty:
            st.write("🏆 **Empreses amb més volum d'adjudicació enguany (Noms Verificats):**")
            
            grafic = alt.Chart(top5).mark_bar(color='#1E88E5', cornerRadiusEnd=4).encode(
                x=alt.X(col_diners, title='Euros (€)'),
                y=alt.Y(col_empresa, sort='-x', title=None),
                tooltip=[col_empresa, alt.Tooltip(col_diners, format=',.2f')]
            ).properties(height=300)
            
            st.altair_chart(grafic, use_container_width=True)
        else:
            st.info("Calculant rànquing d'empreses...")

# 4. RESULTATS DE LA CERCA (NOMÉS SI L'USUARI ESCRIU)
if cerca_usuari:
    st.divider()
    mask = df_any.astype(str).apply(lambda x: x.str.contains(cerca_usuari, case=False)).any(axis=1)
    df_res = df_any[mask].copy()
    
    if not df_res.empty:
        st.subheader(f"📂 Resultats per: '{cerca_usuari}'")
        # Mostrem les columnes que el ciutadà entén
        cols_vides = ['data_adjudicacio_contracte', 'denominacio', col_empresa, col_diners]
        cols_final = [c for c in cols_vides if c in df_res.columns]
        
        st.dataframe(
            df_res[cols_final].sort_values(by=col_diners, ascending=False), 
            use_container_width=True, 
            hide_index=True,
            column_config={col_diners: st.column_config.NumberColumn("Import Adjudicat", format="%.2f €")}
        )
    else:
        st.warning("No s'ha trobat cap contracte per aquesta cerca.")
