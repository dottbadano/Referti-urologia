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
    st.subheader("⚾ Modulo Testicolo - Decision Support System")
    
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
        
        scelta_paziente = st.selectbox("Cerca Paziente Registrato o Nuovo", opzioni_pazienti, key="seleziona_paziente_testicolo")
        
        col1, col2, col3 = st.columns(3)
        
        if scelta_paziente != "➕ Inserisci Nuovo Paziente":
            codice_selezionato = scelta_paziente.split(" - ")[0]
            paziente_info = registro_esistente.get(codice_selezionato, {})
            
            with col1:
                nome = st.text_input("Nome Paziente", value=paziente_info.get("nome", ""), key="testicolo_nome")
            with col2:
                cognome = st.text_input("Cognome Paziente", value=paziente_info.get("cognome", ""), key="testicolo_cognome")
            with col3:
                codice_univoco = st.text_input("Codice Univoco / ID", value=codice_selezionato, key="testicolo_codice", disabled=True)
                
            try:
                dt_nascita_val = datetime.strptime(paziente_info.get("data_nascita", "2000-01-01"), "%Y-%m-%d").date()
            except:
                dt_nascita_val = datetime.today().date()
            data_nascita = st.date_input("Data di Nascita", value=dt_nascita_val, key="testicolo_nascita")
        else:
            with col1:
                nome = st.text_input("Nome Paziente", key="testicolo_nome")
            with col2:
                cognome = st.text_input("Cognome Paziente", key="testicolo_cognome")
            with col3:
                def_code = genera_codice_univoco(nome, cognome) if (nome and cognome) else ""
                codice_univoco = st.text_input("Codice Univoco / ID", value=def_code, key="testicolo_codice")
                
            data_nascita = st.date_input("Data di Nascita", key="testicolo_nascita")

    st.divider()

    # Anamnesi Generale Condivisa con prefisso univoco per evitare collisioni di chiavi
    anamnesi = render_anamnesi_generale(prefix="testicolo")
    anamnesi_ordinata_pdf = formatta_anamnesi_per_pdf(anamnesi)

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
            
            blocco_anamnesi_str = f"\nAnamnesi Generale:\n{anamnesi_ordinata_pdf}" if anamnesi_ordinata_pdf else ""
            note_aggiuntive_str = f"\nNote Cliniche: {note_cliniche}" if note_cliniche.strip() else ""
            
            dettagli_visita = {
                "data": str(datetime.today().date()),
                "tipo": "Visita Urologica - Modulo Testicolo",
                "dettagli": f"Parametri Testicolari:\n• Esame Obiettivo: {esame_obiettivo}\n• Ecocolordoppler: {ecocolordoppler}\n• Marker Tumorali: {marker_tumorali}\n• Sintomatologia Acuta: {dolore_acuto}{blocco_anamnesi_str}{note_aggiuntive_str}"
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
