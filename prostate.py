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
    ELENCO_MESI
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
    
    if isup_num >= 4 or psa > 20 or any(stg in ct_stage for stg in ["cT3a", "cT3b", "cT4"]) or is_terziario_alto:
        return ("Alto / Molto Alto Rischio", True, "Indicata Stadiatura Sistemica (PET/TC PSMA oppure TC + Scintigrafia).")
    
    elif isup_num in [2, 3] or (10 <= psa <= 20) or any(stg in ct_stage for stg in ["cT2b", "cT2c"]):
        if isup_num == 3 or (isup_num == 2 and psa > 10):
            return ("Rischio Intermedio Sfavorevole", True, "Indicata Stadiatura Sistemica (Preferibile PET/TC PSMA).")
        else:
            return ("Rischio Intermedio Favorevole", False, "Stadiatura sistemica NON indicata di routine.")
            
    else:
        return ("Basso Rischio", False, "Stadiatura sistemica NON indicata. Candidato per Sorveglianza Attiva.")

def calcola_timing_controllo(percorso, dati):
    if percorso == "Sorveglianza Attiva":
        isup = dati.get("isup", 1)
        psadt = dati.get("psadt")
        if (psadt is not None and psadt < 36) or isup > 1:
            return {
                "rec_psa": "PSA Sierico tra 3 Mesi (Monitoraggio stretto per cinetica rapida / PSADT < 36m).",
                "rec_rmn": "⚠️ Programmare mpRMN Prostatica urgente (entro 3 mesi).",
                "rec_bx": "⚠️ Ripetere Biopsia Prostatica di Riconferma/Re-stadiatura.",
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
                "rec_imaging": "⚠️ Programmare PET/TC PSMA e TC Torace-Addome di Restaging.",
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
            "2. Seconda Visita / DMT: Referto Stadiatura & Decisione",
            "3. Controllo Successivo / Follow-up PSA",
        ],
        horizontal=True,
    )

    if modalita == "1. Prima Visita: Inquadramento Bioptico & Rischio":
        st.subheader("📋 Inserimento Anagrafica Paziente")
        
        # Gestione Registro ed Espansore Anagrafica Integrato
        registro_esistente = {}
        if os.path.exists("registro_pazienti.json"):
            try:
                with open("registro_pazienti.json", "r", encoding="utf-8") as f:
                    registro_esistente = json.load(f)
            except Exception:
                registro_esistente = {}
                
        opzioni_pazienti = ["➕ Inserisci Nuovo Paziente"] + [f"{code} - {data['cognome']} {data['nome']}" for code, data in registro_esistente.items()]
        scelta_paziente = st.selectbox("Cerca Paziente Registrato o Nuovo", opzioni_pazienti, key="seleziona_paziente_prostata")

        col_a, col_b, col_c = st.columns(3)
        if scelta_paziente != "➕ Inserisci Nuovo Paziente":
            codice_selezionato = scelta_paziente.split(" - ")[0]
            paziente_info = registro_esistente.get(codice_selezionato, {})
            
            with col_a:
                nome_p = st.text_input("Nome Paziente", value=paziente_info.get("nome", ""))
            with col_b:
                cognome_p = st.text_input("Cognome Paziente", value=paziente_info.get("cognome", ""))
            with col_c:
                codice_paziente = st.text_input("Codice Univoco / ID", value=codice_selezionato, disabled=True)
                
            try:
                data_nascita_p = datetime.strptime(paziente_info.get("data_nascita", "1960-01-01"), "%Y-%m-%d").date()
            except:
                data_nascita_p = datetime(1960, 1, 1).date()
            st.date_input("Data di Nascita", value=data_nascita_p, disabled=True)
        else:
            with col_a:
                nome_p = st.text_input("Nome Paziente")
            with col_b:
                cognome_p = st.text_input("Cognome Paziente")
            with col_c:
                def_code = genera_codice_univoco(nome_p, cognome_p) if (nome_p and cognome_p) else ""
                codice_paziente = st.text_input("Codice Univoco / ID", value=def_code)
                
            data_nascita_p = st.date_input("Data di Nascita", datetime(1960, 1, 1))

        st.divider()

        # Anamnesi Generale Condivisa
        anamnesi = render_anamnesi_generale()

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
            st.markdown("🎯 **Valutazione Rischio & Stadiatura**")
            gruppo_rischio, necessita_stadiatura, motivazione_stadiatura = calcola_gruppo_rischio_eau(isup_num, psa_basale, ct_stage, gleason_terziario)
            st.write(f"**Classe di Rischio:** `{gruppo_rischio}`")
            if necessita_stadiatura:
                st.error("⚠️ **STADIATURA SISTEMICA INDICATA**")
            else:
                st.success("✅ **STADIATURA NON INDICATA AB INITIO**")

        st.markdown("---")
        scelta_trattamento = st.selectbox("Trattamento Concordato / Scelto:", ["Sorveglianza Attiva", "Chirurgia (Post-Prostatectomia)", "Radioterapia"]) if not necessita_stadiatura else "In attesa di Stadiatura (DMT II)"

        if st.button("💾 Salvataggio & Genera Report PDF (Prostata)", type="primary"):
            if not nome_p or not cognome_p or not codice_paziente:
                st.error("Inserire Nome, Cognome e Codice Univoco del paziente.")
            else:
                dettagli_str = f"ISUP {isup_num} | Gleason Terziario: {gleason_terziario} | PSA: {psa_basale} ({mese_psa_b} {anno_psa_b}) | {ct_stage} | Rischio: {gruppo_rischio}"
                if anamnesi["ipertensione"]:
                    dettagli_str += " | Ipertensione: Sì"
                if anamnesi["diabete"] != "No":
                    dettagli_str += f" | Diabete: {anamnesi['diabete']}"
                if anamnesi["fumo"] != "Non fumatore":
                    dettagli_str += f" | Fumo: {anamnesi['fumo']}"

                dati_v = {
                    "data": str(datetime.today().date()),
                    "tipo": "Visita I - Inquadramento Bioptico Carcinoma Prostatico",
                    "dettagli": dettagli_str
                }
                
                if "db_pazienti" not in st.session_state:
                    st.session_state["db_pazienti"] = {}
                    
                st.session_state["db_pazienti"][codice_paziente] = {
                    "organo": "PROSTATA",
                    "isup": isup_num,
                    "rischio": gruppo_rischio,
                    "percorso_scelto": scelta_trattamento,
                    "ultimo_psa": psa_basale,
                    "data_ultimo_psa": str(data_psa_basale),
                    "visite": [dati_v]
                }
                salva_db_pazienti(st.session_state["db_pazienti"])
                genera_o_aggiorna_registro(nome_p, cognome_p, data_nascita_p, codice_paziente)
                
                note_pdf_list = [motivazione_stadiatura, f"Percorso assegnato: {scelta_trattamento}"]
                if anamnesi["ipertensione"]:
                    note_pdf_list.append("Nota annessa: Paziente iperteso in anamnesi.")
                if anamnesi["diabete"] != "No":
                    note_pdf_list.append(f"Nota annessa: Diabete mellito ({anamnesi['diabete']}).")
                if anamnesi["fumo"] != "Non fumatore":
                    note_pdf_list.append(f"Nota annessa: Abitudine tabagica ({anamnesi['fumo']}).")

                pdf_bytes = genera_pdf_referto(codice_paziente, dati_v, scelta_trattamento, note_pdf_list, nome=nome_p, cognome=cognome_p)
                st.success(f"Paziente salvato con successo! Codice: `{codice_paziente}`")
                
                st.download_button(
                    label="📄 Scarica Referto PDF Stampabile",
                    data=pdf_bytes,
                    file_name=f"Referto_PROSTATA_{cognome_p}_{nome_p}.pdf",
                    mime="application/pdf"
                )

    elif modalita == "2. Seconda Visita / DMT: Referto Stadiatura & Decisione":
        st.subheader("📑 Seconda Visita / Inquadramento DMT")
        st.info("Fase per l'integrazione di PET/TC PSMA e discussione in Multidisciplinare.")

    elif modalita == "3. Controllo Successivo / Follow-up PSA":
        st.subheader("🔍 Richiama Paziente per Follow-up")
        codice_search = st.text_input("Inserisci Codice Univoco Paziente:").strip().upper()

        if codice_search in st.session_state["db_pazienti"]:
            paziente = st.session_state["db_pazienti"][codice_search]
            st.success(f"Paziente Trovato! ID: {codice_search}")
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
                salva_db_pazienti(st.session_state["db_pazienti"])
                
                note_pdf = [res_fu.get("rec_psa"), res_fu.get("rec_rmn"), res_fu.get("rec_bx"), res_fu.get("rec_imaging")]
                note_pdf = [n for n in note_pdf if n]
                
                pdf_bytes = genera_pdf_referto(codice_search, dati_v, percorso_attuale, note_pdf)
                st.success("Controllo registrato!")
                st.download_button(
                    label="📄 Scarica Referto Follow-up PDF",
                    data=pdf_bytes,
                    file_name=f"FollowUp_PROSTATA_{codice_search}.pdf",
                    mime="application/pdf"
                )
