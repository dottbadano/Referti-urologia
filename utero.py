import streamlit as st
from datetime import datetime
from utils import genera_o_aggiorna_registro, genera_pdf_referto

def render_modulo():
    st.subheader("♀️ Modulo Utero - Decision Support System")
    
    # Anagrafica Paziente
    with st.expander("👤 Anagrafica Paziente", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            nome = st.text_input("Nome Paziente", key="utero_nome")
        with col2:
            cognome = st.text_input("Cognome Paziente", key="utero_cognome")
        with col3:
            codice_univoco = st.text_input("Codice Univoco / ID", key="utero_codice")
            
        data_nascita = st.date_input("Data di Nascita", key="utero_nascita")

    st.divider()

    # Parametri Clinici Utero
    st.markdown("### 📋 Parametri Clinici e Valutazione Ginecologica")
    
    col_a, col_b = st.columns(2)
    with col_a:
        sintomi_ginecologici = st.selectbox(
            "Sintomi / Anamnesi Mestruale",
            [
                "Ciclo regolare / Asintomatica", 
                "Menorragia / Metrorragia (Sanguinamenti anomali)", 
                "Dismenorga severa (Dolore pelvico)", 
                "Sanguinamento in post-menopausa", 
                "Sensazione di peso pelvico"
            ],
            key="utero_sintomi"
        )
        imaging_utero = st.selectbox(
            "Quadro Imaging (Ecografia Transvaginale / RMN)",
            [
                "Normale", 
                "Miomi uterini / Fibromi", 
                "Iperplasia endometriale / Ispessimento rima", 
                "Polipo endometriale", 
                "Sospetta neoformazione miometriale o endometriale"
            ],
            key="utero_imaging"
        )
    with col_b:
        pap_test_hpv = st.selectbox(
            "Stato Screening (Pap-test / HPV test)",
            ["Negativo / Nella norma", "HPV Positivo", "Pap-test alterato / ASC-US / LSIL / HSIL", "Non eseguito di recente"],
            key="utero_screening"
        )
        stato_menopausa = st.selectbox(
            "Stato Riproduttivo",
            ["Età fertile / Regolare", "Perimenopausa", "Post-menopausa"],
            key="utero_menopausa"
        )

    note_cliniche = st.text_area("Note Cliniche / Anamnesi Utero", placeholder="Inserire note cliniche aggiuntive...", key="utero_note")

    st.divider()

    # Percorso Clinico e Raccomandazioni
    st.markdown("### 🧭 Percorso Clinico e Raccomandazioni")
    
    percorso = st.selectbox(
        "Seleziona Percorso Clinico",
        [
            "Follow-up Ginecologico / Monitoraggio Ecografico",
            "Isteroscopia diagnostica ed eventuale biopsia / polipectomia",
            "Valutazione per Trattamento Medico (Ormonale / Sintomatico)",
            "Valutazione Chirurgica Specialistica (Chirurgia Uterina / Miomectomia / Isterectomia)"
        ],
        key="utero_percorso"
    )

    raccomandazioni = []
    if sintomi_ginecologici == "Sanguinamento in post-menopausa" or imaging_utero == "Iperplasia endometriale / Ispessimento rima":
        raccomandazioni.append("URGENTE: Indicazione a isteroscopia diagnostica con biopsia endometriale per escludere patologia neoplastica.")
    elif imaging_utero == "Polipo endometriale":
        raccomandazioni.append("Consigliata isteroscopia operativa per rimozione ed esame istologico del polipo.")
    if pap_test_hpv == "HPV Positivo" or "alterato" in pap_test_hpv:
        raccomandazioni.append("Indicazione a colposcopia di approfondimento per positività/alterazione dello screening.")
    raccomandazioni.append(f"Percorso impostato: {percorso}")

    # Generazione Referto PDF
    if st.button("Genera Referto PDF Utero", type="primary", key="btn_pdf_utero"):
        if nome and cognome and codice_univoco:
            genera_o_aggiorna_registro(nome, cognome, data_nascita, codice_univoco)
            
            dettagli_visita = {
                "data": str(datetime.today().date()),
                "tipo": "Visita Ginecologica - Modulo Utero",
                "dettagli": f"Sintomi: {sintomi_ginecologici} | Imaging: {imaging_utero} | Screening: {pap_test_hpv} | Stato: {stato_menopausa}. Note: {note_cliniche}"
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
                label="📥 Scarica Referto PDF Utero",
                data=pdf_bytes,
                file_name=f"Referto_Utero_{cognome}_{nome}.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("Compilare Nome, Cognome e Codice Univoco per generare il referto.")
