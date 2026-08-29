import csv
from datetime import datetime, timedelta
import hashlib
import math
import os
import streamlit as st

# ==============================================================================
# CONFIGURAZIONE PAGINA STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="2getapp - Clinical Decision Support",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================================================================
# GESTIONE PRIVACY & REGISTRO LOCALE (GDPR COMPLIANT)
# ==============================================================================
REGISTRO_LOCALE_PATH = "Registro_Chiave_Pazienti.csv"


def genera_o_aggiorna_registro(nome, cognome, data_nascita, codice_paziente):
    """Salva il registro con il nome del paziente solo sul PC locale del medico."""
    file_exists = os.path.exists(REGISTRO_LOCALE_PATH)
    with open(REGISTRO_LOCALE_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                ["Nome", "Cognome", "Data_Nascita", "Codice_Paziente"]
            )
        writer.writerow([nome, cognome, str(data_nascita), codice_paziente])


if "db_pazienti" not in st.session_state:
    st.session_state["db_pazienti"] = {}

ELENCO_MESI = [
    "Gennaio",
    "Febbraio",
    "Marzo",
    "Aprile",
    "Maggio",
    "Giugno",
    "Luglio",
    "Agosto",
    "Settembre",
    "Ottobre",
    "Novembre",
    "Dicembre",
]

# ==============================================================================
# FUNZIONI DI CALCOLO SCIENTIFICO (PSADT & TIMING)
# ==============================================================================


def calcola_psadt(psa_precedente, data_precedente, psa_attuale, data_attuale):
    """Calcola il PSA Doubling Time (PSADT) in mesi."""
    if (
        psa_precedente is None
        or psa_precedente <= 0
        or psa_attuale <= psa_precedente
    ):
        return None

    giorni = (data_attuale - data_precedente).days
    if giorni <= 0:
        return None

    try:
        dt_giorni = (math.log(2) * giorni) / math.log(
            psa_attuale / psa_precedente
        )
        dt_mesi = dt_giorni / 30.4375
        return round(dt_mesi, 1)
    except (ValueError, ZeroDivisionError):
        return None


def calcola_gruppo_rischio_eau(isup_num, psa, ct_stage, gleason_terziario):
    """Stratificazione del Rischio EAU/NCCN."""
    is_terziario_alto = gleason_terziario in [
        "Pattern 5 Terziario",
        "Pattern 4 Terziario",
    ]

    if (
        isup_num >= 4
        or psa > 20
        or ct_stage in ["cT3a", "cT3b", "cT4"]
        or is_terziario_alto
    ):
        return (
            "Alto / Molto Alto Rischio",
            True,
            "Indicata Stadiatura Sistemica (PET/TC PSMA oppure TC Torace-Addome + Scintigrafia Ossea) per elevato rischio di micrometastasi.",
        )
    elif isup_num in [2, 3] or (10 <= psa <= 20) or ct_stage == "cT2b-cT2c":
        if isup_num == 3 or (isup_num == 2 and psa > 10):
            return (
                "Rischio Intermedio Sfavorevole",
                True,
                "Indicata Stadiatura Sistemica (Preferibile PET/TC PSMA) prima di definire il trattamento definitivo.",
            )
        else:
            return (
                "Rischio Intermedio Favorevole",
                False,
                "Stadiatura sistemica NON indicata di routine. Paziente orientabile a trattamento locale o Sorveglianza Attiva selettiva.",
            )
    else:
        return (
            "Basso Rischio",
            False,
            "Stadiatura sistemica NON indicata. Candidato ideale per Sorveglianza Attiva.",
        )


def calcola_timing_controllo(percorso, dati):
    """
    Restituisce raccomandazioni e tempistiche specifiche per tipo di follow-up.
    """
    if percorso == "Sorveglianza Attiva":
        isup = dati.get("isup", 1)
        psadt = dati.get("psadt")
        mesi_sa = dati.get("mesi_da_inizio_sa", 6)

        # Allarmi di progressione
        if (psadt is not None and psadt < 36) or isup > 1:
            return {
                "mesi_psa": 3,
                "rec_psa": "PSA Sierico tra 3 Mesi (Monitoraggio stretto per cinetica rapida / PSADT < 36 mesi).",
                "rec_rmn": "⚠️ Programmare mpRMN Prostatica urgente (entro 3 mesi) per valutare progressione di volume o PIRADS.",
                "rec_bx": "⚠️ Ripetere Biopsia Prostatica di Riconferma/Re-stadiatura (Sospetto di progressione di malattia).",
                "alert": "⚠️ ATTENZIONE: PSADT accelerato o ISUP > 1. Valutare l'uscita dalla Sorveglianza Attiva e la discussione DMT per Trattamento Radicale.",
            }
        else:
            # Protocollo SA standard
            prossima_rmn = "Programmare mpRMN Prostatica a 12 mesi dall'inizio della SA (o di controllo annuale)."
            prossima_bx = "Programmare Biopsia Prostatica di Riconferma tra i 12 e i 24 mesi dall'arruolamento."
            return {
                "mesi_psa": 6,
                "rec_psa": "PSA Sierico ogni 6 Mesi + Visita Clinica.",
                "rec_rmn": prossima_rmn,
                "rec_bx": prossima_bx,
                "alert": "🟢 Cinetica del PSA nei limiti. Il paziente può proseguire in sicurezza la Sorveglianza Attiva.",
            }

    elif percorso == "Chirurgia (Post-Prostatectomia)":
        psa = dati.get("psa", 0.0)
        mesi_op = dati.get("mesi_post_op", 0)

        if psa >= 0.20:
            return {
                "mesi_psa": 1,
                "rec_psa": "PSA Sierico Ultrasensibile di riconferma a 30 giorni.",
                "rec_imaging": "⚠️ PET/TC PSMA tempestiva per restaging di malattia.",
                "rec_azione": "Valutazione Radioterapica urgente per Radioterapia di Salvataggio Precoce ± ADT.",
                "alert": "🚨 RECIDIVA BIOCHIMICA CONFIRMATA (PSA ≥ 0.20 ng/ml).",
            }
        elif mesi_op <= 12:
            m = 3
        elif mesi_op <= 36:
            m = 6
        else:
            m = 12

        return {
            "mesi_psa": m,
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
                "mesi_psa": 1,
                "rec_psa": "PSA Sierico di riconferma a 30 giorni.",
                "rec_imaging": "⚠️ Programmare PET/TC PSMA e TC Torace-Addome di Restaging.",
                "rec_azione": "Discussione DMT per Terapia di Salvataggio (Localizzata) o Terapia Sistemica (ADT/ARPI).",
                "alert": "🚨 RECIDIVA BIOCHIMICA CRITERI PHOENIX (Nadir + 2.0 ng/ml).",
            }
        elif mesi_rt <= 24:
            m = 3
        elif mesi_rt <= 60:
            m = 6
        else:
            m = 12

        return {
            "mesi_psa": m,
            "rec_psa": f"PSA Sierico tra {m} mesi + Visita Radioterapica / Oncologica.",
            "rec_imaging": "Imaging non indicato di routine in assenza di incremento sospetto.",
            "rec_azione": "Proseguire il monitoraggio del Nadir del PSA.",
            "alert": "🟢 Cinetica del PSA stabile / post-attinica regolare.",
        }

    return {
        "mesi_psa": 6,
        "rec_psa": "PSA Sierico + Visita di controllo tra 6 Mesi.",
        "rec_imaging": "Sulla base del quadro clinico.",
        "rec_azione": "Standard.",
        "alert": "Info standard.",
    }


# ==============================================================================
# BARRA LATERALE E SELEZIONE MODULO
# ==============================================================================
st.sidebar.title("⚕️ 2getapp")
st.sidebar.caption("Clinical Decision Support in Uro-Oncologia")

organo_selezionato = st.sidebar.selectbox(
    "Seleziona Organo / Patologia:",
    [
        "🧬 PROSTATA",
        "🫘 RENE (RCC)",
        "🫁 VESCICA & UTUC",
        "🥚 TESTICOLO & PENE",
    ],
)

# ==============================================================================
# MODULO 1: PROSTATA
# ==============================================================================
if organo_selezionato == "🧬 PROSTATA":
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

    # --------------------------------------------------------------------------
    # FASE 1: PRIMA VISITA
    # --------------------------------------------------------------------------
    if modalita == "1. Prima Visita: Inquadramento Bioptico & Rischio":
        st.subheader("📋 Inserimento Anagrafica Paziente")

        col_a, col_b = st.columns(2)
        with col_a:
            nome_p = st.text_input("Nome Paziente")
            data_nascita_p = st.date_input(
                "Data di Nascita", datetime(1960, 1, 1)
            )
        with col_b:
            cognome_p = st.text_input("Cognome Paziente")
            hash_id = hashlib.md5(
                f"{nome_p}{cognome_p}{data_nascita_p}".encode()
            ).hexdigest()[:6]
            codice_paziente = f"2GET-{hash_id.upper()}"
            st.info(f"🔑 **Codice Univoco Generato:** `{codice_paziente}`")

        st.markdown("---")
        st.subheader(
            "🔬 Dati Bioptici, Clinici e Imaging Iniziale (mpRMN)"
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            isup_basale = st.selectbox(
                "ISUP Group Bioptico (Gleason Score):",
                [
                    "ISUP 1 (Gleason 3+3)",
                    "ISUP 2 (Gleason 3+4)",
                    "ISUP 3 (Gleason 4+3)",
                    "ISUP 4 (Gleason 4+4)",
                    "ISUP 5 (Gleason 9-10)",
                ],
            )
            isup_num = int(isup_basale.split()[1])

            gleason_terziario = st.selectbox(
                "Gleason Pattern Terziario:",
                [
                    "Assente",
                    "Pattern 4 Terziario",
                    "Pattern 5 Terziario",
                ],
            )

            st.markdown("🗓️ **Mese e Anno Prelievo PSA:**")
            col_m, col_y = st.columns(2)
            with col_m:
                mese_psa_b = st.selectbox(
                    "Mese", ELENCO_MESI, index=datetime.today().month - 1
                )
            with col_y:
                anno_psa_b = st.number_input(
                    "Anno",
                    min_value=2000,
                    max_value=2030,
                    value=datetime.today().year,
                )

            num_mese_b = ELENCO_MESI.index(mese_psa_b) + 1
            data_psa_basale = datetime(anno_psa_b, num_mese_b, 1).date()
            psa_basale = st.number_input(
                "PSA Basale (ng/ml)", value=6.5, step=0.1
            )

        with col2:
            ct_stage = st.selectbox(
                "Stadio T Clinico (Esplorazione Rettale):",
                [
                    "cT1c (Inapprezzabile)",
                    "cT2a (≤ metà di un lobo)",
                    "cT2b (> metà di un lobo)",
                    "cT2c (Entrambi i lobi)",
                    "cT3a (Estensione extracapsulare)",
                    "cT3b (Invasione vescicole seminali)",
                    "cT4 (Fissato o invasione strutture adiacenti)",
                ],
            )

            rmn_pirads = st.selectbox(
                "Reperto mpRMN Prostatica:",
                [
                    "PI-RADS 3",
                    "PI-RADS 4",
                    "PI-RADS 5",
                    "ECE / SVI Sospetta alla RMN",
                    "Non Eseguita",
                ],
            )

        with col3:
            st.markdown("🎯 **Valutazione Rischio & Indicazione Stadiatura**")
            gruppo_rischio, necessita_stadiatura, motivazione_stadiatura = (
                calcola_gruppo_rischio_eau(
                    isup_num, psa_basale, ct_stage, gleason_terziario
                )
            )

            st.write(f"**Classe di Rischio:** `{gruppo_rischio}`")

            if necessita_stadiatura:
                st.error("⚠️ **STADIATURA SISTEMICA INDICATA**")
                st.caption(motivazione_stadiatura)
                opzioni_terapeutiche = "La scelta terapeutica finale sarà definita dopo il referto della stadiatura in DMT II."
            else:
                st.success("✅ **STADIATURA NON INDICATA AB INITIO**")
                st.caption(motivazione_stadiatura)
                if gruppo_rischio == "Basso Rischio":
                    opzioni_terapeutiche = "Opzioni consigliate: Sorveglianza Attiva (Gold Standard), Radioterapia, Prostatectomia Radicale."
                else:
                    opzioni_terapeutiche = "Opzioni consigliate: Prostatectomia Radicale o Radioterapia."

            st.info(f"💡 **Opzioni Terapeutiche Predilette:** {opzioni_terapeutiche}")

        st.markdown("---")

        if not necessita_stadiatura:
            st.subheader("⚖️ Snodo Decisionale Immediato (Senza Stadiatura)")
            scelta_trattamento = st.selectbox(
                "Trattamento Concordato / Scelto:",
                [
                    "Sorveglianza Attiva",
                    "Chirurgia (Post-Prostatectomia)",
                    "Radioterapia",
                ],
            )
        else:
            scelta_trattamento = "In attesa di Stadiatura (DMT II)"

        if st.button("💾 Salvataggio Primo Inquadramento"):
            if not nome_p or not cognome_p:
                st.error("Inserire Nome e Cognome del paziente.")
            else:
                st.session_state["db_pazienti"][codice_paziente] = {
                    "isup": isup_num,
                    "rischio": gruppo_rischio,
                    "necessita_stadiatura": necessita_stadiatura,
                    "stadiato": False,
                    "percorso_scelto": scelta_trattamento,
                    "ultimo_psa": psa_basale,
                    "data_ultimo_psa": data_psa_basale,
                    "data_ultimo_psa_str": f"{mese_psa_b} {anno_psa_b}",
                    "psadt_attuale": None,
                    "visite": [
                        {
                            "data": str(datetime.today().date()),
                            "tipo": "Visita I - Inquadramento Bioptico",
                            "dettagli": f"ISUP {isup_num} | Gleason Terziario: {gleason_terziario} | PSA: {psa_basale} ({mese_psa_b} {anno_psa_b}) | {ct_stage} | Rischio: {gruppo_rischio} | Percorso: {scelta_trattamento}",
                        }
                    ],
                }
                genera_o_aggiorna_registro(
                    nome_p, cognome_p, data_nascita_p, codice_paziente
                )
                st.success(
                    f"Paziente salvato con successo! Codice Univoco: {codice_paziente}."
                )

    # --------------------------------------------------------------------------
    # FASE 2: SECONDA VISITA / DMT II
    # --------------------------------------------------------------------------
    elif modalita == "2. Seconda Visita / DMT: Referto Stadiatura & Decisione":
        st.subheader("🔍 Cerca Paziente per Discussione DMT II")
        codice_search = st.text_input("Inserisci Codice Univoco Paziente:")

        if codice_search in st.session_state["db_pazienti"]:
            paziente = st.session_state["db_pazienti"][codice_search]
            st.success(f"Paziente Trovato! ID: {codice_search}")

            st.write(
                f"**Classe di Rischio Iniziale:** `{paziente.get('rischio')}`"
            )

            st.markdown("---")
            st.subheader("📊 Inserimento Referto Stadiatura (PET PSMA / TC + Scintigrafia)")

            col1, col2 = st.columns(2)
            with col1:
                tipo_imaging = st.selectbox(
                    "Esame di Stadiatura Eseguito:",
                    [
                        "PET/TC PSMA",
                        "TC Torace-Addome + Scintigrafia Ossea",
                        "mpRMN + Scintigrafia",
                    ],
                )
                c_n = st.selectbox(
                    "Stadio Linfonodale Clinico (cN):",
                    [
                        "cN0 (Assenza di adenopatie patologiche)",
                        "cN1 (Linfonodi Pelvici Positivi)",
                        "cNX",
                    ],
                )

            with col2:
                c_m = st.selectbox(
                    "Stadio Metastatico Clinico (cM):",
                    [
                        "cM0 (Assenza di Metastasi a Distanza)",
                        "cM1a (Linfonodi Extra-pelvici)",
                        "cM1b (Metastasi Ossee)",
                        "cM1c (Metastasi Viscerali)",
                    ],
                )

            st.markdown("---")
            st.subheader("⚖️ Snodo Decisionale DMT Finale")

            if c_m != "cM0 (Assenza di Metastasi a Distanza)":
                st.error("🎯 **Indicazione Linee Guida:** Malattia Metastatica (cM1). Terapia Sistemica.")
            elif c_n == "cN1 (Linfonodi Pelvici Positivi)":
                st.warning("🎯 **Indicazione Linee Guida:** Malattia cN1. Radioterapia Pelvica + ADT o Chirurgia Multimodale.")
            else:
                st.success("🎯 **Indicazione Linee Guida:** Malattia Localizzata cM0. Chirurgia Radicale o Radioterapia ± ADT.")

            scelta_trattamento = st.selectbox(
                "Trattamento Concordato in DMT:",
                [
                    "Chirurgia (Post-Prostatectomia)",
                    "Radioterapia",
                    "Terapia Medica / Metastatico",
                    "Sorveglianza Attiva",
                ],
            )

            deviazione = (
                c_m != "cM0 (Assenza di Metastasi a Distanza)"
                and scelta_trattamento in ["Sorveglianza Attiva", "Chirurgia (Post-Prostatectomia)"]
            )
            motivazione_clinica = ""
            if deviazione:
                st.error("⚠️ Deviazione dalle Linee Guida rilevata.")
                motivazione_clinica = st.text_area("Inserisci Motivazione Clinica (Obbligatoria):")

            if st.button("💾 Conferma Decisione DMT"):
                if deviazione and not motivazione_clinica.strip():
                    st.error("Inserire motivazione per la deviazione.")
                else:
                    paziente["stadiato"] = True
                    paziente["percorso_scelto"] = scelta_trattamento
                    paziente["visite"].append({
                        "data": str(datetime.today().date()),
                        "tipo": "Visita II - Referto Stadiatura & Decisione DMT",
                        "dettagli": f"Imaging: {tipo_imaging} | {c_n.split()[0]} {c_m.split()[0]} | Decisione DMT: {scelta_trattamento}"
                        + (f" | Deviazione: {motivazione_clinica}" if motivazione_clinica else ""),
                    })
                    st.success("Decisione DMT salvata nello storico paziente!")
        else:
            st.warning("Codice paziente non trovato.")

    # --------------------------------------------------------------------------
    # FASE 3: CONTROLLO SUCCESSIVO / FOLLOW-UP PSA SPECIFICO
    # --------------------------------------------------------------------------
    elif modalita == "3. Controllo Successivo / Follow-up PSA":
        st.subheader("🔍 Richiama Paziente per Follow-up")
        codice_search = st.text_input("Inserisci Codice Univoco Paziente:")

        if codice_search in st.session_state["db_pazienti"]:
            paziente = st.session_state["db_pazienti"][codice_search]
            st.success(f"Paziente Trovato! ID: {codice_search}")

            percorso_attuale = paziente["percorso_scelto"]
            st.info(f"📌 **Percorso Terapeutico In Corso:** `{percorso_attuale}`")

            # MOSTRA STORICO VISITE
            with st.expander("📜 Visualizza Storico Controlli Precedenti", expanded=False):
                for idx, v in enumerate(paziente["visite"]):
                    st.caption(f"• **{v['data']} ({v['tipo']}):** {v['dettagli']}")

            st.markdown("---")
            st.subheader("🩸 Inserimento Nuova Valutazione PSA")

            col_psa1, col_psa2, col_psa3 = st.columns(3)
            with col_psa1:
                mese_psa_a = st.selectbox(
                    "Mese Prelievo PSA", ELENCO_MESI, index=datetime.today().month - 1
                )
            with col_psa2:
                anno_psa_a = st.number_input(
                    "Anno Prelievo PSA", min_value=2000, max_value=2030, value=datetime.today().year
                )
            with col_psa3:
                psa_attuale = st.number_input(
                    "Valore PSA Sierico (ng/ml):",
                    min_value=0.0,
                    value=float(paziente.get("ultimo_psa", 0.0)),
                    step=0.01,
                    format="%.2f",
                )

            num_mese_a = ELENCO_MESI.index(mese_psa_a) + 1
            data_psa_attuale = datetime(anno_psa_a, num_mese_a, 1).date()
            str_data_psa = f"{mese_psa_a} {anno_psa_a}"

            psa_prec = paziente.get("ultimo_psa")
            data_prec = paziente.get("data_ultimo_psa")

            psadt_calcolato = calcola_psadt(psa_prec, data_prec, psa_attuale, data_psa_attuale)

            if psadt_calcolato is not None:
                st.metric(
                    label="📈 PSA Doubling Time (PSADT) Calcolato",
                    value=f"{psadt_calcolato} Mesi",
                    delta="⚠️ Rapidità Raddoppio (<36m)" if psadt_calcolato < 36 else "Stabile/Lento",
                    delta_color="inverse",
                )
            elif psa_prec is not None and psa_attuale <= psa_prec:
                st.info("ℹ️ **PSADT Non Applicabile:** Valore PSA stabile o in riduzione rispetto al controllo precedente.")

            st.markdown("---")

            # ------------------------------------------------------------------
            # FORM SPECIFICO A SECONDA DEL PERCORSO
            # ------------------------------------------------------------------
            if percorso_attuale == "Sorveglianza Attiva":
                st.subheader("🛡️ Protocollo Follow-up: SORVEGLIANZA ATTIVA")
                
                col_sa1, col_sa2 = st.columns(2)
                with col_sa1:
                    mesi_in_sa = st.number_input("Mesi complessivi in Sorveglianza Attiva:", min_value=1, value=6)
                with col_sa2:
                    eseguita_rmn_recentemente = st.checkbox("Eseguita mpRMN nell'ultimo anno?")

                dati_eval = {
                    "isup": paziente.get("isup", 1),
                    "psadt": psadt_calcolato,
                    "mesi_da_inizio_sa": mesi_in_sa
                }
                res_fu = calcola_timing_controllo("Sorveglianza Attiva", dati_eval)

                if "⚠️" in res_fu["alert"]:
                    st.error(res_fu["alert"])
                else:
                    st.success(res_fu["alert"])

                st.markdown("### 🗓️ Pianificazione Prossimi Esami Consigliati:")
                st.write(f"• **Ripetizione PSA Sierico:** {res_fu['rec_psa']}")
                st.write(f"• **Risonanza Magnetica (mpRMN):** {res_fu['rec_rmn']}")
                st.write(f"• **Biopsia Prostatica:** {res_fu['rec_bx']}")

            elif percorso_attuale == "Chirurgia (Post-Prostatectomia)":
                st.subheader("🔪 Protocollo Follow-up: POST-PROSTATECTOMIA")
                mesi_post_op = st.number_input("Mesi trascorsi dall'Intervento:", min_value=1, value=6)

                res_fu = calcola_timing_controllo("Chirurgia (Post-Prostatectomia)", {"psa": psa_attuale, "mesi_post_op": mesi_post_op})

                if "🚨" in res_fu["alert"]:
                    st.error(res_fu["alert"])
                else:
                    st.success(res_fu["alert"])

                st.markdown("### 🗓️ Pianificazione Prossimo Controllo:")
                st.write(f"• **Raccomandazione PSA:** {res_fu['rec_psa']}")
                st.write(f"• **Imaging Strategico:** {res_fu['rec_imaging']}")
                st.write(f"• **Condotta Clinica:** {res_fu['rec_azione']}")

            elif percorso_attuale == "Radioterapia":
                st.subheader("⚛️ Protocollo Follow-up: POST-RADIOTERAPIA")
                col_rt1, col_rt2 = st.columns(2)
                with col_rt1:
                    mesi_post_rt = st.number_input("Mesi trascorsi dalla RT:", min_value=1, value=12)
                with col_rt2:
                    psa_nadir = st.number_input("PSA Nadir Raggiunto (ng/ml):", min_value=0.0, value=0.10, step=0.01)

                res_fu = calcola_timing_controllo("Radioterapia", {"psa": psa_attuale, "psa_nadir": psa_nadir, "mesi_post_rt": mesi_post_rt})

                if "🚨" in res_fu["alert"]:
                    st.error(res_fu["alert"])
                else:
                    st.success(res_fu["alert"])

                st.markdown("### 🗓️ Pianificazione Prossimo Controllo:")
                st.write(f"• **Raccomandazione PSA:** {res_fu['rec_psa']}")
                st.write(f"• **Imaging Strategico:** {res_fu['rec_imaging']}")
                st.write(f"• **Condotta Clinica:** {res_fu['rec_azione']}")

            else:
                st.subheader("💊 Protocollo Follow-up: TERAPIA MEDICA / METASTATICO")
                res_fu = calcola_timing_controllo("Terapia Medica / Metastatico", {})
                st.write(f"• **Monitoraggio:** {res_fu['rec_psa']}")

            if st.button("💾 Salvataggio Visita di Controllo"):
                paziente["ultimo_psa"] = psa_attuale
                paziente["data_ultimo_psa"] = data_psa_attuale
                paziente["data_ultimo_psa_str"] = str_data_psa
                
                psadt_str = f" | PSADT: {psadt_calcolato} mesi" if psadt_calcolato else ""
                paziente["visite"].append({
                    "data": str(datetime.today().date()),
                    "tipo": f"Follow-up ({percorso_attuale})",
                    "dettagli": f"PSA: {psa_attuale:.2f} ({str_data_psa}){psadt_str} | Indicazioni: {res_fu['rec_psa']}",
                })
                st.success("Controllo registrato con successo nello storico del paziente!")

        else:
            st.warning("Codice paziente non trovato.")

# ==============================================================================
# MODULI RENE, VESCICA, TESTICOLO
# ==============================================================================
elif organo_selezionato == "🫘 RENE (RCC)":
    st.title("🫘 Carcinoma Renale (RCC)")
    st.info("Modulo Stadiatura TNM & IMDC Risk Score.")

elif organo_selezionato == "🫁 VESCICA & UTUC":
    st.title("🫁 Carcinoma Uroteliale Vescicale & UTUC")
    st.info("Stratificazione NMIBC e Elegibilità Cisplatino (Galsky).")

elif organo_selezionato == "🥚 TESTICOLO & PENE":
    st.title("🥚 Tumori del Testicolo & del Pene")
    st.info("Classificazione IGCCCG e Marcatori Sierici.")
