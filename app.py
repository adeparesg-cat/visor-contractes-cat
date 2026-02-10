import streamlit as st
import pandas as pd
import requests

# 1. CONFIGURACIÓ
st.set_page_config(page_title="Visor Contractes 2026", page_icon="💶", layout="wide")

st.title("💶 Visor de Contractes Públics")
st.markdown(f"Connectat al dataset oficial: **ybgg-dgi6** (Generalitat de Catalunya)")

# 2. CONNEXIÓ AMB LA TEVA TROBALLA
DATASET_ID = "ybgg-dgi6"
ENDPOINT = f"https://analisi.transparenciacatalunya.cat/resource/{DATASET_ID}.json"

@st.cache_data(ttl=600)
def carregar_dades():
    # Descarreguem els últims 2.000 contractes per tenir una bona mostra
    # Ordenem per data de publicació descendent (si existeix)
    query = "?$limit=2000"
    
    try:
        response = requests.get(ENDPOINT + query)
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            return df
        else:
            st.error(f"Error {response.status_code} connectant amb l'API.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error de connexió: {e}")
        return pd.DataFrame()

# 3. CÀRREGA I AUTO-DIAGNÒSTIC
with st.spinner("Descarregant el dataset que has trobat..."):
    df = carregar_dades()

if not df.empty:
    # --- AUTO-DETECTOR DE COLUMNES ---
    # La Generalitat canvia els noms sovint. Aquest bloc busca la columna correcta automàticament.
    
    # 1. Busquem la columna de l'Empresa (Adjudicatari)
    col_empresa = next((c for c in df.columns if "adjudicatari" in c.lower() or "denominaci" in c.lower()), None)
    
    # 2. Busquem la columna dels Diners (Import)
    col_diners = next((c for c in df.columns if "import" in c.lower() and "iva" in c.lower()), None)
    if not col_diners: col_diners = next((c for c in df.columns if "import" in c.lower()), None) # Segon intent

    # 3. Busquem la columna del Concepte (Objecte)
    col_concepte = next((c for c in df.columns if "objecte" in c.lower() or "descripci" in c.lower()), None)
    
    # 4. Busquem la Data
    col_data = next((c for c in df.columns if "data" in c.lower()), None)

    # --- INTERFÍCIE ---
    
    if col_empresa and col_diners:
        st.success(f"✅ Dades carregades correctament! Analitzant {len(df)} contractes.")
        
        # BUSCADOR
        busqueda = st.text_input("🔍 Cerca (Empresa o Concepte):", placeholder="Ex: Incasol, Neteja, Sòl...")
        
        if busqueda:
            # Filtre intel·ligent (ignora majúscules/minúscules i accents)
            mask = df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False, na=False)).any(axis=1)
            df_filtrat = df[mask]
            
            if not df_filtrat.empty:
                # Neteja de diners (convertir text a números)
                df_filtrat[col_diners] = pd.to_numeric(df_filtrat[col_diners], errors='coerce')
                total = df_filtrat[col_diners].sum()
                
                # Resultats
                c1, c2 = st.columns(2)
                c1.metric("Contractes Trobats", len(df_filtrat))
                c1.metric("Volum Econòmic", f"{total:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
                
                st.subheader("📝 Detall dels contractes")
                
                # Taula neta
                cols_finals = [c for c in [col_data, col_empresa, col_concepte, col_diners] if c is not None]
                st.dataframe(df_filtrat[cols_finals], use_container_width=True)
            else:
                st.warning(f"No s'ha trobat res per '{busqueda}'.")
        else:
            st.info("👆 Escriu alguna cosa per començar a investigar.")
            st.write("Exemple de dades recents:", df[[col_empresa, col_diners]].head())
            
    else:
        st.warning("⚠️ Hem connectat, però els noms de les columnes són estranys.")
        st.write("Columnes trobades:", df.columns.tolist())
else:
    st.error("No s'han pogut carregar dades. Revisa si l'ID 'ybgg-dgi6' correspon a un dataset públic actiu.")
