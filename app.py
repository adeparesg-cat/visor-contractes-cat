import streamlit as st
import pandas as pd
import requests

# --- 1. CONFIGURACIÓ ---
st.set_page_config(page_title="Visor Contractes Públics", page_icon="🔍", layout="wide")

st.title("🔍 Cercador de Contractes Públics (Versió 2026)")
st.markdown("""
Aquesta versió utilitza **cerca fragmentada** per trobar noms amb accents o lletres diferents.
_Exemple: Prova 'Incasol', 'Agbar' o 'Menjador'._
""")

# --- 2. MOTOR DE CERCA ROBUST ---
@st.cache_data(ttl=600)
def buscar_contractes_robust(text_usuari):
    endpoint = "https://analisi.transparenciacatalunya.cat/resource/jx2x-848j.json"
    
    # Netegem el text i el dividim en paraules
    paraules = text_usuari.strip().upper().split()
    if not paraules:
        return pd.DataFrame()

    # Creem una consulta que busqui CADA paraula a l'adjudicatari o a l'objecte
    # Això ignora els accents perquè busquem trossos de paraula
    condicions = []
    for p in paraules:
        condicions.append(f"(upper(adjudicatari) like '%{p}%' or upper(objecte_del_contracte) like '%{p}%')")
    
    where_clause = " AND ".join(condicions)
    query = f"?$where={where_clause}&$limit=100&$order=data_formalitzaci_del_contracte DESC"
    
    try:
        url_final = endpoint + query
        resposta = requests.get(url_final)
        
        if resposta.status_code == 200:
            return pd.DataFrame(resposta.json())
        else:
            st.error(f"Error de l'API: {resposta.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error de connexió: {e}")
        return pd.DataFrame()

# --- 3. INTERFÍCIE ---

text_usuari = st.text_input("✍️ Què vols buscar?", placeholder="Escriu el nom de l'empresa o el servei...")

if text_usuari:
    with st.spinner("Connectant amb el registre de la Generalitat..."):
        df = buscar_contractes_robust(text_usuari)
        
        if not df.empty:
            # Netegem els noms de les columnes per si de cas
            # Columnes clau: 'adjudicatari', 'objecte_del_contracte', 'import_adjudicaci_amb_iva'
            
            if 'import_adjudicaci_amb_iva' in df.columns:
                df['import_adjudicaci_amb_iva'] = pd.to_numeric(df['import_adjudicaci_amb_iva'], errors='coerce')
                
                total_euros = df['import_adjudicaci_amb_iva'].sum()
                
                st.balloons() # Celebrem que hem trobat dades!
                
                c1, c2 = st.columns(2)
                c1.metric("Volum de la mostra", f"{total_euros:,.2f} €")
                c2.metric("Contractes trobats", len(df))
                
                st.subheader("📋 Llistat detallat")
                
                # Columnes que volem mostrar
                cols = ['data_formalitzaci_del_contracte', 'adjudicatari', 'objecte_del_contracte', 'import_adjudicaci_amb_iva']
                cols_reals = [c for c in cols if c in df.columns]
                
                st.dataframe(
                    df[cols_reals].style.format({"import_adjudicaci_amb_iva": "{:,.2f} €"}),
                    use_container_width=True
                )
            else:
                st.warning("Dades trobades, però sense columna d'import. Mostrant dades brutes:")
                st.write(df.head())
        else:
            st.warning("❌ No hem trobat res. Consell: Escriu només una paraula clau (ex: 'SÒL' en lloc de tota l'adreça).")

st.divider()
st.caption("Dades obertes: jx2x-848j (Generalitat de Catalunya)")
