import streamlit as st
from datetime import datetime
from utils import genera_o_aggiorna_registro, genera_pdf_referto

def render_modulo():
    st.subheader("🔶 Modulo Fegato - Decision Support System")
    
    # Anagrafica Paziente
    with st.expander("👤 Anagrafica Paziente", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            nome = st.text_input("Nome Paziente", key="fegato_nome")
        with col2:
            cognome = st.text_input("Cognome Paziente", key="fegato_cognome")
        with col3:
            codice_univoco = st.text_input("Codice Univoco / ID", key="fegato_codice")
            
        data_nascita = st.date_input("Data di Nascita", key="fegato_nascita")

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
    raccomandazioni.append(f"Percorso impostato: {percorso}")

    # Generazione Referto PDF
    if st.button("Genera Referto PDF Fegato", type="primary", key="btn_pdf_fegato"):
        if nome and cognome and codice_univoco:
            genera_o_aggiorna_registro(nome, cognome, data_nascita, codice_univoco)
            
            dettagli_visita = {
                "data": str(datetime.today().date()),
                "tipo": "Visita Epatologica - Modulo Fegato",
                "dettagli": f"Sintomi: {sintomi_epatica} | Imaging: {imaging_fegato} | Esami: {esami_ematici} | Profilo: {profilo_virale}. Note: {note_cliniche}"
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
