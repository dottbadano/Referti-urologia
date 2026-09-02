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

                # ==========================================
                # PERCORSO 1: SORVEGLIANZA ATTIVA
                # ==========================================
                if "Sorveglianza" in percorso_attuale:
                    st.markdown("### 🔄 Nuova Valutazione: Sorveglianza Attiva")
                    with st.form("form_nuova_valutazione_sa"):
                        col_psa1, col_psa2, col_psa3 = st.columns(3)
                        with col_psa1:
                            mese_psa_a = st.selectbox("Mese Prelievo PSA", ELENCO_MESI, index=datetime.today().month - 1)
                        with col_psa2:
                            anno_psa_a = st.number_input("Anno Prelievo PSA", min_value=2000, max_value=2030, value=datetime.today().year)
                        with col_psa3:
                            psa_attuale = st.number_input("Valore PSA Attuale (ng/ml):", min_value=0.0, value=float(paziente.get("ultimo_psa", 0.0)), step=0.01)

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
                                ]
                            )
                        with col_img2:
                            dre_esito = st.selectbox(
                                "Esplorazione Rettale (DRE):",
                                ["Negativa", "Positiva (Sospetto locale / Modificazione)"]
                            )

                        note_cliniche_fu = st.text_area("Dettagli clinici della visita, sintomi o annotazioni:")

                        scelta_fine_visita = st.selectbox(
                            "Decisione presa a fine visita (Aggiornamento Percorso):",
                            [
                                "Prosegue Sorveglianza Attiva",
                                "Chirurgia (Post-Prostatectomia)",
                                "Radioterapia"
                            ]
                        )

                        submitted_sa = st.form_submit_button("💾 Salva Nuova Valutazione & Genera Referto PDF", type="primary")

                        if submitted_sa:
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
                            st.session_state["db_pazienti"] = db_attivo
                            st.session_state["ultimo_paziente_fu_sa"] = codice_search
                            st.success("✅ Nuova valutazione salvata correttamente nello storico!")

                    if st.session_state.get("ultimo_paziente_fu_sa") == codice_search and paziente["visite"]:
                        ultima_visita = paziente["visite"][-1]
                        note_pdf = [
                            f"Valutazione RMN: {repertoprecise}",
                            f"Esito DRE: {dre_esito}",
                            f"Decisione di fine visita: {scelta_fine_visita}",
                            note_cliniche_fu if 'note_cliniche_fu' in locals() else ""
                        ]
                        note_pdf = [n for n in note_pdf if n]
                        
                        pdf_bytes = genera_pdf_referto(
                            codice_search, 
                            ultima_visita, 
                            paziente.get("percorso_scelto", percorso_attuale), 
                            note_pdf, 
                            nome=paziente.get('nome', ''), 
                            cognome=paziente.get('cognome', '')
                        )
                        
                        st.download_button(
                            label="📄 Scarica Referto Aggiornato in PDF",
                            data=pdf_bytes,
                            file_name=f"Referto_Sorveglianza_Attiva_{codice_search}.pdf",
                            mime="application/pdf",
                            key="download_pdf_sa_aggiornato"
                        )

                # ==========================================
                # PERCORSO 2: CHIRURGIA
                # ==========================================
                elif "Chirurgia" in percorso_attuale:
                    st.markdown("### 🔄 Nuova Valutazione: Post-Prostatectomia Radicale")
                    
                    with st.expander("📋 Istologia Definitiva & Caratteristiche Chirurgiche (Baseline)", expanded=False):
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

                    if pt_stage in ["pT3a", "pT3b", "pT4"] or "R1" in margini_r or "R2" in margini_r:
                        st.error("⚠️ **ATTENZIONE (Fattori di Rischio Anatomo-Patologici):** Rilevato stadio pT3/pT4 e/o Margini Chirurgici Positivi (R1/R2). **Considerare Radioterapia di Salvataggio.**")

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

                        submitted_chir = st.form_submit_button("💾 Salva Nuova Valutazione & Genera Referto PDF", type="primary")

                        if submitted_chir:
                            num_mese_a = ELENCO_MESI.index(mese_psa_a) + 1
                            data_psa_attuale = datetime(anno_psa_a, num_mese_a, 1).date()

                            paziente["ultimo_psa"] = psa_attuale
                            paziente["data_ultimo_psa"] = str(data_psa_attuale)
                            paziente["percorso_scelto"] = scelta_fine_visita

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
                            salva_db_pazienti(db_attivo)
                            st.session_state["db_pazienti"] = db_attivo
                            st.session_state["ultimo_paziente_fu_chirurgia"] = codice_search
                            st.success("✅ Nuova valutazione chirurgica salvata correttamente nello storico!")

                    if 'psa_attuale' in locals() and psa_attuale >= 0.2:
                        st.error("⚠️ **ATTENZIONE (Recidiva Biochimica):** Valore di PSA post-prostatectomia $\\ge 0.2\\text{ ng/ml}$. **Considerare Radioterapia di Salvataggio.**")

                    if st.session_state.get("ultimo_paziente_fu_chirurgia") == codice_search and paziente["visite"]:
                        ultima_visita = paziente["visite"][-1]
                        
                        note_pdf = [
                            f"Stadio Patologico: {pt_stage if 'pt_stage' in locals() else 'pT2'} | {pn_stage if 'pn_stage' in locals() else 'pN0'} | {margini_r if 'margini_r' in locals() else 'R0'} | ISUP {isup_post if 'isup_post' in locals() else '1'}",
                            f"Nerve Sparing: {nerve_sparing if 'nerve_sparing' in locals() else 'No'}",
                            f"Decisione di fine visita: {scelta_fine_visita if 'scelta_fine_visita' in locals() else ''}",
                            note_cliniche_fu if 'note_cliniche_fu' in locals() else ""
                        ]
                        if 'psa_attuale' in locals() and psa_attuale >= 0.2:
                            note_pdf.append("ATTENZIONE: PSA >= 0.2 ng/ml. Valutare radioterapia di salvataggio.")
                            
                        note_pdf = [n for n in note_pdf if n]
                        
                        pdf_bytes = genera_pdf_referto(
                            codice_search, 
                            ultima_visita, 
                            paziente.get("percorso_scelto", percorso_attuale), 
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

                # ==========================================
                # PERCORSO 3: RADIOTERAPIA
                # ==========================================
                elif "Radioterapia" in percorso_attuale:
                    st.subheader("⚡ Follow-up Dedicato: Post-Radioterapia (RT)")
                    
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

                    if "nadir_psa" not in paziente:
                        paziente["nadir_psa"] = None

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

                        submitted_rt = st.form_submit_button("💾 Salva Nuova Valutazione & Genera Referto PDF", type="primary")

                        if submitted_rt:
                            num_mese_a = ELENCO_MESI.index(mese_psa_a) + 1
                            data_psa_attuale = datetime(anno_psa_a, num_mese_a, 1).date()

                            nadir_attuale = paziente.get("nadir_psa")
                            if nadir_attuale is None or psa_attuale < nadir_attuale:
                                paziente["nadir_psa"] = psa_attuale
                                nadir_utilizzato = psa_attuale
                            else:
                                nadir_utilizzato = nadir_attuale

                            paziente["ultimo_psa"] = psa_attuale
                            paziente["data_ultimo_psa"] = str(data_psa_attuale)
                            paziente["percorso_scelto"] = scelta_fine_visita

                            soglia_phoenix = (paziente["nadir_psa"] or 0.0) + 2.0
                            is_recidiva = psa_attuale >= soglia_phoenix
                            msg_phoenix = f"⚠️ RECIDIVA BIOCHIMICA (Criteri Phoenix): PSA ({psa_attuale} ng/ml) >= Nadir ({paziente['nadir_psa']} + 2.0)." if is_recidiva else f"🟢 PSA sotto soglia Phoenix (Nadir: {paziente['nadir_psa']} ng/ml)."

                            dettagli_fu = (
                                f"Controllo Post-Radioterapia\n"
                                f"• Schema: {schema_rt} ({dose_gy} Gy), Linfonodi: {trattamento_linfonodi}\n"
                                f"• Terapia Sistemica: LHRH ({terapia_lhrh}) | ARSI ({terapia_arsi})\n"
                                f"• PSA: {psa_attuale:.3f} ng/ml ({mese_psa_a} {anno_psa_a}) | Nadir: {nadir_utilizzato:.3f} ng/ml\n"
                                f"• Esito Phoenix: {msg_phoenix}\n"
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
                            salva_db_pazienti(db_attivo)
                            st.session_state["db_pazienti"] = db_attivo
                            st.session_state["ultimo_paziente_fu_rt"] = codice_search
                            st.success("✅ Nuova valutazione radioterapica salvata correttamente nello storico!")

                    if "nadir_psa" in paziente and paziente["nadir_psa"] is not None:
                        soglia_chk = paziente["nadir_psa"] + 2.0
                        if float(paziente.get("ultimo_psa", 0.0)) >= soglia_chk:
                            st.error(f"⚠️ Criteri Phoenix superati: PSA attuale >= Nadir ({paziente['nadir_psa']}) + 2.0 ng/ml.")
                        else:
                            st.success(f"🟢 PSA regolare rispetto al Nadir registrato ({paziente['nadir_psa']} ng/ml).")

                    if st.session_state.get("ultimo_paziente_fu_rt") == codice_search and paziente["visite"]:
                        ultima_visita = paziente["visite"][-1]
                        
                        note_pdf = [
                            f"Schema RT: {schema_rt if 'schema_rt' in locals() else ''} ({dose_gy if 'dose_gy' in locals() else ''} Gy)",
                            f"Nadir PSA: {paziente.get('nadir_psa')} ng/ml",
                            f"Decisione di fine visita: {scelta_fine_visita if 'scelta_fine_visita' in locals() else ''}",
                            note_cliniche_fu if 'note_cliniche_fu' in locals() else ""
                        ]
                        note_pdf = [n for n in note_pdf if n]
                        
                        pdf_bytes = genera_pdf_referto(
                            codice_search, 
                            ultima_visita, 
                            paziente.get("percorso_scelto", percorso_attuale), 
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

                # ==========================================
                # PERCORSO 4: TERAPIA MEDICA
                # ==========================================
                else:
                    st.markdown("### 🟡 Protocollo di Terapia Medica Avanzata")
                    st.info("Gestione della malattia metastatica o avanzata, transizione mCRPC, terapie sistemiche, mutazioni HRR/BRCA, salute ossea e monitoraggio di PSA e testosteronemia.")

                    with st.form(key="form_terapia_medica_aggiornato"):
                        st.markdown("#### 🌍 Caratteristiche di Malattia e Volume (Criteri CHAARTED / STAMPEDE)")
                        
                        col_vol1, col_vol2 = st.columns(2)
                        with col_vol1:
                            presenza_metastasi = st.selectbox("Presenza di Metastasi", ["No (M0 / Ormonodipendente non metastatica)", "Sì (M1 / Malattia metastatica)"], key="tm_metastasi_check")
                        with col_vol2:
                            volume_malattia = st.selectbox("Volume di Malattia (Criteri CHAARTED/STAMPEDE)", ["Non applicabile (M0)", "Low Volume (Basso volume)", "High Volume (Alto volume: metastasi viscerali o >=4 lesioni ossee con almeno una extra-assiale/vertebrale)"], key="tm_volume")

                        st.markdown("---")
                        st.markdown("#### 🚨 Stato di Malattia e transizione mCRPC (Resistenza alla Castrazione - Linee Guida EAU/ESMO)")
                        
                        col_crpc1, col_crpc2 = st.columns(2)
                        with col_crpc1:
                            stato_crpc = st.selectbox(
                                "Stato di Resistenza alla Castrazione", 
                                ["No (Sensibile agli androgeni / mHSPC)", "Sì (mCRPC - Resistente alla castrazione con testosterone in target)"], 
                                key="tm_crpc_check"
                            )
                        with col_crpc2:
                            opzione_mcrpc = "Non applicabile"
                            if "Sì (mCRPC" in stato_crpc:
                                opzione_mcrpc = st.selectbox(
                                    "Strategia di Linea Successiva (mCRPC)",
                                    ["Switch di ARSI", "Chemioterapia con Cabazitaxel", "Terapia Radiometabolica (177Lu-PSMA)", "Radio-223 (per metastasi ossee esclusive)"],
                                    key="tm_strat_mcrpc"
                                )
                            else:
                                st.info("Paziente in fase ormonosensibile.")

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
                        st.markdown("#### 💊 Chemioterapia, Target Therapy (PARPi) e Salute Ossea")
                        
                        col_chem1, col_chem2 = st.columns(2)
                        with col_chem1:
                            usa_chemio = st.selectbox("Chemioterapia associata?", ["No", "Sì"], key="tm_chemio_check")
                        with col_chem2:
                            tipo_chemio = st.selectbox("Molecola Chemioterapica", ["Nessuna", "Docetaxel", "Cabazitaxel"], key="tm_tipo_chemio")

                        st.markdown("##### 🧬 Profilo Mutazionale HRR / BRCA e PARP Inibitori")
                        col_parp1, col_parp2 = st.columns(2)
                        with col_parp1:
                            brca_mutato = st.checkbox("Paziente con mutazione BRCA1/2 o HRR (Homologous Recombination Repair esteso)", key="tm_brca_check")
                        with col_parp2:
                            tipo_parpi = st.selectbox("Scelta PARP Inibitore (PARPi)", ["Nessuno", "Olaparib", "Niraparib", "Talazoparib"], key="tm_tipo_parpi")

                        st.markdown("##### 🦴 Protezione Ossea (Bone Health - Prevenzione SRE)")
                        col_bone1, col_bone2 = st.columns(2)
                        with col_bone1:
                            terapia_osso = st.selectbox("Terapia Osteoprotettiva Associata", ["Nessuna", "Acido Zoledronico", "Denosumab"], key="tm_bone_med")
                        with col_bone2:
                            supp_vitd = st.checkbox("Inclusa supplementazione Calcemia / Vitamina D", key="tm_vitd_check")

                        st.markdown("---")
                        st.markdown("#### 📈 Monitoraggio Biochimico (PSA e Testosteronemia)")
                        
                        col_bio1, col_bio2, col_bio3 = st.columns(3)
                        with col_bio1:
                            valore_psa_tm = st.number_input("Valore PSA Attuale (ng/mL)", min_value=0.0, max_value=1000.0, value=float(paziente.get("ultimo_psa", 0.0)), step=0.1, key="tm_psa_val")
                        with col_bio2:
                            valore_testosterone = st.number_input("Testosteronemia (ng/dL)", min_value=0.0, max_value=1500.0, value=0.0, step=1.0, key="tm_testosterone")
                        with col_bio3:
                            target_castrazione = st.selectbox("Target Testosterone di Castrazione (< 50 ng/dL)?", ["Raggiunto (< 50 ng/dL)", "Non raggiunto (>= 50 ng/dL - Fuga biochimica)"], key="tm_target_test")

                        if "Non raggiunto" in target_castrazione:
                            st.error("⚠️ **ATTENZIONE**: Il livello di testosterone non rientra nel range di castrazione (< 50 ng/dL).")
                        else:
                            st.success("✅ Livello di testosteronemia in target di castrazione.")

                        st.markdown("---")
                        scelta_fine_visita_tm = st.selectbox(
                            "Decisione presa a fine visita (Aggiornamento Percorso):",
                            [
                                "Prosegue Terapia Medica in corso",
                                "Switch terapeutico / Modifica Linea Sistemica",
                                "Avvio percorso di cure palliative / supportive"
                            ],
                            key="tm_scelta_fine"
                        )

                        note_tm = st.text_area("Note cliniche, tollerabilità e raccomandazioni di terapia medica:", key="tm_note")
                        
                        submit_tm = st.form_submit_button("💾 Salva Nuova Valutazione & Genera Referto PDF", type="primary")
                        
                        if submit_tm:
                            paziente["ultimo_psa"] = valore_psa_tm
                            paziente["percorso_scelto"] = scelta_fine_visita_tm

                            dettagli_tm = (
                                f"Controllo Terapia Medica Avanzata\n"
                                f"• Stato: {presenza_metastasi} | Volume: {volume_malattia} | mCRPC: {stato_crpc} (Strategia: {opzione_mcrpc})\n"
                                f"• LH-RH: {fatto_lhrh_tm} ({tipo_lhrh_tm}) | ARSI: {usa_arsi_tm} ({tipo_arsi_tm})\n"
                                f"• Chemio: {usa_chemio} ({tipo_chemio}) | HRR/BRCA: {brca_mutato} (PARPi: {tipo_parpi})\n"
                                f"• Bone Health: {terapia_osso} (Vit.D/Ca: {supp_vitd})\n"
                                f"• Biochimica: PSA {valore_psa_tm} ng/mL | Testosterone {valore_testosterone} ng/dL ({target_castrazione})\n"
                                f"• Decisione Fine Visita: {scelta_fine_visita_tm}\n"
                                f"• Note: {note_tm}"
                            )
                            
                            dati_v_tm = {
                                "data": str(datetime.today().date()),
                                "tipo": f"Follow-up Terapia Medica ({scelta_fine_visita_tm})",
                                "dettagli": dettagli_tm
                            }
                            
                            if "visite" not in paziente:
                                paziente["visite"] = []
                            paziente["visite"].append(dati_v_tm)
                            salva_db_pazienti(db_attivo)
                            st.session_state["db_pazienti"] = db_attivo
                            st.session_state["ultimo_paziente_fu_tm"] = codice_search
                            st.success("✅ Nuova valutazione di terapia medica salvata correttamente nello storico!")

                    if st.session_state.get("ultimo_paziente_fu_tm") == codice_search and paziente.get("visite"):
                        ultima_visita = paziente["visite"][-1]
                        
                        note_pdf = [
                            f"Stato mCRPC: {stato_crpc if 'stato_crpc' in locals() else ''}",
                            f"Terapia Sistemica: LHRH ({tipo_lhrh_tm if 'tipo_lhrh_tm' in locals() else ''}), ARSI ({tipo_arsi_tm if 'tipo_arsi_tm' in locals() else ''})",
                            f"Bone Health: {terapia_osso if 'terapia_osso' in locals() else ''}",
                            note_tm if 'note_tm' in locals() else ""
                        ]
                        note_pdf = [n for n in note_pdf if n]

                        pdf_bytes = genera_pdf_referto(
                            codice_search, 
                            ultima_visita, 
                            paziente.get("percorso_scelto", percorso_attuale), 
                            note_pdf, 
                            nome=paziente.get('nome', ''), 
                            cognome=paziente.get('cognome', '')
                        )
                        
                        st.download_button(
                            label="📄 Scarica Referto Terapia Medica in PDF",
                            data=pdf_bytes,
                            file_name=f"Referto_TerapiaMedica_{codice_search}.pdf",
                            mime="application/pdf",
                            key="download_pdf_tm_aggiornato"
                        )
            else:
                st.error(f"Nessun paziente trovato con il codice univoco {codice_search}.")
