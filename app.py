import streamlit as st
import pandas as pd
import requests

# --- 1. CONFIGURACIÓ DE LA PÀGINA ---
st.set_page_config(
    page_title="Visor de Contractes Públics",
    page_icon="💶",
    layout="centered"
)

# Títol i explicació
st.title("💶 On van els meus impostos?")
st.markdown("""
**Buscador de Contractes Públics de la Generalitat de Catalunya.**
Aquesta eina permet consultar en temps real quants diners públics ha rebut una empresa.
_Projecte ciutadà per a l'Open Data Day 2026._
""")

# --- 2. EL MOTOR (BACKEND) ---
# Aquesta funció connecta amb l'API de la Generalitat
@st.cache_data(ttl=600) # Guardem memòria 10 minuts perquè vagi ràpid
def buscar_contractes(nom_empresa):
    # L'API de Dades Obertes (Socrata)
    endpoint = "https://analisi.transparenciacatalunya.cat/resource/jx2x-848j.json"
    
    # Truc tècnic: Filtrem abans de descarregar per no saturar la web
    # Busquem empreses que continguin el text (majúscules)
    nom_majusc = nom_empresa.upper()
    query = f"?$where=upper(adjudicatari) like '%{nom_majusc}%'&$limit=100&$order=data_formalitzaci_del_contracte DESC"
    
    try:
        resposta = requests.get(endpoint + query)
        if resposta.status_code == 200:
            dades = pd.DataFrame(resposta.json())
            return dades
        else:
            return pd.DataFrame() # Retornem buit si hi ha error
    except:
        return pd.DataFrame()

# --- 3. LA INTERFÍCIE (FRONTEND) ---

# Barra de cerca
empresa = st.text_input("🔍 Escriu el nom d'una empresa:", placeholder="Exemple: INDRA, FERROVIAL, CLECE...")

if empresa:
    with st.spinner(f"Buscant contractes de '{empresa}'..."):
        df = buscar_contractes(empresa)
        
        if not df.empty and 'import_adjudicaci_amb_iva' in df.columns:
            # Neteja de dades: Convertim el text a números
            df['import_adjudicaci_amb_iva'] = pd.to_numeric(df['import_adjudicaci_amb_iva'], errors='coerce')
            
            # Càlculs
            total_euros = df['import_adjudicaci_amb_iva'].sum()
            total_contractes = len(df)
            
            st.divider()
            
            # 3 TARGETES RESUM (KPIS)
            col1, col2 = st.columns(2)
            col1.metric("💰 Total Adjudicat (Muestra)", f"{total_euros:,.2f} €")
            col2.metric("📄 Contractes Trobats", total_contractes)
            
            # TAULA DE DADES
            st.subheader("Detall dels últims contractes:")
            
            # Seleccionem només les columnes interessants
            columnes_visibles = ['data_formalitzaci_del_contracte', 'objecte_del_contracte', 'import_adjudicaci_amb_iva', 'departament_ens_adjudicador']
            
            # Si alguna columna no existeix al fitxer original, no petarà
            cols_finals = [c for c in columnes_visibles if c in df.columns]
            
            st.dataframe(
                df[cols_finals].style.format({"import_adjudicaci_amb_iva": "{:,.2f} €"}),
                use_container_width=True
            )
            
            st.info("Nota: Es mostren els últims 100 contractes disponibles a l'API pública.")
            
        else:
            st.warning(f"⚠️ No s'han trobat contractes per a '{empresa}' o l'empresa no apareix amb aquest nom exacte.")
            st.caption("Prova amb una part del nom (ex: 'AGBAR' en lloc de 'Sociedad General de Aguas...').")

st.divider()
st.caption("Dades oficials de: analisi.transparenciacatalunya.cat | API ID: jx2x-848j")
