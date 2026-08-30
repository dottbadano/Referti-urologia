import streamlit as st
from datetime import datetime
from utils import genera_o_aggiorna_registro, genera_pdf_referto

def render_modulo():
    st.subheader("🍋 Modulo Pancreas - Decision Support System")
    
    # Anagrafica Paziente
    with st.expander("👤 Anagrafica Paziente", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            nome = st.text_input("Nome Paziente", key="pancreas_nome")
        with col2:
            cognome = st.text_input("Cognome Paziente", key="pancreas_cognome")
        with col3:
            codice_univoco = st.text_input("Codice Univoco / ID", key="pancreas_codice")
            
        data_nascita = st.date_input("Data di Nascita", key="pancreas_nascita")

    st.divider()

    # Parametri Clinici Pancreas
    st.markdown("### 📋 Parametri Clinici e Valutazione Pancreatica")
    
    col_a, col_b = st.columns(2)
    with col_a:
        sintomi_pancreas = st.selectbox(
            "Sintomi / Quadro Clinico",
            [
                "Asintomatico / Reperto incidentale", 
                "Dolore addominale transfittivo (a barra)", 
                "Ittero ostruttivo (pelle/sclere gialle, feci acoliche)", 
                "Calo ponderale inspiegato / Astenia", 
                "Insorgenza recente di Diabete mellito"
            ],
            key="pancreas_sintomi"
        )
        imaging_pancreas = st.selectbox(
            "Quadro Imaging (TC Addome / RM / Ecoendoscopia)",
            [
                "Pancreas regolare / Normale", 
                "Segni di pancreatite acuta o cronica", 
                "Cisti pancreatica / Lesione cistica (es. IPMN / IPMN branch-duct)", 
                "Lesione focale / Massa solida pancreatica sospetta", 
                "Dilatazione del dotto di Wirsung o biliare principale"
            ],
            key="pancreas_imaging"
        )
    with col_b:
        marker_tumorali = st.selectbox(
            "Marker Tumorali (CA 19-9, CEA)",
            ["Nella norma / Negativi", "CA 19-9 moderatamente elevato", "CA 19-9 marcatamente elevato", "Non dosati"],
            key="pancreas_marker"
        )
        funzione_pancreatica = st.selectbox(
            "Funzione Pancreatica / Esami Ematici",
            ["Enzimi pancreatici (Lipasi/Amilasi) normali", "Iperamilasemia / Iperlipasemia", "Insufficienza pancreatica esocrina (Steatorrea)", "Glicemia alterata / Diabete secondario"],
            key="pancreas_funzione"
        )

    note_cliniche = st.text_area("Note Cliniche / Anamnesi Pancreas", placeholder="Inserire note cliniche aggiuntive...", key="pancreas_note")

    st.divider()

    # Percorso Clinico e Raccomandazioni
    st.markdown("### 🧭 Percorso Clinico e Raccomandazioni")
    
    percorso = st.selectbox(
        "Seleziona Percorso Clinico",
        [
            "Follow-up e Sorveglianza radiologica/ecografica",
            "Approfondimento di II livello (Ecoendoscopia - EUS con eventuale agoaspirato FNA)",
            "Valutazione Chirurgica Specialistica (Chirurgia Pancreatica / Centro Pancreatas)",
            "Gestione medica e nutrizionale (Enzimi / Controllo glicemico / Terapia del dolore)"
        ],
        key="pancreas_percorso"
    )

    raccomandazioni = []
    if imaging_pancreas == "Lesione focale / Massa solida pancreatica sospetta" or marker_tumorali == "CA 19-9 marcatamente elevato" or sintomi_pancreas == "Ittero ostruttivo":
        raccomandazioni.append("URGENTE: Sospetta patologia neoplastica pancreatica o ostruzione biliare. Indicazione a TC con protocollo pancreatico e valutazione urgente in Centro di Chirurgia Pancreatica.")
    elif imaging_pancreas == "Cisti pancreatica / Lesione cistica (es. IPMN / IPMN branch-duct)":
        raccomandazioni.append("Reperto di lesione cistica pancreatica: consigliata esecuzione di Ecoendoscopia (EUS) con studio del liquido cistico per stratificazione del rischio.")
    if "pancreatite" in imaging_pancreas.lower() or "Iperamilasemia" in funzione_pancreatica:
        raccomandazioni.append("Quadro di flogosi pancreatica: monitoraggio idratazione, supporto nutrizionale e valutazione eziologica (es. litiasica).")
    raccomandazioni.append(f"Percorso impostato: {percorso}")

    # Generazione Referto PDF
    if st.button("Genera Referto PDF Pancreas", type="primary", key="btn_pdf_pancreas"):
        if nome and cognome and codice_univoco:
            genera_o_aggiorna_registro(nome, cognome, data_nascita, codice_univoco)
            
            dettagli_visita = {
                "data": str(datetime.today().date()),
                "tipo": "Visita Gastroenterologica/Chirurgica - Modulo Pancreas",
                "dettagli": f"Sintomi: {sintomi_pancreas} | Imaging: {imaging_pancreas} | Marker CA 19-9: {marker_tumorali} | Funzione: {funzione_pancreatica}. Note: {note_cliniche}"
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
                label="📥 Scarica Referto PDF Pancreas",
                data=pdf_bytes,
                file_name=f"Referto_Pancreas_{cognome}_{nome}.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("Compilare Nome, Cognome e Codice Univoco per generare il referto.")
