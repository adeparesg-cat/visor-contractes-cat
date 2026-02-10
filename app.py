import streamlit as st
import pandas as pd
import requests

# 1. CONFIGURACIÓ
st.set_page_config(page_title="Visor Contractes 2026", page_icon="🏦", layout="wide")

st.title("🏦 Visor de Contractes de la Generalitat")
st.markdown("Dades oficials connectades en temps real amb el Portal de Dades Obertes.")

# 2. PROVA DE CONNEXIÓ (El truc per evitar el 404)
# Provarem la nova adreça oficial de la Generalitat
ENDPOINT = "https://dadesobertes.gencat.cat/resource/jx2x-848j.json"

@st.cache_data(ttl=600)
def provar_connexio():
    try:
        # Intentem baixar només 1 fila per saber si la porta està oberta
        r = requests.get(f"{ENDPOINT}?$limit=1")
        return r.status_code == 200
    except:
        return False

if not provar_connexio():
    st.error("🚨 Atenció: El servidor de dades de la Generalitat no respon o ha canviat d'adreça.")
    st.info("Estem provant d'utilitzar l'adreça alternativa...")
    ENDPOINT = "https://analisi.transparenciacatalunya.cat/resource/jx2x-848j.json"

# 3. MOTOR DE CERCA MILLORAT
def buscar_contractes(text):
    # La clau és buscar a la columna 'adjudicatari' de forma neta
    text_net = text.strip().upper()
    
    # Utilitzem 'starts_with' o 'like' però més senzill
    parametres = {
        "$where": f"upper(adjudicatari) like '%{text_net}%' or upper(objecte_del_contracte) like '%{text_net}%'",
        "$limit": 100,
        "$order": "data_formalitzaci_del_contracte DESC"
    }
    
    try:
        resposta = requests.get(ENDPOINT, params=parametres)
        if resposta.status_code == 200:
            return pd.DataFrame(resposta.json())
        else:
            # Si falla, intentem una cerca global sense filtres complexos (més lenta però segura)
            r_global = requests.get(f"{ENDPOINT}?q={text_net}&$limit=50")
            return pd.DataFrame(r_global.json())
    except:
        return pd.DataFrame()

# 4. INTERFÍCIE
cerca = st.text_input("🔍 Escriu el nom d'una empresa (Ex: INCASOL, TELEFONICA, SEAT):")

if cerca:
    with st.spinner('Connectant amb la Generalitat...'):
        df = buscar_contractes(cerca)
        
        if not df.empty:
            st.balloons()
            
            # Netegem la columna d'euros
            if 'import_adjudicaci_amb_iva' in df.columns:
                df['import_adjudicaci_amb_iva'] = pd.to_numeric(df['import_adjudicaci_amb_iva'], errors='coerce')
                total = df['import_adjudicaci_amb_iva'].sum()
                st.metric("Total adjudicat trobat", f"{total:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
            
            # Mostrem la taula
            cols_ok = [c for c in ['data_formalitzaci_del_contracte', 'adjudicatari', 'objecte_del_contracte', 'import_adjudicaci_amb_iva'] if c in df.columns]
            st.dataframe(df[cols_ok], use_container_width=True)
        else:
            st.warning("⚠️ No hem trobat resultats. Prova amb una paraula més curta (ex: 'SOL' en lloc de 'INCASOL').")

st.divider()
st.caption("Font de dades: jx2x-848j (Registre Públic de Contractes de Catalunya)")
