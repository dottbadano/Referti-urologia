import streamlit as st
from datetime import datetime
from utils import genera_o_aggiorna_registro, genera_pdf_referto

def render_modulo():
    st.subheader("🎀 Modulo Seno - Decision Support System")
    
    # Anagrafica Paziente
    with st.expander("👤 Anagrafica Paziente", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            nome = st.text_input("Nome Paziente", key="seno_nome")
        with col2:
            cognome = st.text_input("Cognome Paziente", key="seno_cognome")
        with col3:
            codice_univoco = st.text_input("Codice Univoco / ID", key="seno_codice")
            
        data_nascita = st.date_input("Data di Nascita", key="seno_nascita")

    st.divider()

    # Parametri Clinici Seno
    st.markdown("### 📋 Parametri Clinici e Valutazione Senologica")
    
    col_a, col_b = st.columns(2)
    with col_a:
        sintomi_seno = st.selectbox(
            "Sintomi / Esame Obiettivo",
            [
                "Asintomatica / Controllo periodico", 
                "Nodulo palpabile", 
                "Dolore mammario (Mastodinia)", 
                "Secrezione dal capezzolo (Ematica / Citerina)", 
                "Alterazioni cutanee o del capezzolo (Retrazione / Eczema)"
            ],
            key="seno_sintomi"
        )
        imaging_seno = st.selectbox(
            "Quadro Imaging (Mammografia / Ecografia)",
            [
                "Negativo / Nella norma (BI-RADS 1)", 
                "Reperto benigno (BI-RADS 2)", 
                "Reperto probabilmente benigno (BI-RADS 3)", 
                "Anomalia sospetta (BI-RADS 4)", 
                "Reperto altamente sospetto per malignità (BI-RADS 5)"
            ],
            key="seno_imaging"
        )
    with col_b:
        densita_ghiandolare = st.selectbox(
            "Densità Ghiandolare (ACR)",
            ["Tipo A (Fattivamente adiposa)", "Tipo B (Aree di densità fibroghiandolare sparsa)", "Tipo C (Eterogeneamente densa)", "Tipo D (Estremamente densa)"],
            key="seno_acr"
        )
        familiarita_seno = st.selectbox(
            "Familiarità / Anamnesi Genetica",
            ["Assente", "Presente (Parenti di 1° / 2° grado)", "Mutazione genetica nota (BRCA1 / BRCA2 o simili)"],
            key="seno_familiarita"
        )

    note_cliniche = st.text_area("Note Cliniche / Anamnesi Seno", placeholder="Inserire note cliniche aggiuntive...", key="seno_note")

    st.divider()

    # Percorso Clinico e Raccomandazioni
    st.markdown("### 🧭 Percorso Clinico e Raccomandazioni")
    
    percorso = st.selectbox(
        "Seleziona Percorso Clinico",
        [
            "Screening periodico di controllo (Mammografia annuale/biennale)",
            "Follow-up a breve termine (Controllo ecografico a 6 mesi - BI-RADS 3)",
            "Approfondimento diagnostico con Biopsia (Agoaspirato / Core-biopsy)",
            "Valutazione Senologica Oncologica e Stadiazione"
        ],
        key="seno_percorso"
    )

    raccomandazioni = []
    if imaging_seno in ["Anomalia sospetta (BI-RADS 4)", "Reperto altamente sospetto per malignità (BI-RADS 5)"] or sintomi_seno == "Nodulo palpabile":
        raccomandazioni.append("URGENTE: Reperto sospetto o nodulo palpabile, indicazione a esecuzione immediata di Core-biopsy ed ecografia/mammografia di approfondimento.")
    elif imaging_seno == "Reperto probabilmente benigno (BI-RADS 3)":
        raccomandazioni.append("Consigliato monitoraggio ecografico/mammografico ravvicinato a 6 mesi.")
    if familiarita_seno == "Mutazione genetica nota (BRCA1 / BRCA2 o simili)":
        raccomandazioni.append("Paziente ad alto rischio genetico: inserire in programma di sorveglianza integrata (RMN mammaria annuale).")
    raccomandazioni.append(f"Percorso impostato: {percorso}")

    # Generazione Referto PDF
    if st.button("Genera Referto PDF Seno", type="primary", key="btn_pdf_seno"):
        if nome and cognome and codice_univoco:
            genera_o_aggiorna_registro(nome, cognome, data_nascita, codice_univoco)
            
            dettagli_visita = {
                "data": str(datetime.today().date()),
                "tipo": "Visita Senologica - Modulo Seno",
                "dettagli": f"Sintomi: {sintomi_seno} | Imaging: {imaging_seno} | Densità ACR: {densita_ghiandolare} | Familiarità: {familiarita_seno}. Note: {note_cliniche}"
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
                label="📥 Scarica Referto PDF Seno",
                data=pdf_bytes,
                file_name=f"Referto_Seno_{cognome}_{nome}.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("Compilare Nome, Cognome e Codice Univoco per generare il referto.")
