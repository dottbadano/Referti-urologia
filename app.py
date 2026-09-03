import streamlit as st

# Configurazione pagina Streamlit (deve essere sempre la prima chiamata Streamlit)
st.set_page_config(page_title="2gether", layout="wide")

# CSS globale per ottimizzare l'interattività e ridurre i repaint superflui
st.markdown("""
<style>
div.stCheckbox {
    cursor: pointer;
}
div.stCheckbox label {
    cursor: pointer;
    display: flex;
    align-items: center;
    width: 100%;
    user-select: none;
}
div.stCheckbox label p {
    cursor: pointer;
    flex-grow: 1;
}
</style>
""", unsafe_allow_html=True)

# Inizializzazione centralizzata e ottimizzata del Database Pazienti con TTL
@st.cache_data(ttl=60)
def _carica_db_iniziale():
    from utils import carica_db_pazienti
    return carica_db_pazienti()

if "db_pazienti" not in st.session_state:
    st.session_state["db_pazienti"] = _carica_db_iniziale()

# Menu di navigazione laterale con brand 2gether
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

# Mappatura pulita dei moduli per evitare catene if-elif ridondanti e pesanti
MODULI_ORGANO = {
    "🧬 Prostata": "prostata",
    "💧 Vescica": "vescica",
    "🫘 Rene": "rene",
    "⚾ Testicolo": "testicolo",
    "🫁 Polmone": "polmone",
    "🌀 Colon": "colon",
    "♀️ Utero": "utero",
    "🌸 Ovaio": "ovaio",
    "🎀 Seno": "seno",
    "🔶 Fegato": "fegato",
    "🍋 Pancreas": "pancreas"
}

scelta_modulo = st.sidebar.radio(
    "Seleziona Modulo Organo:",
    list(MODULI_ORGANO.keys()),
    key="nav_scelta_organo"
)

# Caricamento dinamico e sicuro del modulo selezionato tramite importlib
import importlib

nom_modulo = MODULI_ORGANO.get(scelta_modulo)
if nom_modulo:
    try:
        modulo_caricato = importlib.import_module(nom_modulo)
        if hasattr(modulo_caricato, "render_modulo"):
            modulo_caricato.render_modulo()
        else:
            st.error(f"Il modulo '{nom_modulo}' non contiene la funzione 'render_modulo()'.")
    except ImportError as e:
        st.error(f"Impossibile caricare il modulo per l'organo selezionato ({nom_modulo}): {e}")
