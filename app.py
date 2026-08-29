import math
from datetime import datetime
import streamlit as st

st.set_page_config(page_title="Refertatore Urologico", page_icon="🩺", layout="wide")

st.title("🩺 Assistente Referti Urologia")

# --- 0. TIPO DI PRESTAZIONE ---
st.header("0. Tipo di Prestazione")
tipo_visita = st.selectbox(
    "Seleziona il tipo di prestazione/patologia:",
    [
        "Visita tumore prostata",
        "Visita urologica prostata",
        "Cistoscopia",
        "Visita tumore vescica",
        "Visita colica renale",
    ],
)

# --- 1. DATI ANAGRAFICI ---
st.header("1. Dati Anagrafici Paziente")
col_a1, col_a2 = st.columns(2)
with col_a1:
    nome_paziente = st.text_input("Cognome e Nome Paziente", "Rossi Mario")
    data_visita = st.date_input("Data Visita / Discussione DMT", datetime.today())
with col_a2:
    data_nascita = st.date_input(
        "Data di Nascita",
        value=datetime(1960, 1, 1),
        min_value=datetime(1920, 1, 1),
        max_value=datetime.today(),
    )
    eta = (
        data_visita.year
        - data_nascita.year
        - ((data_visita.month, data_visita.day) < (data_nascita.month, data_nascita.day))
    )
    st.info(f"📅 **Età calcolata:** {eta} anni")

# --- SEZIONE SPECIFICA: TUMORE PROSTATA ---
if tipo_visita == "Visita tumore prostata":
    st.markdown("---")
    st.header("2. Parametri Clinico-Stadiativi Basali (Oncologia Prostatica)")

    col1, col2, col3 = st.columns(3)
    with col1:
        psa = st.number_input("PSA Sierico Basale (ng/ml)", value=6.50, step=0.10, format="%.2f")
        prostate_vol = st.number_input("Volume Prostatico cc (per PSAD)", value=40, step=5)
        psad = psa / prostate_vol if prostate_vol > 0 else 0.0
        st.caption(f"**PSAD Calcolata:** {psad:.2f} ng/ml/cc")

    with col2:
        isup_group = st.selectbox(
            "ISUP Group (Gleason Score):",
            [
                "ISUP 1 (Gleason 3+3=6)",
                "ISUP 2 (Gleason 3+4=7 - Prevalenza Pattern 3)",
                "ISUP 3 (Gleason 4+3=7 - Prevalenza Pattern 4)",
                "ISUP 4 (Gleason 4+4=8 / 3+5=8)",
                "ISUP 5 (Gleason 9-10)",
            ],
        )
        ecog_ps = st.selectbox("Performance Status ECOG:", ["ECOG 0", "ECOG 1", "ECOG 2", "ECOG 3"])

    with col3:
        c_stage = st.selectbox(
            "Stadio Clinico T (DRE / mpRMN):",
            ["cT1c", "cT2a", "cT2b", "cT2c", "cT3a", "cT3b", "cT4"],
        )
        carote_pos = st.number_input("Carote Positive", value=2, min_value=1)
        carote_tot = st.number_input("Carote Totali Prelevate", value=12, min_value=1)
        perc_carote = (carote_pos / carote_tot) * 100 if carote_tot > 0 else 0
        st.caption(f"**Carico bioptico:** {carote_pos}/{carote_tot} ({perc_carote:.1f}%)")

    st.subheader("Summary Esami di Staging Clinico-Strumentale")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        mp_rmn = st.text_input("Risonanza Magnetica Prostatica (mpRMN)", "PIRADS 4 - Sede PZ Dsn - ECE: No - SVI: No")
    with col_s2:
        pet_psma = st.text_input("PET/TC PSMA / Scintigrafia / TC", "Negativa per localizzazioni ripetitive a distanza")

# --- ALTRE TIPOLOGIE DI VISITA (Interfaccia Standard) ---
else:
    st.markdown("---")
    st.header("2. Dati CliniciGenerali")
    luts_input = st.text_input("Sintomatologia / Note Anamnestiche", "LUTS moderati")
    eo_input = st.text_area("Esame Obiettivo", "Addome trattabile, non dolente.")
    consigli_input = st.text_area("Raccomandazioni", "Controllo periodico tra 12 mesi.")


# --- GENERAZIONE REFERTO ---
if st.button("🚀 Genera Referto e Analisi"):
    st.markdown("---")
    st.subheader("📋 Referto Generato")

    if tipo_visita == "Visita tumore prostata":
        # Determinazione Classe di Rischio e Parere DMT
         parere_dmt = ""
         classe_rischio = ""

        if "ISUP 1" in isup_group and psa < 10 and c_stage in ["cT1c", "cT2a"]:
            classe_rischio = "BASSO RISCHIO"
            parere_dmt = """Caso clinico collegialmente analizzato e discusso in sede di Multidisciplinare (DMT). Alla luce del quadro istopatologico (ISUP Group 1 / Gleason Score 3+3=6), dei valori sierici del PSA sierico (< 10 ng/ml) e della stadiazione clinico-strumentale (cT1c-T2a), la patologia si stratifica secondo le Linee Guida internazionali di riferimento (EAU/NCCN/AIOM) nella classe a Basso Rischio di progressione.

In conformità con le raccomandazioni scientifiche vigenti, si consiglia ed indica prioritariamente l'inserimento in un programma di Sorveglianza Attiva secondo protocollo codificato (monitoraggio seriale del PSA, mpRMN e re-biopsia temporizzata). Contestualmente, nell'ambito di una corretta informazione ed alleanza terapeutica, vengono considerate ed illustrate come opzioni alternative a finalità radicale/curativa il trattamento chirurgico (Prostatectomia Radicale) e la Radioterapia (EBRT/SBRT). La scelta finale sull'iter da intraprendere sarà definita previa valutazione multidisciplinare delle comorbilità e ponderata decisione condivisa con il paziente."""

        elif "ISUP 2" in isup_group and perc_carote < 50 and psa <= 20 and c_stage in ["cT1c", "cT2a", "cT2b"]:
            classe_rischio = "INTERMEDIO FAVOREVOLE"
            parere_dmt = """Caso clinico analizzato e discusso collegialmente in sede di Multidisciplinare (DMT). L'integrazione dei parametri clinico-laboratoristici con i reperti anatomo-patologici (ISUP Group 2 / Gleason Score 3+4=7 con prevalenza di Pattern 3, singolo fattore di rischio intermedio e carico bioptico < 50%) definisce una classe di Rischio Intermedio Favorevole ai sensi delle Linee Guida di settore (EAU/NCCN).

In accordo con le raccomandazioni vigenti, si pone indicazione a trattamento locale a fine curativo mediante Prostatectomia Radicale (con eventuale linfoadenectomia di stadiazione sulla base delle carte di rischio) oppure Radioterapia radicale. Qualora sussistano specifici criteri di selezione (bassa densità di PSA, comorbilità rilevanti o motivata preferenza del paziente) e previa adeguata informazione, può essere presa in considerazione l'opzione della Sorveglianza Attiva con monitoraggio stringente. La decisione finale sarà condivisa con il paziente in base al bilancio tra tollerabilità ed aspettativa di vita."""

        elif "ISUP 3" in isup_group or ("ISUP 2" in isup_group and perc_carote >= 50):
            classe_rischio = "INTERMEDIO SFAVOREVOLE"
            parere_dmt = """Caso clinico riesaminato in sede di DMT Uro-Oncologico. Il quadro anatomopatologico e clinico (ISUP Group 2 con carico bioptico ≥ 50% ovvero ISUP Group 3 / Gleason Score 4+3=7 con prevalenza di Pattern 4 o molteplici fattori intermedi) configura una classe di Rischio Intermedio Sfavorevole.

In ottemperanza alle Linee Guida internazionali, per un'accurata stratificazione e stadiazione di malattia si ritiene indicata/raccomandata l'esecuzione di completamento diagnostico mediante PET/TC con PSMA (ovvero TC addome-pelvi e scintigrafia ossea). All'esito dello staging, si conferma la formale indicazione a trattamento locale ad intenzione curativa: le opzioni validate comprendono l'intervento chirurgico di Prostatectomia Radicale (con linfoadenectomia pelvica) ovvero la Radioterapia associata a Terapia di Deprivazione Androgenica (ADT) a breve/medio termine (4-6 mesi). La scelta terapeutica definitiva sarà ponderata con il paziente previa valutazione dello stato generale e del profilo di tollerabilità."""

        else:
            classe_rischio = "ALTO RISCHIO / LOCALMENTE AVANZATO"
            parere_dmt = """Caso discusso in sede di DMT Uro-Oncologico. La combinazione dei fattori prognostici sfavorevoli, inclusa la presenza di elevata gradazione bioptica (ISUP Group 4 o 5 / Gleason Score ≥ 8), PSA > 20 ng/ml o cT2c/cT3, colloca il quadro patologico nella categoria ad Alto Rischio secondo i criteri della letteratura scientifica accreditata.

Ai fini di un corretto inquadramento stadiativo primario e per l'esclusione di localizzazioni secondarie occulte, si pone indicazione prioritaria all'esecuzione di PET/TC con PSMA, in accordo con le raccomandazioni delle Linee Guida vigenti. All'esito dell'imaging, si prospetta una strategia terapeutica multimodale: le opzioni standard comprendono la Radioterapia ad alto dosaggio in combinazione con la Deprivazione Androgenica (ADT) a lungo termine (18-36 mesi) ed eventuale associazione di agenti ormonali di nuova generazione (NHA), oppure la Prostatectomia Radicale con Linfoadenectomia pelvica estesa nell'ambito di un programma integrato. La pianificazione finale verrà concordata nell'ambito di una decisione clinica condivisa con il paziente."""

        referto_finale = f"""# VERBALE MULTIDISCIPLINARE (DMT) - CARCINOMA DELLA PROSTATA

**Paziente:** {nome_paziente}
**Data di Nascita:** {data_nascita.strftime('%d/%m/%Y')} ({eta} anni)
**Data Discussione:** {data_visita.strftime('%d/%m/%Y')}

---

### 1. DATI ANAGRAFICI E PARAMETRI CLINICO-STADIATIVI BASALI
* **PSA Sierico Basale:** {psa:.2f} ng/ml (PSAD: {psad:.2f} ng/ml/cc)
* **ISUP Group (Gleason):** {isup_group}
* **Stadio Clinico T (DRE/RM):** {c_stage}
* **Biopsia Prostatica:** {carote_pos}/{carote_tot} carote positive ({perc_carote:.1f}% coinvolgimento)
* **Performance Status:** {ecog_ps}
* **Classe di Rischio Calcolata:** {classe_rischio}

---

### 2. SUMMARY ESAMI DI STAGING CLINICO-STRUMENTALE
* **mpRMN Prostatica:** {mp_rmn}
* **PET/TC PSMA / Staging:** {pet_psma}

---

### 3. PARERE COLLEGIALE DMT
{parere_dmt}
"""
        st.code(referto_finale, language="markdown")

    else:
        # Generazione Standard per altre prestazioni
        referto_standard = f"""**REFERTO DI {tipo_visita.upper()}**
**Paziente:** {nome_paziente}
**Data di Nascita:** {data_nascita.strftime('%d/%m/%Y')} (Anni: {eta}) — **Data:** {data_visita.strftime('%d/%m/%Y')}

**ANAMNESI ED ESAMI IN VISIONE:**
* {luts_input}

**ESAME OBIETTIVO:**
* {eo_input}

**RACCOMANDAZIONI:**
{consigli_input}
"""
        st.code(referto_standard, language="markdown")
