from datetime import datetime
import streamlit as st
from utils import genera_pdf_referto, salva_db_pazienti

def render_prostatectomia(paziente, db_attivo, codice_search):
    """Modulo dedicato alla gestione e follow-up dopo Prostatectomia Radicale."""
    st.markdown("### 🔵 Protocollo Post-Prostatectomia Radicale")
    st.info("Gestione clinica e monitoraggio biochimico post-chirurgico con esame istologico definitivo, controllo soglia PSA e tabella di follow-up.")
    
    with st.form(key="form_prostatectomia"):
        st.markdown("#### 🔬 Esame Istologico Definitivo")
        col_st1, col_st2, col_st3 = st.columns(3)
        with col_st1:
            pt_stage = st.selectbox("Stadio pT", ["pT2", "pT3a", "pT3b", "pT4"], key="px_pt")
        with col_st2:
            pn_stage = st.selectbox("Stadio pN", ["pN0", "pN1", "pNpx"], key="px_pn")
        with col_st3:
            margini_r = st.selectbox("Stato Margini Chirurgici (R)", ["R0 (negativi)", "R1 (focali/positivi)", "R2 (macroscopicamente positivi)"], key="px_r")

        st.markdown("---")
        st.markdown("#### 📈 Monitoraggio PSA Post-Operatorio")
        st.write("Il cut-off di allerta biochimica post-operatoria è fissato a **0.2 ng/mL**. Oltre questa soglia si attiva l'indicazione clinica per stadizzazione con PET-PSMA.")
        
        col_psa_post1, col_psa_post2, col_psa_post3 = st.columns(3)
        with col_psa_post1:
            valore_psa_post = st.number_input("Valore PSA Post-Operatorio (ng/mL)", min_value=0.0, max_value=50.0, value=0.0, step=0.01, key="px_psa_val")
        with col_psa_post2:
            mese_psa_post = st.selectbox("Mese Dosaggio", ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"], key="px_psa_mese")
        with col_psa_post3:
            anno_psa_post = st.number_input("Anno Dosaggio", min_value=2000, max_value=2100, value=datetime.today().year, step=1, key="px_psa_anno")

        # Controllo soglia di allerta per PET-PSMA
        allerta_pet = False
        if valore_psa_post >= 0.2:
            allerta_pet = True
            st.error(f"⚠️ **ATTENZIONE**: Il valore di PSA ({valore_psa_post} ng/mL) raggiunge o supera la soglia critica di 0.2 ng/mL. Indicazione clinica per rivalutazione con PET-PSMA.")
        else:
            st.success("✅ Valore di PSA post-operatorio inferiore alla soglia di allerta (0.2 ng/mL).")

        st.markdown("---")
        st.markdown("#### 📅 Tabella di Scadenziario Follow-up PSA (Standard)")
        st.write("Calendario consigliato dei controlli biochimici nel primo periodo post-chirurgico:")
        
        st.markdown("""
        | Tempistica Controllo | Obiettivo Clinico |
        | :--- | :--- |
        | **6 Settimane / 3 Mesi** | Valutazione nadir del PSA post-chirurgico |
        | **6 Mesi** | Controllo di stabilità biochimica |
        | **12 Mesi** | Rivalutazione annuale completa e controllo continenza/funzione |
        | **Ogni 6 Mesi (anni 2-3)** | Monitoraggio routinario |
        | **Ogni 12 Mesi (dal 4° anno)** | Follow-up a lungo termine |
        """)

        st.markdown("---")
        note_px = st.text_area("Note cliniche e raccomandazioni post-operatorie:", key="px_note")
        
        submit_px = st.form_submit_button("💾 Salva Dati Prostatectomia", type="primary")
        
        if submit_px:
            dettagli_px = (
                f"Prostatectomia Radicale - Istologico: {pt_stage}, {pn_stage}, Margini {margini_r} | "
                f"PSA Post-Op: {valore_psa_post} ng/mL ({mese_psa_post} {anno_psa_post}) "
                f"{'(ALLERTA PET-PSMA ATTIVATA)' if allerta_pet else '(Sotto soglia 0.2)'}\n"
                f"Note: {note_px}"
            )
            dati_v_px = {
                "data": str(datetime.today().date()),
                "tipo": "Follow-up Post-Prostatectomia",
                "dettagli": dettagli_px
            }
            if "visite" not in paziente:
                paziente["visite"] = []
            paziente["visite"].append(dati_v_px)
            salva_db_pazienti(db_attivo)
            st.success("Dati post-prostatectomia salvati correttamente!")

            # Generazione immediata del PDF per la stampa
            pdf_bytes = genera_pdf_referto(
                codice_search, 
                dati_v_px, 
                percorso="Monitoraggio post-prostatectomia radicale", 
                note_raccomandazioni=[note_px], 
                nome=paziente['nome'], 
                cognome=paziente['cognome']
            )
            st.download_button(
                label="📥 Scarica Referto / Verbale in PDF",
                data=pdf_bytes,
                file_name=f"Report_Prostatectomia_{codice_search}_{datetime.today().date()}.pdf",
                mime="application/pdf",
                key="download_pdf_prostatectomia"
            )
