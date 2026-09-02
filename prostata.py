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

def genera_testo_patologia(gruppo_rischio, scelta_trattamento):
    testo_scelta = "Trattamento chirurgico di Prostatectomia Radicale" if scelta_trattamento == "Chirurgia (Post-Prostatectomia)" else scelta_trattamento
    
    if gruppo_rischio == "Basso Rischio":
        base = (
            "Alla luce del quadro istopatologico (ISUP 1 / Gleason Score 3+3=6), "
            "dei valori sierici del PSA e della stadiazione clinico-strumentale, "
            "la malattia si stratifica secondo le Linee Guida internazionali di riferimento "
            "(EAU/NCCN/AIOM) nella classe a Basso Rischio di progressione. "
            "In conformità con le raccomandazioni scientifiche vigenti, si discute con il paziente "
            "l'opzione della Sorveglianza Attiva quale prima scelta raccomandata, "
            "contestualmente alle alternative terapeutiche a finalità radicale quali il trattamento chirurgico di Prostatectomia Radicale "
            "e la Radioterapia. Debitamente informato di benefici e rischi connessi con la sua decisione il paziente decide per:\n\n\n"
        )
    elif gruppo_rischio == "Rischio Intermedio Favorevole":
        base = (
            "L'integrazione dei parametri clinico-laboratoristici con i reperti anatomo-patologici "
            "(ISUP Group 2 / Gleason Score 3+4=7 con prevalenza di Pattern 3 e carico bioptico <50%) "
            "definisce una classe di Rischio Intermedio Favorevole ai sensi delle Linee Guida di settore "
            "(EAU/NCCN). Si pongono in discussione le opzioni terapeutiche a finalità radicale (trattamento chirurgico di Prostatectomia Radicale o Radioterapia) "
            "nonché, in presenza di specifici criteri di selezione e dopo un'adeguata informazione, l'opzione della Sorveglianza Attiva. "
            "Debitamente informato di benefici e rischi connessi con la sua decisione il paziente decide per:\n\n\n"
        )
    elif gruppo_rischio == "Rischio Intermedio Sfavorevole":
        base = (
            "Il quadro anatomopatologico (ISUP Group 2 con carico bioptico ≥50% ovvero ISUP Group 3 / Gleason Score 4+3=7) "
            "configura una classe di Rischio Intermedio Sfavorevole, per la quale si pone indicazione a completamento stadiativo "
            "mediante PET/TC con PSMA. Le opzioni terapeutiche validate comprendono il trattamento chirurgico di Prostatectomia Radicale "
            "o la Radioterapia associata a Deprivazione Androgenica a breve termine. "
            "Debitamente informato di benefici e rischi connessi con la sua decisione il paziente decide per:\n\n\n"
        )
    elif "Alto" in gruppo_rischio:
        base = (
            "Caso discusso in sede di DMT Uro-Oncologico. La presenza di fattori prognostici sfavorevoli "
            "(ISUP Group ≥4 / Gleason Score ≥8) colloca il quadro nella categoria ad Alto Rischio. "
            "Si pone indicazione prioritaria a PET/TC con PSMA e successivo approccio terapeutico multimodale "
            "(Radioterapia con ADT a lungo termine o trattamento chirurgico di Prostatectomia Radicale con linfoadenectomia estesa). "
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
                "rec_azione": "Valutazione uscita dalla Sorveglianza Attiva.",
                "alert": "⚠️ ATTENZIONE: PSADT accelerato o ISUP > 1. Valutare l'uscita dalla Sorveglianza Attiva.",
            }
        else:
            return {
                "rec_psa": "PSA Sierico ogni 6 Mesi + Visita Clinica.",
                "rec_rmn": "Programmare mpRMN Prostatica a 12 mesi dall'inizio della SA (o di controllo annuale).",
                "rec_bx": "Programmare Biopsia Prostatica di Riconferma tra i 12 e i 24 mesi.",
                "rec_azione": "Proseguire protocollo di monitoraggio.",
                "alert": "🟢 Cinetica del PSA nei limiti. Proseguire Sorveglianza Attiva.",
            }
    elif percorso.startswith("Chirurgia"):
        psa = dati.get("psa", 0.0)
        if psa >= 0.20:
            return {
                "rec_psa": "PSA Sierico Ultrasensibile di riconferma a 30 giorni.",
                "rec_imaging": "⚠️ PET/TC PSMA tempestiva per restaging.",
                "rec_azione": "Valutazione Radioterapica per Radioterapia di Salvataggio Precoce ± ADT.",
                "alert": "🚨 RECIDIVA BIOCHIMICA CONFERMATA (PSA ≥ 0.20 ng/ml).",
            }
        return {
            "rec_psa": "PSA Sierico Ultrasensibile di controllo semestrale + Visita Urologica.",
            "rec_imaging": "Imaging non indicato di routine in assenza di incremento del PSA.",
            "rec_azione": "Proseguire follow-up oncologico regolare.",
            "alert": "🟢 PSA nei limiti di negatività (<0.20 ng/ml).",
        }
    elif percorso == "Radioterapia":
        psa = dati.get("psa", 0.0)
        psa_nadir = dati.get("psa_nadir", 0.0)
        if psa_nadir > 0 and (psa - psa_nadir) >= 2.0:
            return {
                "rec_psa": "PSA Sierico di riconferma a 30 giorni.",
                "rec_imaging": "⚠️ Programmare PET/TC PSMA e TC Torace-Addome di Re-stadiazione.",
                "rec_azione": "Discussione DMT per Terapia di Salvataggio o Sistemica.",
                "alert": "🚨 RECIDIVA BIOCHIMICA CRITERI PHOENIX (Nadir + 2.0 ng/ml).",
            }
        return {
            "rec_psa": "PSA Sierico semestrale + Visita Radioterapica / Oncologica.",
            "rec_imaging": "Imaging non indicato di routine in assenza di incremento sospetto.",
            "rec_azione": "Proseguire monitoraggio del Nadir.",
            "alert": "🟢 Cinetica del PSA stabile / post-attinica regolare.",
        }
    elif "Terapia Medica" in percorso or "Ormonale" in percorso:
        return {
            "rec_psa": "PSA Sierico, Testosterone totale e Profilo Metabolico ogni 3 mesi.",
            "rec_imaging": "Imaging di rivalutazione secondo risposta clinica / biochimica.",
            "rec_azione": "Monitoraggio tollerabilità ed efficacia della terapia sistemica.",
            "alert": "🔵 Paziente in trattamento medico / deprivazione androgenica.",
        }
    return {"rec_psa": "PSA + Visita tra 6 Mesi.", "alert": "Info standard."}

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
                f"In conformità alle Linee Guida oncologiche internazionali, NON SUSSISTE INDICAZIONE A TRATTAMENTI CHIRURGICI AGGRESSIVI O A FINALITÀ RADICALE (es. Prostatectomia Radicale), "
                f"poiché i rischi operatori e la mortalità non correlata al cancro superano il beneficio atteso."
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
                opzioni_trattamento = ["Sorveglianza Attiva", "Chirurgia (Post-Prostatectomia)", "Radioterapia"]
            else:
                opzioni_trattamento = ["Sorveglianza Attiva", "Chirurgia (Post-Prostatectomia)", "Radioterapia", "Terapia Medica / Ormonale"]

        scelta_trattamento = st.selectbox("Trattamento Proposto / Concordato:", opzioni_trattamento)

        conferma_eccezione_chirurgia = False
        if aspettativa_vita < 10.0 and "Chirurgia" in scelta_trattamento:
            st.warning("Attenzione: L'aspettativa di vita stimata del paziente è < 10 anni, ma è stata selezionata l'opzione chirurgica.")
            conferma_eccezione_chirurgia = st.checkbox(
                "Consapevole dell'aspettativa di vita < 10 anni si decide in assenso col paziente per intervento chirurgico"
            )

        if st.button("Salvataggio & Genera Report PDF (Prima Visita)", type="primary"):
            if not nome_p or not cognome_p or not codice_paziente:
                st.error("Inserire Nome, Cognome e Codice Univoco del paziente.")
            elif aspettativa_vita < 10.0 and "Chirurgia" in scelta_trattamento and not conferma_eccezione_chirurgia:
                st.error("Errore: Per procedere con la chirurgia con un'aspettativa < 10 anni, è obbligatorio selezionare la spunta di deroga/consapevolezza clinica.")
            else:
                salva_paziente_su_drive(
                    nome=nome_p,
                    cognome=cognome_p,
                    data_nascita=data_nascita_p,
                    codice_univoco=codice_paziente
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
                    opzioni_definitivo = ["Sorveglianza Attiva", "Chirurgia (Post-Prostatectomia)", "Radioterapia"]
                else:
                    opzioni_definitivo = ["Sorveglianza Attiva", "Chirurgia (Post-Prostatectomia)", "Radioterapia", "Terapia Medica / Ormonale (ADT / NHA)"]

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
                        codice_search, 
                        ultima_visita, 
                        paz_aggiornato.get("percorso_scelto", nuovo_trattamento), 
                        [esito_stadiazione, nota_dmt], 
                        nome=paz_aggiornato.get('nome',''), 
                        cognome=paz_aggiornato.get('cognome','')
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
                elif percorso_attuale.startswith("Chirurgia"):
                    res_fu = calcola_timing_controllo("Chirurgia", {"psa": psa_attuale})
                elif percorso_attuale == "Radioterapia":
                    res_fu = calcola_timing_controllo("Radioterapia", {"psa": psa_attuale, "psa_nadir": 0.1})
                else:
                    res_fu = calcola_timing_controllo("Terapia Medica / Ormonale", {"psa": psa_attuale})

                st.markdown("Indicazioni di Monitoraggio Personalizzate")
                st.info(f"Controllo Biochimico: {res_fu['rec_psa']}")
                if res_fu.get('rec_rmn'):
                    st.write(f"- {res_fu['rec_rmn']}")
                if res_fu.get('rec_bx'):
                    st.write(f"- {res_fu['rec_bx']}")
                if res_fu.get('rec_imaging'):
                    st.warning(res_fu['rec_imaging'])
                
                if res_fu.get('alert'):
                    st.warning(res_fu['alert'])

                note_cliniche_fu = st.text_area("Note cliniche aggiuntive per la visita di controllo:")

                if st.button("Salva Visita di Follow-up & Genera PDF", type="primary"):
                    paziente["ultimo_psa"] = psa_attuale
                    paziente["data_ultimo_psa"] = str(data_psa_attuale)
                    
                    dettagli_fu = f"Percorso: {percorso_attuale}\nPSA: {psa_attuale:.2f} ng/ml ({mese_psa_a} {anno_psa_a})"
                    if psadt_calcolato:
                        dettagli_fu += f" | PSADT: {psadt_calcolato} mesi"
                    if note_cliniche_fu:
                        dettagli_fu += f"\nNote: {note_cliniche_fu}"

                    dati_v = {
                        "data": str(datetime.today().date()),
                        "tipo": f"Follow-up Dedicato ({percorso_attuale})",
                        "dettagli": dettagli_fu
                    }
                    paziente["visite"].append(dati_v)
                    salva_db_pazienti(db_attivo)
                    st.session_state["db_pazienti"] = db_attivo
                    st.session_state["ultimo_paziente_fu_prostata"] = codice_search
                    st.success("Controllo di follow-up registrato e salvato con successo nel database!")

                if "ultimo_paziente_fu_prostata" in st.session_state and st.session_state["ultimo_paziente_fu_prostata"] == codice_search:
                    paz_aggiornato = db_attivo[codice_search]
                    ultima_visita = paz_aggiornato["visite"][-1]
                    
                    note_pdf = [
                        res_fu.get("alert"), 
                        res_fu.get("rec_psa"), 
                        res_fu.get("rec_rmn"), 
                        res_fu.get("rec_bx"), 
                        res_fu.get("rec_imaging"),
                        res_fu.get("rec_azione"),
                        note_cliniche_fu
                    ]
                    note_pdf = [n for n in note_pdf if n]
                    
                    pdf_bytes = genera_pdf_referto(codice_search, ultima_visita, percorso_attuale, note_pdf, nome=paz_aggiornato.get('nome',''), cognome=paz_aggiornato.get('cognome',''))
                    st.download_button(
                        label="Scarica Referto Follow-up PDF",
                        data=pdf_bytes,
                        file_name=f"FollowUp_{percorso_attuale.replace(' ', '_')}_{codice_search}.pdf",
                        mime="application/pdf"
                    )
            else:
                st.error(f"Nessun paziente trovato con il codice univoco {codice_search}.")
