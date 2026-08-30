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
    st.subheader("🔶 Modulo Fegato - Decision Support System")
    
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
        
        scelta_paziente = st.selectbox("Cerca Paziente Registrato o Nuovo", opzioni_pazienti, key="seleziona_paziente_fegato")
        
        col1, col2, col3 = st.columns(3)
        
        if scelta_paziente != "➕ Inserisci Nuovo Paziente":
            codice_selezionato = scelta_paziente.split(" - ")[0]
            paziente_info = registro_esistente.get(codice_selezionato, {})
            
            with col1:
                nome = st.text_input("Nome Paziente", value=paziente_info.get("nome", ""), key="fegato_nome")
            with col2:
                cognome = st.text_input("Cognome Paziente", value=paziente_info.get("cognome", ""), key="fegato_cognome")
            with col3:
                codice_univoco = st.text_input("Codice Univoco / ID", value=codice_selezionato, key="fegato_codice", disabled=True)
                
            try:
                dt_nascita_val = datetime.strptime(paziente_info.get("data_nascita", "2000-01-01"), "%Y-%m-%d").date()
            except:
                dt_nascita_val = datetime.today().date()
            data_nascita = st.date_input("Data di Nascita", value=dt_nascita_val, key="fegato_nascita")
        else:
            with col1:
                nome = st.text_input("Nome Paziente", key="fegato_nome")
            with col2:
                cognome = st.text_input("Cognome Paziente", key="fegato_cognome")
            with col3:
                def_code = genera_codice_univoco(nome, cognome) if (nome and cognome) else ""
                codice_univoco = st.text_input("Codice Univoco / ID", value=def_code, key="fegato_codice")
                
            data_nascita = st.date_input("Data di Nascita", key="fegato_nascita")

    st.divider()

    # Anamnesi Generale Condivisa
    anamnesi = render_anamnesi_generale()

    st.divider()

    # Parametri Clinici Fegato
    st.markdown("### 📋 Parametri Clinici e Valutazione Epatologica")
    
    col_a, col_b = st.columns(2)
    with col_a:
        sintomi_epatica = st.selectbox(
            "Sintomi / Quadro Clinico",
            [
                "Asintomatico / Reperto incidentale", 
                "Astenia marcata / Fatica cronica", 
                "Ittero (colorazione gialla di sclere/cute)", 
                "Ascite / Distensione addominale", 
                "Dolore ipocondrio destro"
            ],
            key="fegato_sintomi"
        )
        imaging_fegato = st.selectbox(
            "Quadro Imaging (Ecografia / TC / RM)",
            [
                "Fegato regolare / Normale", 
                "Steatosi epatica (Fegato grasso / NAFLD/MASLD)", 
                "Epatopatia cronica / Segni di cirrosi", 
                "Nodulo epatico singolo / Lesione focale", 
                "Multipli nodi / Sospetta neoformazione epatica"
            ],
            key="fegato_imaging"
        )
    with col_b:
        esami_ematici = st.selectbox(
            "Enzimi Epatici e Funzionalità (AST, ALT, GGT, Bilirubina, INR)",
            ["Nella norma", "Lieve/Moderato incremento delle transaminasi", "Alterazione marcata degli indici di colestasi o citolisi", "Compromissione sintetica (INR alterato / Albuminemia bassa)"],
            key="fegato_ematici"
        )
        profilo_virale = st.selectbox(
            "Eziologia / Stato Virale e Metabolico",
            ["Non nota / Negativa", "HBsAg Positivo (Epatite B)", "HCV Ab Positivo (Epatite C)", "Sindrome Metabolica / Steatosi (MASLD)"],
            key="fegato_virale"
        )

    note_cliniche = st.text_area("Note Cliniche / Anamnesi Fegato", placeholder="Inserire note cliniche aggiuntive...", key="fegato_note")

    st.divider()

    # Percorso Clinico e Raccomandazioni
    st.markdown("### 🧭 Percorso Clinico e Raccomandazioni")
    
    percorso = st.selectbox(
        "Seleziona Percorso Clinico",
        [
            "Follow-up e Monitoraggio Epatologico periodico",
            "Approfondimento di II livello (TC con mezzo di contrasto trifasica / Elastografia FibroScan)",
            "Valutazione per Trattamento Antivirale specifico",
            "Consulenza Epatologica / Centro Trapianti e Oncologia Epatobiliare"
        ],
        key="fegato_percorso"
    )

    raccomandazioni = []
    if imaging_fegato in ["Nodulo epatico singolo / Lesione focale", "Multipli nodi / Sospetta neoformazione epatica"]:
        raccomandazioni.append("URGENTE: Presenza di lesione focale epatica, indicazione a TC/RM con mezzo di contrasto e valutazione specialistica epatobiliare/oncologica.")
    if "cirrosi" in imaging_fegato.lower() or "Compromissione sintetica" in esami_ematici:
        raccomandazioni.append("Quadro di epatopatia avanzata: consigliato monitoraggio ecografico semestrale per screening HCC e valutazione clinica specialistica.")
    elif imaging_fegato == "Steatosi epatica (Fegato grasso / NAFLD/MASLD)":
        raccomandazioni.append("Consigliata modificazione dello stile di vita, calo ponderale e controllo dei fattori di rischio metabolici.")
    
    # Integrazione dati anamnestici generali
    if anamnesi["ipertensione"]:
        raccomandazioni.append("Nota annessa: Paziente iperteso in anamnesi.")
    if anamnesi["diabete"] != "No":
        raccomandazioni.append(f"Nota annessa: Diabete mellito ({anamnesi['diabete']}).")
    if anamnesi["fumo"] != "Non fumatore":
        raccomandazioni.append(f"Nota annessa: Abitudine tabagica ({anamnesi['fumo']}).")

    raccomandazioni.append(f"Percorso impostato: {percorso}")

    # Generazione Referto PDF
    if st.button("Genera Referto PDF Fegato", type="primary", key="btn_pdf_fegato"):
        if nome and cognome and codice_univoco:
            genera_o_aggiorna_registro(nome, cognome, data_nascita, codice_univoco)
            
            dettagli_visita = {
                "data": str(datetime.today().date()),
                "tipo": "Visita Epatologica - Modulo Fegato",
                "dettagli": f"Sintomi: {sintomi_epatica} | Imaging: {imaging_fegato} | Esami: {esami_ematici} | Profilo: {profilo_virale}. Anamnesi gen: Ipertensione={anamnesi['ipertensione']}, Diabete={anamnesi['diabete']}, Fumo={anamnesi['fumo']}. Note: {note_cliniche}"
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
                label="📥 Scarica Referto PDF Fegato",
                data=pdf_bytes,
                file_name=f"Referto_Fegato_{cognome}_{nome}.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("Compilare Nome, Cognome e Codice Univoco per generare il referto.")
