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
    st.subheader("🌸 Modulo Ovaio - Decision Support System")
    
    with st.expander("👤 Anagrafica Paziente", expanded=True):
        registro_esistente = {}
        if os.path.exists("registro_pazienti.json"):
            try:
                with open("registro_pazienti.json", "r", encoding="utf-8") as f:
                    registro_esistente = json.load(f)
            except Exception:
                registro_esistente = {}
                
        opzioni_pazienti = ["➕ Inserisci Nuovo Paziente"] + [f"{code} - {data['cognome']} {data['nome']}" for code, data in registro_esistente.items()]
        
        scelta_paziente = st.selectbox("Cerca Paziente Registrato o Nuovo", opzioni_pazienti, key="seleziona_paziente_ovaio")
        
        col1, col2, col3 = st.columns(3)
        
        if scelta_paziente != "➕ Inserisci Nuovo Paziente":
            codice_selezionato = scelta_paziente.split(" - ")[0]
            paziente_info = registro_esistente.get(codice_selezionato, {})
            
            with col1:
                nome = st.text_input("Nome Paziente", value=paziente_info.get("nome", ""), key="ovaio_nome")
            with col2:
                cognome = st.text_input("Cognome Paziente", value=paziente_info.get("cognome", ""), key="ovaio_cognome")
            with col3:
                codice_univoco = st.text_input("Codice Univoco / ID", value=codice_selezionato, key="ovaio_codice", disabled=True)
                
            try:
                dt_nascita_val = datetime.strptime(paziente_info.get("data_nascita", "2000-01-01"), "%Y-%m-%d").date()
            except:
                dt_nascita_val = datetime.today().date()
            data_nascita = st.date_input("Data di Nascita", value=dt_nascita_val, key="ovaio_nascita")
        else:
            with col1:
                nome = st.text_input("Nome Paziente", key="ovaio_nome")
            with col2:
                cognome = st.text_input("Cognome Paziente", key="ovaio_cognome")
            with col3:
                def_code = genera_codice_univoco(nome, cognome) if (nome and cognome) else ""
                codice_univoco = st.text_input("Codice Univoco / ID", value=def_code, key="ovaio_codice")
                
            data_nascita = st.date_input("Data di Nascita", key="ovaio_nascita")

    st.divider()

    # Anamnesi Generale Condivisa con prefisso univoco
    anamnesi = render_anamnesi_generale(prefix="ovaio")
    anamnesi_ordinata_pdf = formatta_anamnesi_per_pdf(anamnesi)

    st.divider()

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

    if st.button("Genera Referto PDF Ovaio", type="primary", key="btn_pdf_ovaio"):
        if nome and cognome and codice_univoco:
            genera_o_aggiorna_registro(nome, cognome, data_nascita, codice_univoco)
            
            blocco_anamnesi_str = f"\nAnamnesi Generale:\n{anamnesi_ordinata_pdf}" if anamnesi_ordinata_pdf else ""
            
            dettagli_visita = {
                "data": str(datetime.today().date()),
                "tipo": "Visita Ginecologica - Modulo Ovaio",
                "dettagli": f"Parametri Ginecologici Annessiali:\n• Sintomi: {sintomi_ovarici}\n• Imaging: {imaging_ovaio}\n• Marker Tumorali: {marker_tumorali}\n• Stato Ormonale: {stato_menopausa}{blocco_anamnesi_str}\n\nNote Cliniche:\n{note_cliniche if note_cliniche else 'Nessuna nota aggiuntiva.'}"
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
