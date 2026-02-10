import streamlit as st
import pandas as pd
import requests

# 1. CONFIGURACIÓ DE LA PÀGINA
st.set_page_config(page_title="Monitor de Contractes", page_icon="💰", layout="wide")

st.title("💰 Monitor de Contractes Públics")
st.markdown("Cerca en temps real al registre oficial de la Generalitat de Catalunya.")

# 2. CONFIGURACIÓ DE LA BASE DE DADES
# Aquesta és l'adreça oficial (ID: jx2x-848j)
ENDPOINT = "https://analisi.transparenciacatalunya.cat/resource/jx2x-848j.json"

def cercar_dades(text):
    # Preparem la consulta de forma segura
    # Busquem el text a la columna 'adjudicatari' (l'empresa)
    filtre = f"upper(adjudicatari) like '%{text.upper()}%' or upper(objecte_del_contracte) like '%{text.upper()}%'"
    
    parametres = {
        "$where": filtre,
        "$limit": 50,
        "$order": "data_formalitzaci_del_contracte DESC"
    }
    
    try:
        # Fem la petició passant els paràmetres per separat (això evita el 404)
        resposta = requests.get(ENDPOINT, params=parametres)
        
        if resposta.status_code == 200:
            return pd.DataFrame(resposta.json())
        else:
            st.error(f"Error de la Generalitat: {resposta.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error de connexió: {e}")
        return pd.DataFrame()

# 3. INTERFÍCIE D'USUARI
cerca = st.text_input("🔍 Escriu el nom de l'empresa o concepte:", placeholder="Ex: Incasol, Telefonica, Menjador...")

if cerca:
    with st.spinner('Buscant dades oficials...'):
        df = cercar_dades(cerca)
        
        if not df.empty:
            st.balloons()
            
            # Netegem la columna de diners
            if 'import_adjudicaci_amb_iva' in df.columns:
                df['import_adjudicaci_amb_iva'] = pd.to_numeric(df['import_adjudicaci_amb_iva'], errors='coerce')
                total = df['import_adjudicaci_amb_iva'].sum()
                
                # Resum
                st.metric("Total adjudicat en aquesta cerca", f"{total:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
                
                # Taula neta
                cols_interessants = ['data_formalitzaci_del_contracte', 'adjudicatari', 'objecte_del_contracte', 'import_adjudicaci_amb_iva']
                existing_cols = [c for c in cols_interessants if c in df.columns]
                
                st.dataframe(df[existing_cols], use_container_width=True)
            else:
                st.write("Dades trobades:", df)
        else:
            st.warning("⚠️ No s'ha trobat res. Prova amb una sola paraula (ex: en lloc de 'Institut Catala del Sol' posa només 'SOL').")

st.divider()
st.caption("Font: analisi.transparenciacatalunya.cat (Dataset jx2x-848j)")
