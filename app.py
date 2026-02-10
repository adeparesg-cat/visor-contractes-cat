import streamlit as st
import pandas as pd
import requests
import altair as alt
import streamlit.components.v1 as components # Necessari per fer l'auto-scroll

# 1. CONFIGURACIÓ
st.set_page_config(page_title="Monitor 2026", page_icon="📊", layout="wide")

st.title("📊 Monitor de Contractació Pública 2026")
st.markdown("Dades oficials de la Generalitat de Catalunya (Dataset: ybgg-dgi6).")

# 2. FUNCIÓ PER NETEJAR ENLLAÇOS
def netejar_enllac(valor):
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
cerca_usuari = st.text_input("🔍 Investiga una empresa:", placeholder="Escriu i prem Enter (Ex: Indra, Clece, Neteja...)")

st.divider()

with st.spinner("Actualitzant dades del 2026..."):
    df_any = carregar_dades_2026()

if not df_any.empty:
    # --- DETECTOR DE COLUMNES CLAU ---
    col_diners = next((c for c in df_any.columns if "import_adjudicacio_amb_iva" in c), None)
    
    # En
