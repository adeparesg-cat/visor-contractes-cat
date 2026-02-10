import streamlit as st
import pandas as pd
import requests
import altair as alt
import streamlit.components.v1 as components

# 1. CONFIGURACIÓ DE LA PÀGINA
st.set_page_config(page_title="Monitor Contractes 2026", page_icon="📊", layout="wide")

st.title("📊 Monitor de Contractació Pública 2026")
st.markdown("Dades oficials de la Generalitat de Catalunya (Dataset: **ybgg-dgi6**)")

# 2. FUNCIONS DE SUPORT
def netejar_enllac(valor):
    if isinstance(valor, dict):
        return valor.get('url', '')
    return str(valor) if pd.notna(valor) else ''

@st.cache_data(ttl=3600)
def carregar_dades_2026():
    url = "https://analisi.transparenciacatalunya.cat/resource/ybgg-dgi6.json"
    query = "?$where=data_adjudicacio_contracte >= '2026-01-01T00:00:00.000'&$limit=5000"
    try:
        r = requests.get(url + query, timeout=15)
        if r.status_code == 200:
            return pd.DataFrame(r.json())
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# 3. INTERFÍCIE DE CERCA
cerca_usuari = st.text_input("🔍 Cerca per NOM D'EMPRESA:", placeholder="Escriu i prem Enter...")

st.divider()

with st.spinner("Actualitzant dades del 2026..."):
    df_any = carregar_dades_2026()

if not df_any.empty:
    # --- CONFIGURACIÓ DE COLUMNES ---
    COL_DINERS = 'import_adjudicacio_amb_iva'
    COL_EMPRESA = 'denominacio_adjudicatari'
    COL_LINK = 'enllac_publicacio'
    
    if COL_LINK in df_any.columns:
        df_any[COL_LINK] = df_any[COL_LINK].apply(netejar_enllac)
    
    if COL_DINERS in df_any.columns:
        df_any[COL_DINERS] = pd.to_numeric(df_any[COL_DINERS], errors='coerce').fillna(0)

    # --- DASHBOARD GENERAL ---
    total_2026 = df_any[COL_DINERS].sum()
    st.markdown(f"### 💰 Total invertit el 2026: <span style='color:#1E88E5'>{total_2026:,.2f} €</span>", unsafe_allow_html=True)

    if COL_EMPRESA in df_any.columns:
        df_any['empresa_grafic'] = df_any[COL_EMPRESA].astype(str).apply(lambda x: x.split('||')[0][:50])
        top5 = df_any.groupby('empresa_grafic')[COL_DINERS].sum().reset_index()
        top5 = top5[top5['empresa_grafic'] != 'nan'].sort_values(by=COL_DINERS, ascending=False).head(5)
        
        if not top5.empty:
            st.write("🏆 **Top 5 Empreses amb més adjudicacions (2026):**")
            grafic = alt.Chart(top5).mark_bar(color='#1E88E5', cornerRadiusEnd=4).encode(
                x=alt.X(COL_DINERS, title='Euros (€)'),
                y=alt.Y('empresa_grafic', sort='-x', title=None),
                tooltip=['empresa_grafic', alt.Tooltip(COL_DINERS, format=',.2f')]
            ).properties(height=300)
            st.altair_chart(grafic, use_container_width=True)

    # --- LÒGICA DE CERCA (NOMÉS EMPRESA) ---
    if cerca_usuari:
        # 1. Filtre estricte per columna empresa
        mask = df_any[COL_EMPRESA].astype(str).str.contains(cerca_usuari, case=False, na=False)
        df_res = df_any[mask].copy()

        # Marcatge per a l'scroll
        st.markdown('<div id="resultats_ancora"></div>', unsafe_allow_html=True)
        st.divider()

        if not df_res.empty:
            # 2. Comptador de resultats
            st.success(f"✅ S'han trobat **{len(df_res)}** contractes per a l'empresa: *'{cerca_usuari}'*")
            
            mapa_cols = {
                'data_adjudicacio_contracte': 'Data',
                'denominacio': 'Títol del Contracte',
                COL_EMPRESA: 'Empresa',
                COL_DINERS: 'Import',
                COL_LINK: 'Enllaç'
            }
            
            cols_finals = [c for c in mapa_cols.keys() if c in df_res.columns]
            df_display = df_res[cols_finals].rename(columns=mapa_cols)
            
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Import": st.column_config.NumberColumn(format="%.2f €"),
                    "Data": st.column_config.DateColumn(format="DD/MM/YYYY"),
                    "Enllaç": st.column_config.LinkColumn("Fitxa", display_text="Obrir 🔗")
                }
            )

            # 3. JavaScript Robust per al Scroll
            js_scroll = """
            <script>
                function doScroll() {
                    const selectors = [
                        '.main', 
                        'section.main', 
                        'div[data-testid="stAppViewContainer"]'
                    ];
                    
                    // Intentem trobar el contenidor principal de Streamlit
                    let container = null;
                    for (const s of selectors) {
                        const el = window.parent.document.querySelector(s);
                        if (el) { container = el; break; }
                    }

                    if (container) {
                        // Baixem fins al final o fins a una posició alta
                        container.scrollTo({
                            top: container.scrollHeight,
                            behavior: 'smooth'
                        });
                    } else {
                        // Pla B: Scroll de la finestra nativa
                        window.parent.scrollTo({
                            top: 2000, 
                            behavior: 'smooth'
                        });
                    }
                }
                setTimeout(doScroll, 800); // Temps suficient per carregar la taula
            </script>
            """
            components.html(js_scroll, height=0)

        else:
            st.warning(f"No s'ha trobat cap empresa que contingui '{cerca_usuari}'.")
else:
    st.error("Error de connexió.")
