from datetime import datetime
import streamlit as st
from utils import (
    carica_db_pazienti,
    salva_db_pazienti,
    genera_pdf_referto,
    ELENCO_MESI
)

def render_followup_chirurgia():
    st.subheader("🔪 Follow-up Dedicato: Post-Prostatectomia Radicale")
    
    db_file = carica_db_pazienti()
    codice_search = st.text_input("Inserisci Codice Univoco Paziente:", key="search_fu_chirurgia").strip().upper()

    if not codice_search:
        st.warning("⚠️ Inserisci il codice univoco del paziente per accedere al follow-up chirurgico.")
        return

    if codice_search not in db_file:
        st.error(f"❌ Nessun paziente trovato con il codice `{codice_search}`.")
        return

    paziente = db_file[codice_search]
    st.success(f"Paziente Trovato: **{paziente.get('cognome', '')} {paziente.get('nome', '')}** (ID: `{codice_search}`)")
    st.info("🎯 **Protocollo Attivo:** Follow-up Post-Chirurgico (Prostatectomia Radicale)")

    # Dati Istologici Definitivi (Prima Visita o Riepilogo)
    with st.expander("📋 Istologia Definitiva & Caratteristiche Chirurgiche (Baseline Post-Op)", expanded=False):
        col_st1, col_st2, col_st3 = st.columns(3)
        with col_st1:
            pt_stage = st.selectbox("Stadio Patologico (pT):", ["pT2", "pT3a", "pT3b", "pT4"], key="chir_pt")
        with col_st2:
            pn_stage = st.selectbox("Stato Linfonodale (pN):", ["pN0", "pN1", "pNX"], key="chir_pn")
        with col_st3:
            margini_r = st.selectbox("Margini Chirurgici (R):", ["R0 (Negativi)", "R1 (Microscopici positivi)", "R2 (Macroscopici positivi)"], key="chir_r")

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            isup_post = st.selectbox("Gruppo ISUP Post-Op:", [1, 2, 3, 4, 5], key="chir_isup")
        with col_g2:
            nerve_sparing = st.selectbox("Nerve Sparing:", ["No", "Monolaterale", "Bilaterale"], key="chir_ns")

    # Verifica Allerte Baseline (pT3+ o Margini positivi)
    if pt_stage in ["pT3a", "pT3b", "pT4"] or "R1" in margini_r or "R2" in margini_r:
        st.error("⚠️ **ATTENZIONE (Fattori di Rischio Anatomo-Patologici):** Rilevato stadio pT3/pT4 e/o Margini Chirurgici Positivi (R1/R2). **Considerare Radioterapia di Salvataggio (o adiuvante secondo indicazione multidisciplinare).**")

    # Visualizzazione Storico Visite
    with st.expander("📂 Visualizza Storico Visite e Controlli Chirurgici Precedenti", expanded=False):
        visite = paziente.get("visite", [])
        if not visite:
            st.write("Nessuna visita registrata nello storico.")
        for idx, v in enumerate(visite, 1):
            st.markdown(f"**Controllo {idx} — Data: {v.get('data')} | Tipo: {v.get('tipo')}**")
            st.text(v.get('dettagli', 'Nessun dettaglio'))
            st.markdown("---")

    st.markdown("---")
    st.markdown("### 🔄 Nuova Valutazione / Controllo Post-Op")

    with st.form("form_nuova_valutazione_chirurgia"):
        col_psa1, col_psa2, col_psa3 = st.columns(3)
        with col_psa1:
            mese_psa_a = st.selectbox("Mese Prelievo PSA", ELENCO_MESI, index=datetime.today().month - 1)
        with col_psa2:
            anno_psa_a = st.number_input("Anno Prelievo PSA", min_value=2000, max_value=2030, value=datetime.today().year)
        with col_psa3:
            psa_attuale = st.number_input("Valore PSA Post-Op (ng/ml):", min_value=0.0, value=float(paziente.get("ultimo_psa", 0.0)), step=0.001, format="%.3f")

        note_cliniche_fu = st.text_area("Dettagli clinici della visita, continenza, potenza o annotazioni:")

        scelta_fine_visita = st.selectbox(
            "Decisione presa a fine visita (Aggiornamento Percorso):",
            [
                "Prosegue Follow-up Biochimico",
                "Radioterapia di Salvataggio",
                "Terapia Ormonale / Altro"
            ]
        )

        submitted = st.form_submit_button("💾 Salva Nuova Valutazione & Genera Referto PDF", type="primary")

        if submitted:
            num_mese_a = ELENCO_MESI.index(mese_psa_a) + 1
            data_psa_attuale = datetime(anno_psa_a, num_mese_a, 1).date()

            paziente["ultimo_psa"] = psa_attuale
            paziente["data_ultimo_psa"] = str(data_psa_attuale)
            paziente["percorso_scelto"] = scelta_fine_visita

            # Controllo soglia < 0.2 per recidiva biochimica
            stato_psa_txt = "Negativo / Indetectable (< 0.2 ng/ml)" if psa_attuale < 0.2 else "⚠️ POSITIVO / Rialzo (≥ 0.2 ng/ml - Sospetta Recidiva Biochimica)"

            dettagli_fu = (
                f"Controllo Post-Prostatectomia Radicale\n"
                f"• Istologia: {pt_stage}, {pn_stage}, {margini_r}, ISUP {isup_post}, Nerve-Sparing: {nerve_sparing}\n"
                f"• PSA: {psa_attuale:.3f} ng/ml ({mese_psa_a} {anno_psa_a}) -> {stato_psa_txt}\n"
                f"• Decisione Finale: {scelta_fine_visita}"
            )
            if note_cliniche_fu:
                dettagli_fu += f"\n• Note Cliniche: {note_cliniche_fu}"

            dati_nuova_visita = {
                "data": str(datetime.today().date()),
                "tipo": f"Controllo Chirurgico ({scelta_fine_visita})",
                "dettagli": dettagli_fu
            }

            paziente["visite"].append(dati_nuova_visita)
            salva_db_pazienti(db_file)
            st.session_state["ultimo_paziente_fu_chirurgia"] = codice_search
            st.success("✅ Nuova valutazione chirurgica salvata correttamente nello storico!")

    # Box Alert Dinamico per PSA Post-Op >= 0.2
    if 'psa_attuale' in locals() and psa_attuale >= 0.2:
        st.error("⚠️ **ATTENZIONE (Recidiva Biochimica):** Valore di PSA post-prostatectomia $\\ge 0.2\\text{ ng/ml}$. **Considerare Radioterapia di Salvataggio.**")

    # Gestione download referto aggiornato
    if st.session_state.get("ultimo_paziente_fu_chirurgia"] == codice_search and paziente["visite"]:
        ultima_visita = paziente["visite"][-1]
        
        note_pdf = [
            f"Stadio Patologico: {pt_stage} | {pn_stage} | {margini_r} | ISUP {isup_post}",
            f"Nerve Sparing: {nerve_sparing}",
            f"Decisione di fine visita: {scelta_fine_visita}",
            note_cliniche_fu
        ]
        if 'psa_attuale' in locals() and psa_attuale >= 0.2:
            note_pdf.append("ATTENZIONE: PSA >= 0.2 ng/ml. Valutare radioterapia di salvataggio.")
            
        note_pdf = [n for n in note_pdf if n]
        
        pdf_bytes = genera_pdf_referto(
            codice_search, 
            ultima_visita, 
            scelta_fine_visita, 
            note_pdf, 
            nome=paziente.get('nome', ''), 
            cognome=paziente.get('cognome', '')
        )
        
        st.download_button(
            label="📄 Scarica Referto Post-Chirurgico in PDF",
            data=pdf_bytes,
            file_name=f"Referto_Chirurgia_{codice_search}.pdf",
            mime="application/pdf",
            key="download_pdf_chirurgia_aggiornato"
        )
