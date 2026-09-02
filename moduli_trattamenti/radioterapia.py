from datetime import datetime
import streamlit as st
from utils import (
    carica_db_pazienti,
    salva_db_pazienti,
    genera_pdf_referto,
    ELENCO_MESI
)

def calcola_criteri_phoenix(nadir_psa, psa_attuale, storia_psa):
    """
    Criteri Phoenix (ASTRO/RTOG): Recidiva biochimica post-radioterapia 
    definita come un incremento del PSA pari o superiore al nadir + 2.0 ng/ml.
    """
    if nadir_psa is None:
        return False, "Nadir non ancora registrato."
    
    soglia_recidiva = nadir_psa + 2.0
    if psa_attuale >= soglia_recidiva:
        return True, f"⚠️ RECIDIVA BIOCHIMICA (Criteri Phoenix): PSA attuale ({psa_attuale} ng/ml) >= Nadir ({nadir_psa} ng/ml) + 2.0 ng/ml (Soglia: {soglia_recidiva:.2f} ng/ml)."
    else:
        return False, f"🟢 PSA sotto soglia Phoenix (Nadir: {nadir_psa} ng/ml, Soglia allerta: {soglia_recidiva:.2f} ng/ml)."

def render_followup_radioterapia():
    st.subheader("⚡ Follow-up Dedicato: Post-Radioterapia (RT)")
    
    db_file = carica_db_pazienti()
    codice_search = st.text_input("Inserisci Codice Univoco Paziente:", key="search_fu_rt").strip().upper()

    if not codice_search:
        st.warning("⚠️ Inserisci il codice univoco del paziente per accedere al follow-up radioterapico.")
        return

    if codice_search not in db_file:
        st.error(f"❌ Nessun paziente trovato con il codice `{codice_search}`.")
        return

    paziente = db_file[codice_search]
    st.success(f"Paziente Trovato: **{paziente.get('cognome', '')} {paziente.get('nome', '')}** (ID: `{codice_search}`)")
    st.info("🎯 **Protocollo Attivo:** Follow-up Post-Radioterapia")

    # Dettagli del Trattamento Radioterapico (Baseline)
    with st.expander("📋 Dettagli Trattamento Radioterapico & Terapia Sistemica (Baseline)", expanded=False):
        col_rt1, col_rt2, col_rt3 = st.columns(3)
        with col_rt1:
            schema_rt = st.selectbox(
                "Schema Radioterapico:",
                [
                    "Convenzionale / Frazionamento Standard",
                    "Ipofrazionato Moderato",
                    "Stereotassico / SBRT Ultra-ipofrazionato (5 sedute)",
                    "Altro / Brachiterapia"
                ],
                key="rt_schema"
            )
        with col_rt2:
            dose_gy = st.number_input("Dose Totale (Gy):", min_value=0.0, max_value=100.0, value=78.0, step=0.5, key="rt_gy")
        with col_rt3:
            trattamento_linfonodi = st.selectbox("Irradiazione Linfonodale:", ["No", "Sì (Pelvici / Selettivi)"], key="rt_ln")

        col_ter1, col_ter2 = st.columns(2)
        with col_ter1:
            terapia_lhrh = st.selectbox(
                "Terapia con LHRH (Agonista/Antagonista):",
                ["Non associata", "Leuprorelina", "Triptorelina", "Relugolix"],
                key="rt_lhrh"
            )
        with col_ter2:
            terapia_arsi = st.selectbox(
                "Inibitore del Recettore degli Androgeni (ARSI):",
                ["Non associato", "Apalutamide", "Darolutamide", "Enzalutamide", "Abiraterone"],
                key="rt_arsi"
            )

    # Gestione del Nadir PSA nel profilo paziente
    if "nadir_psa" not in paziente:
        paziente["nadir_psa"] = None

    # Visualizzazione Storico Visite
    with st.expander("📂 Visualizza Storico Visite e Controlli RT Precedenti", expanded=False):
        visite = paziente.get("visite", [])
        if not visite:
            st.write("Nessuna visita registrata nello storico.")
        for idx, v in enumerate(visite, 1):
            st.markdown(f"**Controllo {idx} — Data: {v.get('data')} | Tipo: {v.get('tipo')}**")
            st.text(v.get('dettagli', 'Nessun dettaglio'))
            st.markdown("---")

    st.markdown("---")
    st.markdown("### 🔄 Nuova Valutazione / Controllo Post-RT")

    with st.form("form_nuova_valutazione_rt"):
        col_psa1, col_psa2, col_psa3 = st.columns(3)
        with col_psa1:
            mese_psa_a = st.selectbox("Mese Prelievo PSA", ELENCO_MESI, index=datetime.today().month - 1)
        with col_psa2:
            anno_psa_a = st.number_input("Anno Prelievo PSA", min_value=2000, max_value=2030, value=datetime.today().year)
        with col_psa3:
            psa_attuale = st.number_input("Valore PSA Attuale (ng/ml):", min_value=0.0, value=float(paziente.get("ultimo_psa", 0.0)), step=0.001, format="%.3f")

        note_cliniche_fu = st.text_area("Dettagli clinici della visita, tossicità genito-urinaria/intestinale o annotazioni:")

        scelta_fine_visita = st.selectbox(
            "Decisione presa a fine visita (Aggiornamento Percorso):",
            [
                "Prosegue Follow-up Biochimico RT",
                "Approfondimento di Stadiazione (PET-Cholina / PSMA)",
                "Terapia Medica di Salvataggio / OME"
            ]
        )

        submitted = st.form_submit_button("💾 Salva Nuova Valutazione & Genera Referto PDF", type="primary")

        if submitted:
            num_mese_a = ELENCO_MESI.index(mese_psa_a) + 1
            data_psa_attuale = datetime(anno_psa_a, num_mese_a, 1).date()

            # Aggiornamento logica Nadir PSA
            nadir_attuale = paziente.get("nadir_psa")
            if nadir_attuale is None or psa_attuale < nadir_attuale:
                paziente["nadir_psa"] = psa_attuale
                nadir_utilizzato = psa_attuale
            else:
                nadir_utilizzato = nadir_attuale

            paziente["ultimo_psa"] = psa_attuale
            paziente["data_ultimo_psa"] = str(data_psa_attuale)
            paziente["percorso_scelto"] = scelta_fine_visita

            # Valutazione Criteri Phoenix
            is_recidiva, messaggio_phoenix = calcola_criteri_phoenix(paziente["nadir_psa"], psa_attuale, paziente.get("visite", []))

            dettagli_fu = (
                f"Controllo Post-Radioterapia\n"
                f"• Schema: {schema_rt} ({dose_gy} Gy), Linfonodi: {trattamento_linfonodi}\n"
                f"• Terapia Sistemica: LHRH ({terapia_lhrh}) | ARSI ({terapia_arsi})\n"
                f"• PSA: {psa_attuale:.3f} ng/ml ({mese_psa_a} {anno_psa_a}) | Nadir: {nadir_utilizzato:.3f} ng/ml\n"
                f"• Esito Phoenix: {messaggio_phoenix}\n"
                f"• Decisione Finale: {scelta_fine_visita}"
            )
            if note_cliniche_fu:
                dettagli_fu += f"\n• Note Cliniche: {note_cliniche_fu}"

            dati_nuova_visita = {
                "data": str(datetime.today().date()),
                "tipo": f"Controllo RT ({scelta_fine_visita})",
                "dettagli": dettagli_fu
            }

            paziente["visite"].append(dati_nuova_visita)
            salva_db_pazienti(db_file)
            st.session_state["ultimo_paziente_fu_rt"] = codice_search
            st.success("✅ Nuova valutazione radioterapica salvata correttamente nello storico!")

    # Box Alert Dinamico per Criteri Phoenix
    if "nadir_psa" in paziente and paziente["nadir_psa"] is not None:
        is_rec_alert, msg_alert = calcola_criteri_phoenix(paziente["nadir_psa"], paziente.get("ultimo_psa", 0.0), paziente.get("visite", []))
        if is_rec_alert:
            st.error(f"⚠️ **{msg_alert}**")
        else:
            st.success(f"🟢 **{msg_alert}**")

    # Gestione download referto aggiornato
    if st.session_state.get("ultimo_paziente_fu_rt"] == codice_search and paziente["visite"]:
        ultima_visita = paziente["visite"][-1]
        
        note_pdf = [
            f"Schema RT: {schema_rt} ({dose_gy} Gy) | Linfonodi: {trattamento_linfonodi}",
            f"Terapia associata: LHRH ({terapia_lhrh}), ARSI ({terapia_arsi})",
            f"Nadir PSA: {paziente.get('nadir_psa')} ng/ml",
            f"Decisione di fine visita: {scelta_fine_visita}",
            note_cliniche_fu
        ]
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
            label="📄 Scarica Referto Post-Radioterapia in PDF",
            data=pdf_bytes,
            file_name=f"Referto_Radioterapia_{codice_search}.pdf",
            mime="application/pdf",
            key="download_pdf_rt_aggiornato"
        )
