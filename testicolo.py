import streamlit as st
from datetime import datetime
from utils import genera_o_aggiorna_registro, genera_pdf_referto

def render_modulo():
    st.subheader("⚾ Modulo Testicolo - Decision Support System")
    
    # Anagrafica Paziente
    with st.expander("👤 Anagrafica Paziente", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            nome = st.text_input("Nome Paziente", key="testicolo_nome")
        with col2:
            cognome = st.text_input("Cognome Paziente", key="testicolo_cognome")
        with col3:
            codice_univoco = st.text_input("Codice Univoco / ID", key="testicolo_codice")
            
        data_nascita = st.date_input("Data di Nascita", key="testicolo_nascita")

    st.divider()

    # Parametri Clinici Testicolo
    st.markdown("### 📋 Parametri Clinici e Valutazione Urologica Testicolo")
    
    col_a, col_b = st.columns(2)
    with col_a:
        esame_obiettivo = st.selectbox(
            "Esame Obiettivo Scrotale",
            [
                "Normale", 
                "Tumefazione / Nodulo Testicolare Sospetto", 
                "Epididimite / Orchite Acuta", 
                "Idrocele / Varicocele", 
                "Segno di Prehn Positivo / Negativo (Torsione Sospetta)"
            ],
            key="testicolo_obiettivo"
        )
        ecocolordoppler = st.selectbox(
            "Ecocolordoppler Scrotale",
            [
                "Non eseguito", 
                "Normale", 
                "Lesione Solida Intratesticolare Sospetta", 
                "Segni di Flogosi / Epididimite", 
                "Assenza di Flusso (Sospetta Torsione)", 
                "Varicocele / Idrocele"
            ],
            key="testicolo_ecocolordoppler"
        )
    with col_b:
        marker_tumorali = st.selectbox(
            "Marker Tumorali Sierici (Beta-HCG, AFP, LDH)",
            ["Negativi / Nella norma", "Elevati (Sospetta Neoplasia)", "Non dosati / In attesa"],
            key="testicolo_marker"
        )
        dolore_acuto = st.selectbox(
            "Sintomatologia Acuta",
            ["Nessun dolore", "Dolore lieve / Graduale", "Dolore acuto improvviso (Urgenza)"],
            key="testicolo_dolore"
        )

    note_cliniche = st.text_area("Note Cliniche / Anamnesi Testicolo", placeholder="Inserire note cliniche aggiuntive...", key="testicolo_note")

    st.divider()

    # Percorso Clinico e Raccomandazioni
    st.markdown("### 🧭 Percorso Clinico e Raccomandazioni")
    
    percorso = st.selectbox(
        "Seleziona Percorso Clinico",
        [
            "Monitoraggio / Follow-up Clinico",
            "Valutazione Chirurgica Urgente (Esplorazione Scrotale)",
            "Approfondimento Oncologico e Staging (TC Addome-Torace)",
            "Terapia Medica per Flogosi / Orchiepididimite"
        ],
        key="testicolo_percorso"
    )

    raccomandazioni = []
    if dolore_acuto == "Dolore acuto improvviso (Urgenza)" or ecocolordoppler == "Assenza di Flusso (Sospetta Torsione)":
        raccomandazioni.append("URGENZA CHIRURGICA: Sospetta torsione testicolare, indicazione a esplorazione scrotale immediata.")
    if esame_obiettivo == "Tumefazione / Nodulo Testicolare Sospetto" or ecocolordoppler == "Lesione Solida Intratesticolare Sospetta":
        raccomandazioni.append("Sospetta lesione neoplastica: indicazione a dosaggio marker, visita urologica urgente e valutazione per orchifunicolectomia radicale.")
    if "Flogosi" in esame_obiettivo or ecocolordoppler == "Segni di Flogosi / Epididimite":
        raccomandazioni.append("Consigliata terapia antibiotica mirata e riposo funzionale con supporto scrotale.")
    raccomandazioni.append(f"Percorso impostato: {percorso}")

    # Generazione Referto PDF
    if st.button("Genera Referto PDF Testicolo", type="primary", key="btn_pdf_testicolo"):
        if nome and cognome and codice_univoco:
            genera_o_aggiorna_registro(nome, cognome, data_nascita, codice_univoco)
            
            dettagli_visita = {
                "data": str(datetime.today().date()),
                "tipo": "Visita Urologica - Modulo Testicolo",
                "dettagli": f"Esame Obiettivo: {esame_obiettivo} | Ecocolordoppler: {ecocolordoppler} | Marker: {marker_tumorali} | Dolore: {dolore_acuto}. Note: {note_cliniche}"
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
                label="📥 Scarica Referto PDF Testicolo",
                data=pdf_bytes,
                file_name=f"Referto_Testicolo_{cognome}_{nome}.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("Compilare Nome, Cognome e Codice Univoco per generare il referto.")
