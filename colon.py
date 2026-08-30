import streamlit as st
from datetime import datetime
from utils import genera_o_aggiorna_registro, genera_pdf_referto

def render_modulo():
    st.subheader("🌀 Modulo Colon - Decision Support System")
    
    # Anagrafica Paziente
    with st.expander("👤 Anagrafica Paziente", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            nome = st.text_input("Nome Paziente", key="colon_nome")
        with col2:
            cognome = st.text_input("Cognome Paziente", key="colon_cognome")
        with col3:
            codice_univoco = st.text_input("Codice Univoco / ID", key="colon_codice")
            
        data_nascita = st.date_input("Data di Nascita", key="colon_nascita")

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
    raccomandazioni.append(f"Percorso impostato: {percorso}")

    # Generazione Referto PDF
    if st.button("Genera Referto PDF Colon", type="primary", key="btn_pdf_colon"):
        if nome and cognome and codice_univoco:
            genera_o_aggiorna_registro(nome, cognome, data_nascita, codice_univoco)
            
            dettagli_visita = {
                "data": str(datetime.today().date()),
                "tipo": "Visita Gastroenterologica - Modulo Colon",
                "dettagli": f"Sintomi: {sintomi_intestinali} | Endoscopia: {esame_endoscopico} | Sangue Occulto: {sangue_occulto} | Familiarità: {familiarita}. Note: {note_cliniche}"
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
