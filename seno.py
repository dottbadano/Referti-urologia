import streamlit as st
import os
import json
from datetime import datetime
from utils import (
    genera_o_aggiorna_registro, 
    genera_pdf_referto, 
    genera_codice_univoco, 
    render_anamnesi_generale,
    formatta_anamnesi_per_pdf
)

def render_modulo():
    st.subheader("🎀 Modulo Seno - Decision Support System")
    
    # Anagrafica Paziente con ricerca o inserimento nuovo
    with st.expander("👤 Anagrafica Paziente", expanded=True):
        registro_esistente = {}
        if os.path.exists("registro_pazienti.json"):
            try:
                with open("registro_pazienti.json", "r", encoding="utf-8") as f:
                    registro_esistente = json.load(f)
            except Exception:
                registro_esistente = {}
                
        opzioni_pazienti = ["➕ Inserisci Nuovo Paziente"] + [f"{code} - {data['cognome']} {data['nome']}" for code, data in registro_esistente.items()]
        
        scelta_paziente = st.selectbox("Cerca Paziente Registrato o Nuovo", opzioni_pazienti, key="seleziona_paziente_seno")
        
        col1, col2, col3 = st.columns(3)
        
        if scelta_paziente != "➕ Inserisci Nuovo Paziente":
            codice_selezionato = scelta_paziente.split(" - ")[0]
            paziente_info = registro_esistente.get(codice_selezionato, {})
            
            with col1:
                nome = st.text_input("Nome Paziente", value=paziente_info.get("nome", ""), key="seno_nome")
            with col2:
                cognome = st.text_input("Cognome Paziente", value=paziente_info.get("cognome", ""), key="seno_cognome")
            with col3:
                codice_univoco = st.text_input("Codice Univoco / ID", value=codice_selezionato, key="seno_codice", disabled=True)
                
            try:
                dt_nascita_val = datetime.strptime(paziente_info.get("data_nascita", "2000-01-01"), "%Y-%m-%d").date()
            except:
                dt_nascita_val = datetime.today().date()
            data_nascita = st.date_input("Data di Nascita", value=dt_nascita_val, key="seno_nascita")
        else:
            with col1:
                nome = st.text_input("Nome Paziente", key="seno_nome")
            with col2:
                cognome = st.text_input("Cognome Paziente", key="seno_cognome")
            with col3:
                def_code = genera_codice_univoco(nome, cognome) if (nome and cognome) else ""
                codice_univoco = st.text_input("Codice Univoco / ID", value=def_code, key="seno_codice")
                
            data_nascita = st.date_input("Data di Nascita", key="seno_nascita")

    st.divider()

    # Anamnesi Generale Condivisa con prefisso univoco per evitare collisioni di chiavi
    anamnesi = render_anamnesi_generale(prefix="seno")
    anamnesi_ordinata_pdf = formatta_anamnesi_per_pdf(anamnesi)

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
            
            blocco_anamnesi_str = f"\nAnamnesi Generale:\n{anamnesi_ordinata_pdf}" if anamnesi_ordinata_pdf else ""
            note_aggiuntive_str = f"\nNote Cliniche: {note_cliniche}" if note_cliniche.strip() else ""
            
            dettagli_visita = {
                "data": str(datetime.today().date()),
                "tipo": "Visita Senologica - Modulo Seno",
                "dettagli": f"Parametri Senologici:\n• Sintomi: {sintomi_seno}\n• Imaging: {imaging_seno}\n• Densità ACR: {densita_ghiandolare}\n• Familiarità: {familiarita_seno}{blocco_anamnesi_str}{note_aggiuntive_str}"
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
