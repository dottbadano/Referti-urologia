import streamlit as st
from datetime import datetime
from utils import genera_o_aggiorna_registro, genera_pdf_referto

def render_modulo():
    st.subheader("🩺 Modulo Vescica - Decision Support System")
    
    # Anagrafica Paziente
    with st.expander("👤 Anagrafica Paziente", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            nome = st.text_input("Nome Paziente", key="vescica_nome")
        with col2:
            cognome = st.text_input("Cognome Paziente", key="vescica_cognome")
        with col3:
            codice_univoco = st.text_input("Codice Univoco / ID", key="vescica_codice")
            
        data_nascita = st.date_input("Data di Nascita", key="vescica_nascita")

    st.divider()

    # Parametri Clinici Vescica
    st.markdown("### 📋 Parametri Clinici e Valutazione Urologica Vescica")
    
    col_a, col_b = st.columns(2)
    with col_a:
        sintomi_luts = st.selectbox(
            "Sintomi LUTS / Vescica Iperattiva",
            ["Assenti", "Lieve (IPSS basso)", "Moderato (IPSS medio)", "Severo (IPSS alto)"],
            key="vescica_luts"
        )
        citologia = st.selectbox(
            "Esame Citologico Urinario",
            ["Negativo", "Positivo", "Dubbio / Sospetto", "Non eseguito"],
            key="vescica_citologia"
        )
    with col_b:
        pvr = st.number_input("Residuo Post-Minzionale (PVR - ml)", min_value=0, value=0, step=10, key="vescica_pvr")
        cistoscopia = st.selectbox(
            "Quadro Cistoscopico",
            ["Normale", "Sospetta Neoformazione", "Iperemia / Flogosi", "Trabecolatura", "Non eseguita"],
            key="vescica_cistoscopia"
        )

    note_cliniche = st.text_area("Note Cliniche / Anamnesi Vescica", placeholder="Inserire note cliniche aggiuntive...", key="vescica_note")

    st.divider()

    # Percorso Clinico e Raccomandazioni
    st.markdown("### 🧭 Percorso Clinico e Raccomandazioni")
    
    percorso = st.selectbox(
        "Seleziona Percorso Clinico",
        [
            "Follow-up Conservativo / Monitoraggio",
            "Approfondimento Endoscopico (TURBT programmata)",
            "Terapia Medica (Anticolinergici / Beta-3 agonisti)",
            "Valutazione Urodinamica"
        ],
        key="vescica_percorso"
    )

    raccomandazioni = []
    if citologia == "Positivo" or cistoscopia == "Sospetta Neoformazione":
        raccomandazioni.append("Indicazione a Cistoscopia in Sala Operatoria / TURBT urgente.")
    if pvr > 100:
        raccomandazioni.append("Valutare cateterismo o gestione del residuo post-minzionale elevato.")
    raccomandazioni.append(f"Percorso impostato: {percorso}")

    # Generazione Referto PDF
    if st.button("Genera Referto PDF Vescica", type="primary", key="btn_pdf_vescica"):
        if nome and cognome and codice_univoco:
            genera_o_aggiorna_registro(nome, cognome, data_nascita, codice_univoco)
            
            dettagli_visita = {
                "data": str(datetime.today().date()),
                "tipo": "Visita Urologica - Modulo Vescica",
                "dettagli": f"Sintomi: {sintomi_luts} | Citologia: {citologia} | PVR: {pvr} ml | Cistoscopia: {cistoscopia}. Note: {note_cliniche}"
            }
            
            pdf_bytes = genera_pdf_referto(
                codice_paziente=codice_univoco,
                dati_visita=dettagli_visita,
                percorso=percorso,
                note_raccomandazioni=raccomandazioni,
                nome=nome,
                cognome=cognome
            )
            
            st.success("Referto generato con successo!")
            st.download_button(
                label="📥 Scarica Referto PDF Vescica",
                data=pdf_bytes,
                file_name=f"Referto_Vescica_{cognome}_{nome}.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("Compilare Nome, Cognome e Codice Univoco per generare il referto.")
