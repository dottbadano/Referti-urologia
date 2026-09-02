import streamlit as st

# Configurazione pagina Streamlit
st.set_page_config(page_title="2gether", layout="wide")

# CSS per rendere l'intera riga del checkbox (testo compreso) interamente cliccabile
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
    [
        "🧬 Prostata", 
        "💧 Vescica", 
        "🫘 Rene", 
        "⚾ Testicolo", 
        "🫁 Polmone", 
        "🌀 Colon", 
        "♀️ Utero", 
        "🌸 Ovaio", 
        "🎀 Seno", 
        "🔶 Fegato", 
        "🍋 Pancreas"
    ]
)

# Caricamento moduli d'organo direttamente dalla root principale
if scelta_modulo == "🧬 Prostata":
    import prostata
    prostata.render_modulo()
elif scelta_modulo == "💧 Vescica":
    import vescica
    vescica.render_modulo()
elif scelta_modulo == "🫘 Rene":
    import rene
    rene.render_modulo()
elif scelta_modulo == "⚾ Testicolo":
    import testicolo
    testicolo.render_modulo()
elif scelta_modulo == "🫁 Polmone":
    import polmone
    polmone.render_modulo()
elif scelta_modulo == "🌀 Colon":
    import colon
    colon.render_modulo()
elif scelta_modulo == "♀️ Utero":
    import utero
    utero.render_modulo()
elif scelta_modulo == "🌸 Ovaio":
    import ovaio
    ovaio.render_modulo()
elif scelta_modulo == "🎀 Seno":
    import seno
    seno.render_modulo()
elif scelta_modulo == "🔶 Fegato":
    import fegato
    fegato.render_modulo()
elif scelta_modulo == "🍋 Pancreas":
    import pancreas
    pancreas.render_modulo()
