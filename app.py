import streamlit as st
import pandas as pd
import requests

# 1. CONFIGURACIÓ
st.set_page_config(page_title="Visor 360º Contractes", page_icon="🌍", layout="wide")

st.title("🌍 Visor 360º de Contractes Públics")
st.markdown("""
**Buscador Universal:** Cerca per empresa, per organisme públic o per concepte.
_Exemple: Escriu 'Incasol' per veure què contracten, o 'Neteja' per veure serveis._
""")

# 2. DESCÀRREGA DE DADES MASSIVA (ÚLTIMS 1000 CONTRACTES)
@st.cache_data(ttl=600)
def carregar_dades_recents():
    # URL oficial (jx2x-848j)
    endpoint = "https://analisi.transparenciacatalunya.cat/resource/jx2x-848j.json"
    
    # Descarreguem els últims 1000 sense filtres (per tenir-ho tot)
    query = "?$limit=1000&$order=data_formalitzaci_del_contracte DESC"
    
    try:
        data = pd.read_json(endpoint + query)
        return data
    except Exception as e:
        st.error(f"Error carregant dades: {e}")
        return pd.DataFrame()

# Carreguem les dades només entrar (així va super ràpid després)
with st.spinner("Carregant els últims 1.000 contractes de la Generalitat..."):
    df_mestre = carregar_dades_recents()

# 3. INTERFÍCIE DE CERCA
if not df_mestre.empty:
    st.success(f"✅ Dades connectades: Tenim {len(df_mestre)} contractes frescos a la memòria.")
    
    # Text de cerca
    text_usuari = st.text_input("🔍 Què vols trobar?", placeholder="Ex: Incasol, Sòl, Menjador, Seguretat...")

    if text_usuari:
        # --- FILTRE UNIVERSAL (MÀGIA PYTHON) ---
        # Aquesta línia busca el text a QUALSEVOL columna de la taula
        # Ignora majúscules/minúscules (case=False)
        filtre = df_mestre.apply(lambda row: row.astype(str).str.contains(text_usuari, case=False).any(), axis=1)
        df_resultat = df_mestre[filtre]
        
        # 4. RESULTATS
        if not df_resultat.empty:
            # Netegem columna diners
            if 'import_adjudicaci_amb_iva' in df_resultat.columns:
                df_resultat['import_adjudicaci_amb_iva'] = pd.to_numeric(df_resultat['import_adjudicaci_amb_iva'], errors='coerce')
                total = df_resultat['import_adjudicaci_amb_iva'].sum()
                
                # Mètriques
                c1, c2, c3 = st.columns(3)
                c1.metric("Contractes trobats", len(df_resultat))
                c2.metric("Volum total", f"{total:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
                # Dada curiosa: Qui és l'organisme que més surt?
                top_organisme = df_resultat['departament_ens_adjudicador'].mode()[0] if 'departament_ens_adjudicador' in df_resultat.columns else "Desconegut"
                c3.metric("Organisme principal", top_organisme)

            st.divider()
            st.subheader(f"Resultats per: '{text_usuari}'")
            
            # Mostrem les columnes clau
            cols_clau = ['data_formalitzaci_del_contracte', 'departament_ens_adjudicador', 'adjudicatari', 'objecte_del_contracte', 'import_adjudicaci_amb_iva']
            cols_finals = [c for c in cols_clau if c in df_resultat.columns]
            
            st.dataframe(
                df_resultat[cols_finals].style.format({"import_adjudicaci_amb_iva": "{:,.2f} €"}),
                use_container_width=True
            )
        else:
            st.warning(f"⚠️ No hem trobat '{text_usuari}' entre els últims 1.000 contractes.")
            st.info("Prova amb una paraula més genèrica.")

    else:
        # Si no busques res, mostrem els últims 5 per fer bonic
        st.info("👆 Escriu alguna cosa per començar. Aquí tens els 5 últims contractes signats a Catalunya:")
        st.dataframe(df_mestre.head(5), use_container_width=True)

else:
    st.error("No s'han pogut carregar les dades. Revisa la connexió a internet.")

st.caption("Dades: Transparència Catalunya (API Socrata)")
