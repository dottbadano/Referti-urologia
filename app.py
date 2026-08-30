import streamlit as st

# Configurazione pagina Streamlit
st.set_page_config(page_title="2gether", layout="wide")

# Inizializzazione del Database Pazienti
if "db_pazienti" not in st.session_state:
    from utils import carica_db_pazienti
    st.session_state["db_pazienti"] = carica_db_pazienti()

# Menu di navigazione laterale con brand 2gether e payoff corretto per sfondo scuro
st.sidebar.markdown(
    """
    <div style="padding-bottom: 20px;">
        <h1 style="margin: 0; font-size: 1.8rem; font-family: sans-serif; line-height: 1.1;">
            <span style="color: red;">2</span><span style="color: white;">gether</span>
        </h1>
        <p style="color: #a0aec0; font-size: 0.8rem; font-style: italic; margin: 4px 0 0 0;">
            the answer is just next 2U
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

scelta_modulo = st.sidebar.radio(
    "Seleziona Modulo Organo:",
    ["🧬 Prostata", "💧 Vescica", "🫘 Rene", "⚾ Testicolo"]
)

# Caricamento moduli dinamico
if scelta_modulo == "🧬 Prostata":
    import prostate
    prostate.render_modulo()
elif scelta_modulo == "💧 Vescica":
    import vescica
    vescica.render_modulo()
elif scelta_modulo == "🫘 Rene":
    st.info("Modulo Rene in fase di creazione...")
elif scelta_modulo == "⚾ Testicolo":
    st.info("Modulo Testicolo in fase di creazione...")
