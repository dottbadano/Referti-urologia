import streamlit as st
from datetime import datetime
from utils import genera_o_aggiorna_registro, genera_pdf_referto

def render_modulo():
    st.subheader("🌸 Modulo Ovaio - Decision Support System")
    
    # Anagrafica Paziente
    with st.expander("👤 Anagrafica Paziente", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            nome = st.text_input("Nome Paziente", key="ovaio_nome")
        with col2:
            cognome = st.text_input("Cognome Paziente", key="ovaio_cognome")
        with col3:
            codice_univoco = st.text_input("Codice Univoco / ID", key="ovaio_codice")
            
        data_nascita = st.date_input("Data di Nascita", key="ovaio_nascita")

    st.divider()

    # Parametri Clinici Ovaio
    st.markdown("### 📋 Parametri Clinici e Valutazione Ginecologica Annessiale")
    
    col_a, col_b = st.columns(2)
    with col_a:
        sintomi_ovarici = st.selectbox(
            "Sintomi / Quadro Clinico",
            [
                "Asintomatica / Reperto incidentale", 
                "Dolore pelvico cronico / ricorrente", 
                "Dolore pelvico acuto (Sospetta torsione/rottura ciste)", 
                "Distensione addominale / Meteorismo persistente", 
                "Sintomi urinari o digestivi da compressione"
            ],
            key="ovaio_sintomi"
        )
        imaging_ovaio = st.selectbox(
            "Quadro Ecografico / Imaging Annessiale",
            [
                "Ovaie normali / Normodirette", 
                "Ciste ovarica semplice / Funzionale", 
                "Endometrioma / Ciste endometriosica", 
                "Ciste complessa / Sospetta (setti, escrescenze papillari)", 
                "Massa annessiale solida o misto-solida bilaterale"
            ],
            key="ovaio_imaging"
        )
    with col_b:
        marker_tumorali = st.selectbox(
            "Marker Tumorali (CA 125, HE4, ROMA Index)",
            ["Nella norma / Negativi", "CA 125 moderatamente elevato", "Elevati (Sospetta neoplasia ovarica)", "Non dosati"],
            key="ovaio_marker"
        )
        stato_menopausa = st.selectbox(
            "Stato Ormonale",
            ["Età fertile / Pre-menopausa", "Post-menopausa"],
            key="ovaio_menopausa"
        )

    note_cliniche = st.text_area("Note Cliniche / Anamnesi Ovaio", placeholder="Inserire note cliniche aggiuntive...", key="ovaio_note")

    st.divider()

    # Percorso Clinico e Raccomandazioni
    st.markdown("### 🧭 Percorso Clinico e Raccomandazioni")
    
    percorso = st.selectbox(
        "Seleziona Percorso Clinico",
        [
            "Follow-up ecografico a breve termine (Controllo ciste)",
            "Approfondimento di II livello (RMN pelvica con MdC / Consulenza Oncologica)",
            "Valutazione per Trattamento Chirurgico Laparoscopico Conservativo (Cistectomia)",
            "Trattamento Chirurgico Radicale / Staging Oncologico (Laparotomia/Laparoscopia)"
        ],
        key="ovaio_percorso"
    )

    raccomandazioni = []
    if sintomi_ovarici == "Dolore pelvico acuto (Sospetta torsione/rottura ciste)":
        raccomandazioni.append("URGENTE: Sospetta urgenza annessiale (torsione/rottura), indicazione a valutazione chirurgica immediata.")
    if imaging_ovaio in ["Ciste complessa / Sospetta (setti, escrescenze papillari)", "Massa annessiale solida o misto-solida bilaterale"] or marker_tumorali == "Elevati (Sospetta neoplasia ovarica)":
        raccomandazioni.append("URGENTE: Sospetta lesione ovarica a rischio oncologico. Indicazione a consulenza ginecologica-oncologica e stadiazione avanzata.")
    elif imaging_ovaio == "Endometrioma / Ciste endometriosica":
        raccomandazioni.append("Valutazione per eventuale gestione medica o trattamento conservativo laparoscopico in base alla sintomatologia dolorosa o ricerca di gravidanza.")
    raccomandazioni.append(f"Percorso impostato: {percorso}")

    # Generazione Referto PDF
    if st.button("Genera Referto PDF Ovaio", type="primary", key="btn_pdf_ovaio"):
        if nome and cognome and codice_univoco:
            genera_o_aggiorna_registro(nome, cognome, data_nascita, codice_univoco)
            
            dettagli_visita = {
                "data": str(datetime.today().date()),
                "tipo": "Visita Ginecologica - Modulo Ovaio",
                "dettagli": f"Sintomi: {sintomi_ovarici} | Imaging: {imaging_ovaio} | Marker: {marker_tumorali} | Stato: {stato_menopausa}. Note: {note_cliniche}"
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
                label="📥 Scarica Referto PDF Ovaio",
                data=pdf_bytes,
                file_name=f"Referto_Ovaio_{cognome}_{nome}.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("Compilare Nome, Cognome e Codice Univoco per generare il referto.")
