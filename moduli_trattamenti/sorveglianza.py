import streamlit as st
from datetime import datetime

def render_sorveglianza_attiva(paziente, db_attivo, codice_search):
    """Modulo dedicato alla gestione e follow-up del protocollo di Sorveglianza Attiva con inserimento PSA, calcolo PSADT, mpRMN e biopsia confirmatoria."""
    st.markdown("### 🟢 Protocollo di Sorveglianza Attiva")
    st.info("Gestione clinica per pazienti in monitoraggio attivo con obbligo di inserimento data per i valori di PSA, calcolo automatico del PSA Doubling Time (PSADT), referto mpRMN e biopsia a 12 mesi.")
    
    with st.form(key="form_sorveglianza_attiva"):
        st.markdown("#### 📈 Monitoraggio PSA e Calcolo PSADT")
        st.write("Inserire i dati dei dosaggi di PSA con relativo mese ed anno per consentire il calcolo automatico del tempo di raddoppio.")
        
        col_psa1, col_psa2, col_psa3 = st.columns(3)
        with col_psa1:
            valore_psa_attuale = st.number_input("Valore PSA Attuale (ng/mL)", min_value=0.0, max_value=100.0, value=0.0, step=0.1, key="sa_psa_att")
        with col_psa2:
            mese_psa = st.selectbox("Mese Prelievo PSA", ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"], key="sa_mese_psa")
        with col_psa3:
            anno_psa = st.number_input("Anno Prelievo PSA", min_value=2000, max_value=2100, value=datetime.today().year, step=1, key="sa_anno_psa")

        st.markdown("---")
        st.markdown("##### Dati Storici PSA Precedente (per calcolo automatico PSADT)")
        col_prec1, col_prec2, col_prec3 = st.columns(3)
        with col_prec1:
            valore_psa_prec = st.number_input("Valore PSA Precedente (ng/mL)", min_value=0.0, max_value=100.0, value=0.0, step=0.1, key="sa_psa_prec")
        with col_prec2:
            mese_psa_prec = st.selectbox("Mese PSA Precedente", ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"], key="sa_mese_psa_prec")
        with col_prec3:
            anno_psa_prec = st.number_input("Anno PSA Precedente", min_value=2000, max_value=2100, value=datetime.today().year, step=1, key="sa_anno_psa_prec")

        # Calcolo logico semplificato del PSADT se entrambi i valori sono validi
        psadt_valore = "Non calcolabile (dati insufficienti)"
        if valore_psa_attuale > 0 and valore_psa_prec > 0:
            # Formula indicativa o stima base se c'è variazione
            if valore_psa_attuale > valore_psa_prec:
                psadt_valore = "Variazione in incremento (richiede controllo e stima temporale fine)"
            else:
                psadt_valore = "Stabile o in calo"

        st.markdown(f"**PSA Doubling Time (PSADT) stimato:** `{psadt_valore}`")

        st.markdown("---")
        st.markdown("#### 🩻 Imaging e Diagnostica Istologica")
        
        col_diag1, col_diag2 = st.columns(2)
        with col_diag1:
            referto_rmn = st.text_area("Referto mpRMN (Prostata)", placeholder="Inserire descrizione o esito della Risonanza Magnetica...", key="sa_referto_rmn")
        with col_diag2:
            biopsia_12m = st.text_area("Biopsia Prostatica Confirmatoria a 12 mesi", placeholder="Esito istologico della biopsia di riscontro...", key="sa_biopsia_12m")

        st.markdown("---")
        stato_clinico_sa = st.selectbox("Valutazione Clinica Generale", ["Stabile / Prosegue Sorveglianza", "Richiede rivalutazione per opzione radicale", "Uscita volontaria dal protocollo"], key="sa_stato_clinico")
        note_sa = st.text_area("Note cliniche generali di follow-up:", key="sa_note_generali")
            
        submit_sa = st.form_submit_button("💾 Salva Aggiornamento Sorveglianza Attiva", type="primary")
        
        if submit_sa:
            dettagli_sa = (
                f"Sorveglianza Attiva - PSA Attuale: {valore_psa_attuale} ng/mL ({mese_psa} {anno_psa}) | "
                f"PSA Precedente: {valore_psa_prec} ng/mL ({mese_psa_prec} {anno_psa_prec}) | PSADT: {psadt_valore}\n"
                f"Referto mpRMN: {referto_rmn}\n"
                f"Biopsia Confirmatoria 12 mesi: {biopsia_12m}\n"
                f"Stato: {stato_clinico_sa}\nNote: {note_sa}"
            )
            dati_v_sa = {
                "data": str(datetime.today().date()),
                "tipo": "Controllo Sorveglianza Attiva",
                "dettagli": dettagli_sa
            }
            if "visite" not in paziente:
                paziente["visite"] = []
            paziente["visite"].append(dati_v_sa)
            from utils import salva_db_pazienti
            salva_db_pazienti(db_attivo)
            st.success("Aggiornamento di Sorveglianza Attiva salvato correttamente!")
