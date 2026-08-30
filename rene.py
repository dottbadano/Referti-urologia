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
    st.subheader("🫘 Modulo Rene - Decision Support System")
    
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
        
        scelta_paziente = st.selectbox("Cerca Paziente Registrato o Nuovo", opzioni_pazienti, key="seleziona_paziente_rene")
        
        col1, col2, col3 = st.columns(3)
        
        if scelta_paziente != "➕ Inserisci Nuovo Paziente":
            codice_selezionato = scelta_paziente.split(" - ")[0]
            paziente_info = registro_esistente.get(codice_selezionato, {})
            
            with col1:
                nome = st.text_input("Nome Paziente", value=paziente_info.get("nome", ""), key="rene_nome")
            with col2:
                cognome = st.text_input("Cognome Paziente", value=paziente_info.get("cognome", ""), key="rene_cognome")
            with col3:
                codice_univoco = st.text_input("Codice Univoco / ID", value=codice_selezionato, key="rene_codice", disabled=True)
                
            try:
                dt_nascita_val = datetime.strptime(paziente_info.get("data_nascita", "2000-01-01"), "%Y-%m-%d").date()
            except:
                dt_nascita_val = datetime.today().date()
            data_nascita = st.date_input("Data di Nascita", value=dt_nascita_val, key="rene_nascita")
        else:
            with col1:
                nome = st.text_input("Nome Paziente", key="rene_nome")
            with col2:
                cognome = st.text_input("Cognome Paziente", key="rene_cognome")
            with col3:
                def_code = genera_codice_univoco(nome, cognome) if (nome and cognome) else ""
                codice_univoco = st.text_input("Codice Univoco / ID", value=def_code, key="rene_codice")
                
            data_nascita = st.date_input("Data di Nascita", key="rene_nascita")

    st.divider()

    # Anamnesi Generale Condivisa con prefisso univoco per evitare collisioni di chiavi
    anamnesi = render_anamnesi_generale(prefix="rene")
    anamnesi_ordinata_pdf = formatta_anamnesi_per_pdf(anamnesi)

    st.divider()

    # Parametri Clinici Rene
    st.markdown("### 📋 Parametri Clinici e Valutazione Urologica Rene")
    
    col_a, col_b = st.columns(2)
    with col_a:
        creatinina = st.number_input("Creatinina Sierica (mg/dL)", min_value=0.0, value=1.0, step=0.1, key="rene_creatinina")
        egfr = st.number_input("eGFR (mL/min/1.73m²)", min_value=0.0, value=90.0, step=1.0, key="rene_egfr")
        ematuria = st.selectbox(
            "Ematuria",
            ["Assente", "Microematuria", "Macroematuria"],
            key="rene_ematuria"
        )
    with col_b:
        imaging_rene = st.selectbox(
            "Quadro Imaging (Ecografia / TC)",
            [
                "Normale", 
                "Cisti Renale Semplice (Bosniak I / II)", 
                "Cisti Complessa (Bosniak III / IV)", 
                "Sospetta Neoformazione Solida", 
                "Litiasi Renale (Calcolosi)"
            ],
            key="rene_imaging"
        )
        proteinuria = st.selectbox(
            "Proteinuria",
            ["Assente / Negativa", "Lieve", "Moderata / Elevata", "Non eseguita"],
            key="rene_proteinuria"
        )

    note_cliniche = st.text_area("Note Cliniche / Anamnesi Rene", placeholder="Inserire note cliniche aggiuntive...", key="rene_note")

    st.divider()

    # Percorso Clinico e Raccomandazioni
    st.markdown("### 🧭 Percorso Clinico e Raccomandazioni")
    
    percorso = st.selectbox(
        "Seleziona Percorso Clinico",
        [
            "Follow-up Nefrologico / Monitoraggio Funzione Renale",
            "Approfondimento Urologico per Neoformazione (TC con MdC)",
            "Trattamento Calcolosi Renale (Litiasi)",
            "Sorveglianza Cisti Renali Complesse"
        ],
        key="rene_percorso"
    )

    raccomandazioni = []
    if imaging_rene in ["Cisti Complessa (Bosniak III / IV)", "Sospetta Neoformazione Solida"]:
        raccomandazioni.append("Indicazione urgente a valutazione urologica/chirurgica oncologica e TC trifasica.")
    if egfr < 60:
        raccomandazioni.append("Segnalata riduzione del filtrato glomerulare (eGFR < 60): consigliata valutazione nefrologica.")
    if imaging_rene == "Litiasi Renale (Calcolosi)":
        raccomandazioni.append("Valutazione per eventuale trattamento endoscopico o litotrissia.")

    raccomandazioni.append(f"Percorso impostato: {percorso}")

    # Generazione Referto PDF
    if st.button("Genera Referto PDF Rene", type="primary", key="btn_pdf_rene"):
        if nome and cognome and codice_univoco:
            genera_o_aggiorna_registro(nome, cognome, data_nascita, codice_univoco)
            
            blocco_anamnesi_str = f"\nAnamnesi Generale:\n{anamnesi_ordinata_pdf}" if anamnesi_ordinata_pdf else ""
            note_aggiuntive_str = f"\nNote Cliniche: {note_cliniche}" if note_cliniche.strip() else ""
            
            dettagli_visita = {
                "data": str(datetime.today().date()),
                "tipo": "Visita Urologica - Modulo Rene",
                "dettagli": f"Parametri Renali:\n• Creatinina: {creatinina} mg/dL\n• eGFR: {egfr} mL/min\n• Ematuria: {ematuria}\n• Imaging: {imaging_rene}\n• Proteinuria: {proteinuria}{blocco_anamnesi_str}{note_aggiuntive_str}"
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
                label="📥 Scarica Referto PDF Rene",
                data=pdf_bytes,
                file_name=f"Referto_Rene_{cognome}_{nome}.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("Compilare Nome, Cognome e Codice Univoco per generare il referto.")
