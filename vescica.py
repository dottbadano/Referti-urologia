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
    st.subheader("💧 Modulo Vescica - Decision Support System")
    
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
        
        scelta_paziente = st.selectbox("Cerca Paziente Registrato o Nuovo", opzioni_pazienti, key="seleziona_paziente_vescica")
        
        col1, col2, col3 = st.columns(3)
        
        if scelta_paziente != "➕ Inserisci Nuovo Paziente":
            codice_selezionato = scelta_paziente.split(" - ")[0]
            paziente_info = registro_esistente.get(codice_selezionato, {})
            
            with col1:
                nome = st.text_input("Nome Paziente", value=paziente_info.get("nome", ""), key="vescica_nome")
            with col2:
                cognome = st.text_input("Cognome Paziente", value=paziente_info.get("cognome", ""), key="vescica_cognome")
            with col3:
                codice_univoco = st.text_input("Codice Univoco / ID", value=codice_selezionato, key="vescica_codice", disabled=True)
                
            try:
                dt_nascita_val = datetime.strptime(paziente_info.get("data_nascita", "2000-01-01"), "%Y-%m-%d").date()
            except:
                dt_nascita_val = datetime.today().date()
            data_nascita = st.date_input("Data di Nascita", value=dt_nascita_val, key="vescica_nascita")
        else:
            with col1:
                nome = st.text_input("Nome Paziente", key="vescica_nome")
            with col2:
                cognome = st.text_input("Cognome Paziente", key="vescica_cognome")
            with col3:
                def_code = genera_codice_univoco(nome, cognome) if (nome and cognome) else ""
                codice_univoco = st.text_input("Codice Univoco / ID", value=def_code, key="vescica_codice")
                
            data_nascita = st.date_input("Data di Nascita", key="vescica_nascita")

    st.divider()

    # Anamnesi Generale Condivisa
    anamnesi = render_anamnesi_generale()

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
        ematuria_vescica = st.selectbox(
            "Ematuria (Macro/Micro)",
            ["Assente", "Microematuria", "Macroematuria (Indication to Cystoscopy)"],
            key="vescica_ematuria"
        )
    with col_b:
        imaging_vescica = st.selectbox(
            "Quadro Imaging / Cistoscopia",
            [
                "Normale", 
                "Sospetta neoformazione endovescicale", 
                "Ipertrofia prostatica ostruttiva con residuo", 
                "Trabecolazione vescicale severa", 
                "Litiasi vescicale"
            ],
            key="vescica_imaging"
        )
        fumo_vescica = st.selectbox(
            "Abitudine Tabagica (Fattore di Rischio Uroteliale)",
            ["Non fumatore", "Ex fumatore", "Fumatore attivo"],
            key="vescica_fumo_uro"
        )

    note_cliniche = st.text_area("Note Cliniche / Anamnesi Vescica", placeholder="Inserire note cliniche aggiuntive...", key="vescica_note")

    st.divider()

    # Percorso Clinico e Raccomandazioni
    st.markdown("### 🧭 Percorso Clinico e Raccomandazioni")
    
    percorso = st.selectbox(
        "Seleziona Percorso Clinico",
        [
            "Follow-up e Trattamento Medico LUTS",
            "Cistoscopia diagnostica di approfondimento",
            "Valutazione Chirurgica Endoscopica (TURBT / Resezione Transuretrale di Lesione Vescicale)",
            "Sorveglianza / Gestione Citologia Positiva o Ematuria"
        ],
        key="vescica_percorso"
    )

    raccomandazioni = []
    if ematuria_vescica == "Macroematuria (Indication to Cystoscopy)" or imaging_vescica == "Sospetta neoformazione endovescicale":
        raccomandazioni.append("URGENTE: Presenza di macroematuria o sospetta neoformazione. Indicazione a Cistoscopia diagnostica ed ecografia/TC uro-grafica.")
    if citologia == "Positivo":
        raccomandazioni.append("Citologia urinaria positiva: programmare cistoscopia in narcosi / mappatura e endoscopia delle alte vie urinarie.")
    if fumo_vescica == "Fumatore attivo":
        raccomandazioni.append("Fattore di rischio maggiore per carcinoma uroteliale: raccomandata cessazione fumo.")
    
    # Integrazione dati anamnestici generali
    if anamnesi["ipertensione"]:
        raccomandazioni.append("Nota annessa: Paziente iperteso in anamnesi.")
    if anamnesi["diabete"] != "No":
        raccomandazioni.append(f"Nota annessa: Diabete mellito ({anamnesi['diabete']}).")
    if anamnesi["fumo"] != "Non fumatore":
        raccomandazioni.append(f"Nota annessa: Abitudine tabagica generale ({anamnesi['fumo']}).")

    raccomandazioni.append(f"Percorso impostato: {percorso}")

    # Generazione Referto PDF
    if st.button("Genera Referto PDF Vescica", type="primary", key="btn_pdf_vescica"):
        if nome and cognome and codice_univoco:
            genera_o_aggiorna_registro(nome, cognome, data_nascita, codice_univoco)
            
            dettagli_visita = {
                "data": str(datetime.today().date()),
                "tipo": "Visita Urologica - Modulo Vescica",
                "dettagli": f"LUTS: {sintomi_luts} | Citologia: {citologia} | Ematuria: {ematuria_vescica} | Imaging/Cistoscopia: {imaging_vescica} | Fumo: {fumo_vescica} | Anamnesi gen: Ipertensione={anamnesi['ipertensione']}, Diabete={anamnesi['diabete']}. Note: {note_cliniche}"
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
