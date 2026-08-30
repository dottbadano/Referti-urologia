import streamlit as st

# Configurazione pagina Streamlit
st.set_page_config(page_title="DSS Urologia", layout="wide")

# Inizializzazione del Database Pazienti
if "db_pazienti" not in st.session_state:
    from utils import carica_db_pazienti
    st.session_state["db_pazienti"] = carica_db_pazienti()

# Menu di navigazione con icona vescica aggiornata
st.sidebar.title("🫀 DSS Urologia") # oppure "💧 DSS Urologia"
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
