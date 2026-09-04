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
        st.markdown("### Inquadramento Iniziale, Stadiazione TNM e Stratificazione del Volume di Malattia")
        
        with st.form(key="form_prima_visita_medica"):
            st.markdown("**1. Stadiazione Clinica TNM:**")
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1:
                t_stage = st.selectbox("Stadio T (Primario):", ["cT1c", "cT2a", "cT2b", "cT2c", "cT3a", "cT3b", "cT4"])
            with col_t2:
                n_stage = st.selectbox("Stadio N (Linfonodi Regionali):", ["cN0", "cN1", "cNX"])
            with col_t3:
                m_stage = st.selectbox("Stadio M (Metastasi a Distanza):", ["cM0", "cM1a (Linfonodi non regionali)", "cM1b (Ossee)", "cM1c (Viscerali / Altre)"])

            st.markdown("---")
            st.markdown("**2. Valutazione del Volume di Malattia Ossea e Viscerale (Criteri CHAARTED / STAMPEDE):**")
            
            presenza_metastasi_ossee = st.checkbox("Il paziente presenta metastasi ossee (M1b)?")
            
            num_lesioni_ossee = "Non applicabile / M0"
            volume_malattia = "Non Metastatico / Basso Rischio"
            
            if "cM1b" in m_stage or "cM1c" in m_stage or presenza_metastasi_ossee:
                num_lesioni_ossee = st.selectbox(
                    "Numero e Sede delle Lesioni Ossee (Determinante per Alto/Basso Volume):",
                    [
                        "Meno di 4 lesioni, tutte confinate allo scheletro appendicolare o pelvico/colonna (Basso Volume / Low-Volume)",
                        "4 o più lesioni ossee, con almeno una lesione al di fuori dello scheletro appendicolare o della pelvi/colonna vertebrale (Alto Volume / High-Volume)",
                        "Presenza di metastasi viscerali estese (Alto Volume)"
                    ]
                )
                if "Alto Volume" in num_lesioni_ossee:
                    volume_malattia = "Alto Volume / High-Volume (High-Risk)"
                    st.error("🔥 **Alert Clinico (Criteri CHAARTED / STAMPEDE / ARASENS / PEACE-1):** Malattia metastatica ad ALTO VOLUME. È fortemente indicata la **TRIPLICE TERAPIA** (ADT + ARPI + Chemioterapia con Docetaxel) per massimizzare la sopravvivenza globale.")
                else:
                    volume_malattia = "Basso Volume / Low-Volume (Low-Risk)"
                    st.warning("⚖️ **Alert Clinico (Criteri ARCHES / TITAN):** Malattia metastatica a BASSO VOLUME. È indicata la **DUPLICE TERAPIA** (ADT + ARPI), mentre la chemioterapia di supporto non è routinariamente raccomandata.")
            else:
                st.info("🛡️ Paziente M0 (Non Metastatico). Indicato il monitoraggio o trattamento mirato/ADT con eventuale ARPI nel setting ad alto rischio (es. nmCRPC con PSADT rapido).")

            st.markdown("---")
            st.markdown("**3. Screening delle Comorbilità per la Scelta dell'ARPI (Enzalutamide, Apalutamide, Darolutamide, Abiraterone):**")
            
            comor_scelta = st.multiselect(
                "Seleziona le condizioni cliniche e patologie concomitanti del paziente:",
                [
                    "Scompenso cardiaco congestizio (ICC)",
                    "Ipertensione arteriosa severa / mal controllata",
                    "Diabete mellito (in particolare se scompensato)",
                    "Storia di epilessia / crisi convulsive / alterazioni neurologiche centrali",
                    "Politerapia complessa / rischio elevato di interazioni farmacologiche (CYP450)",
                    "Decadimento cognitivo / fragilità geriatrica marcata",
                    "Insufficienza epatica moderata / severa"
                ],
                key="comor_scelta_prima_visita"
            )
            
            # Logica di supporto alla scelta ARPI basata sulle comorbilità selezionate
            if "Storia di epilessia / crisi convulsive / alterazioni neurologiche centrali" in comor_scelta:
                st.error("⚠️ **Controindicazione per Enzalutamide**: alto rischio di abbassamento della soglia convulsa. Preferire Darolutamide o Apalutamide.")
            if "Scompenso cardiaco congestizio (ICC)" in comor_scelta or "Ipertensione arteriosa severa / mal controllata" in comor_scelta or "Diabete mellito (in particolare se scompensato)" in comor_scelta:
                st.warning("⚠️ **Cautela con Abiraterone Acetato**: l'uso obbligatorio di prednisone/prednisolone e l'eccesso di mineralcorticoidi possono aggravare scompenso cardiaco, ipertensione e controllo glicemico. Preferire Darolutamide o Enzalutamide.")
            if "Politerapia complessa / rischio elevato di interazioni farmacologiche (CYP450)" in comor_scelta or "Decadimento cognitivo / fragilità geriatrica marcata" in comor_scelta:
                st.success("✅ **Darolutamide raccomandata**: profilo favorevole grazie alla minima penetrazione della barriera emato-encefalica e al basso impatto sulle interazioni epatiche.")

            st.markdown("---")
            psa_iniziale = st.number_input("Valore PSA Iniziale (ng/ml):", min_value=0.0, step=0.1, value=float(paziente.get("ultimo_psa", 0.0)))
            
            scelta_farmaco_iniziale = st.selectbox(
                "Strategia Terapeutica e Farmaco Scelto:",
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
                dettagli_pv = (
                    f"TNM: T={t_stage}, N={n_stage}, M={m_stage}\n"
                    f"Metastasi Ossee: {'Sì' if presenza_metastasi_ossee else 'No'} | Dettaglio: {num_lesioni_ossee}\n"
                    f"Volume di Malattia: {volume_malattia}\n"
                    f"Comorbilità Rilevanti: {', '.join(comor_scelta) if comor_scelta else 'Nessuna'}\n"
                    f"PSA Iniziale: {psa_iniziale} ng/ml\n"
                    f"Trattamento Scelto: {scelta_farmaco_iniziale}\n"
                    f"Note: {note_prima_visita}"
                )
                
                nuova_visita = {
                    "data": data_v_str,
                    "tipo": "Prima Visita Terapia Medica / Stadiazione TNM & Comorbilità",
                    "dettagli": dettagli_pv
                }
                
                if "visite" not in paziente:
                    paziente["visite"] = []
                paziente["visite"].append(nuova_visita)
                paziente["ultimo_psa"] = psa_iniziale
                paziente["data_ultimo_psa"] = data_v_str
                paziente["percorso_scelto"] = scelta_farmaco_iniziale
                
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
                f"Metastasi Ossee e Volume: {num_lesioni_ossee} ({volume_malattia})",
                f"Comorbilità registrate: {', '.join(comor_scelta) if comor_scelta else 'Nessuna'}",
                f"Trattamento Iniziale Scelto: {scelta_farmaco_iniziale}",
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

        with st.expander("💊 Consulente Scelta ARPI in base alle Comorbilità", expanded=False):
            comor_scelta_fu = st.multiselect(
                "Aggiorna condizioni cliniche concomitanti:",
                [
                    "Scompenso cardiaco congestizio (ICC)",
                    "Ipertensione arteriosa severa / mal controllata",
                    "Diabete mellito",
                    "Storia di epilessia / crisi convulsive / alterazioni neurologiche centrali",
                    "Politerapia complessa / rischio interazioni CYP450",
                    "Decadimento cognitivo / fragilità geriatrica"
                ],
                key="comor_arpi_selezionate_fu"
            )
            if "Storia di epilessia / crisi convulsive / alterazioni neurologiche centrali" in comor_scelta_fu:
                st.warning("⚠️ **Evitare Enzalutamide**: abbassa la soglia convulsa. Preferire Darolutamide o Apalutamide.")
            if "Scompenso cardiaco congestizio (ICC)" in comor_scelta_fu or "Ipertensione arteriosa severa / mal controllata" in comor_scelta_fu:
                st.warning("⚠️ **Cautela con Abiraterone**: richiede steroide e causa ritenzione di mineralcorticoidi.")

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
