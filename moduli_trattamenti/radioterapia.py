from datetime import datetime
import streamlit as st
from utils import genera_pdf_referto, salva_db_pazienti

def render_radioterapia(paziente, db_attivo, codice_search):
    """Modulo dedicato alla gestione e follow-up del trattamento Radioterapico con dettagli sui farmaci LH-RH e ARSI."""
    st.markdown("### 🟡 Protocollo di Radioterapia")
    st.info("Gestione del trattamento radioterapico, impostazione della dose, terapia ormonale associata con selezione specifica e ARSI, e monitoraggio biochimico con criteri di Phoenix (Nadir + 2 ng/mL).")
    
    # Sezione di monitoraggio PSA e calcolo Phoenix posta FUORI dal form per reattività immediata
    st.markdown("#### 📈 Monitoraggio PSA e Criteri di Recidiva (Phoenix)")
    st.write("Il cut-off di ripresa biochimica post-radioterapia è definito secondo i **Criteri di Phoenix** come **Nadir + 2.0 ng/mL**.")
    
    col_psa_rt1, col_psa_rt2, col_psa_rt3 = st.columns(3)
    with col_psa_rt1:
        valore_nadir = st.number_input("Valore Nadir PSA raggiunto (ng/mL)", min_value=0.0, max_value=50.0, value=0.0, step=0.01, key="rt_nadir")
    with col_psa_rt2:
        valore_psa_attuale_rt = st.number_input("Valore PSA Attuale di Controllo (ng/mL)", min_value=0.0, max_value=50.0, value=0.0, step=0.01, key="rt_psa_att")
    with col_psa_rt3:
        soglia_phoenix = valore_nadir + 2.0
        st.metric("Soglia Critica di Recidiva (Nadir + 2)", f"{soglia_phoenix:.2f} ng/mL")

    allerta_phoenix = False
    if valore_nadir > 0 and valore_psa_attuale_rt >= soglia_phoenix:
        allerta_phoenix = True
        st.error(f"🚨 **ALLERTA BIOCHIMICA (Criteri di Phoenix)**: Il PSA attuale ({valore_psa_attuale_rt} ng/mL) supera la soglia critica di Nadir + 2 ng/mL ({soglia_phoenix:.2f} ng/mL). Sospetta recidiva biochimica.")
    else:
        st.success("✅ Valore di PSA sotto la soglia di fallimento biochimico di Phoenix.")

    st.markdown("---")

    with st.form(key="form_radioterapia"):
        st.markdown("#### ⚡ Caratteristiche del Trattamento Radioterapico")
        
        col_rt1, col_rt2, col_rt3 = st.columns(3)
        with col_rt1:
            tipo_rt = st.selectbox("Tipologia di Frazionamento", ["Standard", "Ipofrazionata moderata", "Ipofrazionata ultra (5 sedute)", "Single Treatment (SBRT/HDR)"], key="rt_tipo")
        with col_rt2:
            dose_gy = st.number_input("Dose Totale (Gy)", min_value=0.0, max_value=100.0, value=0.0, step=0.5, key="rt_gy")
        with col_rt3:
            classe_rischio = st.selectbox("Classe di Rischio NCCN/EAU", ["Basso Rischio", "Intermedio Favorevole", "Intermedio Sfavorevole", "Alto Rischio", "Molto Alto Rischio"], key="rt_rischio")

        st.markdown("---")
        st.markdown("#### 💉 Terapia Ormonale e Associazione ARSI")
        
        col_LHRH1, col_LHRH2, col_LHRH3 = st.columns(3)
        with col_LHRH1:
            fatto_lhrh = st.selectbox("Terapia LH-RH eseguita?", ["No", "Sì"], key="rt_lhrh_check")
        with col_LHRH2:
            tipo_lhrh = st.selectbox("Molecola LH-RH", ["Nessuna", "Triptorelina", "Leuprorelina", "Relugolix"], key="rt_tipo_lhrh")
        with col_LHRH3:
            data_inizio_lhrh = st.date_input("Data di inizio terapia LH-RH", value=datetime.today(), key="rt_lhrh_data")

        col_arsi1, col_arsi2 = st.columns(2)
        with col_arsi1:
            usa_arsi = st.selectbox("Associazione con ARSI (Androgen Receptor Signaling Inhibitor)?", ["No", "Sì"], key="rt_arsi_check")
        with col_arsi2:
            tipo_arsi = st.selectbox("Molecola ARSI", ["Nessuna", "Apalutamide", "Darolutamide", "Enzalutamide", "Abiraterone"], key="rt_tipo_arsi")

        if fatto_lhrh == "Sì":
            if "Basso" in classe_rischio:
                st.info("ℹ️ **Linee Guida**: Per i pazienti a basso rischio, la terapia ormonale neoadiuvante/adiuvante non è solitamente raccomandata.")
            elif "Intermedio" in classe_rischio:
                st.info("ℹ️ **Linee Guida (Rischio Intermedio)**: Raccomandata terapia ormonale a breve termine (4-6 mesi).")
            elif "Alto" in classe_rischio or "Molto Alto" in classe_rischio:
                st.warning("⚠️ **Linee Guida (Alto/Molto Alto Rischio)**: Raccomandata terapia ormonale a lungo termine (18-36 mesi).")

        st.markdown("---")
        st.markdown("#### 📅 Tabella di Scadenziario Follow-up PSA Post-Radioterapia")
        st.markdown("""
        | Tempistica Controllo | Obiettivo Clinico |
        | :--- | :--- |
        | **3 - 6 Mesi** | Prima valutazione di tendenza del PSA post-trattamento |
        | **Ogni 6 Mesi (per i primi 3 anni)** | Monitoraggio ravvicinato del trend e ricerca del Nadir |
        | **Ogni 12 Mesi (dal 4° anno in poi)** | Follow-up a lungo termine |
        """)

        st.markdown("---")
        note_rt = st.text_area("Note cliniche e raccomandazioni radioterapiche:", key="rt_note")
        
        submit_rt = st.form_submit_button("💾 Salva Dati Radioterapia", type="primary")
        
        if submit_rt:
            dettagli_rt = (
                f"Radioterapia - Tipo: {tipo_rt}, Dose: {dose_gy} Gy, Rischio: {classe_rischio} | "
                f"Terapia LH-RH: {fatto_lhrh} (Molecola: {tipo_lhrh}, Inizio: {data_inizio_lhrh if fatto_lhrh=='Sì' else 'N/A'}) | "
                f"ARSI: {usa_arsi} (Molecola: {tipo_arsi}) | "
                f"Nadir: {valore_nadir} ng/mL, PSA Attuale: {valore_psa_attuale_rt} ng/mL "
                f"{'(ATTIVATA ALLERTA PHOENIX NADIR+2)' if allerta_phoenix else '(Sotto soglia Phoenix)'}\n"
                f"Note: {note_rt}"
            )
            dati_v_rt = {
                "data": str(datetime.today().date()),
                "tipo": "Follow-up Radioterapia",
                "dettagli": dettagli_rt
            }
            if "visite" not in paziente:
                paziente["visite"] = []
            paziente["visite"].append(dati_v_rt)
            salva_db_pazienti(db_attivo)
            st.success("Dati di radioterapia salvati correttamente!")

            pdf_bytes = genera_pdf_referto(
                codice_search, 
                dati_v_rt, 
                percorso="Monitoraggio post-trattamento radioterapico", 
                note_raccomandazioni=[note_rt], 
                nome=paziente['nome'], 
                cognome=paziente['cognome']
            )
            st.download_button(
                label="📥 Scarica Referto / Verbale in PDF",
                data=pdf_bytes,
                file_name=f"Report_Radioterapia_{codice_search}_{datetime.today().date()}.pdf",
                mime="application/pdf",
                key="download_pdf_radioterapia"
            )
