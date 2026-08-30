import streamlit as st
import os
import json
from datetime import datetime
from utils import (
    genera_o_aggiorna_registro, 
    genera_pdf_referto, 
    genera_codice_univoco, 
    render_anamnesi_generale
)

def render_modulo():
    st.subheader("🌀 Modulo Colon - Decision Support System")
    
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
        
        scelta_paziente = st.selectbox("Cerca Paziente Registrato o Nuovo", opzioni_pazienti, key="seleziona_paziente_colon")
        
        col1, col2, col3 = st.columns(3)
        
        if scelta_paziente != "➕ Inserisci Nuovo Paziente":
            codice_selezionato = scelta_paziente.split(" - ")[0]
            paziente_info = registro_esistente.get(codice_selezionato, {})
            
            with col1:
                nome = st.text_input("Nome Paziente", value=paziente_info.get("nome", ""), key="colon_nome")
            with col2:
                cognome = st.text_input("Cognome Paziente", value=paziente_info.get("cognome", ""), key="colon_cognome")
            with col3:
                codice_univoco = st.text_input("Codice Univoco / ID", value=codice_selezionato, key="colon_codice", disabled=True)
                
            try:
                dt_nascita_val = datetime.strptime(paziente_info.get("data_nascita", "2000-01-01"), "%Y-%m-%d").date()
            except:
                dt_nascita_val = datetime.today().date()
            data_nascita = st.date_input("Data di Nascita", value=dt_nascita_val, key="colon_nascita")
        else:
            with col1:
                nome = st.text_input("Nome Paziente", key="colon_nome")
            with col2:
                cognome = st.text_input("Cognome Paziente", key="colon_cognome")
            with col3:
                def_code = genera_codice_univoco(nome, cognome) if (nome and cognome) else ""
                codice_univoco = st.text_input("Codice Univoco / ID", value=def_code, key="colon_codice")
                
            data_nascita = st.date_input("Data di Nascita", key="colon_nascita")

    st.divider()

    # Anamnesi Generale Condivisa
    anamnesi = render_anamnesi_generale()

    st.divider()

    # Parametri Clinici Colon
    st.markdown("### 📋 Parametri Clinici e Valutazione Gastroenterologica")
    
    col_a, col_b = st.columns(2)
    with col_a:
        sintomi_intestinali = st.selectbox(
            "Sintomi Principali / Alvo",
            [
                "Alvo normovalido", 
                "Stipsi cronica", 
                "Diarrea persistente", 
                "Alvo alternato", 
                "Rettorragia / Sanguinamento"
            ],
            key="colon_sintomi"
        )
        esame_endoscopico = st.selectbox(
            "Quadro Endoscopico (Colonscopia)",
            [
                "Non eseguita", 
                "Negativo / Normale", 
                "Polipo/i intestinale/i (rimosso/biopsiato)", 
                "Diverticolosi del colon", 
                "Sospetta neoformazione / Massa stenosante", 
                "Segni di flogosi (MICI / Colite)"
            ],
            key="colon_endoscopia"
        )
    with col_b:
        sangue_occulto = st.selectbox(
            "Test Sangue Occulto nelle Feci (SOF)",
            ["Non eseguito", "Negativo", "Positivo"],
            key="colon_sof"
        )
        familiarita = st.selectbox(
            "Familiarità per Cancro Colorettale",
            ["Assente", "Presente (Parenti di 1° grado)", "Anamnesi positiva o sindrome genetica nota"],
            key="colon_familiarita"
        )

    note_cliniche = st.text_area("Note Cliniche / Anamnesi Colon", placeholder="Inserire note cliniche aggiuntive...", key="colon_note")

    st.divider()

    # Percorso Clinico e Raccomandazioni
    st.markdown("### 🧭 Percorso Clinico e Raccomandazioni")
    
    percorso = st.selectbox(
        "Seleziona Percorso Clinico",
        [
            "Screening e Prevenzione / Follow-up a lungo termine",
            "Sorveglianza Endoscopica Post-Polipectomia",
            "Approfondimento per Sanguinamento / Colonscopia Completa",
            "Valutazione Chirurgica Oncologica (Staging / TC Addome)"
        ],
        key="colon_percorso"
    )

    raccomandazioni = []
    if sintomi_intestinali == "Rettorragia / Sanguinamento" or sangue_occulto == "Positivo":
        raccomandazioni.append("Consigliata esecuzione tempestiva di colonscopia totale con biopsie se non recente.")
    if esame_endoscopico == "Sospetta neoformazione / Massa stenosante":
        raccomandazioni.append("URGENTE: Sospetta lesione neoplastica del colon, indicazione a stadiazione TC torace-addome e consulenza chirurgica.")
    elif esame_endoscopico == "Polipo/i intestinale/i (rimosso/biopsiato)":
        raccomandazioni.append("In attesa di esame istologico sui polipi rimossi per definire l'intervallo di sorveglianza.")
    
    # Integrazione dati anamnestici generali nelle raccomandazioni o dettagli
    if anamnesi["ipertensione"]:
        raccomandazioni.append("Nota annessa: Paziente iperteso in anamnesi.")
    if anamnesi["diabete"] != "No":
        raccomandazioni.append(f"Nota annessa: Diabete mellito ({anamnesi['diabete']}).")
    if anamnesi["fumo"] != "Non fumatore":
        raccomandazioni.append(f"Nota annessa: Abitudine tabagica ({anamnesi['fumo']}).")

    raccomandazioni.append(f"Percorso impostato: {percorso}")

    # Generazione Referto PDF
    if st.button("Genera Referto PDF Colon", type="primary", key="btn_pdf_colon"):
        if nome and cognome and codice_univoco:
            genera_o_aggiorna_registro(nome, cognome, data_nascita, codice_univoco)
            
            dettagli_visita = {
                "data": str(datetime.today().date()),
                "tipo": "Visita Gastroenterologica - Modulo Colon",
                "dettagli": f"Sintomi: {sintomi_intestinali} | Endoscopia: {esame_endoscopico} | Sangue Occulto: {sangue_occulto} | Familiarità: {familiarita}. Anamnesi gen: Ipertensione={anamnesi['ipertensione']}, Diabete={anamnesi['diabete']}, Fumo={anamnesi['fumo']}. Note: {note_cliniche}"
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
                label="📥 Scarica Referto PDF Colon",
                data=pdf_bytes,
                file_name=f"Referto_Colon_{cognome}_{nome}.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("Compilare Nome, Cognome e Codice Univoco per generare il referto.")
