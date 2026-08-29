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

# Lista Mesi per il Selectbox
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
    """
    Calcola il PSA Doubling Time (PSADT) in mesi basandosi sui mesi/anni del prelievo.
    Formula: PSADT = [ln(2) * giorni_trascorsi] / ln(PSA_attuale / PSA_precedente)
    """
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


def calcola_timing_controllo(percorso, dati):
    """Restituisce: (Mesi al prossimo controllo, Esami raccomandati)"""
    if percorso == "Sorveglianza Attiva":
        isup = dati.get("isup", 1)
        psadt = dati.get("psadt")
        if isup > 1 or (psadt is not None and psadt < 36):
            return (
                3,
                "PSA Sierico + Visita Clinica (Monitoraggio stretto per sospetta progressione/PSADT rapido)",
            )
        return 6, "PSA Sierico + Visita Clinica (Programmare mpRMN a 12 mesi)"

    elif percorso == "Chirurgia (Post-Prostatectomia)":
        psa = dati.get("psa", 0.0)
        mesi_op = dati.get("mesi_post_op", 0)

        if psa >= 0.20:
            return (
                1,
                "⚠️ RECIDIVA BIOCHIMICA (PSA ≥ 0.20 ng/ml): Eseguire PET/TC PSMA tempestiva e richiedere consulenza Radioterapica per RT di Salvataggio.",
            )
        elif mesi_op <= 12:
            return 3, "PSA Sierico Ultrasensibile + Visita Urologica"
        elif mesi_op <= 36:
            return 6, "PSA Sierico + Visita Urologica"
        return 12, "PSA Sierico Anno + Visita Urologica Controllo"

    elif percorso == "Radioterapia":
        psa = dati.get("psa", 0.0)
        psa_nadir = dati.get("psa_nadir", 0.0)
        mesi_rt = dati.get("mesi_post_rt", 0)

        if (psa - psa_nadir) >= 2.0:
            return (
                1,
                "⚠️ RECIDIVA BIOCHIMICA PHOENIX (Nadir + 2.0 ng/ml): Programmare PET/TC PSMA e restaging sistemico per terapia di salvataggio/sistemica.",
            )
        elif mesi_rt <= 24:
            return 3, "PSA Sierico + Visita Oncologica/Radioterapica"
        elif mesi_rt <= 60:
            return 6, "PSA Sierico + Visita Clinica"
        return 12, "PSA Sierico Anno + Visita Clinica"

    elif percorso in ["Terapia Medica / Metastatico", "Avanzato/Metastatico"]:
        progressione = dati.get("progressione", False)
        crpc = dati.get("crpc", False)

        if crpc or progressione:
            return (
                2,
                "PSA + Testosterone Sierico (<50 ng/dL) + Imaging di Restaging (TC Addome/Torace + Scintigrafia od eventuale PET PSMA) + Valutazione test BRCA/HRR.",
            )
        return (
            3,
            "PSA + Testosterone Sierico + Valutazione Tollerabilità/Tossicità Terapeutica",
        )

    return 6, "PSA Sierico + Visita Clinica Standard"


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
            "1. Primo Inquadramento DMT & Stadiatura Basale",
            "2. Richiama Paziente / Inserisci Nuova Visita",
        ],
        horizontal=True,
    )

    # --------------------------------------------------------------------------
    # FASE 1: PRIMO INQUADRAMENTO DMT BASALE
    # --------------------------------------------------------------------------
    if modalita == "1. Primo Inquadramento DMT & Stadiatura Basale":
        st.subheader("📋 Inserimento Dati Paziente & Anagrafica Locale")

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
        st.subheader("📊 Stadiatura Clinica e Quadro di Rischio")

        col1, col2, col3 = st.columns(3)
        with col1:
            isup_basale = st.selectbox(
                "ISUP Group Bioptico (Gleason):",
                [
                    "ISUP 1 (Gleason 3+3)",
                    "ISUP 2 (Gleason 3+4)",
                    "ISUP 3 (Gleason 4+3)",
                    "ISUP 4 (Gleason 4+4)",
                    "ISUP 5 (Gleason 9-10)",
                ],
            )
            isup_num = int(isup_basale.split()[1])

            # DATA PRELIEVO PSA BASALE - SOLO MESE E ANNO
            st.markdown("🗓️ **Mese e Anno Prelievo PSA Basale:**")
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

            # Converti in oggetto datetime (primo giorno del mese)
            num_mese_b = ELENCO_MESI.index(mese_psa_b) + 1
            data_psa_basale = datetime(anno_psa_b, num_mese_b, 1).date()

            psa_basale = st.number_input(
                "PSA Basale (ng/ml)", value=6.5, step=0.1
            )

        with col2:
            imaging_stadiativo = st.multiselect("Imaging Stadiativo Eseguito:", [
                "PET/TC PSMA",
                "TC Addome Completo e Torace",
                "Scintigrafia Ossea Total-Body",
                "mpRMN Prostatica",
            ])
            c_n = st.selectbox(
                "Stadio Linfonodale Clinico (cN):",
                ["cN0", "cN1 (Linfonodi Pelvici Positivi)", "cNX"],
            )

        with col3:
            c_m = st.selectbox(
                "Stadio Metastatico Clinico (cM):",
                [
                    "cM0 (Assenza di Metastasi)",
                    "cM1a (Linfonodi Extra-pelvici)",
                    "cM1b (Metastasi Ossee)",
                    "cM1c (Metastasi Viscerali)",
                ],
            )

        # RACCOMANDAZIONE GUIDELINE AUTOMATICA
        raccomandazione_lg = "Sorveglianza Attiva"
        if c_m != "cM0 (Assenza di Metastasi)":
            raccomandazione_lg = "Terapia Medica / Metastatico"
        elif isup_num >= 4 or psa_basale > 20 or c_n == "cN1":
            raccomandazione_lg = (
                "Radioterapia o Chirurgia (Alto Rischio / Multimodale)"
            )
        elif isup_num in [2, 3]:
            raccomandazione_lg = "Chirurgia o Radioterapia"

        st.warning(
            f"🎯 **Indicazione Linee Guida Ufficiali (EAU/NCCN):** {raccomandazione_lg}"
        )

        st.markdown("---")
        st.subheader("⚖️ Snodo Decisionale DMT & Congruenza Terapeutica")

        scelta_trattamento = st.selectbox(
            "Trattamento Concordato in DMT / Scelto dal Paziente:",
            [
                "Sorveglianza Attiva",
                "Chirurgia (Post-Prostatectomia)",
                "Radioterapia",
                "Terapia Medica / Metastatico",
            ],
        )

        deviazione = False
        if isup_num >= 4 and scelta_trattamento == "Sorveglianza Attiva":
            deviazione = True
        elif (
            c_m != "cM0 (Assenza di Metastasi)"
            and scelta_trattamento
            in ["Sorveglianza Attiva", "Chirurgia (Post-Prostatectomia)"]
        ):
            deviazione = True

        motivazione_clinica = ""
        if deviazione:
            st.error(
                "⚠️ **ATTENZIONE: La scelta terapeutica diverge dalle Linee Guida di riferimento.**"
            )
            motivazione_clinica = st.text_area(
                "Spiegazione / Motivazione Clinica della Deviazione (Obbligatoria per Tracciabilità Medico-Legale):",
                help="Inserire i motivi clinici, comorbilità o preferenze del paziente che hanno portato a questa scelta.",
            )

        if st.button("💾 Conferma Inquadramento e Archivia Paziente"):
            if deviazione and not motivazione_clinica.strip():
                st.error(
                    "Impossibile salvare: Inserire la motivazione clinica per giustificare la deviazione dalle Linee Guida."
                )
            elif not nome_p or not cognome_p:
                st.error("Inserire Nome e Cognome del paziente.")
            else:
                st.session_state["db_pazienti"][codice_paziente] = {
                    "isup": isup_num,
                    "percorso_scelto": scelta_trattamento,
                    "ultimo_psa": psa_basale,
                    "data_ultimo_psa": data_psa_basale,
                    "data_ultimo_psa_str": f"{mese_psa_b} {anno_psa_b}",
                    "psadt_attuale": None,
                    "visite": [
                        {
                            "data": str(datetime.today().date()),
                            "tipo": "Inquadramento DMT Basale",
                            "dettagli": f"ISUP {isup_num} | PSA: {psa_basale} ng/ml ({mese_psa_b} {anno_psa_b}) | {c_n} {c_m} | Scelta: {scelta_trattamento}"
                            + (
                                f" | Deviazione Note: {motivazione_clinica}"
                                if motivazione_clinica
                                else ""
                            ),
                        }
                    ],
                }
                genera_o_aggiorna_registro(
                    nome_p, cognome_p, data_nascita_p, codice_paziente
                )
                st.success(
                    f"Paziente archiviato con successo! Codice Univoco: {codice_paziente}."
                )
                st.info(
                    "Il file 'Registro_Chiave_Pazienti.csv' è stato aggiornato sul tuo PC."
                )

    # --------------------------------------------------------------------------
    # FASE 2: RICHIAMA PAZIENTE / NUOVA VISITA DI CONTROLLO
    # --------------------------------------------------------------------------
    elif modalita == "2. Richiama Paziente / Inserisci Nuova Visita":
        st.subheader("🔍 Cerca Paziente in Archivio")
        codice_search = st.text_input(
            "Inserisci Codice Univoco Paziente (es. 2GET-A8B9C):"
        )

        if codice_search in st.session_state["db_pazienti"]:
            paziente = st.session_state["db_pazienti"][codice_search]
            st.success(f"Paziente Trovato! ID: {codice_search}")

            # MOSTRA STORICO
            st.write("**📜 Storico Valutazioni e PSA Precedenti:**")
            for idx, v in enumerate(paziente["visite"]):
                st.caption(
                    f"• **Visita {idx+1} ({v['data']}) - {v['tipo']}:** {v['dettagli']}"
                )

            st.markdown("---")
            st.subheader("➕ Inserisci Nuova Visita di Controllo")
            percorso_attuale = paziente["percorso_scelto"]
            st.info(f"**Percorso Clinico Attuale:** {percorso_attuale}")

            # PRELIEVO PSA E SELEZIONE MESE/ANNO
            st.markdown("🩸 **Nuova Valutazione PSA Sierico**")
            col_psa1, col_psa2, col_psa3 = st.columns(3)

            with col_psa1:
                mese_psa_a = st.selectbox(
                    "Mese Prelievo PSA",
                    ELENCO_MESI,
                    index=datetime.today().month - 1,
                )
            with col_psa2:
                anno_psa_a = st.number_input(
                    "Anno Prelievo PSA",
                    min_value=2000,
                    max_value=2030,
                    value=datetime.today().year,
                )
            with col_psa3:
                psa_attuale = st.number_input(
                    "Valore PSA Sierico (ng/ml):",
                    min_value=0.0,
                    value=float(paziente.get("ultimo_psa", 0.0)),
                    step=0.01,
                    format="%.2f",
                )

            # Converti data in datetime.date (1° del mese)
            num_mese_a = ELENCO_MESI.index(mese_psa_a) + 1
            data_psa_attuale = datetime(anno_psa_a, num_mese_a, 1).date()
            str_data_psa = f"{mese_psa_a} {anno_psa_a}"

            # CALCOLO PSADT AUTOMATICO
            psa_prec = paziente.get("ultimo_psa")
            data_prec = paziente.get("data_ultimo_psa")

            psadt_calcolato = calcola_psadt(
                psa_prec, data_prec, psa_attuale, data_psa_attuale
            )

            if psadt_calcolato is not None:
                st.metric(
                    label="📈 PSA Doubling Time (PSADT) Calcolato Automaticamente",
                    value=f"{psadt_calcolato} Mesi",
                    delta=(
                        "⚠️ Raddoppio Rapido (<10 mesi)"
                        if psadt_calcolato < 10
                        else "Stabile/Lento"
                    ),
                    delta_color="inverse",
                )
            elif psa_prec is not None and psa_attuale <= psa_prec:
                st.info(
                    "ℹ️ **PSADT non applicabile**: Il valore di PSA è stabile o in calo rispetto al controllo precedente."
                )

            st.markdown("---")

            # ------------------------------------------------------------------
            # FOLLOW-UP POST-CHIRURGIA
            # ------------------------------------------------------------------
            if percorso_attuale == "Chirurgia (Post-Prostatectomia)":
                with st.form("form_chirurgia"):
                    data_v = st.date_input(
                        "Data Visita Odierna", datetime.today()
                    )
                    mesi_post_op = st.number_input(
                        "Mesi trascorsi dall'Intervento Chirugico",
                        min_value=1,
                        value=6,
                    )

                    btn_salva = st.form_submit_button("💾 Salva Visita")

                    if btn_salva:
                        mesi_prossimo, esami_rec = calcola_timing_controllo(
                            percorso_attuale,
                            {"psa": psa_attuale, "mesi_post_op": mesi_post_op},
                        )
                        data_prossima = data_v + timedelta(
                            days=mesi_prossimo * 30
                        )

                        st.markdown("---")
                        st.subheader("🗓️ Programmazione Prossimo Controllo")
                        st.info(
                            f"**Timing Consigliato:** Tra **{mesi_prossimo} mesi**"
                        )
                        st.success(
                            f"**Data Prevista Controllo:** {data_prossima.strftime('%d/%m/%Y')}"
                        )
                        st.write(f"**Esami da Richiedere:** {esami_rec}")

                        status = (
                            "RECIDIVA BIOCHIMICA (PSA ≥ 0.20)"
                            if psa_attuale >= 0.20
                            else "Controllo Regolare"
                        )
                        psadt_str = (
                            f" | PSADT: {psadt_calcolato} mesi"
                            if psadt_calcolato
                            else ""
                        )

                        paziente["ultimo_psa"] = psa_attuale
                        paziente["data_ultimo_psa"] = data_psa_attuale
                        paziente["data_ultimo_psa_str"] = str_data_psa
                        paziente["visite"].append({
                            "data": str(data_v),
                            "tipo": "Follow-up Post-Chirurgia",
                            "dettagli": f"PSA: {psa_attuale:.2f} ({str_data_psa}){psadt_str} | Status: {status} | Prossimo Controllo: {data_prossima.strftime('%d/%m/%Y')}",
                        })

            # ------------------------------------------------------------------
            # FOLLOW-UP POST-RADIOTERAPIA
            # ------------------------------------------------------------------
            elif percorso_attuale == "Radioterapia":
                with st.form("form_rt"):
                    data_v = st.date_input(
                        "Data Visita Odierna", datetime.today()
                    )
                    mesi_post_rt = st.number_input(
                        "Mesi trascorsi dal termine della RT",
                        min_value=1,
                        value=12,
                    )
                    psa_nadir = st.number_input(
                        "PSA Nadir Raggiunto (ng/ml)", step=0.01, format="%.2f"
                    )

                    btn_salva = st.form_submit_button("💾 Salva Visita")

                    if btn_salva:
                        mesi_prossimo, esami_rec = calcola_timing_controllo(
                            percorso_attuale,
                            {
                                "psa": psa_attuale,
                                "psa_nadir": psa_nadir,
                                "mesi_post_rt": mesi_post_rt,
                            },
                        )
                        data_prossima = data_v + timedelta(
                            days=mesi_prossimo * 30
                        )

                        st.markdown("---")
                        st.subheader("🗓️ Programmazione Prossimo Controllo")
                        st.info(
                            f"**Timing Consigliato:** Tra **{mesi_prossimo} mesi**"
                        )
                        st.success(
                            f"**Data Prevista Controllo:** {data_prossima.strftime('%d/%m/%Y')}"
                        )
                        st.write(f"**Esami da Richiedere:** {esami_rec}")

                        psadt_str = (
                            f" | PSADT: {psadt_calcolato} mesi"
                            if psadt_calcolato
                            else ""
                        )

                        paziente["ultimo_psa"] = psa_attuale
                        paziente["data_ultimo_psa"] = data_psa_attuale
                        paziente["data_ultimo_psa_str"] = str_data_psa
                        paziente["visite"].append({
                            "data": str(data_v),
                            "tipo": "Follow-up Post-RT",
                            "dettagli": f"PSA: {psa_attuale:.2f} ({str_data_psa} - Nadir: {psa_nadir:.2f}){psadt_str} | Prossimo Controllo: {data_prossima.strftime('%d/%m/%Y')}",
                        })

            # ------------------------------------------------------------------
            # FOLLOW-UP TERAPIA MEDICA / METASTATICO (BRCA / HRR MODULO)
            # ------------------------------------------------------------------
            elif percorso_attuale in [
                "Terapia Medica / Metastatico",
                "Avanzato/Metastatico",
            ]:
                with st.form("form_onco"):
                    data_v = st.date_input(
                        "Data Visita Odierna", datetime.today()
                    )

                    st.markdown("🧬 **Assetto Genetico e Molecolare:**")
                    test_brca = st.selectbox(
                        "Stato Mutazionale BRCA1/2 - HRR:",
                        [
                            "Non Eseguito",
                            "BRCA1/2 Mutato (Germinale/Somatico)",
                            "HRR Mutato (non BRCA)",
                            "Wild Type (Negativo)",
                        ],
                    )

                    st.markdown("💊 **Stato Clinico e Linea Terapeutica:**")
                    crpc = st.checkbox(
                        "Stato Castration-Resistant (mCRPC / nmCRPC)"
                    )
                    progressione = st.checkbox(
                        "Innalzamento PSA consecutivo / Progresione Strumentale"
                    )

                    btn_salva = st.form_submit_button(
                        "💾 Salva Valutazione Oncologica"
                    )

                    if btn_salva:
                        mesi_prossimo, esami_rec = calcola_timing_controllo(
                            percorso_attuale,
                            {"crpc": crpc, "progressione": progressione},
                        )
                        data_prossima = data_v + timedelta(
                            days=mesi_prossimo * 30
                        )

                        st.markdown("---")
                        st.subheader(
                            "🗓️ Programmazione Prossimo Controllo Oncologico"
                        )
                        st.info(
                            f"**Timing Consigliato:** Tra **{mesi_prossimo} mesi**"
                        )
                        st.success(
                            f"**Data Prevista Controllo:** {data_prossima.strftime('%d/%m/%Y')}"
                        )
                        st.write(f"**Esami Obbligatori:** {esami_rec}")

                        if "BRCA" in test_brca:
                            st.warning(
                                "💡 **Indicazione Terapeutica:** Presenza di mutazione BRCA. Valutare idoneità a PARP-Inibitori (es. Olaparib) in combinazione o monoterapia."
                            )

                        psadt_str = (
                            f" | PSADT: {psadt_calcolato} mesi"
                            if psadt_calcolato
                            else ""
                        )

                        paziente["ultimo_psa"] = psa_attuale
                        paziente["data_ultimo_psa"] = data_psa_attuale
                        paziente["data_ultimo_psa_str"] = str_data_psa
                        paziente["visite"].append({
                            "data": str(data_v),
                            "tipo": "Oncologia Avanzata/Metastatica",
                            "dettagli": f"PSA: {psa_attuale:.2f} ({str_data_psa}){psadt_str} | BRCA: {test_brca} | CRPC: {crpc} | Prossima Visita: {data_prossima.strftime('%d/%m/%Y')}",
                        })
        else:
            st.warning(
                "Codice non trovato. Verifica il codice univoco sul tuo file 'Registro_Chiave_Pazienti.csv' locale."
            )

# ==============================================================================
# MODULO 2: RENE (RCC)
# ==============================================================================
elif organo_selezionato == "🫘 RENE (RCC)":
    st.title("🫘 Carcinoma Renale (RCC) - Decision Support System")
    st.info("Modulo Stadiatura TNM, Score IMDC (Heng) per M-RCC e SSIGN Score.")

    st.subheader("Calcolatore IMDC Risk Score (per M-RCC Metastatico)")
    c1, c2 = st.columns(2)
    with c1:
        ecog = st.checkbox("Karnofsky Performance Status < 80% (o ECOG ≥ 2)")
        time_dx = st.checkbox(
            "Tempo da Diagnosi a Trattamento Sistemico < 1 Anno"
        )
        hb = st.checkbox("Emoglobina < Limite Inferiore della Norma (LNN)")
    with c2:
        ca = st.checkbox(
            "Calcio Sierico Corretto > 10.0 mg/dL (Ipercalcemia)"
        )
        anc = st.checkbox("Neutrofili Assoluti (ANC) > ULN")
        plt = st.checkbox("Piastrine > ULN (Piastritosi)")

    score_imdc = sum([ecog, time_dx, hb, ca, anc, plt])

    if score_imdc == 0:
        st.success("🟢 **Rischio IMDC: FAVOREVOLE (0 Fattori)**")
        st.write(
            "**Indicazione Terapeutica:** Doppietta Immuno-TKI o Immuno-Immuno secondo linee guida EAU."
        )
    elif score_imdc in [1, 2]:
        st.warning("🟡 **Rischio IMDC: INTERMEDIO (1-2 Fattori)**")
        st.write(
            "**Indicazione Terapeutica:** Immuno-Immuno (Nivolumab+Ipilimumab) o Immuno-TKI."
        )
    else:
        st.error("🔴 **Rischio IMDC: SFAVOREVOLE / POOR (≥ 3 Fattori)**")
        st.write(
            "**Indicazione Terapeutica:** Immuno-Immuno (Nivolumab+Ipilimumab) o Immuno-TKI."
        )

# ==============================================================================
# MODULO 3: VESCICA & UTUC
# ==============================================================================
elif organo_selezionato == "🫁 VESCICA & UTUC":
    st.title("🫁 Carcinoma Uroteliale Vescicale & UTUC")
    st.info("Modulo Stratificazione EAU NMIBC & Criteri Elegibilità Cisplatino.")

    st.subheader("Criteri di Elegibilità al Cisplatino (Galsky Criteria)")
    g1, g2 = st.columns(2)
    with g1:
        ecog_g = st.radio("ECOG Performance Status:", [0, 1, 2, 3])
        egfr = st.number_input("eGFR / Clearance Creatinina (ml/min)", value=65)
    with g2:
        neuropatia = st.checkbox("Neuropatia Periferica ≥ Grado 2")
        ototossicita = st.checkbox("Ipoacusia / Ototossicità ≥ Grado 2")
        sfoc = st.checkbox("Scompenso Cardiaco NYHA ≥ Class III")

    unfit = (
        (ecog_g >= 2)
        or (egfr < 60)
        or neuropatia
        or ototossicita
        or sfoc
    )

    if unfit:
        st.error("🚫 **PAZIENTE UNFIT AL CISPLATINO**")
        st.write(
            "**Strategia Alternativa:** Schemi a base di Carboplatino, Immunoterapia (Pembrolizumab) o Atezolizumab."
        )
    else:
        st.success("✅ **PAZIENTE FIT AL CISPLATINO**")
        st.write(
            "**Strategia Standard:** Chemioterapia Neoadiuvante con Gemcitabina + Cisplatino (GC) o ddMVAC."
        )

# ==============================================================================
# MODULO 4: TESTICOLO & PENE
# ==============================================================================
elif organo_selezionato == "🥚 TESTICOLO & PENE":
    st.title("🥚 Tumori del Testicolo & del Pene")
    st.info("Classificazione Prognostica IGCCCG e Marcatori Sierici (S-Category).")

    afp = st.number_input("Alfa-Fetoproteina (AFP) ng/ml", value=5.0)
    hcg = st.number_input("Beta-hCG mIU/ml", value=2.0)
    ldh = st.number_input("LDH (x ULN)", value=1.0)

    st.caption("Stratificazione del rischio secondo criteri IGCCCG per neoplasie germinali.")
