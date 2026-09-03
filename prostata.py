from datetime import datetime
import math
import streamlit as st
from utils import (
    carica_db_pazienti,
    salva_db_pazienti,
    genera_o_aggiorna_registro,
    genera_pdf_referto,
    salva_paziente_su_drive,
    ELENCO_MESI
)
from anamnesi_comune import (
    render_anagrafica_e_anamnesi_unificata,
    formatta_anamnesi_per_pdf_unificata
)

# --- FUNZIONI DI SUPPORTO PER IL FOLLOW-UP ---

def calcola_psadt(psa_precedente, data_precedente_str, psa_attuale, data_attuale):
    """Calcola il tempo di raddoppio del PSA (PSADT) in mesi."""
    try:
        if not psa_precedente or not data_precedente_str:
            return None
        p_prec = float(psa_precedente)
        if p_prec <= 0 or psa_attuale <= 0:
            return None
        
        d_prec = datetime.strptime(data_precedente_str, "%Y-%m-%d").date()
        giorni_diff = (data_attuale - d_prec).days
        if giorni_diff <= 0:
            return None
        
        anni_diff = giorni_diff / 365.25
        if psa_attuale <= p_prec:
            return "Stabile / In calo"
        
        import math
        psadt = (365.25 * math.log(2) * anni_diff) / (math.log(psa_attuale / p_prec) * 365.25 / 30.44)
        return round(psadt, 1)
    except Exception:
        return None

# --- MODULI DI FOLLOW-UP AVANZATO ---

def render_followup_sorveglianza_avanzato(paziente, db_attivo, codice_search):
    st.markdown("---")
    st.markdown("### 🔄 Gestione Follow-up: Sorveglianza Attiva")
    
    with st.form("form_nuova_valutazione_sa"):
        col_psa1, col_psa2, col_psa3 = st.columns(3)
        with col_psa1:
            mese_psa_a = st.selectbox("Mese Prelievo PSA", ELENCO_MESI, index=datetime.today().month - 1, key="sa_mese_psa")
        with col_psa2:
            anno_psa_a = st.number_input("Anno Prelievo PSA", min_value=2000, max_value=2030, value=datetime.today().year, key="sa_anno_psa")
        with col_psa3:
            psa_attuale = st.number_input("Valore PSA Attuale (ng/ml):", min_value=0.0, value=float(paziente.get("ultimo_psa", 0.0)), step=0.01, key="sa_valore_psa")

        col_img1, col_img2 = st.columns(2)
        with col_img1:
            repertoprecise = st.selectbox(
                "Reperto RMN di Controllo (Punteggio PRECISE):",
                [
                    "Non Eseguita",
                    "PRECISE 1 - Regressione sostanziale",
                    "PRECISE 2 - Lieve regressione",
                    "PRECISE 3 - Stabile / Nessun cambiamento significativo",
                    "PRECISE 4 - Moderata evidenza di progressione",
                    "PRECISE 5 - Sostanziale evidenza di progressione"
                ],
                key="sa_reperto_precise"
            )
        with col_img2:
            dre_esito = st.selectbox(
                "Esplorazione Rettale (DRE):",
                ["Negativa", "Positiva (Sospetto locale / Modificazione)"],
                key="sa_esito_dre"
            )

        note_cliniche_fu = st.text_area("Dettagli clinici della visita, sintomi o annotazioni:", key="sa_note_cliniche")

        scelta_fine_visita = st.selectbox(
            "Decisione presa a fine visita (Aggiornamento Percorso):",
            [
                "Prosegue Sorveglianza Attiva",
                "Prostatectomia",
                "Radioterapia"
            ],
            key="sa_decisione_fine"
        )

        submitted = st.form_submit_button("💾 Salva Nuova Valutazione & Genera Referto PDF", type="primary")

        if submitted:
            num_mese_a = ELENCO_MESI.index(mese_psa_a) + 1
            data_psa_attuale = datetime(anno_psa_a, num_mese_a, 1).date()
            
            psadt_calcolato = calcola_psadt(paziente.get("ultimo_psa"), paziente.get("data_ultimo_psa"), psa_attuale, data_psa_attuale)

            paziente["ultimo_psa"] = psa_attuale
            paziente["data_ultimo_psa"] = str(data_psa_attuale)
            paziente["percorso_scelto"] = scelta_fine_visita
            
            dettagli_fu = (
                f"Controllo Follow-up (Sorveglianza Attiva)\n"
                f"• PSA: {psa_attuale:.2f} ng/ml ({mese_psa_a} {anno_psa_a})\n"
                f"• PSADT Calcolato: {psadt_calcolato if psadt_calcolato else 'Stabile / Non calcolabile'} mesi\n"
                f"• RMN Controllo (PRECISE): {repertoprecise}\n"
                f"• Esplorazione Rettale (DRE): {dre_esito}\n"
                f"• Decisione Finale: {scelta_fine_visita}"
            )
            if note_cliniche_fu:
                dettagli_fu += f"\n• Note Cliniche: {note_cliniche_fu}"

            dati_nuova_visita = {
                "data": str(datetime.today().date()),
                "tipo": f"Visita di Controllo ({scelta_fine_visita})",
                "dettagli": dettagli_fu
            }
            
            paziente["visite"].append(dati_nuova_visita)
            salva_db_pazienti(db_attivo)
            st.session_state["ultimo_paziente_fu_sa"] = codice_search
            st.success("✅ Nuova valutazione di sorveglianza salvata correttamente!")

    if st.session_state.get("ultimo_paziente_fu_sa") == codice_search and paziente["visite"]:
        ultima_visita = paziente["visite"][-1]
        note_pdf = [
            f"Valutazione RMN: {repertoprecise}",
            f"Esito DRE: {dre_esito}",
            f"Decisione di fine visita: {scelta_fine_visita}",
            note_cliniche_fu
        ]
        note_pdf = [n for n in note_pdf if n]
        
        pdf_bytes = genera_pdf_referto(
            codice_search, ultima_visita, scelta_fine_visita, note_pdf, 
            nome=paziente.get('nome', ''), cognome=paziente.get('cognome', '')
        )
        st.download_button(
            label="📄 Scarica Referto Sorveglianza Attiva PDF",
            data=pdf_bytes,
            file_name=f"Referto_Sorveglianza_Attiva_{codice_search}.pdf",
            mime="application/pdf",
            key="dl_pdf_sa"
        )


def render_followup_chirurgia_avanzato(paziente, db_attivo, codice_search):
    st.markdown("---")
    st.markdown("### 🔪 Gestione Follow-up: Prostatectomia")
    
    with st.form("form_nuova_valutazione_ch"):
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            mese_psa_c = st.selectbox("Mese Dosaggio PSA", ELENCO_MESI, index=datetime.today().month - 1, key="ch_mese_psa")
        with col_c2:
            anno_psa_c = st.number_input("Anno Dosaggio PSA", min_value=2000, max_value=2030, value=datetime.today().year, key="ch_anno_psa")
        with col_c3:
            psa_post = st.number_input("Valore PSA Post-Operatorio (ng/ml):", min_value=0.0, value=float(paziente.get("ultimo_psa", 0.0)), step=0.001, format="%.3f", key="ch_valore_psa")

        col_q1, col_q2 = st.columns(2)
        with col_q1:
            continenza = st.selectbox(
                "Stato della Continenza Urinaria:",
                [
                    "Completamente continente (0 pad/die)",
                    "Lieve incontinenza / Sicurezza (1 pad di sicurezza/die)",
                    "Incontinenza da sforzo moderata (2 pad/die)",
                    "Incontinenza severa (> 2 pad/die o pannolone)"
                ],
                key="ch_continenza"
            )
        with col_q2:
            funzione_erettile = st.selectbox(
                "Funzione Erettile / Riabilitazione:",
                [
                    "Non valutabile / Paziente non interessato",
                    "Funzione preservata / Valida con o senza farmaci",
                    "Disfunzione erettile parziale / In trattamento riabilitativo",
                    "Disfunzione erettile severa / Organica stabile"
                ],
                key="ch_erezione"
            )

        note_chirurgia = st.text_area("Note cliniche di controllo post-operatorio o terapie adiuvanti:", key="ch_note")

        scelta_fine_chirurgia = st.selectbox(
            "Esito / Gestione post-operatoria:",
            [
                "Follow-up regolare (PSA Indetectable / Negativo)",
                "Sospetta Recidiva Biochimica (PSA in incremento / persistente)",
                "Avvio Radioterapia di Salvataggio",
                "Avvio Terapia Medica / Ormonale"
            ],
            key="ch_decisione_fine"
        )

        submitted_ch = st.form_submit_button("💾 Salva Visita Prostatectomia & Genera PDF", type="primary")

        if submitted_ch:
            num_mese_c = ELENCO_MESI.index(mese_psa_c) + 1
            data_psa_c = datetime(anno_psa_c, num_mese_c, 1).date()

            paziente["ultimo_psa"] = psa_post
            paziente["data_ultimo_psa"] = str(data_psa_c)
            paziente["percorso_scelto"] = scelta_fine_chirurgia

            dettagli_ch = (
                f"Controllo Prostatectomia\n"
                f"• PSA: {psa_post:.3f} ng/ml ({mese_psa_c} {anno_psa_c})\n"
                f"• Continenza Urinaria: {continenza}\n"
                f"• Funzione Erettile: {funzione_erettile}\n"
                f"• Esito / Programma: {scelta_fine_chirurgia}"
            )
            if note_chirurgia:
                dettagli_ch += f"\n• Note Cliniche: {note_chirurgia}"

            dati_visita_ch = {
                "data": str(datetime.today().date()),
                "tipo": f"Controllo Prostatectomia ({scelta_fine_chirurgia})",
                "dettagli": dettagli_ch
            }
            paziente["visite"].append(dati_visita_ch)
            salva_db_pazienti(db_attivo)
            st.session_state["ultimo_paziente_fu_ch"] = codice_search
            st.success("✅ Controllo di prostatectomia salvato con successo!")

    if st.session_state.get("ultimo_paziente_fu_ch") == codice_search and paziente["visite"]:
        ultima_visita = paziente["visite"][-1]
        note_pdf_ch = [f"Continenza: {continenza}", f"Funzione Erettile: {funzione_erettile}", note_chirurgia]
        note_pdf_ch = [n for n in note_pdf_ch if n]

        pdf_bytes = genera_pdf_referto(
            codice_search, ultima_visita, scelta_fine_chirurgia, note_pdf_ch,
            nome=paziente.get('nome', ''), cognome=paziente.get('cognome', '')
        )
        st.download_button(
            label="📄 Scarica Referto Prostatectomia PDF",
            data=pdf_bytes,
            file_name=f"Referto_Prostatectomia_{codice_search}.pdf",
            mime="application/pdf",
            key="dl_pdf_ch"
        )


def render_followup_radioterapia_avanzato(paziente, db_attivo, codice_search):
    st.markdown("---")
    st.markdown("### 放射线 Gestione Follow-up: Radioterapia")
    
    with st.form("form_nuova_valutazione_rt"):
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            mese_psa_r = st.selectbox("Mese Dosaggio PSA", ELENCO_MESI, index=datetime.today().month - 1, key="rt_mese_psa")
        with col_r2:
            anno_psa_r = st.number_input("Anno Dosaggio PSA", min_value=2000, max_value=2030, value=datetime.today().year, key="rt_anno_psa")
        with col_r3:
            psa_rt = st.number_input("Valore PSA Post-Radioterapia (ng/ml):", min_value=0.0, value=float(paziente.get("ultimo_psa", 0.0)), step=0.001, format="%.3f", key="rt_valore_psa")

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            tossicita_urinaria = st.selectbox(
                "Tossicità Urinaria tardiva / irritativa (RTOG):",
                ["Assente / Grado 0", "Grado 1 (Pollachiuria lieve / Disuria lieve)", "Grado 2 (Pollachiuria marcata / Antispastici necessari)", "Grado 3-4 (Ematuria severa / Ostruzione)"],
                key="rt_toss_urinaria"
            )
        with col_t2:
            tossicita_rettale = st.selectbox(
                "Tossicità Rettale tardiva (RTOG):",
                ["Assente / Grado 0", "Grado 1 (Rettorragia occasionale / Tenesmo lieve)", "Grado 2 (Rettorragia ricorrente / Diarrea gestibile)", "Grado 3-4 (Sanguinamento importante / Ulcerazione)"],
                key="rt_toss_rettale"
            )

        note_rt = st.text_area("Annotazioni cliniche post-radioterapia o terapie associate:", key="rt_note")

        scelta_fine_rt = st.selectbox(
            "Esito / Programma di controllo Radioterapia:",
            [
                "Follow-up regolare post-RT (Nadir stabile)",
                "Sospetta Recidiva Biochimica (Definizione Phoenix: Nadir + 2 ng/ml)",
                "Indicazione a Rivalutazione con PET PSMA / RMN",
                "Avvio Terapia Ormonale di salvataggio"
            ],
            key="rt_decisione_fine"
        )

        submitted_rt = st.form_submit_button("💾 Salva Visita Radioterapia & Genera PDF", type="primary")

        if submitted_rt:
            num_mese_r = ELENCO_MESI.index(mese_psa_r) + 1
            data_psa_r = datetime(anno_psa_r, num_mese_r, 1).date()

            paziente["ultimo_psa"] = psa_rt
            paziente["data_ultimo_psa"] = str(data_psa_r)
            paziente["percorso_scelto"] = scelta_fine_rt

            dettagli_rt = (
                f"Controllo Follow-up Radioterapia\n"
                f"• PSA: {psa_rt:.3f} ng/ml ({mese_psa_r} {anno_psa_r})\n"
                f"• Tossicità Urinaria: {tossicita_urinaria}\n"
                f"• Tossicità Rettale: {tossicita_rettale}\n"
                f"• Esito / Programma: {scelta_fine_rt}"
            )
            if note_rt:
                dettagli_rt += f"\n• Note Cliniche: {note_rt}"

            dati_visita_rt = {
                "data": str(datetime.today().date()),
                "tipo": f"Controllo Post-Radioterapia ({scelta_fine_rt})",
                "dettagli": dettagli_rt
            }
            paziente["visite"].append(dati_visita_rt)
            salva_db_pazienti(db_attivo)
            st.session_state["ultimo_paziente_fu_rt"] = codice_search
            st.success("✅ Controllo radioterapico salvato con successo!")

    if st.session_state.get("ultimo_paziente_fu_rt") == codice_search and paziente["visite"]:
        ultima_visita = paziente["visite"][-1]
        note_pdf_rt = [f"Tossicità Urinaria: {tossicita_urinaria}", f"Tossicità Rettale: {tossicita_rettale}", note_rt]
        note_pdf_rt = [n for n in note_pdf_rt if n]

        pdf_bytes = genera_pdf_referto(
            codice_search, ultima_visita, scelta_fine_rt, note_pdf_rt,
            nome=paziente.get('nome', ''), cognome=paziente.get('cognome', '')
        )
        st.download_button(
            label="📄 Scarica Referto Radioterapia PDF",
            data=pdf_bytes,
            file_name=f"Referto_Radioterapia_{codice_search}.pdf",
            mime="application/pdf",
            key="dl_pdf_rt"
        )


def render_terapia_medica(paziente, db_attivo, codice_search):
    st.markdown("---")
    st.markdown("### 💊 Gestione Follow-up: Terapia Medica / Ormonale")
    
    with st.form("form_nuova_valutazione_tm"):
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            mese_psa_tm = st.selectbox("Mese Dosaggio PSA", ELENCO_MESI, index=datetime.today().month - 1, key="tm_mese_psa")
        with col_m2:
            anno_psa_tm = st.number_input("Anno Dosaggio PSA", min_value=2000, max_value=2030, value=datetime.today().year, key="tm_anno_psa")
        with col_m3:
            psa_tm = st.number_input("Valore PSA in Terapia (ng/ml):", min_value=0.0, value=float(paziente.get("ultimo_psa", 0.0)), step=0.001, format="%.3f", key="tm_valore_psa")

        tipo_trattamento_ormonale = st.selectbox(
            "Schema di Terapia Medica in Atto / Modificato:",
            [
                "Deprivazione Androgenica (ADT) con Analogo LHRH / Antagonista",
                "ADT + Antiandrogeno di I/II generazione (es. Abiraterone, Enzalutamide, Apalutamide)",
                "Chemioterapia concomitante / sequenziale (es. Docetaxel)",
                "Sospensione temporanea / Intermittenza terapeutica programmata"
            ],
            key="tm_schema"
        )

        tolleranza_effetti = st.text_area("Tollerabilità clinica, effetti collaterali (es. vampate, astenia, profilo metabolico/osseo):", key="tm_tolleranza")

        scelta_fine_tm = st.selectbox(
            "Programma clinico di fine visita (Terapia Medica):",
            [
                "Prosegue terapia medica in corso",
                "Richiesta rivalutazione stadiativa per progressione biochimica (mCRPC)",
                "Modifica / Switch molecolare della terapia sistemica"
            ],
            key="tm_decisione_fine"
        )

        submitted_tm = st.form_submit_button("💾 Salva Visita Terapia Medica & Genera PDF", type="primary")

        if submitted_tm:
            num_mese_tm = ELENCO_MESI.index(mese_psa_tm) + 1
            data_psa_tm = datetime(anno_psa_tm, num_mese_tm, 1).date()

            paziente["ultimo_psa"] = psa_tm
            paziente["data_ultimo_psa"] = str(data_psa_tm)
            paziente["percorso_scelto"] = scelta_fine_tm

            dettagli_tm = (
                f"Controllo Follow-up Terapia Medica / Ormonale\n"
                f"• PSA: {psa_tm:.3f} ng/ml ({mese_psa_tm} {anno_psa_tm})\n"
                f"• Schema Terapeutico: {tipo_trattamento_ormonale}\n"
                f"• Programma: {scelta_fine_tm}"
            )
            if tolleranza_effetti:
                dettagli_tm += f"\n• Tollerabilità / Effetti Collaterali: {tolleranza_effetti}"

            dati_visita_tm = {
                "data": str(datetime.today().date()),
                "tipo": f"Controllo Terapia Medica ({scelta_fine_tm})",
                "dettagli": dettagli_tm
            }
            paziente["visite"].append(dati_visita_tm)
            salva_db_pazienti(db_attivo)
            st.session_state["ultimo_paziente_fu_tm"] = codice_search
            st.success("✅ Controllo terapia medica salvato con successo!")

    if st.session_state.get("ultimo_paziente_fu_tm"] == codice_search and paziente["visite"]:
        ultima_visita = paziente["visite"][-1]
        note_pdf_tm = [f"Schema: {tipo_trattamento_ormonale}", tolleranza_effetti]
        note_pdf_tm = [n for n in note_pdf_tm if n]

        pdf_bytes = genera_pdf_referto(
            codice_search, ultima_visita, scelta_fine_tm, note_pdf_tm,
            nome=paziente.get('nome', ''), cognome=paziente.get('cognome', '')
        )
        st.download_button(
            label="📄 Scarica Referto Terapia Medica PDF",
            data=pdf_bytes,
            file_name=f"Referto_Terapia_Medica_{codice_search}.pdf",
            mime="application/pdf",
            key="dl_pdf_tm"
        )


# --- FUNZIONI DI UTILITÀ GLOBALI ---

def genera_testo_patologia(gruppo_rischio, scelta_trattamento):
    testo_scelta = "Trattamento chirurgico di Prostatectomia" if scelta_trattamento == "Prostatectomia" else scelta_trattamento
    
    if gruppo_rischio == "Basso Rischio":
        base = (
            "Alla luce del quadro istopatologico (ISUP 1 / Gleason Score 3+3=6), "
            "dei valori sierici del PSA e della stadiazione clinico-strumentale, "
            "la malattia si stratifica secondo le Linee Guida internazionali di riferimento "
            "(EAU/NCCN/AIOM) nella classe a Basso Rischio di progressione. "
            "In conformità con le raccomandazioni scientifiche vigenti, si discute con il paziente "
            "l'opzione della Sorveglianza Attiva quale prima scelta raccomandata, "
            "contestualmente alle alternative terapeutiche a finalità radicale quali il trattamento chirurgico di Prostatectomia "
            "e la Radioterapia. Debitamente informato di benefici e rischi connessi con la sua decisione il paziente decide per:\n\n\n"
        )
    elif gruppo_rischio == "Rischio Intermedio Favorevole":
        base = (
            "L'integrazione dei parametri clinico-laboratoristici con i reperti anatomo-patologici "
            "(ISUP Group 2 / Gleason Score 3+4=7 con prevalenza di Pattern 3 e carico bioptico <50%) "
            "definisce una classe di Rischio Intermedio Favorevole ai sensi delle Linee Guida di settore "
            "(EAU/NCCN). Si pongono in discussione le opzioni terapeutiche a finalità radicale (trattamento chirurgico di Prostatectomia o Radioterapia) "
            "nonché, in presenza di specifici criteri di selezione e dopo un'adeguata informazione, l'opzione della Sorveglianza Attiva. "
            "Debitamente informato di benefici e rischi connessi con la sua decisione il paziente decide per:\n\n\n"
        )
    elif gruppo_rischio == "Rischio Intermedio Sfavorevole":
        base = (
            "Il quadro anatomopatologico (ISUP Group 2 con carico bioptico ≥50% ovvero ISUP Group 3 / Gleason Score 4+3=7) "
            "configura una classe di Rischio Intermedio Sfavorevole, per la quale si pone indicazione a completamento stadiativo "
            "mediante PET/TC con PSMA. Le opzioni terapeutiche validate comprendono il trattamento chirurgico di Prostatectomia "
            "o la Radioterapia associata a Deprivazione Androgenica a breve termine. "
            "Debitamente informato di benefici e rischi connessi con la sua decisione il paziente decide per:\n\n\n"
        )
    elif "Alto" in gruppo_rischio:
        base = (
            "Caso discusso in sede di DMT Uro-Oncologico. La presenza di fattori prognostici sfavorevoli "
            "(ISUP Group ≥4 / Gleason Score ≥8) colloca il quadro nella categoria ad Alto Rischio. "
            "Si pone indicazione prioritaria a PET/TC con PSMA e successivo approccio terapeutico multimodale "
            "(Radioterapia con ADT a lungo termine o trattamento chirurgico di Prostatectomia con linfoadenectomia estesa). "
            "Debitamente informato di benefici e rischi connessi con la sua decisione il paziente decide per:\n\n\n"
        )
    else:
        base = (
            "Alla luce del quadro clinico-strumentale di patologia localmente avanzata, "
            "si raccomanda completamento stadiativo con PET/TC con PSMA e approccio terapeutico integrato "
            "(Radioterapia ad alto dosaggio con ADT a lungo termine o chirurgia in casi selezionati). "
            "Debitamente informato di benefici e rischi connessi con la sua decisione il paziente decide per:\n\n\n"
        )
    
    return base + f"<font size='+2'>{testo_scelta}</font>"


def ottieni_db_aggiornato():
    db_file = carica_db_pazienti()
    if "db_pazienti" not in st.session_state:
        st.session_state["db_pazienti"] = db_file
    else:
        st.session_state["db_pazienti"].update(db_file)
    return st.session_state["db_pazienti"]


def stima_aspettativa_vita_charlson(data_nascita, charlson_score, ecog_score=0, adl_score=6, iadl_score=8, g8_score=17, gds_score=0):
    eta = (datetime.today().date() - data_nascita).days // 365
    
    if eta < 60:
        base_anni = 30
    elif eta < 65:
        base_anni = 25
    elif eta < 70:
        base_anni = 20
    elif eta < 75:
        base_anni = 16
    elif eta < 80:
        base_anni = 11
    else:
        base_anni = 7
        
    penalizzazione = charlson_score * 2.0
    
    if ecog_score >= 2:
        penalizzazione += 3.0
    elif ecog_score == 1:
        penalizzazione += 1.0
        
    if adl_score < 6:
        penalizzazione += (6 - adl_score) * 2.0
        
    if iadl_score < 8:
        penalizzazione += (8 - iadl_score) * 0.5
        
    if g8_score <= 14:
        penalizzazione += 2.0
        
    if gds_score >= 6:
        penalizzazione += 1.5

    aspettativa_stimata = max(2, base_anni - penalizzazione)
    return round(aspettativa_stimata, 1), eta


def calcola_gruppo_rischio_eau(isup_num, psa, ct_stage, gleason_terziario):
    is_terziario_alto = gleason_terziario in ["Pattern 5 Terziario", "Pattern 4 Terziario"]
    
    if any(stg in ct_stage for stg in ["cT3a", "cT3b", "cT4"]):
        return ("Localmente Avanzato", True, "Indicata Stadiazione Sistemica (PET/TC PSMA e Imaging di Staging).")
    elif isup_num >= 4 or psa > 20 or is_terziario_alto:
        return ("Alto / Molto Alto Rischio", True, "Indicata Stadiazione Sistemica (PET/TC PSMA oppure TC + Scintigrafia).")
    elif isup_num in [2, 3] or (10 <= psa <= 20) or any(stg in ct_stage for stg in ["cT2b", "cT2c"]):
        if isup_num == 3 or (isup_num == 2 and psa > 10):
            return ("Rischio Intermedio Sfavorevole", True, "Indicata Stadiazione Sistemica (Preferibile PET/TC PSMA).")
        else:
            return ("Rischio Intermedio Favorevole", False, "Stadiazione sistemica NON indicata di routine.")
    else:
        return ("Basso Rischio", False, "Stadiazione sistemica NON indicata. Candidato per Sorveglianza Attiva.")


# --- STRUTTURA PRINCIPALE DELL'APPLICAZIONE ---

def render_modulo():
    st.title("Carcinoma Prostatico - Decision Support System")

    db_attivo = ottieni_db_aggiornato()

    modalita = st.radio(
        "Seleziona Fase del Patient Journey:",
        [
            "1. Prima Visita: Inquadramento Bioptico & Rischio",
            "2. Rivalutazione dopo Stadiazione & Scelta Trattamento",
            "3. Follow-up Dedicato (Post-Trattamento / Sorveglianza)",
        ],
        horizontal=True,
    )

    if modalita == "1. Prima Visita: Inquadramento Bioptico & Rischio":
        st.subheader("Inquadramento Clinico & Anamnesi Globale (Prostata)")

        paziente_info = render_anagrafica_e_anamnesi_unificata(sigla_organo="P", prefix="prostata")
        
        nome_p = paziente_info["nome"]
        cognome_p = paziente_info["cognome"]
        codice_paziente = str(paziente_info["id_univoco"]).strip().upper()
        data_nascita_p = datetime.strptime(paziente_info["data_nascita"], "%Y-%m-%d").date()
        totale_g8 = paziente_info["g8_score"]
        charlson_score = paziente_info["charlson_score"]

        st.markdown("---")
        st.subheader("Parametri di Performance Status & Valutazione Oncogeriatrica")
        col_g1, col_g2, col_g3, col_g4, col_g5 = st.columns(5)
        with col_g1:
            ecog_score = st.selectbox("ECOG Status", [0, 1, 2, 3, 4], index=0)
        with col_g2:
            adl_score = st.selectbox("ADL (0-6)", [0, 1, 2, 3, 4, 5, 6], index=6)
        with col_g3:
            iadl_score = st.selectbox("IADL (0-8)", [0, 1, 2, 3, 4, 5, 6, 7, 8], index=8)
        with col_g4:
            gds_score = st.slider("GDS (Depressione 0-15)", min_value=0, max_value=15, value=0)
        with col_g5:
            st.metric("Screening G8", f"{totale_g8}/17")

        aspettativa_vita, eta_paziente = stima_aspettativa_vita_charlson(
            data_nascita_p, charlson_score, ecog_score, adl_score, iadl_score, totale_g8, gds_score
        )

        st.markdown("---")
        if aspettativa_vita < 10.0:
            st.error(
                f"ATTENZIONE CLINICA CRITICA (Aspettativa di Vita Stimata: < 10 Anni | Età: {eta_paziente} aa, Charlson: {charlson_score}, ECOG: {ecog_score}, G8: {totale_g8})\n\n"
                f"L'aspettativa di vita residua stimata è inferiore a 10 anni. "
                f"In conformità alle Linee Guida oncologiche internazionali, NON SUSSISTE INDICAZIONE A TRATTAMENTI CHIRURGICI AGGRESSIVI O A FINALITÀ RADICALE (es. Prostatectomia)."
            )
        else:
            st.success(
                f"Valutazione Aspettativa di Vita: Stimata a ~{aspettativa_vita} anni (Età: {eta_paziente} aa, Charlson: {charlson_score}, ECOG: {ecog_score}). "
                f"Il paziente rientra nei criteri di idoneità per trattamenti a finalità radicale."
            )
        st.markdown("---")

        anamnesi_ordinata_pdf = formatta_anamnesi_per_pdf_unificata(paziente_info)

        st.subheader("Dati Bioptici, Clinici e Imaging Iniziale (mpRMN)")

        col1, col2, col3 = st.columns(3)
        with col1:
            isup_basale = st.selectbox(
                "ISUP Group Bioptico:",
                ["ISUP 1 (Gleason 3+3)", "ISUP 2 (Gleason 3+4)", "ISUP 3 (Gleason 4+3)", "ISUP 4 (Gleason 4+4)", "ISUP 5 (Gleason 9-10)"]
            )
            isup_num = int(isup_basale.split()[1])
            gleason_terziario = st.selectbox("Gleason Pattern Terziario:", ["Assente", "Pattern 4 Terziario", "Pattern 5 Terziario"])

            col_m, col_y = st.columns(2)
            with col_m:
                mese_psa_b = st.selectbox("Mese PSA", ELENCO_MESI, index=datetime.today().month - 1)
            with col_y:
                anno_psa_b = st.number_input("Anno PSA", min_value=2000, max_value=2030, value=datetime.today().year)

            num_mese_b = ELENCO_MESI.index(mese_psa_b) + 1
            data_psa_basale = datetime(anno_psa_b, num_mese_b, 1).date()
            psa_basale = st.number_input("PSA Basale (ng/ml)", value=6.5, step=0.1)

        with col2:
            ct_stage = st.selectbox(
                "Stadio T Clinico:",
                ["cT1c (Inapprezzabile)", "cT2a (≤ metà di un lobo)", "cT2b (> metà di un lobo)", "cT2c (Entrambi i lobi)", "cT3a (Extracapsulare)", "cT3b (Vescicole)", "cT4 (Fissato/Adiacenti)"]
            )
            rmn_pirads = st.selectbox("Reperto mpRMN Prostatica:", ["PI-RADS 3", "PI-RADS 4", "PI-RADS 5", "ECE / SVI Sospetta alla RMN", "Non Eseguita"])

        with col3:
            st.markdown("Valutazione Rischio & Stadiazione")
            gruppo_rischio, necessita_stadiazione, motivazione_stadiazione = calcola_gruppo_rischio_eau(isup_num, psa_basale, ct_stage, gleason_terziario)
            st.write(f"Classe di Rischio / Stadio: {gruppo_rischio}")
            if necessita_stadiazione:
                st.error("STADIAZIONE SISTEMICA INDICATA")
            else:
                st.success("STADIAZIONE NON INDICATA AB INITIO")

        st.markdown("---")
        
        if necessita_stadiazione:
            opzioni_trattamento = ["In attesa di Stadiazione (DMT)"]
        else:
            if gruppo_rischio in ["Basso Rischio", "Rischio Intermedio Favorevole"]:
                opzioni_trattamento = ["Sorveglianza Attiva", "Prostatectomia", "Radioterapia"]
            else:
                opzioni_trattamento = ["Sorveglianza Attiva", "Prostatectomia", "Radioterapia", "Terapia Medica / Ormonale"]

        scelta_trattamento = st.selectbox("Trattamento Proposto / Concordato:", opzioni_trattamento)

        conferma_eccezione_chirurgia = False
        if aspettativa_vita < 10.0 and "Prostatectomia" in scelta_trattamento:
            st.warning("Attenzione: L'aspettativa di vita stimata del paziente è < 10 anni, ma è stata selezionata l'opzione chirurgica.")
            conferma_eccezione_chirurgia = st.checkbox(
                "Consapevole dell'aspettativa di vita < 10 anni si decide in assenso col paziente per intervento chirurgico"
            )

        if st.button("Salvataggio & Genera Report PDF (Prima Visita)", type="primary"):
            if not nome_p or not cognome_p or not codice_paziente:
                st.error("Inserire Nome, Cognome e Codice Univoco del paziente.")
            elif aspettativa_vita < 10.0 and "Prostatectomia" in scelta_trattamento and not conferma_eccezione_chirurgia:
                st.error("Errore: Per procedere con la chirurgia con un'aspettativa < 10 anni, è obbligatorio selezionare la spunta di deroga clinica.")
            else:
                salva_paziente_su_drive(
                    nome=nome_p, cognome=cognome_p, data_nascita=data_nascita_p, codice_univoco=codice_paziente
                )

                blocco_anamnesi_str = f"\nAnamnesi e Profilo Clinico:\n{anamnesi_ordinata_pdf}" if anamnesi_ordinata_pdf else ""
                dettagli_str = (
                    f"Parametri Prostatici & Oncogeriatrici:\n"
                    f"• ISUP Group: {isup_basale}\n• Gleason Terziario: {gleason_terziario}\n"
                    f"• PSA Basale: {psa_basale} ng/ml ({mese_psa_b} {anno_psa_b})\n• Stadio Clinico: {ct_stage}\n"
                    f"• mpRMN: {rmn_pirads}\n• Classe Rischio: {gruppo_rischio}\n"
                    f"• Charlson Index: {charlson_score} | ECOG: {ecog_score}\n"
                    f"• ADL: {adl_score}/6 | IADL: {iadl_score}/8 | G8: {totale_g8}/17 | GDS: {gds_score}/15\n"
                    f"• Aspettativa di Vita Stimata: ~{aspettativa_vita} anni"
                )
                if conferma_eccezione_chirurgia:
                    dettagli_str += "\n• NOTA DEROGA CLINICA: Consapevole dell'aspettativa di vita < 10 anni si decide in assenso col paziente per intervento chirurgico."
                if blocco_anamnesi_str:
                    dettagli_str += blocco_anamnesi_str

                dati_v = {
                    "data": str(datetime.today().date()),
                    "tipo": "Visita I - Inquadramento Bioptico Carcinoma Prostatico",
                    "dettagli": dettagli_str
                }
                
                db_attivo[codice_paziente] = {
                    "organo": "PROSTATA",
                    "nome": nome_p,
                    "cognome": cognome_p,
                    "data_nascita": str(data_nascita_p),
                    "isup": isup_num,
                    "rischio": gruppo_rischio,
                    "percorso_scelto": scelta_trattamento,
                    "ultimo_psa": psa_basale,
                    "data_ultimo_psa": str(data_psa_basale),
                    "g8_score": totale_g8,
                    "visite": [dati_v]
                }
                
                salva_db_pazienti(db_attivo)
                st.session_state["db_pazienti"] = db_attivo
                genera_o_aggiorna_registro(nome_p, cognome_p, data_nascita_p, codice_paziente)
                
                st.session_state["ultimo_paziente_salvato_prostata"] = codice_paziente
                st.success(f"Paziente salvato con successo! Codice univoco: {codice_paziente}")

        if "ultimo_paziente_salvato_prostata" in st.session_state and st.session_state["ultimo_paziente_salvato_prostata"] in db_attivo:
            cod_salvato = st.session_state["ultimo_paziente_salvato_prostata"]
            paz_corrente = db_attivo[cod_salvato]
            
            note_pdf_list = [
                motivazione_stadiazione, 
                f"Percorso assegnato: {scelta_trattamento}", 
                f"ECOG: {ecog_score} | ADL: {adl_score}/6 | IADL: {iadl_score}/8",
                f"Screening G8: {totale_g8}/17 | GDS: {gds_score}/15",
                f"Charlson Index: {charlson_score}",
                f"Aspettativa di vita stimata: ~{aspettativa_vita} anni"
            ]
            if conferma_eccezione_chirurgia:
                note_pdf_list.append("NOTA DEROGA CLINICA: Consapevole dell'aspettativa di vita < 10 anni si decide in assenso col paziente per intervento chirurgico.")
            if anamnesi_ordinata_pdf:
                note_pdf_list.append(f"Anamnesi:\n{anamnesi_ordinata_pdf}")

            testo_descrittivo_finale = genera_testo_patologia(gruppo_rischio, scelta_trattamento)
            note_pdf_list.append(testo_descrittivo_finale)

            pdf_bytes = genera_pdf_referto(cod_salvato, paz_corrente["visite"][-1], scelta_trattamento, note_pdf_list, nome=paz_corrente['nome'], cognome=paz_corrente['cognome'])
            
            st.download_button(
                label="Scarica Referto Prima Visita PDF",
                data=pdf_bytes,
                file_name=f"Referto_PROSTATA_{paz_corrente['cognome']}_{paz_corrente['nome']}.pdf",
                mime="application/pdf"
            )

    elif modalita == "2. Rivalutazione dopo Stadiazione & Scelta Trattamento":
        st.subheader("Rivalutazione post-Stadiazione (DMT) & Selezione Trattamento Definitivo")
        
        db_attivo = ottieni_db_aggiornato()
        codice_search = st.text_input("Inserisci Codice Univoco Paziente:", key="search_dmt_prostata").strip().upper()
        
        if not codice_search:
            st.warning("Inserisci il codice univoco del paziente per sbloccare la rivalutazione.")
        else:
            if codice_search in db_attivo:
                paziente = db_attivo[codice_search]
                st.success(f"Paziente Trovato: {paziente.get('cognome', '')} {paziente.get('nome', '')} (ID: {codice_search})")
                st.info(f"Rischio Iniziale: {paziente.get('rischio', 'Non definito')} | Percorso attuale: {paziente.get('percorso_scelto', 'Non definito')}")
                
                with st.expander("Visualizza Storico Visite Precedenti", expanded=False):
                    for idx, v in enumerate(paziente.get("visite", []), 1):
                        st.markdown(f"Visita {idx} - Data: {v.get('data')} | Tipo: {v.get('tipo')}")
                        st.text(v.get('dettagli', 'Nessun dettaglio'))
                        st.markdown("---")
                
                st.markdown("Esito Esami di Stadiazione e Scelta Terapeutica")
                esito_stadiazione = st.selectbox(
                    "Esito Imaging di Stadiazione (es. PET/TC PSMA / TC / Scintigrafia):",
                    [
                        "Negativo per malattia a distanza (Staging M0)",
                        "Positivo per recidiva locale / Sede di malattia primitiva",
                        "Positivo per linfonodi regionali / pelvici",
                        "Positivo per metastasi a distanza (M1)"
                    ]
                )
                
                rischio_paz = paziente.get("rischio", "")
                if rischio_paz in ["Basso Rischio", "Rischio Intermedio Favorevole"]:
                    opzioni_definitivo = ["Sorveglianza Attiva", "Prostatectomia", "Radioterapia"]
                else:
                    opzioni_definitivo = ["Sorveglianza Attiva", "Prostatectomia", "Radioterapia", "Terapia Medica / Ormonale"]

                nuovo_trattamento = st.selectbox("Selezione Trattamento Definitivo Concordato:", opzioni_definitivo)
                nota_dmt = st.text_area("Note della Discussione Multidisciplinare (DMT) / Motivazione clinica:")
                    
                if st.button("Salva Rivalutazione & Genera Referto DMT", type="primary"):
                    paziente["percorso_scelto"] = nuovo_trattamento
                    dettagli_v2 = f"Esito Stadiazione: {esito_stadiazione}\nTrattamento Definitivo Selezionato: {nuovo_trattamento}\nNote DMT: {nota_dmt}"
                    
                    dati_v = {
                        "data": str(datetime.today().date()),
                        "tipo": "Rivalutazione post-Stadiazione & Scelta Trattamento",
                        "dettagli": dettagli_v2
                    }
                    paziente["visite"].append(dati_v)
                    salva_db_pazienti(db_attivo)
                    st.session_state["db_pazienti"] = db_attivo
                    st.session_state["ultimo_paziente_rivalutato_prostata"] = codice_search
                    st.success("Rivalutazione salvata con successo nel database!")

                if "ultimo_paziente_rivalutato_prostata" in st.session_state and st.session_state["ultimo_paziente_rivalutato_prostata"] == codice_search:
                    paz_aggiornato = db_attivo[codice_search]
                    ultima_visita = paz_aggiornato["visite"][-1]
                    pdf_bytes = genera_pdf_referto(
                        codice_search, ultima_visita, paz_aggiornato.get("percorso_scelto", nuovo_trattamento), 
                        [esito_stadiazione, nota_dmt], nome=paz_aggiornato.get('nome',''), cognome=paz_aggiornato.get('cognome','')
                    )
                    st.download_button(
                        label="Scarica Referto Rivalutazione / DMT PDF",
                        data=pdf_bytes,
                        file_name=f"Rivalutazione_DMT_PROSTATA_{codice_search}.pdf",
                        mime="application/pdf"
                    )
            else:
                st.error(f"Nessun paziente trovato con il codice univoco {codice_search}.")

    elif modalita == "3. Follow-up Dedicato (Post-Trattamento / Sorveglianza)":
        st.subheader("Gestione Follow-up Clinico Dedicato")
        
        db_attivo = ottieni_db_aggiornato()
        codice_search = st.text_input("Inserisci Codice Univoco Paziente:", key="search_fu_prostata").strip().upper()

        if not codice_search:
            st.warning("Inserisci il codice univoco del paziente per accedere al follow-up personalizzato.")
        else:
            if codice_search in db_attivo:
                paziente = db_attivo[codice_search]
                percorso_attuale = paziente.get("percorso_scelto", "Sorveglianza Attiva")
                
                st.success(f"Paziente Trovato: {paziente.get('cognome', '')} {paziente.get('nome', '')} (ID: {codice_search})")
                st.info(f"Percorso Terapeutico Attivo / Protocollo di Follow-up: {percorso_attuale}")
                
                with st.expander("Visualizza Storico Visite del Paziente", expanded=False):
                    for idx, v in enumerate(paziente.get("visite", []), 1):
                        st.markdown(f"Visita {idx} - Data: {v.get('data')} | Tipo: {v.get('tipo')}")
                        st.text(v.get('dettagli', 'Nessun dettaglio'))
                        st.markdown("---")

                st.markdown("---")
                
                # Smistamento dinamico basato sul percorso registrato
                percorso_lower = percorso_attuale.lower()
                
                if "sorveglianza" in percorso_lower:
                    render_followup_sorveglianza_avanzato(paziente, db_attivo, codice_search)
                elif "prostatectomia" in percorso_lower or "chirurgia" in percorso_lower:
                    render_followup_chirurgia_avanzato(paziente, db_attivo, codice_search)
                elif "radioterapia" in percorso_lower:
                    render_followup_radioterapia_avanzato(paziente, db_attivo, codice_search)
                elif "terapia" in percorso_lower or "ormonale" in percorso_lower:
                    render_terapi_medica = render_terapia_medica(paziente, db_attivo, codice_search)
                else:
                    render_followup_sorveglianza_avanzato(paziente, db_attivo, codice_search)
            else:
                st.error(f"Nessun paziente trovato con il codice univoco {codice_search}.")
