import streamlit as st
import pandas as pd
import requests
import altair as alt

# 1. CONFIGURACIÓ
st.set_page_config(page_title="Monitor 2026", page_icon="📊", layout="wide")

st.title("📊 Monitor de Contractació Pública 2026")
st.markdown("Dades oficials de la Generalitat de Catalunya en temps real (Dataset: ybgg-dgi6).")

# 2. CÀRREGA DE DADES ESTRUCTURAL (EL DASHBOARD)
# Descarreguem TOTS els contractes del 2026 per fer les estadístiques
@st.cache_data(ttl=3600) # Guardem això 1 hora perquè no canvia tant ràpid
def carregar_estadistiques_2026():
    url = "https://analisi.transparenciacatalunya.cat/resource/ybgg-dgi6.json"
    
    # TRUC: Filtrem només els contractes d'aquest any (des de l'1 de gener de 2026)
    # Això fa que l'app vagi ràpid i les dades siguin actuals "del que portem d'any"
    query = "?$where=data_adjudicacio_contracte >= '2026-01-01T00:00:00.000'&$limit=10000"
    
    try:
        r = requests.get(url + query)
        if r.status_code == 200:
            df = pd.DataFrame(r.json())
            # Netegem els diners immediatament
            if 'import_adjudicacio_amb_iva' in df.columns:
                df['import_adjudicacio_amb_iva'] = pd.to_numeric(df['import_adjudicacio_amb_iva'], errors='coerce').fillna(0)
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# 3. FUNCIÓ DE CERCA ESPECÍFICA (Sota demanda)
def cercar_empresa(text):
    url = "https://analisi.transparenciacatalunya.cat/resource/ybgg-dgi6.json"
    # Aquesta cerca només s'activa quan l'usuari escriu
    params = {
        "$q": text,
        "$limit": 50,
        "$order": "data_adjudicacio_contracte DESC"
    }
    try:
        r = requests.get(url, params=params)
        return pd.DataFrame(r.json()) if r.status_code == 200 else pd.DataFrame()
    except:
        return pd.DataFrame()

# --- PART 1: EL CERCADOR (A DALT DE TOT) ---
col_cerca, col_buit = st.columns([2,1])
with col_cerca:
    text_cerca = st.text_input("🔍 Investiga una empresa:", placeholder="Escriu aquí per activar el cercador (Ex: Indra, Securitas, Neteja...)")

# --- PART 2: EL GRÀFIC I EL TOTAL (SEMPRE VISIBLES A SOTA) ---
with st.spinner("Calculant la despesa del 2026..."):
    df_2026 = carregar_estadistiques_2026()

if not df_2026.empty:
    st.divider()
    
    # A. EL TOTAL GASTAT (KPI)
    total_any = df_2026['import_adjudicacio_amb_iva'].sum()
    st.subheader(f"💰 Despesa total en contractes aquest 2026: :blue[{total_any:,.2f} €]")
    
    # B. EL GRÀFIC (TOP 5 EMPRESES)
    # Agrupem per empresa i sumem els diners
    if 'adjudicatari' in df_2026.columns:
        ranking = df_2026.groupby('adjudicatari')['import_adjudicacio_amb_iva'].sum().reset_index()
        ranking = ranking.sort_values(by='import_adjudicacio_amb_iva', ascending=False).head(5)
        
        st.write("🏆 **Top 5 Empreses amb més adjudicacions enguany:**")
        
        # Creem un gràfic de barres bonic amb Altair
        chart = alt.Chart(ranking).mark_bar().encode(
            x=alt.X('import_adjudicacio_amb_
