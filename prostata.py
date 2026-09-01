from datetime import datetime
import hashlib
import math
import streamlit as st
import os
import json
from utils import (
    salva_db_pazienti, 
    genera_o_aggiorna_registro, 
    genera_pdf_referto, 
    genera_codice_univoco, 
    render_anamnesi_generale, 
    formatta_anamnesi_per_pdf,
salva_paziente_su_drive
  from utils import ELENCO_MESI
)

TESTO_BASSO_RISCHIO = (
    "Alla luce del quadro istopatologico (ISUP 1 / Gleason Score 3+3=6), "
    "dei valori sierici del PSA e della stadiazione clinico-strumentale, "
    "la malattia si stratifica secondo le Linee Guida internazionali di riferimento "
    "(EAU/NCCN/AIOM) nella classe a Basso Rischio di progressione. "
    "In conformità con le raccomandazioni scientifiche vigenti, si ritiene indicata "
    "in prima istanza l'opzione della Sorveglianza Attiva secondo protocollo codificato. "
    "Contestualmente, nell'ambito di una corretta informazione ed alleanza terapeutica, "
    "vengono considerate ed illustrate come opzioni alternative a finalità radicale/curativa "
    "la Chirurgia (Prostatectomia Radicale) e la Radioterapia. La scelta finale sull'iter "
    "da intraprendere sarà definita previa valutazione multidisciplinare delle comorbilità "
    "e ponderata decisione condivisa con il paziente."
)

TESTO_INTERMEDIO_FAVOREVOLE = (
    "L'integrazione dei parametri clinico-laboratoristici con i reperti anatomo-patologici "
    "(ISUP Group 2 / Gleason Score 3+4=7 con prevalenza di Pattern 3 e carico bioptico <50%) "
    "definisce una classe di Rischio Intermedio Favorevole ai sensi delle Linee Guida di settore "
    "(EAU/NCCN). In accordo con le raccomandazioni vigenti, si pone indicazione a trattamento "
    "locale a fine curativo mediante Prostatectomia Radicale oppure Radioterapia. Qualora "
    "sussistano specifici criteri di selezione e dopo un'adeguata informazione, può essere presa "
    "in considerazione anche l'opzione della Sorveglianza Attiva con monitoraggio stringente. "
    "La decisione finale sarà condivisa con il paziente in base al bilancio tra tollerabilità ed aspettativa di vita."
)

TESTO_INTERMEDIO_SFAVOREVOLE = (
    "Il quadro anatomopatologico (ISUP Group 2 con carico bioptico ≥50% ovvero ISUP Group 3 / Gleason Score 4+3=7 con "
    "prevalenza di Pattern 4) configura una classe di Rischio Intermedio Sfavorevole. "
    "In ottemperanza alle Linee Guida internazionali, per un'accurata stratificazione e stadiazione di malattia "
    "si ritiene opportuno il completamento diagnostico mediante PET/TC con PSMA. Sulla base dell'esito dello staging "
    "strumentale, si conferma l'indicazione a trattamento ad intenzione curativa: le opzioni validate comprendono "
    "l'intervento chirurgico di Prostatectomia Radicale (con linfoadenectomia di stadiazione) ovvero la Radioterapia "
    "associata a Deprivazione Androgenica a breve/medio termine (ADT 4-6 mesi). La scelta della strategia "
    "terapeutica definitiva sarà ponderata con il paziente previa valutazione delle comorbilità e del profilo funzionale."
)

TESTO_ALTO_RISCHIO = (
    "Caso discusso in sede di DMT Uro-Oncologico. La combinazione dei fattori prognostici "
    "sfavorevoli, inclusa la presenza di gradazione bioptica elevata (ISUP Group 4 o "
    "5 / Gleason Score ≥8), colloca il quadro patologico nella categoria ad Alto "
    "Rischio secondo i criteri della letteratura scientifica accreditata. Ai fini di "
    "un corretto inquadramento stadiativo primario e per l'esclusione di patologia "
    "secondaria/occulta, si pone indicazione prioritaria all'esecuzione di PET/TC "
    "con PSMA, in accordo con le raccomandazioni delle Linee Guida di riferimento. "
    "All'esito dell'imaging, si prospetta una strategia terapeutica multimodale: le "
    "opzioni standard comprendono la Radioterapia ad alto dosaggio in combinazione "
    "con la Deprivazione Androgenica a lungo termine (18-36 mesi) ed eventuale "
    "terapia ormonale di nuova generazione, oppure l'intervento di Prostatectomia "
    "Radicale con Linfoadenectomia pelvica estesa nell'ambito di un programma "
    "integrato. La pianificazione finale verrà concordata con il paziente "
    "nell'ambito di una decisione clinica condivisa."
)

TESTO_LOCALMENTE_AVANZATO = (
    "Alla luce del quadro clinico-strumentale di patologia localmente avanzata "
    "(sospetto/accertato sconfinamento extracapsulare, invasione delle vescicole seminali o "
    "coinvolgimento linfonodale), si raccomanda l'esecuzione di PET/TC con PSMA per completamento "
    "dello staging sistemico di malattia prima dell'avvio del trattamento. In conformità alle Linee Guida "
    "di settore, si conferma la necessità di un approccio multimodale, individuando come prima opzione "
    "raccomandata il trattamento Radioterapico ad alto dosaggio associato a Terapia di Deprivazione "
    "Androgenica (ADT) a lungo termine e/o agenti ormonali di nuova generazione, ovvero l'opzione "
    "chirurgica integrata (Prostatectomia Radicale con Linfoadenectomia estesa) in casi selezionati. "
    "Il piano di cura definitivo sarà definito in stretta alleanza terapeutica con il paziente."
)

def calcola_psadt(psa_precedente, data_precedente_str, psa_attuale, data_attuale):
    if psa_precedente is None or psa_precedente <= 0 or psa_attuale <= psa_precedente or not data_precedente_str:
        return None
    try:
        data_precedente = datetime.strptime(data_precedente_str, "%Y-%m-%d").date()
        giorni = (data_attuale - data_precedente).days
        if giorni <= 0:
            return None
        dt_giorni = (math.log(2) * giorni) / math.log(psa_attuale / psa_precedente)
        return round(dt_giorni / 30.4375, 1)
    except Exception:
        return None

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

def calcola_timing_controllo(percorso, dati):
    if percorso == "Sorveglianza Attiva":
        isup = dati.get("isup", 1)
        psadt = dati.get("psadt")
        if (psadt is not None and psadt < 36) or isup > 1:
            return {
                "rec_psa": "PSA Sierico tra 3 Mesi (Monitoraggio stretto per cinetica rapida / PSADT < 36m).",
                "rec_rmn": "⚠️ Programmare mpRMN Prostatica urgente (entro 3 mesi).",
                "rec_bx": "⚠️ Ripetere Biopsia Prostatica di Riconferma/Re-stadiazione.",
                "alert": "⚠️ ATTENZIONE: PSADT accelerato o ISUP > 1. Valutare l'uscita dalla Sorveglianza Attiva.",
            }
        else:
            return {
                "rec_psa": "PSA Sierico ogni 6 Mesi + Visita Clinica.",
                "rec_rmn": "Programmare mpRMN Prostatica a 12 mesi dall'inizio della SA (o di controllo annuale).",
                "rec_bx": "Programmare Biopsia Prostatica di Riconferma tra i 12 e i 24 mesi.",
                "alert": "🟢 Cinetica del PSA nei limiti. Proseguire Sorveglianza Attiva.",
            }
    elif percorso == "Chirurgia (Post-Prostatectomia)":
        psa = dati.get("psa", 0.0)
        mesi_op = dati.get("mesi_post_op", 0)
        if psa >= 0.20:
            return {
                "rec_psa": "PSA Sierico Ultrasensibile di riconferma a 30 giorni.",
                "rec_imaging": "⚠️ PET/TC PSMA tempestiva per restaging.",
                "rec_azione": "Valutazione Radioterapica per Radioterapia di Salvataggio Precoce ± ADT.",
                "alert": "🚨 RECIDIVA BIOCHIMICA CONFERMATA (PSA ≥ 0.20 ng/ml).",
            }
        m = 3 if mesi_op <= 12 else (6 if mesi_op <= 36 else 12)
        return {
            "rec_psa": f"PSA Sierico Ultrasensibile tra {m} mesi + Visita Urologica.",
            "rec_imaging": "Imaging non indicato di routine in assenza di incremento del PSA.",
            "rec_azione": "Proseguire follow-up oncologico regolare.",
            "alert": "🟢 PSA nei limiti di negatività (<0.20 ng/ml).",
        }
    elif percorso == "Radioterapia":
        psa = dati.get("psa", 0.0)
        psa_nadir = dati.get("psa_nadir", 0.0)
        mesi_rt = dati.get("mesi_post_rt", 0)
        if psa_nadir > 0 and (psa - psa_nadir) >= 2.0:
            return {
                "rec_psa": "PSA Sierico di riconferma a 30 giorni.",
                "rec_imaging": "⚠️ Programmare PET/TC PSMA e TC Torace-Addome di Re-stadiazione.",
                "rec_azione": "Discussione DMT per Terapia di Salvataggio o Sistemica.",
                "alert": "🚨 RECIDIVA BIOCHIMICA CRITERI PHOENIX (Nadir + 2.0 ng/ml).",
            }
        m = 3 if mesi_rt <= 24 else (6 if mesi_rt <= 60 else 12)
        return {
            "rec_psa": f"PSA Sierico tra {m} mesi + Visita Radioterapica / Oncologica.",
            "rec_imaging": "Imaging non indicato di routine in assenza di incremento sospetto.",
            "rec_azione": "Proseguire monitoraggio del Nadir.",
            "alert": "🟢 Cinetica del PSA stabile / post-attinica regolare.",
        }
    return {"rec_psa": "PSA + Visita tra 6 Mesi.", "alert": "Info standard."}

def render_modulo():
    st.title("🧬 Carcinoma Prostatico - Decision Support System")

    modalita = st.radio(
        "Seleziona Fase del Patient Journey:",
        [
            "1. Prima Visita: Inquadramento Bioptico & Rischio",
            "2. Seconda Visita / DMT: Referto Stadiazione & Decisione",
            "3. Controllo Successivo / Follow-up PSA",
        ],
        horizontal=True,
    )

    if modalita == "1. Prima Visita: Inquadramento Bioptico & Rischio":
        st.subheader("📋 Inserimento Anagrafica Paziente (Nuovo Accesso)")
        
        if "prostata_nome" not in st.session_state: st.session_state["prostata_nome"] = ""
        if "prostata_cognome" not in st.session_state: st.session_state["prostata_cognome"] = ""
        if "prostata_id" not in st.session_state: st.session_state["prostata_id"] = ""

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            nome_p = st.text_input("Nome Paziente", key="input_nome_prostata")
        with col_b:
            cognome_p = st.text_input("Cognome Paziente", key="input_cognome_prostata")
        
        if nome_p != st.session_state["prostata_nome"] or cognome_p != st.session_state["prostata_cognome"]:
            st.session_state["prostata_nome"] = nome_p
            st.session_state["prostata_cognome"] = cognome_p
            if nome_p and cognome_p:
                st.session_state["prostata_id"] = genera_codice_univoco(nome_p, cognome_p)
            else:
                st.session_state["prostata_id"] = ""
            st.rerun()

        with col_c:
            col_sub1, col_sub2 = st.columns([2, 1])
            with col_sub1:
                codice_paziente = st.text_input(
                    "Codice Univoco / ID", 
                    value=st.session_state["prostata_id"], 
                    key="input_id_prostata"
                )
                if codice_paziente != st.session_state["prostata_id"]:
                    st.session_state["prostata_id"] = codice_paziente
            with col_sub2:
                st.write("") 
                st.write("")
                if st.button("🔄 Genera", key="btn_rigenera_prostata"):
                    if st.session_state["prostata_nome"] and st.session_state["prostata_cognome"]:
                        st.session_state["prostata_id"] = genera_codice_univoco(st.session_state["prostata_nome"], st.session_state["prostata_cognome"])
                        st.rerun()
                    else:
                        st.warning("Inserisci nome e cognome.")

        data_nascita_p = st.date_input("Data di Nascita", datetime(1960, 1, 1))

        st.divider()

        anamnesi = render_anamnesi_generale(prefix="prostata")
        anamnesi_ordinata_pdf = formatta_anamnesi_per_pdf(anamnesi)

        st.divider()
        st.subheader("🔬 Dati Bioptici, Clinici e Imaging Iniziale (mpRMN)")

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
            st.markdown("🎯 **Valutazione Rischio & Stadiazione**")
            gruppo_rischio, necessita_stadiazione, motivazione_stadiazione = calcola_gruppo_rischio_eau(isup_num, psa_basale, ct_stage, gleason_terziario)
            st.write(f"**Classe di Rischio / Stadio:** `{gruppo_rischio}`")
            if necessita_stadiazione:
                st.error("⚠️ **STADIAZIONE SISTEMICA INDICATA**")
            else:
                st.success("✅ **STADIAZIONE NON INDICATA AB INITIO**")

        st.markdown("---")
        scelta_trattamento = st.selectbox("Trattamento Concordato / Scelto:", ["Sorveglianza Attiva", "Chirurgia (Post-Prostatectomia)", "Radioterapia"]) if not necessita_stadiazione else "In attesa di Stadiazione (DMT II)"

        if st.button("💾 Salvataggio & Genera Report PDF (Prostata)", type="primary"):
            if not nome_p or not cognome_p or not codice_paziente:
                st.error("Inserire Nome, Cognome e Codice Univoco del paziente.")
            else:
                blocco_anamnesi_str = f"\nAnamnesi Generale:\n{anamnesi_ordinata_pdf}" if anamnesi_ordinata_pdf else ""
                
                dettagli_str = f"Parametri Prostatici:\n• ISUP Group: {isup_num}\n• Gleason Terziario: {gleason_terziario}\n• PSA Basale: {psa_basale} ng/ml ({mese_psa_b} {anno_psa_b})\n• Stadio Clinico: {ct_stage}\n• mpRMN: {rmn_pirads}\n• Classe Rischio: {gruppo_rischio}{blocco_anamnesi_str}"

                dati_v = {
                    "data": str(datetime.today().date()),
                    "tipo": "Visita I - Inquadramento Bioptico Carcinoma Prostatico",
                    "dettagli": dettagli_str
                }
                
                if "db_pazienti" not in st.session_state:
                    st.session_state["db_pazienti"] = {}
                    
                st.session_state["db_pazienti"][codice_paziente] = {
                    "organo": "PROSTATA",
                    "nome": nome_p,
                    "cognome": cognome_p,
                    "isup": isup_num,
                    "rischio": gruppo_rischio,
                    "percorso_scelto": scelta_trattamento,
                    "ultimo_psa": psa_basale,
                    "data_ultimo_psa": str(data_psa_basale),
                    "visite": [dati_v]
                }
                salva_db_pazienti(st.session_state["db_pazienti"])
                genera_o_aggiorna_registro(nome_p, cognome_p, data_nascita_p, codice_paziente)
                salva_paziente_su_drive(nome_p, cognome_p, data_nascita_p, codice_univoco)
                note_pdf_list = [motivazione_stadiazione, f"Percorso assegnato: {scelta_trattamento}"]
                if gruppo_rischio == "Basso Rischio":
                    note_pdf_list.append(TESTO_BASSO_RISCHIO)
                elif gruppo_rischio == "Rischio Intermedio Favorevole":
                    note_pdf_list.append(TESTO_INTERMEDIO_FAVOREVOLE)
                elif gruppo_rischio == "Rischio Intermedio Sfavorevole":
                    note_pdf_list.append(TESTO_INTERMEDIO_SFAVOREVOLE)
                elif "Alto" in gruppo_rischio:
                    note_pdf_list.append(TESTO_ALTO_RISCHIO)
                elif gruppo_rischio == "Localmente Avanzato":
                    note_pdf_list.append(TESTO_LOCALMENTE_AVANZATO)

                pdf_bytes = genera_pdf_referto(codice_paziente, dati_v, scelta_trattamento, note_pdf_list, nome=nome_p, cognome=cognome_p)
                st.success(f"Paziente salvato con successo! Codice: `{codice_paziente}`")
                
                st.download_button(
                    label="📄 Scarica Referto PDF Stampabile",
                    data=pdf_bytes,
                    file_name=f"Referto_PROSTATA_{cognome_p}_{nome_p}.pdf",
                    mime="application/pdf"
                )

    elif modalita == "2. Seconda Visita / DMT: Referto Stadiazione & Decisione":
        st.subheader("📑 Seconda Visita / Inquadramento DMT")
        
        codice_search = st.text_input("Inserisci Codice Univoco Paziente (Obbligatorio per procedere):", key="search_dmt_prostata").strip().upper()
        
        if not codice_search:
            st.warning("⚠️ Inserisci il codice univoco del paziente per sbloccare la scheda della seconda visita.")
        else:
            db_attivo = st.session_state.get("db_pazienti", {})
            
            if codice_search in db_attivo:
                paziente = db_attivo[codice_search]
                st.success(f"Paziente Trovato: {paziente.get('cognome', '')} {paziente.get('nome', '')} (ID: {codice_search})")
                
                with st.expander("📂 Visualizza Storico Visite / Dati Precedenti del Paziente", expanded=True):
                    visite_prec = paziente.get("visite", [])
                    for idx, v in enumerate(visite_prec, 1):
                        st.markdown(f"**Visita {idx} - Data: {v.get('data')} | Tipo: {v.get('tipo')}**")
                        st.text(v.get('dettagli', 'Nessun dettaglio'))
                        st.markdown("---")
                
                st.markdown("### ✍️ Inserimento Seconda Visita / Esito Stadiazione")
                esito_stadiazione = st.selectbox("Esito Imaging di Stadiazione (es. PET/TC PSMA):", ["Negativo per malattia a distanza", "Positivo per recidiva locale", "Positivo per linfonodi regionali/pelvici", "Positivo per M1 (distanza)"])
                nota_dmt = st.text_area("Note della Discussione Multidisciplinare (DMT):")
                
                if st.button("💾 Salva Seconda Visita & Genera PDF", type="primary"):
                    dettagli_v2 = f"Esito Stadiazione: {esito_stadiazione}\nNote DMT: {nota_dmt}"
                    dati_v = {
                        "data": str(datetime.today().date()),
                        "tipo": "Seconda Visita / DMT & Stadiazione",
                        "dettagli": dettagli_v2
                    }
                    paziente["visite"].append(dati_v)
                    salva_db_pazienti(db_attivo)
                    
                    pdf_bytes = genera_pdf_referto(codice_search, dati_v, paziente.get("percorso_scelto", "Non definito"), [esito_stadiazione, nota_dmt], nome=paziente.get('nome',''), cognome=paziente.get('cognome',''))
                    st.success("Seconda visita salvata con successo!")
                    st.download_button(
                        label="📄 Scarica Referto Seconda Visita PDF",
                        data=pdf_bytes,
                        file_name=f"SecondaVisita_PROSTATA_{codice_search}.pdf",
                        mime="application/pdf"
                    )
            else:
                st.error("❌ Nessun paziente trovato con questo codice univoco. Verifica l'ID inserito.")

    elif modalita == "3. Controllo Successivo / Follow-up PSA":
        st.subheader("🔍 Richiama Paziente per Follow-up")
        
        codice_search = st.text_input("Inserisci Codice Univoco Paziente (Obbligatorio):", key="search_fu_prostata").strip().upper()

        if not codice_search:
            st.warning("⚠️ Inserisci il codice univoco del paziente per accedere al modulo di follow-up.")
        else:
            db_attivo = st.session_state.get("db_pazienti", {})
            if codice_search in db_attivo:
                paziente = db_attivo[codice_search]
                st.success(f"Paziente Trovato: {paziente.get('cognome', '')} {paziente.get('nome', '')} (ID: {codice_search})")
                
                with st.expander("📂 Visualizza Storico Visite / Follow-up Precedenti", expanded=True):
                    visite_prec = paziente.get("visite", [])
                    for idx, v in enumerate(visite_prec, 1):
                        st.markdown(f"**Controllo {idx} - Data: {v.get('data')} | Tipo: {v.get('tipo')}**")
                        st.text(v.get('dettagli', 'Nessun dettaglio'))
                        st.markdown("---")

                percorso_attuale = paziente.get("percorso_scelto", "Sorveglianza Attiva")

                st.markdown("---")
                col_psa1, col_psa2, col_psa3 = st.columns(3)
                with col_psa1:
                    mese_psa_a = st.selectbox("Mese Prelievo PSA", ELENCO_MESI, index=datetime.today().month - 1)
                with col_psa2:
                    anno_psa_a = st.number_input("Anno Prelievo PSA", min_value=2000, max_value=2030, value=datetime.today().year)
                with col_psa3:
                    psa_attuale = st.number_input("Valore PSA Sierico (ng/ml):", min_value=0.0, value=float(paziente.get("ultimo_psa", 0.0)), step=0.01)

                num_mese_a = ELENCO_MESI.index(mese_psa_a) + 1
                data_psa_attuale = datetime(anno_psa_a, num_mese_a, 1).date()
                psadt_calcolato = calcola_psadt(paziente.get("ultimo_psa"), paziente.get("data_ultimo_psa"), psa_attuale, data_psa_attuale)

                if percorso_attuale == "Sorveglianza Attiva":
                    res_fu = calcola_timing_controllo("Sorveglianza Attiva", {"isup": paziente.get("isup", 1), "psadt": psadt_calcolato})
                elif percorso_attuale == "Chirurgia (Post-Prostatectomia)":
                    res_fu = calcola_timing_controllo("Chirurgia (Post-Prostatectomia)", {"psa": psa_attuale, "mesi_post_op": 6})
                else:
                    res_fu = calcola_timing_controllo("Radioterapia", {"psa": psa_attuale, "psa_nadir": 0.1, "mesi_post_rt": 12})

                st.info(f"**Indicazioni:** {res_fu['rec_psa']}")

                if st.button("💾 Salvataggio Visita & Genera PDF Controllo", type="primary"):
                    paziente["ultimo_psa"] = psa_attuale
                    paziente["data_ultimo_psa"] = str(data_psa_attuale)
                    
                    dati_v = {
                        "data": str(datetime.today().date()),
                        "tipo": f"Follow-up ({percorso_attuale}) Carcinoma Prostatico",
                        "dettagli": f"PSA: {psa_attuale:.2f} ({mese_psa_a} {anno_psa_a}) | PSADT: {psadt_calcolato} mesi"
                    }
                    paziente["visite"].append(dati_v)
                    salva_db_pazienti(db_attivo)
                    
                    note_pdf = [res_fu.get("rec_psa"), res_fu.get("rec_rmn"), res_fu.get("rec_bx"), res_fu.get("rec_imaging")]
                    note_pdf = [n for n in note_pdf if n]
                    
                    pdf_bytes = genera_pdf_referto(codice_search, dati_v, percorso_attuale, note_pdf, nome=paziente.get('nome',''), cognome=paziente.get('cognome',''))
                    st.success("Controllo registrato!")
                    st.download_button(
                        label="📄 Scarica Referto Follow-up PDF",
                        data=pdf_bytes,
                        file_name=f"FollowUp_PROSTATA_{codice_search}.pdf",
                        mime="application/pdf"
                    )
            else:
                st.error("❌ Nessun paziente trovato con questo codice univoco. Verifica l'ID inserito.")
