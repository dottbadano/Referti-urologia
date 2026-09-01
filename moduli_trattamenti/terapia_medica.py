import streamlit as st
from datetime import datetime

def render_terapia_medica(paziente, db_attivo, codice_search):
    """Modulo dedicato alla gestione e follow-up della Terapia Medica (ormonale, ARSI, chemioterapia e PARPi)."""
    st.markdown("### 🟡 Protocollo di Terapia Medica Avanzata")
    st.info("Gestione della malattia metastatica o avanzata, definizione del volume tumorale (Criteri CHAARTED/STAMPEDE), terapie sistemiche (LH-RH, ARSI, chemioterapia), mutazioni BRCA e target therapy (PARPi), con monitoraggio di PSA e testosteronemia.")
    
    with st.form(key="form_terapia_medica"):
        st.markdown("#### 🌍 Caratteristiche di Malattia e Volume (Criteri CHAARTED / STAMPEDE)")
        
        col_vol1, col_vol2 = st.columns(2)
        with col_vol1:
            presenza_metastasi = st.selectbox("Presenza di Metastasi", ["No (M0 / Ormonodipendente non metastatica)", "Sì (M1 / Malattia metastatica)"], key="tm_metastasi_check")
        with col_vol2:
            volume_malattia = st.selectbox("Volume di Malattia (Criteri CHAARTED/STAMPEDE)", ["Non applicabile (M0)", "Low Volume (Basso volume)", "High Volume (Alto volume: metastasi viscerali o >=4 lesioni ossee con almeno una extra-assiale/vertebrale)"], key="tm_volume")

        st.markdown("---")
        st.markdown("#### 💉 Terapia Ormonale e ARSI")
        
        col_LHRH1, col_LHRH2, col_LHRH3 = st.columns(3)
        with col_LHRH1:
            fatto_lhrh_tm = st.selectbox("Terapia LH-RH in corso?", ["No", "Sì"], key="tm_lhrh_check")
        with col_LHRH2:
            tipo_lhrh_tm = st.selectbox("Molecola LH-RH", ["Nessuna", "Triptorelina", "Leuprorelina", "Relugolix"], key="tm_tipo_lhrh")
        with col_LHRH3:
            data_inizio_lhrh_tm = st.date_input("Data di inizio LH-RH", value=datetime.today(), key="tm_lhrh_data")

        col_arsi1, col_arsi2 = st.columns(2)
        with col_arsi1:
            usa_arsi_tm = st.selectbox("Associazione con ARSI?", ["No", "Sì"], key="tm_arsi_check")
        with col_arsi2:
            tipo_arsi_tm = st.selectbox("Molecola ARSI", ["Nessuna", "Apalutamide", "Darolutamide", "Enzalutamide", "Abiraterone"], key="tm_tipo_arsi")

        st.markdown("---")
        st.markdown("#### 💊 Chemioterapia e Target Therapy (PARP Inibitori)")
        
        col_chem1, col_chem2 = st.columns(2)
        with col_chem1:
            usa_chemio = st.selectbox("Chemioterapia associata?", ["No", "Sì"], key="tm_chemio_check")
        with col_chem2:
            tipo_chemio = st.selectbox("Molecola Chemioterapica", ["Nessuna", "Docetaxel", "Cabazitaxel"], key="tm_tipo_chemio")

        st.markdown("##### 🧬 Profilo Mutazionale e PARP Inibitori")
        col_parp1, col_parp2 = st.columns(2)
        with col_parp1:
            brca_mutato = st.checkbox("Paziente con mutazione BRCA1/2 o HRR (Homologous Recombination Repair)", key="tm_brca_check")
        with col_parp2:
            tipo_parpi = st.selectbox("Scelta PARP Inibitore (PARPi)", ["Nessuno", "Olaparib", "Niraparib", "Talazoparib"], key="tm_tipo_parpi")

        st.markdown("---")
        st.markdown("#### 📈 Monitoraggio Biochimico (PSA e Testosteronemia)")
        
        col_bio1, col_bio2, col_bio3 = st.columns(3)
        with col_bio1:
            valore_psa_tm = st.number_input("Valore PSA Attuale (ng/mL)", min_value=0.0, max_value=1000.0, value=0.0, step=0.1, key="tm_psa_val")
        with col_bio2:
            valore_testosterone = st.number_input("Testosteronemia (ng/dL)", min_value=0.0, max_value=1500.0, value=0.0, step=1.0, key="tm_testosterone")
        with col_bio3:
            target_castrazione = st.selectbox("Target Testosterone di Castrazione (< 50 ng/dL)?", ["Raggiunto (< 50 ng/dL)", "Non raggiunto (>= 50 ng/dL - Fuga biochimica)"], key="tm_target_test")

        # Controllo testosteronemia
        if "Non raggiunto" in target_castrazione:
            st.error("⚠️ **ATTENZIONE**: Il livello di testosterone non rientra nel range di castrazione chirurgica/medica (< 50 ng/dL). Valutare la compliance o l'efficacia del blocco androgenico.")
        else:
            st.success("✅ Livello di testosteronemia in target di castrazione.")

        st.markdown("---")
        st.markdown("#### 📅 Tabella di Scadenziario Follow-up Terapia Medica")
        st.markdown("""
        | Tempistica Controllo | Obiettivo Clinico |
        | :--- | :--- |
        | **Ogni 1 - 3 Mesi** | Dosaggio PSA, testosteronemia e valutazione clinica di tolleranza alla terapia sistemica |
        | **Ogni 3 - 6 Mesi** | Rivalutazione radiologica di stesura di malattia (TC/Scintigrafia o PET nei casi indicati) |
        | **Ad ogni ciclo (durante chemioterapia)** | Esami ematochimici completi, emocromo e funzione epatica/renale |
        """)

        st.markdown("---")
        note_tm = st.text_area("Note cliniche e raccomandazioni di terapia medica:", key="tm_note")
        
        submit_tm = st.form_submit_button("💾 Salva Dati Terapia Medica", type="primary")
        
        if submit_tm:
            dettagli_tm = (
                f"Terapia Medica - Metastasi: {presenza_metastasi}, Volume: {volume_malattia} | "
                f"LH-RH: {fatto_lhrh_tm} (Molecola: {tipo_lhrh_tm}) | ARSI: {usa_arsi_tm} (Molecola: {tipo_arsi_tm}) | "
                f"Chemioterapia: {usa_chemio} ({tipo_chemio}) | BRCA Mutato: {brca_mutato} (PARPi: {tipo_parpi}) | "
                f"PSA: {valore_psa_tm} ng/mL, Testosterone: {valore_testosterone} ng/dL ({target_castrazione})\n"
                f"Note: {note_tm}"
            )
            dati_v_tm = {
                "data": str(datetime.today().date()),
                "tipo": "Follow-up Terapia Medica",
                "dettagli": dettagli_tm
            }
            if "visite" not in paziente:
                paziente["visite"] = []
            paziente["visite"].append(dati_v_tm)
            from utils import salva_db_pazienti
            salva_db_pazienti(db_attivo)
            st.success("Dati di terapia medica salvati correttamente!")
