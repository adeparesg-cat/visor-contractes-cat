import streamlit as st
import pandas as pd
import requests

# 1. CONFIGURACIÓ DE PÀGINA
st.set_page_config(page_title="Visor Contractes Públics", page_icon="💶", layout="wide")

st.title("💶 Visor de Contractes Públics de Catalunya")
st.markdown("""
**Buscador Oficial:** Descobreix quines empreses reben contractes públics i per quin import.
_Dades en temps real del portal de Transparència (Dataset: ybgg-dgi6)._
""")

# 2. CÀRREGA DE DADES (Optimitzada)
@st.cache_data(ttl=600)
def carregar_dades():
    # URL del dataset bo que has trobat
    url = "https://analisi.transparenciacatalunya.cat/resource/ybgg-dgi6.json"
    
    # Descarreguem els últims 5.000 contractes per tenir una bona base
    params = {
        "$limit": 5000,
        "$order": "data_publicacio DESC"
    }
    
    try:
        r = requests.get(url, params=params)
        if r.status_code == 200:
            return pd.DataFrame(r.json())
        else:
            return pd.DataFrame()
    except:
        return pd.DataFrame()

# Carreguem dades amb spinner
with st.spinner("Connectant amb el registre oficial de contractes..."):
    df = carregar_dades()

# 3. NETEJA I PREPARACIÓ DE COLUMNES
if not df.empty:
    # Seleccionem només les columnes que ens interessen i les renombrem si existeixen
    # Aquestes són les columnes típiques d'aquest dataset
    columnes_clau = {
        'data_publicacio': 'DATA',
        'ambit': 'ORGANISME (QUI PAGA)',
        'denominacio': 'OBJECTE DEL CONTRACTE',
        'adjudicatari': 'EMPRESA GUANYADORA',
        'import_adjudicacio_amb_iva': 'IMPORT (€)'
    }
    
    # Filtrem només les que realment existeixen al fitxer descarregat
    columnes_existents = {k: v for k, v in columnes_clau.items() if k in df.columns}
    
    # Creem un nou DataFrame només amb aquestes columnes i els canviem el nom
    df_net = df[columnes_existents.keys()].rename(columns=columnes_existents)
    
    # Convertim la columna de diners a números per poder sumar
    if 'IMPORT (€)' in df_net.columns:
        df_net['IMPORT (€)'] = pd.to_numeric(df_net['IMPORT (€)'], errors='coerce').fillna(0)

    # 4. EL BUSCADOR
    st.success(f"✅ Dades actualitzades: {len(df_net)} contractes analitzats.")
    
    text_cerca = st.text_input("🔍 Cerca per EMPRESA o per CONCEPTE:", placeholder="Ex: Ferrovial, Neteja, Sòl, Indra...")
    
    if text_cerca:
        # Filtre intel·ligent: Busca el text a TOTA la taula (ignorant majúscules/minúscules)
        filtre = df_net.astype(str).apply(lambda x: x.str.contains(text_cerca, case=False)).any(axis=1)
        df_resultat = df_net[filtre]
        
        if not df_resultat.empty:
            # MÈTRIQUES (KPIS)
            total_diners = df_resultat['IMPORT (€)'].sum()
            
            c1, c2 = st.columns(2)
            c1.metric("Contractes Trobats", len(df_resultat))
            c2.metric("Volum Econòmic Total", f"{total_diners:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
            
            st.divider()
            st.subheader("📋 Detall dels contractes")
            
            # Mostrem la taula maca i ordenada per data
            st.dataframe(
                df_resultat.sort_values(by="DATA", ascending=False),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "IMPORT (€)": st.column_config.NumberColumn(format="%.2f €"),
                    "DATA": st.column_config.DateColumn(format="DD/MM/YYYY")
                }
            )
        else:
            st.warning(f"No s'ha trobat cap contracte amb la paraula '{text_cerca}'.")
    else:
        st.info("👆 Escriu el nom d'una empresa per veure quants diners públics rep.")
        # Mostrem els 5 últims contractes d'exemple
        st.write("Últims contractes públics signats a Catalunya:")
        st.dataframe(df_net.head(5), use_container_width=True, hide_index=True)

else:
    st.error("Error de connexió. Torna-ho a provar en uns minuts.")
