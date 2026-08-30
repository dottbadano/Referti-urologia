import streamlit as st
from datetime import datetime
from utils import genera_o_aggiorna_registro, genera_pdf_referto

def render_modulo():
    st.subheader("🫁 Modulo Polmone - Decision Support System")
    
    # Anagrafica Paziente
    with st.expander("👤 Anagrafica Paziente", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            nome = st.text_input("Nome Paziente", key="polmone_nome")
        with col2:
            cognome = st.text_input("Cognome Paziente", key="polmone_cognome")
        with col3:
            codice_univoco = st.text_input("Codice Univoco / ID", key="polmone_codice")
            
        data_nascita = st.date_input("Data di Nascita", key="polmone_nascita")

    st.divider()

    # Parametri Clinici Polmone
    st.markdown("### 📋 Parametri Clinici e Valutazione Pneumologica")
    
    col_a, col_b = st.columns(2)
    with col_a:
        sintomi_respiratori = st.selectbox(
            "Sintomi Principali",
            [
                "Assenti", 
                "Tosse cronica / persistente", 
                "Dispnea (affanno) da sforzo / a riposo", 
                "Emottisi (sangue nell'escreato)", 
                "Dolore toracico"
            ],
            key="polmone_sintomi"
        )
        imaging_torace = st.selectbox(
            "Quadro Imaging (RX Torace / TC Torace)",
            [
                "Normale / Negativo", 
                "Nodulo Polmonare Solitario (NPS)", 
                "Addensamento parenchimale / Sospetta Neoplasia", 
                "Versamento pleurico", 
                "Segni di BPCO / Enfisema"
            ],
            key="polmone_imaging"
        )
    with col_b:
        funzione_respiratoria = st.selectbox(
            "Spirometria / Funzione Respiratoria",
            ["Normale", "Deficit ventilatorio ostruttivo", "Deficit ventilatorio restrittivo", "Non eseguita"],
            key="polmone_spirometria"
        )
        abitudine_tabagica = st.selectbox(
            "Storia Tabagica",
            ["Non fumatore", "Ex fumatore", "Fumatore attivo (Pack-years elevati)"],
            key="polmone_fumo"
        )

    note_cliniche = st.text_area("Note Cliniche / Anamnesi Polmone", placeholder="Inserire note cliniche aggiuntive...", key="polmone_note")

    st.divider()

    # Percorso Clinico e Raccomandazioni
    st.markdown("### 🧭 Percorso Clinico e Raccomandazioni")
    
    percorso = st.selectbox(
        "Seleziona Percorso Clinico",
        [
            "Follow-up e Monitoraggio Radiologico",
            "Approfondimento Pneumologico e TC Torace con MdC",
            "Valutazione per Broncoscopia / Biopsia",
            "Gestione Terapia Broncodilatatrice / BPCO"
        ],
        key="polmone_percorso"
    )

    raccomandazioni = []
    if sintomi_respiratori == "Emottisi (sangue nell'escreato)" or imaging_torace == "Addensamento parenchimale / Sospetta Neoplasia":
        raccomandazioni.append("URGENTE: Indicazione a TC torace con contrasto e visita pneumologica/oncologica per sospetta neoformazione.")
    if imaging_torace == "Nodulo Polmonare Solitario (NPS)":
        raccomandazioni.append("Segnalato Nodulo Polmonare Solitario: impostare protocollo di monitoraggio volumetrico o PET-TC secondo linee guida.")
    if abitudine_tabagica == "Fumatore attivo (Pack-years elevati)":
        raccomandazioni.append("Consigliato programma di cessazione del fumo e valutazione per screening polmonare a basse dosi.")
    raccomandazioni.append(f"Percorso impostato: {percorso}")

    # Generazione Referto PDF
    if st.button("Genera Referto PDF Polmone", type="primary", key="btn_pdf_polmone"):
        if nome and cognome and codice_univoco:
            genera_o_aggiorna_registro(nome, cognome, data_nascita, codice_univoco)
            
            dettagli_visita = {
                "data": str(datetime.today().date()),
                "tipo": "Visita Pneumologica - Modulo Polmone",
                "dettagli": f"Sintomi: {sintomi_respiratori} | Imaging: {imaging_torace} | Spirometria: {funzione_respiratoria} | Fumo: {abitudine_tabagica}. Note: {note_cliniche}"
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
                label="📥 Scarica Referto PDF Polmone",
                data=pdf_bytes,
                file_name=f"Referto_Polmone_{cognome}_{nome}.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("Compilare Nome, Cognome e Codice Univoco per generare il referto.")
