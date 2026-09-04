import streamlit as st
from datetime import datetime
import math
from utils import salva_db_pazienti, genera_pdf_referto

def calcola_psdt_e_trend(visite_paziente, psa_attuale, data_attuale_str):
    """
    Calcola il PSA Doubling Time (PSADT) in mesi utilizzando i dati storici del paziente.
    """
    storico_psa = []
    for v in visite_paziente:
        dettagli = v.get("dettagli", "")
        for riga in dettagli.split("\n"):
            if "PSA:" in riga or "PSA Attuale:" in riga:
                try:
                    val_str = riga.split(":")[-1].replace("ng/ml", "").strip()
                    val = float(val_str)
                    data_v = datetime.strptime(v.get("data", str(datetime.today().date())), "%Y-%m-%d")
                    storico_psa.append((data_v, val))
                except ValueError:
                    pass

    data_corrente = datetime.strptime(data_attuale_str, "%Y-%m-%d")
    storico_psa.append((data_corrente, float(psa_attuale)))
    
    storico_psa = sorted(list(set(storico_psa)), key=lambda x: x[0])
    
    if len(storico_psa) < 2:
        return "Dati insufficienti per il calcolo del PSADT (necessari almeno 2 rilasci temporali)", None

    data_prec, psa_prec = storico_psa[-2]
    delta_giorni = (data_corrente - data_prec).days
    
    if delta_giorni <= 0 or psa_prec <= 0 or psa_attuale <= psa_prec:
        return "PSA stabile in riduzione o azzerato (PSADT non calcolabile o non applicabile)", None

    delta_mesi = delta_giorni / 30.44
    psadt_mesi = (delta_mesi * math.log(2)) / math.log(psa_attuale / psa_prec)
    
    return f"PSA Doubling Time stimato: ~{round(psadt_mesi, 1)} mesi (rispetto al controllo precedente del {data_prec.strftime('%d/%m/%Y')})", round(psadt_mesi, 1)

def render_terapia_medica(paziente, db_attivo, codice_search):
    st.subheader("Gestione Terapia Medica / Ormonale & Decision Support Avanzato")
    
    st.markdown(f"**Paziente:** {paziente.get('cognome', '')} {paziente.get('nome', '')} (ID: {codice_search})")
    
    tipo_accesso = st.radio(
        "Seleziona Tipo di Visita Medica:",
        ["Prima Visita / Inquadramento & Stadiazione TNM", "Follow-up / Controllo Periodico"],
        horizontal=True
    )

    if tipo_accesso == "Prima Visita / Inquadramento & Stadiazione TNM":
        st.markdown("### Inquadramento Iniziale, Stadiazione TNM e Stratificazione del Volume")
        
        with st.form(key="form_prima_visita_medica"):
            st.markdown("**1. Stadiazione Clinica TNM Coerente:**")
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1:
                t_stage = st.selectbox("Stadio T (Primario):", ["cT1c", "cT2a", "cT2b", "cT2c", "cT3a", "cT3b", "cT4"])
            with col_t2:
                n_stage = st.selectbox("Stadio N (Linfonodi Regionali):", ["cN0", "cN1", "cNX"])
            with col_t3:
                m_stage = st.selectbox("Stadio M (Metastasi a Distanza):", ["cM0", "cM1a (Linfonodi non regionali)", "cM1b (Ossee)", "cM1c (Viscerali / Altre)"])

            st.markdown("---")
            st.markdown("**2. Dettaglio Metastasi e Criteri di Volume (CHAARTED / STAMPEDE):**")
            
            # Se M è M1b o M1c, lo segnaliamo coerentemente
            ha_metastasi = "M1" in m_stage
            
            num_lesioni_ossee = 0
            flag_metastasi_viscerali = False
            
            if "cM1b" in m_stage or "cM1c" in m_stage or ha_metastasi:
                st.info(f"Quadro clinico metastatico rilevato da stadiazione ({m_stage}). Inserire dettagli di diffusione:")
                if "cM1b" in m_stage or "cM1b" in str(m_stage):
                    num_lesioni_ossee = st.number_input("Numero di lesioni ossee stimate (1 - 50):", min_value=0, max_value=50, value=1)
                if "cM1c" in m_stage or st.checkbox("Presenti anche metastasi viscerali (es. fegato, polmone)?"):
                    flag_metastasi_viscerali = True
            
            # Determinazione automatica High / Low volume secondo CHAARTED (>=4 lesioni con almeno 1 extra-assiale) o presenza viscerale
            is_high_volume = (num_lesioni_ossee >= 4) or flag_metastasi_viscerali
            
            if ha_metastasi:
                if is_high_volume:
                    st.error("🔥 **Classificazione: ALTO VOLUME / HIGH-RISK** ( >=4 lesioni ossee o metastasi viscerali presenti).")
                else:
                    st.warning("⚖️ **Classificazione: BASSO VOLUME / LOW-RISK** (< 4 lesioni ossee e assenza di metastasi viscerali).")
            else:
                st.success("🛡️ **Classificazione: M0 (Non Metastatico)**.")

            st.markdown("---")
            st.markdown("**3. Flag delle Comorbidità Mediche (per la scelta dell'ARPI):**")
            
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                flag_scompenso = st.checkbox("Scompenso cardiaco congestizio (ICC)")
                flag_ipertensione = st.checkbox("Ipertensione arteriosa severa / mal controllata")
                flag_diabete = st.checkbox("Diabete mellito (in particolare scompensato)")
            with col_c2:
                flag_epilessia = st.checkbox("Storia di epilessia / crisi convulsive / rischio neurologico")
                flag_politerapia = st.checkbox("Politerapia complessa / rischio interazioni CYP450")
                flag_fragilita = st.checkbox("Decadimento cognitivo / fragilità geriatrica")

            st.markdown("---")
            st.markdown("**4. Valutazione di Fitness per la Chemioterapia (Docetaxel):**")
            paziente_fit_ct = st.radio(
                "Il paziente è considerato FIT per la chemioterapia con Docetaxel?",
                ["Sì, paziente fit (idoneo alla triplice terapia se alto volume)", "No, paziente UNFIT per chemioterapia (optare per doppietta)"],
                horizontal=True
            )

            # --- MOTORE DECISIONALE AUTOMATICO (Terapia e ARPI) ---
            st.markdown("### 💡 Suggerimento Terapeutico Basato su Linee Guida e Trial Clinici")
            
            # Scelta Doppietta vs Triplice
            consiglio_terapia = ""
            if not ha_metastasi:
                consiglio_terapia = "Terapia mirata / ADT +/- ARPI (setting M0 / nmCRPC)"
                st.info(f"**Indicazione:** {consiglio_terapia}")
            elif not is_high_volume:
                consiglio_terapia = "Duplice Terapia (ADT + ARPI)"
                st.warning(f"**Indicazione:** {consiglio_terapia}. Nei pazienti a basso volume di malattia mHSPC, i trial **ARCHES** (Enzalutamide) e **TITAN** (Apalutamide) dimostrano un beneficio netto con la duplice terapia; la chemioterapia aggiuntiva non è routinariamente raccomandata.")
            else:
                # Alto volume
                if "Sì" in paziente_fit_ct:
                    consiglio_terapia = "Triplice Terapia (ADT + Docetaxel + ARPI)"
                    st.error(f"**Indicazione:** {consiglio_terapia}. Sulla base dei trial **ARASENS** (con Darolutamide, Smith et al., NEJM 2022) e **PEACE-1** (con Abiraterone, Chi et al., Lancet 2022), nei pazienti mHSPC ad alto volume e fit per chemioterapia, la triplice terapia offre il massimo vantaggio di sopravvivenza globale (OS).")
                else:
                    consiglio_terapia = "Duplice Terapia (ADT + ARPI) - Paziente Unfit per CT"
                    st.warning(f"**Indicazione:** {consiglio_terapia}. Poiché il paziente è valutato **UNFIT per la chemioterapia**, l'alternativa raccomandata consiste nella duplice terapia con ADT associata a un ARPI.")

            # Scelta ARPI specifico basato sulle comorbilità (senza tendina ma con flag)
            consiglio_arsi = ""
            giustificazione_arsi = ""
            
            if flag_epilessia:
                consiglio_arsi = "Darolutamide o Apalutamide"
                giustificazione_arsi = "Enzalutamide è controindicata/sconsigliata per il rischio di abbassamento della soglia convulsa. Darolutamide presenta minima penetrazione della barriera emato-encefalica."
            elif flag_scompenso or flag_ipertensione or flag_diabete:
                consiglio_arsi = "Darolutamide o Enzalutamide"
                giustificazione_arsi = "Cautela con Abiraterone Acetato in quanto richiede l'uso di prednisone e causa ritenzione di mineralcorticoidi, aggravando scompenso cardiaco, ipertensione e diabete."
            elif flag_politerapia or flag_fragilita:
                consiglio_arsi = "Darolutamide"
                giustificazione_arsi = "Darolutamide è indicata per il basso profilo di interazioni farmacologiche epatiche (CYP450) e la minima penetrazione della barriera emato-encefalica (Trial ARAMIS / ARASENS)."
            else:
                consiglio_arsi = "Enzalutamide, Apalutamide, Darolutamide o Abiraterone"
                giustificazione_arsi = "In assenza di comorbilità restrittive, tutti gli ARPI registrati sono validi opzioni in base ai trial ARCHES, TITAN, ARAMIS e LATITUDE."

            st.success(f"**ARPI Consigliato:** {consiglio_arsi}\n\n**Giustificazione Clinica:** {giustificazione_arsi}")

            st.markdown("---")
            psa_iniziale = st.number_input("Valore PSA Iniziale (ng/ml):", min_value=0.0, step=0.1, value=float(paziente.get("ultimo_psa", 0.0)))
            
            scelta_farmaco_finale = st.selectbox(
                "Conferma Strategia Terapeutica Prescritta:",
                [
                    "ADT Monoterapia",
                    "Duplice Terapia: ADT + Darolutamide",
                    "Duplice Terapia: ADT + Enzalutamide",
                    "Duplice Terapia: ADT + Apalutamide",
                    "Duplice Terapia: ADT + Abiraterone + Prednisone",
                    "Triplice Terapia: ADT + Docetaxel + Darolutamide (Trial ARASENS)",
                    "Triplice Terapia: ADT + Docetaxel + Abiraterone (Trial PEACE-1)"
                ]
            )
            
            note_prima_visita = st.text_area("Note cliniche generali e programma terapeutico:")
            
            submitted_pv = st.form_submit_button("Salva Prima Visita e Genera Report", type="primary")
            
            if submitted_pv:
                data_v_str = str(datetime.today().date())
                comor_elenco = []
                if flag_scompenso: comor_elenco.append("Scompenso cardiaco")
                if flag_ipertensione: comor_elenco.append("Ipertensione")
                if flag_diabete: comor_elenco.append("Diabete")
                if flag_epilessia: comor_elenco.append("Epilessia/Neurologico")
                if flag_politerapia: comor_elenco.append("Politerapia")
                if flag_fragilita: comor_elenco.append("Fragilità")

                dettagli_pv = (
                    f"TNM: T={t_stage}, N={n_stage}, M={m_stage}\n"
                    f"Lesioni Ossee: {num_lesioni_ossee} | Metastasi Viscerali: {'Sì' if flag_metastasi_viscerali else 'No'}\n"
                    f"Volume: {'Alto Volume' if is_high_volume else 'Basso Volume / M0'}\n"
                    f"Fitness Chemioterapia: {paziente_fit_ct}\n"
                    f"Comorbilità: {', '.join(comor_elenco) if comor_elenco else 'Nessuna'}\n"
                    f"Suggerimento Decisionale: {consiglio_terapia} | ARPI: {consiglio_arsi}\n"
                    f"PSA Iniziale: {psa_iniziale} ng/ml\n"
                    f"Trattamento Prescritto: {scelta_farmaco_finale}\n"
                    f"Note: {note_prima_visita}"
                )
                
                nuova_visita = {
                    "data": data_v_str,
                    "tipo": "Prima Visita Terapia Medica / Inquadramento TNM & Decision Support",
                    "dettagli": dettagli_pv
                }
                
                if "visite" not in paziente:
                    paziente["visite"] = []
                paziente["visite"].append(nuova_visita)
                paziente["ultimo_psa"] = psa_iniziale
                paziente["data_ultimo_psa"] = data_v_str
                paziente["percorso_scelto"] = scelta_farmaco_finale
                
                db_attivo[codice_search] = paziente
                salva_db_pazienti(db_attivo)
                st.session_state["db_pazienti"] = db_attivo
                st.session_state["ultimo_salvataggio_medico"] = codice_search
                st.success("Prima visita medica salvata correttamente!")

        # Download referto prima visita fuori dal form
        if st.session_state.get("ultimo_salvataggio_medico") == codice_search and paziente.get("visite"):
            ultima_v = paziente["visite"][-1]
            note_pdf_pv = [
                f"Stadiazione TNM: T={t_stage}, N={n_stage}, M={m_stage}",
                f"Volume di Malattia: {'Alto Volume' if is_high_volume else 'Basso Volume/M0'} (Lesioni ossee: {num_lesioni_ossee})",
                f"Indicazione Terapeutica Generata: {consiglio_terapia}",
                f"ARPI Consigliato e Giustificato: {consiglio_arsi} ({giustificazione_arsi})",
                f"Trattamento Scelto: {scelta_farmaco_finale}",
                f"Note cliniche: {note_prima_visita}"
            ]
            pdf_bytes_pv = genera_pdf_referto(
                codice_search, ultima_v, "Inquadramento Terapia Medica", note_pdf_pv,
                nome=paziente.get('nome',''), cognome=paziente.get('cognome','')
            )
            st.download_button(
                label="Scarica Referto Prima Visita Medica PDF",
                data=pdf_bytes_pv,
                file_name=f"PrimaVisita_Medica_{paziente.get('cognome','')}_{codice_search}.pdf",
                mime="application/pdf"
            )

    else:
        # SEZIONE FOLLOW-UP
        st.subheader("Gestione Follow-up & Monitoraggio Periodico")
        
        with st.expander("🚨 Supporto Decisionale: Evidenze Trial Clinici (Triple/Double Therapy)", expanded=False):
            st.markdown(
                "* **ARASENS (NEJM 2022):** Darolutamide + ADT + Docetaxel riduce il rischio di morte del 32.5% nel mHSPC ad alto volume.\n"
                "* **PEACE-1 (Lancet 2022):** Abiraterone + ADT + Docetaxel migliora la sopravvivenza globale nell'alto volume.\n"
                "* **ARCHES / TITAN:** Supportano la duplice terapia con ARPI nei contesti a basso volume o sensibili."
            )

        with st.form(key="form_terapia_medica_avanzata"):
            st.markdown("### Aggiornamento Schema Terapeutico e Parametri Biochimici")
            
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                linea_trattamento = st.selectbox(
                    "Fase / Linea di Trattamento in Corso:",
                    [
                        "1° Linea: ADT in monoterapia",
                        "1° Linea: Duplice Terapia (ADT + ARPI)",
                        "1° Linea: Triplice Terapia (ADT + ARPI + Docetaxel)",
                        "Setting mHSPC (Sensibile agli Ormoni)",
                        "Setting nmCRPC (Resistente alla Castrazione Non Metastasico)",
                        "Setting mCRPC (Resistente alla Castrazione Metastasico)",
                        "Terapia di Seconda Linea o successive / Altro"
                    ]
                )
            with col_s2:
                farmaco_specifico = st.text_input("Specificare farmaco in corso:")

            st.markdown("---")
            st.markdown("**Monitoraggio Biochimico (PSA & Testosterone)**")
            
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                valore_psa_attuale = st.number_input("PSA Attuale (ng/ml):", min_value=0.0, step=0.1, value=float(paziente.get("ultimo_psa", 0.0)))
            with col_b2:
                valore_testosterone = st.number_input("Testosterone Totale (ng/dl):", min_value=0.0, step=0.1, value=0.5, help="Target < 50 ng/dl")
            with col_b3:
                stato_castrazione = st.selectbox("Stato di Castrazione Biochimica:", ["Raggiunto (< 50 ng/dl)", "Non raggiunto / Fuga ormonale", "Non dosato"])

            st.markdown("---")
            st.markdown("**Imaging di Ristadiazione e Tossicità**")
            
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                esito_imaging = st.selectbox(
                    "Esito Eventuale Imaging di Ristadiazione:",
                    ["Non eseguito in questo controllo", "Stabile / Assenza di progressione", "Risposta parziale", "Progressione biochimica (PSA-only)", "Progressione d'organo / Nuove lesioni"]
                )
                vampate = st.selectbox("Vampate vasomotorie:", ["Assenti", "Lieve (gestibile)", "Moderata", "Severa"])
            with col_i2:
                astenia = st.selectbox("Astenia / Fatigue:", ["Assente", "Grado 1 (Lieve)", "Grado 2 (Moderata)", "Grado 3 (Severa)"])
                terapia_osso = st.multiselect(
                    "Supporto Osseo:",
                    ["Acido Zoledronico", "Denosumab", "Integrazione Calcio + Vitamina D", "Altro"]
                )
                
            sintomi_metabolici = st.multiselect(
                "Effetti Metabolici e Cardiovascolari:",
                ["Aumento ponderale", "Riduzione massa muscolare", "Osteopenia / Osteoporosi", "Alterazioni lipidiche", "Ipertensione arteriosa"]
            )
                
            note_cliniche = st.text_area("Note Cliniche o Variazioni Posologiche:")
            
            submitted_fu = st.form_submit_button("Salva Follow-up e Prepara Referto", type="primary")
            
            if submitted_fu:
                data_visita_str = str(datetime.today().date())
                risultato_psdt_txt, _ = calcola_psdt_e_trend(paziente.get("visite", []), valore_psa_attuale, data_visita_str)
                
                dettagli_visita = (
                    f"Linea: {linea_trattamento} | Farmaco: {farmaco_specifico if farmaco_specifico else 'Non specificato'}\n"
                    f"PSA Attuale: {valore_psa_attuale} ng/ml | {risultato_psdt_txt}\n"
                    f"Testosterone Totale: {valore_testosterone} ng/dl ({stato_castrazione})\n"
                    f"Imaging: {esito_imaging}\n"
                    f"Tossicità: Astenia ({astenia}), Vampate ({vampate})\n"
                    f"Supporto Osseo: {', '.join(terapia_osso) if terapia_osso else 'Nessuno'}\n"
                    f"Note: {note_cliniche}"
                )
                
                nuova_visita = {
                    "data": data_visita_str,
                    "tipo": "Follow-up Terapia Medica / Ormonale Avanzato",
                    "dettagli": dettagli_visita
                }
                
                if "visite" not in paziente:
                    paziente["visite"] = []
                paziente["visite"].append(nuova_visita)
                paziente["ultimo_psa"] = valore_psa_attuale
                paziente["data_ultimo_psa"] = data_visita_str
                
                db_attivo[codice_search] = paziente
                salva_db_pazienti(db_attivo)
                st.session_state["db_pazienti"] = db_attivo
                st.session_state["ultimo_salvataggio_medico"] = codice_search
                st.success("Follow-up salvato correttamente!")

        # Download fuori dal form per il follow-up
        if st.session_state.get("ultimo_salvataggio_medico") == codice_search and paziente.get("visite"):
            ultima_visita = paziente["visite"][-1]
            testo_psdt_pdf, _ = calcola_psdt_e_trend(paziente.get("visite", [])[:-1], paziente.get("ultimo_psa"), str(datetime.today().date()))
            
            note_pdf = [
                f"Schema Terapeutico: {linea_trattamento}",
                f"Valore PSA di controllo: {valore_psa_attuale} ng/ml",
                f"Andamento e Cinetica: {testo_psdt_pdf}",
                f"Testosterone Totale: {valore_testosterone} ng/dl ({stato_castrazione})",
                f"Stato Imaging: {esito_imaging}",
                f"Tossicità: Astenia ({astenia}), Vampate ({vampate})",
                f"Note cliniche: {note_cliniche}"
            ]
            
            pdf_bytes = genera_pdf_referto(
                codice_search, ultima_visita, "Terapia Medica / Ormonale", note_pdf,
                nome=paziente.get('nome', ''), cognome=paziente.get('cognome', '')
            )
            
            st.download_button(
                label="Scarica Referto Follow-up Medico PDF",
                data=pdf_bytes,
                file_name=f"FollowUp_Medico_{paziente.get('cognome', '')}_{codice_search}.pdf",
                mime="application/pdf"
            )
