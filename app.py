import streamlit as st
import pandas as pd
import requests

# --- 1. CONFIGURACIÓ ---
st.set_page_config(page_title="Visor Contractes Públics", page_icon="💶", layout="centered")

st.title("💶 On van els meus impostos?")
st.markdown("""
**Buscador de Contractes Públics de la Generalitat de Catalunya.**
Consulta quants diners públics rep una empresa en temps real.
_Projecte per a l'Open Data Day 2026._
""")

# --- 2. BACKEND (CONNEXIONS) ---

# URL de l'API de Socrata (Generalitat)
ENDPOINT = "https://analisi.transparenciacatalunya.cat/resource/jx2x-848j.json"

# FUNCIÓ 1: Aconseguir la llista d'empreses (PER AL DESPLEGABLE)
@st.cache_data(ttl=3600) # Guardem la llista 1 hora
def carregar_llista_empreses():
    # Descarreguem els últims 3000 contractes per treure els noms de les empreses actives
    query = "?$select=adjudicatari&$limit=3000&$order=data_formalitzaci_del_contracte DESC"
    try:
        resposta = requests.get(ENDPOINT + query)
        df = pd.DataFrame(resposta.json())
        # Netegem: traiem duplicats i ordenem alfabèticament
        llista = df['adjudicatari'].dropna().unique().tolist()
        llista.sort()
        return llista
    except:
        return []

# FUNCIÓ 2: Buscar contractes d'una empresa concreta
@st.cache_data(ttl=600)
def buscar_contractes(nom_empresa):
    # Busquem per text exacte o parcial
    nom_majusc = nom_empresa.upper()
    query = f"?$where=upper(adjudicatari) like '%{nom_majusc}%'&$limit=100&$order=data_formalitzaci_del_contracte DESC"
    
    try:
        resposta = requests.get(ENDPOINT + query)
        if resposta.status_code == 200:
            return pd.DataFrame(resposta.json())
        else:
            return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- 3. FRONTEND (PART VISUAL) ---

st.info("💡 Estem carregant el llistat d'empreses actives de la Generalitat...")
llista_empreses = carregar_llista_empreses()

# CONTENIDOR DE CERCA
with st.container(border=True):
    st.subheader("🔍 Cerca l'empresa")
    
    # OPCIÓ A: DESPLEGABLE (Molt més fàcil)
    # Afegim una opció buida al principi
    opcions = ["Select..."] + llista_empreses
    
    empresa_seleccionada = st.selectbox(
        "Tria una empresa de la llista (pots escriure per buscar):",
        options=opcions,
        index=0
    )
    
    # OPCIÓ B: MANUAL (Per si no surt a la llista)
    st.markdown("---")
    empresa_manual = st.text_input("O escriu el nom manualment (si no la trobes a dalt):", placeholder="Ex: INSTITUT CATALA DEL SOL")

# LÒGICA DE DECISIÓ: Quina empresa busquem?
empresa_final = ""
if empresa_seleccionada != "Select...":
    empresa_final = empresa_seleccionada
elif empresa_manual:
    empresa_final = empresa_manual

# --- 4. RESULTATS ---
if empresa_final:
    st.divider()
    with st.spinner(f"Analitzant dades de: {empresa_final}..."):
        df = buscar_contractes(empresa_final)
        
        if not df.empty and 'import_adjudicaci_amb_iva' in df.columns:
            # Convertim text a números
            df['import_adjudicaci_amb_iva'] = pd.to_numeric(df['import_adjudicaci_amb_iva'], errors='coerce')
            
            total_euros = df['import_adjudicaci_amb_iva'].sum()
            total_contractes = len(df)
            
            # KPIS
            c1, c2 = st.columns(2)
            c1.metric("Total Rebut (Mostra)", f"{total_euros:,.2f} €")
            c2.metric("Contractes Trobats", total_contractes)
            
            # TAULA
            st.dataframe(
                df[['data_formalitzaci_del_contracte', 'objecte_del_contracte', 'import_adjudicaci_amb_iva']].style.format({"import_adjudicaci_amb_iva": "{:,.2f} €"}),
                use_container_width=True
            )
        else:
            st.error(f"❌ No s'han trobat contractes per a: {empresa_final}")
            st.warning("Truc: Si busques 'INCASOL', prova d'escriure 'SOL' o 'INSTITUT' al buscador manual.")

st.caption("Dades: Transparència Catalunya (API Socrata)")
