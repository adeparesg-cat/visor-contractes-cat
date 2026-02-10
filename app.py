import streamlit as st
import pandas as pd
import requests

# --- 1. CONFIGURACIÓ ---
st.set_page_config(page_title="Visor Contractes Públics", page_icon="🔍", layout="centered")

st.title("🔍 Cercador de Contractes Públics")
st.markdown("""
**Busca qualsevol empresa, NIF o concepte.**
_Exemple: Prova de buscar "menjador", "ferrovial" o "institut catala del sol"._
""")

# --- 2. MOTOR DE CERCA INTEL·LIGENT (API Socrata) ---
@st.cache_data(ttl=600)
def buscar_contractes_smart(text_cerca):
    endpoint = "https://analisi.transparenciacatalunya.cat/resource/jx2x-848j.json"
    
    # EL TRUC: Fem servir el paràmetre 'q' (Global Search) en lloc de 'where'.
    # Això busca el text a TOTS els camps i és molt més tolerant amb els accents.
    query = f"?q={text_cerca}&$limit=100"
    
    try:
        resposta = requests.get(endpoint + query)
        if resposta.status_code == 200:
            return pd.DataFrame(resposta.json())
        else:
            return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

# --- 3. INTERFÍCIE (SENSE DESPLEGABLE) ---

# Hem tret el desplegable perquè alentia l'app i donava problemes.
# Ara tenim una barra de cerca potent (com Google).

text_usuari = st.text_input("✍️ Què vols buscar?", placeholder="Escriu aquí el nom de l'empresa o tema...")

if text_usuari:
    with st.spinner(f"Rastrejant dades oficials per: '{text_usuari}'..."):
        df = buscar_contractes_smart(text_usuari)
        
        if not df.empty:
            # Netegem la columna de diners (de vegades ve com a text)
            if 'import_adjudicaci_amb_iva' in df.columns:
                df['import_adjudicaci_amb_iva'] = pd.to_numeric(df['import_adjudicaci_amb_iva'], errors='coerce')
                
                # Càlculs bàsics
                total_euros = df['import_adjudicaci_amb_iva'].sum()
                total_trobats = len(df)
                
                st.success(f"✅ Hem trobat {total_trobats} contractes relacionats!")
                
                # Mètriques
                c1, c2 = st.columns(2)
                c1.metric("Volum Econòmic Trobats", f"{total_euros:,.2f} €")
                c2.metric("Nº de Contractes", total_trobats)
                
                st.divider()
                st.subheader("📋 Detall dels contractes")
                
                # Mostrem una taula neta
                columnes_a_mostrar = ['data_formalitzaci_del_contracte', 'adjudicatari', 'objecte_del_contracte', 'import_adjudicaci_amb_iva']
                
                # Assegurem que les columnes existeixen abans de pintar-les
                cols_finals = [c for c in columnes_a_mostrar if c in df.columns]
                
                st.dataframe(
                    df[cols_finals].style.format({"import_adjudicaci_amb_iva": "{:,.2f} €"}),
                    use_container_width=True
                )
            else:
                st.warning("Hem trobat dades, però falta la columna d'import econòmic.")
                st.write(df)
                
        else:
            st.error(f"❌ No s'ha trobat res per: '{text_usuari}'")
            st.info("Consell: Prova amb una sola paraula clau (ex: 'SÒL' o 'INSTITUT').")

st.divider()
st.caption("Dades: Transparència Catalunya (API Socrata)")
