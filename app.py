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
        "Tumore prostata biopsia",
        "Follow-up post-prostatectomia radicale",
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
        - ((data_visita.month, data_visita.day) < (data_visita.month, data_visita.day))
    )
    st.info(f"📅 **Età calcolata:** {eta} anni")

# --- SEZIONE SPECIFICA: TUMORE PROSTATA BIOPSIA ---
if tipo_visita == "Tumore prostata biopsia":
    st.markdown("---")
    st.header("2. Parametri Clinico-Stadiativi Basali e Bioptici")

    col1, col2, col3 = st.columns(3)
    with col1:
        psa = st.number_input("PSA Sierico Basale (ng/ml)", value=6.50, step=0.10, format="%.2f")
        prostate_vol = st.number_input("Volume Prostatico cc (per PSAD)", value=40, step=5)
        psad = psa / prostate_vol if prostate_vol > 0 else 0.0
        st.caption(f"**PSAD Calcolata:** {psad:.2f} ng/ml/cc")

    with col2:
        gleason_score = st.selectbox(
            "Gleason Score Bioptico Primo + Secondo:",
            [
                "3+3 (ISUP 1)",
                "3+4 (ISUP 2)",
                "4+3 (ISUP 3)",
                "4+4 (ISUP 4)",
                "3+5 (ISUP 4)",
                "4+5 (ISUP 5)",
                "5+4 (ISUP 5)",
                "5+5 (ISUP 5)",
            ],
        )
        has_tertiary = st.checkbox("Presenza di Pattern Terziario?")
        tertiary_pattern = None
        if has_tertiary:
            tertiary_pattern = st.selectbox("Pattern Terziario:", ["Pattern 4", "Pattern 5"])

        ecog_ps = st.selectbox("Performance Status ECOG:", ["ECOG 0", "ECOG 1", "ECOG 2", "ECOG 3"])

    with col3:
        dre_stage = st.selectbox(
            "Stadio Clinico all'Esplorazione Rettale (DRE):",
            ["cT1c", "cT2a", "cT2b", "cT2c", "cT3a", "cT3b"],
        )
        carote_pos = st.number_input("Carote Positive", value=2, min_value=1)
        carote_tot = st.number_input("Carote Totali Prelevate", value=12, min_value=1)
        perc_carote = (carote_pos / carote_tot) * 100 if carote_tot > 0 else 0
        st.caption(f"**Carico bioptico:** {carote_pos}/{carote_tot} ({perc_carote:.1f}%)")

    st.subheader("3. Inquadramento mpRMN Prostatica (Flag/Tendina)")
    col_rm1, col_rm2, col_rm3 = st.columns(3)
    with col_rm1:
        pirads = st.selectbox("PIRADS Lesione Indice:", ["PIRADS 3", "PIRADS 4", "PIRADS 5", "Non Eseguita / Negativa"])
    with col_rm2:
        ece_rmn = st.checkbox("ECE alla mpRMN (Estensione Extraprostatica - cT3a)")
    with col_rm3:
        svi_rmn = st.checkbox("SVI alla mpRMN (Invasione Vescicole Seminali - cT3b)")

    rmn_text_summary = f"{pirads}"
    if ece_rmn:
        rmn_text_summary += " - Presenza di ECE (cT3a)"
    if svi_rmn:
        rmn_text_summary += " - Presenza di SVI (cT3b)"
    if not ece_rmn and not svi_rmn and pirads != "Non Eseguita / Negativa":
        rmn_text_summary += " - Sede confinata alla ghiandola (cT2)"

# --- SEZIONE SPECIFICA: FOLLOW-UP POST-PROSTATECTOMIA RADICALE ---
elif tipo_visita == "Follow-up post-prostatectomia radicale":
    st.markdown("---")
    st.header("2. Dati Istologici Definitivi ed Chirurgici")

    col_fu1, col_fu2, col_fu3 = st.columns(3)
    with col_fu1:
        tecnica_intervento = st.selectbox(
            "Tecnica Chirurgica ed Approccio:",
            [
                "Prostatectomia Radicale Robotica (RARP)",
                "Prostatectomia Radicale Laparoscopica (LRP)",
                "Prostatectomia Radicale Open (ORP)",
            ],
        )
        nerve_sparing = st.selectbox(
            "Risparmio Nervoso (Nerve-Sparing):",
            [
                "Nerve-Sparing Bilaterale",
                "Nerve-Sparing Monolaterale",
                "Non Nerve-Sparing (Resezione ampia)",
            ],
        )
        pt_stage = st.selectbox("Stadio pT Definitivo:", ["pT2", "pT3a (ECE)", "pT3b (SVI)", "pT4"])

    with col_fu2:
        pn_stage = st.selectbox("Stadio pN Definitivo:", ["pN0 (Linfonodi negativi)", "pN1 (Linfonodi positivi)", "pNX (Linfoadenectomia non eseguita)"])
        linfonodi_pos = 0
        linfonodi_tot = 0
        if "pN1" in pn_stage:
            linfonodi_pos = st.number_input("N° Linfonodi Positivi", value=1, min_value=1)
            linfonodi_tot = st.number_input("N° Linfonodi Totali Asportati", value=12, min_value=1)
            
        isup_postop = st.selectbox(
            "Gleason / ISUP Definitivo (Pezzo Operatorio):",
            [
                "ISUP 1 (Gleason 3+3=6)",
                "ISUP 2 (Gleason 3+4=7)",
                "ISUP 3 (Gleason 4+3=7)",
                "ISUP 4 (Gleason 4+4 / 3+5 / 5+3=8)",
                "ISUP 5 (Gleason 9-10)",
            ],
        )

    with col_fu3:
        margini_r = st.selectbox("Margini di Resezione Chirurgica:", ["R0 (Margini chirurgici indenni)", "R1 (Margini chirurgici positivi/focali)"])
        ecog_ps_fu = st.selectbox("Performance Status ECOG:", ["ECOG 0", "ECOG 1", "ECOG 2", "ECOG 3"])
        terapie_pregresse = st.multiselect(
            "Trattamenti Post-Operatorii Già Eseguiti:",
            ["Nessun trattamento ad oggi", "Radioterapia Adiuvante (aRT)", "Radioterapia di Salvataggio (sRT)", "Terapia di Deprivazione Androgenica (ADT)"],
            default=["Nessun trattamento ad oggi"],
        )

    st.subheader("3. Valutazione Oncologica (PSA) e Funzionale")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        psa_postop = st.number_input("PSA Attuale / Nadir (ng/ml)", value=0.01, step=0.01, format="%.2f")
    with col_f2:
        continenza_status = st.selectbox(
            "Stato Continenza Urinaria:",
            [
                "Continente",
                "1 salva-slip / die",
                "2 salva-slip / die",
                "1 pad / die",
                "2 pad / die",
                "Incontinenza completa",
            ],
        )
    with col_f3:
        potenza_status = st.selectbox(
            "Stato Funzione Erettile:",
            [
                "Potenza sessuale conservata",
                "Potenza conservata con ausilio di PDE5-i (es. Tadalafil/Sildenafil)",
                "Potenza conservata con terapia intracavernosa (Prostaglandine / PGE1)",
                "Deficit erettile completo / Non responsivo",
            ],
        )

# --- ALTRE TIPOLOGIE DI VISITA (Interfaccia Standard) ---
else:
    st.markdown("---")
    st.header("2. Dati Clinici Generali")
    luts_input = st.text_input("Sintomatologia / Note Anamnestiche", "LUTS moderati")
    eo_input = st.text_area("Esame Obiettivo", "Addome trattabile, non dolente.")
    consigli_input = st.text_area("Raccomandazioni", "Controllo periodico tra 12 mesi.")


# --- GENERAZIONE REFERTO ---
if st.button("🚀 Genera Referto e Analisi Stadiativa"):
    st.markdown("---")
    st.subheader("📋 Referto Generato")

    if tipo_visita == "Tumore prostata biopsia":
        # MAPPA ISUP DAL GLEASON
        isup_val = 1
        if "3+3" in gleason_score:
            isup_val = 1
        elif "3+4" in gleason_score:
            isup_val = 2
        elif "4+3" in gleason_score:
            isup_val = 3
        elif "4+4" in gleason_score or "3+5" in gleason_score:
            isup_val = 4
        else:
            isup_val = 5

        c_stage_final = dre_stage
        if svi_rmn:
            c_stage_final = "cT3b"
        elif ece_rmn and dre_stage not in ["cT3b"]:
            c_stage_final = "cT3a"

        risk_override_reason = []

        if c_stage_final in ["cT3a", "cT3b", "cT4"] or psa > 20 or isup_val >= 4:
            classe_rischio = "ALTO RISCHIO / LOCALMENTE AVANZATO"
            if c_stage_final in ["cT3a", "cT3b"] and isup_val <= 2:
                risk_override_reason.append(f"Upgrade ad Alto Rischio per evidenza RMN/DRE di estensione extraprostatica ({c_stage_final}).")
        elif isup_val == 3 or (isup_val == 2 and (perc_carote >= 50 or psa > 10)):
            classe_rischio = "INTERMEDIO SFAVOREVOLE"
            if has_tertiary and tertiary_pattern == "Pattern 5":
                risk_override_reason.append("Caratteristiche di aggressività aumentata per Pattern 5 Terziario.")
        elif (isup_val == 2 and perc_carote < 50 and psa <= 10) or (isup_val == 1 and (c_stage_final in ["cT2b", "cT2c"] or psa > 10)):
            classe_rischio = "INTERMEDIO FAVOREVOLE"
        else:
            classe_rischio = "BASSO RISCHIO"

        logit_lni = -4.5 + (0.05 * psa) + (0.8 * (isup_val - 1)) + (0.9 if "cT3" in c_stage_final else 0.3 if "cT2" in c_stage_final else 0)
        risk_lni = (1 / (1 + math.exp(-logit_lni))) * 100
        risk_lni = max(1.0, min(risk_lni, 85.0))

        logit_csm = -3.8 + (0.03 * psa) + (0.6 * (isup_val - 1)) + (0.04 * (eta - 60))
        risk_csm_15yr = (1 / (1 + math.exp(-logit_csm))) * 100
        risk_csm_15yr = max(0.5, min(risk_csm_15yr, 70.0))

        indicazione_plnd = "INDICATA (Rischio LNI > 5%)" if risk_lni >= 5.0 else "NON NECESSARIA (Rischio LNI < 5%)"

        parere_dmt = ""
        if classe_rischio == "BASSO RISCHIO":
            parere_dmt = """Caso clinico discusso in sede Multidisciplinare (DMT). Alla luce del quadro istopatologico (ISUP 1), dei valori sierici del PSA (< 10 ng/ml) e dell'imaging RMN/DRE confinato (cT1c-cT2a), la patologia si stratifica nella classe a BASSO RISCHIO.

In conformità alle Linee Guida EAU/NCCN, si raccomanda prioritariamente l'inserimento in un programma di Sorveglianza Attiva (SA) secondo protocollo codificato. Come opzioni alternative a finalità radicale si prospettano la Prostatectomia Radicale o la Radioterapia."""

        elif classe_rischio == "INTERMEDIO FAVOREVOLE":
            if isup_val == 1:
                parere_dmt = """Caso clinico discusso in sede Multidisciplinare (DMT). La presenza di un quadro istopatologico ISUP 1 (Gleason Score 3+3=6) associato a stadio clinicamente confinato (cT2b/cT2c) o PSA lievemente incrementato configura una classe di RISCHIO INTERMEDIO FAVOREVOLE.

In accordo con le Linee Guida internazionali (EAU/NCCN), la **Sorveglianza Attiva (SA)** con monitoraggio stringente rimane l'opzione di gestione prioritaria e raccomandata, al fine di evitare il sovratrattamento. Nell'ambito della decisione condivisa con il paziente, vengono altresì illustrate le opzioni a finalità curativa (Prostatectomia Radicale o Radioterapia radicale)."""
            else:
                parere_dmt = """Caso clinico discusso in sede Multidisciplinare (DMT). I parametri clinico-bioptici (ISUP 2 con carico bioptico < 50%, PSA <= 10 ng/ml) configurano una classe di RISCHIO INTERMEDIO FAVOREVOLE.

In accordo con le Linee Guida, si pone indicazione a trattamento radicale primario mediante Prostatectomia Radicale o Radioterapia. In casi selezionati e previo adeguato counseling, può essere presa in considerazione l'opzione della Sorveglianza Attiva con monitoraggio stringente."""

        elif classe_rischio == "INTERMEDIO SFAVOREVOLE":
            parere_dmt = """Caso clinico discusso in sede Multidisciplinare (DMT). Il quadro anatomopatologico e clinico configura una classe di RISCHIO INTERMEDIO SFAVOREVOLE.

Si raccomanda completamento stadiativo con PET/TC PSMA. Si conferma l'indicazione a trattamento ad intenzione curativa mediante Prostatectomia Radicale (con eventuale Linfoadenectomia Pelvica se MSKCC > 5%) oppure Radioterapia radicale associata ad Androgeno-Deprivazione (ADT) a breve termine (4-6 mesi)."""

        else:
            parere_dmt = """Caso discusso in sede Multidisciplinare (DMT). La presenza di fattori di rischio elevati (Gleason Score elevato, PSA > 20 ng/ml e/o estensione extraprostatica ECE/SVI alla RMN) colloca il quadro nella categoria ad ALTO RISCHIO / LOCALMENTE AVANZATO.

Ai fini stadiativi si richiede prioritaria esecuzione di PET/TC PSMA. Si prospetta una strategia terapeutica integrata: Radioterapia ad alto dosaggio in combinazione con ADT a lungo termine (18-36 mesi) +/- agenti ormonali di nuova generazione (NHA), oppure Prostatectomia Radicale con Linfoadenectomia Pelvica estesa nell'ambito di un percorso multimodale."""

        if risk_override_reason:
            st.warning("⚠️ **AUTOMATIC OVERRIDE DI SICUREZZA:** " + " ".join(risk_override_reason))

        terziario_str = f" (Pattern Terziario: {tertiary_pattern})" if has_tertiary else ""

        referto_finale = f"""# VERBALE MULTIDISCIPLINARE (DMT) - CARCINOMA DELLA PROSTATA

**Paziente:** {nome_paziente}
**Data di Nascita:** {data_nascita.strftime('%d/%m/%Y')} ({eta} anni)
**Data Discussione:** {data_visita.strftime('%d/%m/%Y')}

---

### 1. PARAMETRI CLINICO-STADIATIVI E BIOPTICI
* **PSA Sierico Basale:** {psa:.2f} ng/ml (PSAD: {psad:.2f} ng/ml/cc)
* **Gleason Score Bioptico:** {gleason_score}{terziario_str} -> **ISUP Group {isup_val}**
* **Stadio Clinico DRE:** {dre_stage}
* **Stadio Clinico Integrato (DRE + mpRMN):** {c_stage_final}
* **Biopsia Prostatica:** {carote_pos}/{carote_tot} carote positive ({perc_carote:.1f}% coinvolgimento)
* **Performance Status:** {ecog_ps}
* **Classe di Rischio Calcolata:** {classe_rischio}

---

### 2. INQUADRAMENTO mpRMN PROSTATICA
* **Referto mpRMN:** {rmn_text_summary}

---

### 3. NOMOGRAMMI DI PREDIZIONE MSKCC (SLOAN KETTERING)
* **Rischio Coinvolgimento Linfonodale (LNI MSKCC):** {risk_lni:.1f}%
* **Indicazione a Linfoadenectomia Pelvica (ePLND):** {indicazione_plnd}
* **Stima Mortalità Cancro-Specifica a 15 anni (senza trattamento):** {risk_csm_15yr:.1f}%

---

### 4. PARERE COLLEGIALE E RACCOMANDAZIONI DMT
{parere_dmt}
"""
        st.code(referto_finale, language="markdown")

    elif tipo_visita == "Follow-up post-prostatectomia radicale":
        # ALGORITMO RECIDIVA BIOCHIMICA (BCR)
        is_bcr = psa_postop >= 0.20
        status_oncologico = "RECIDIVA BIOCHIMICA (BCR) CONFIRMATA" if is_bcr else "MALATTIA IN CONTROLLO BIOCHIMICO"

        if is_bcr:
            st.error("🚨 **ALERT CLINICO: RECIDIVA BIOCHIMICA RILEVATA (PSA ≥ 0.20 ng/ml)**")
            parere_dmt_fu = f"""Caso clinico analizzato in sede di Multidisciplinare (DMT) nel contesto del follow-up oncologico post-prostatectomia radicale. 
A fronte di un valore sierico di PSA pari a **{psa_postop:.2f} ng/ml** (superiore alla soglia di cut-off clinico di 0.20 ng/ml), si pone diagnosi formale di **Recidiva Biochimica (BCR)** ai sensi delle Linee Guida EAU/NCCN.

**INDICAZIONE CLINICA ED ITER STRUMENTALE:**
In accordo con i protocolli internazionali vigenti, si pone indicazione prioritaria ed indifferibile all'esecuzione di **PET/TC con PSMA** per la caratterizzazione stadiativa e la precisa localizzazione topografica della ripresa di malattia (recidiva locale in loggia prostatica vs nodale pelvica vs sistemica a distanza). All'esito del completamento biostadiativo, il caso verrà rivalutato per la pianificazione del trattamento di salvataggio (Radioterapia di Salvataggio precoce sRT +/- Terapia di Deprivazione Androgenica ADT)."""
        else:
            parere_dmt_fu = f"""Caso clinico valutato in sede di Follow-Up Oncologico Uro-Oncologico. Il controllo del PSA sierico (**{psa_postop:.2f} ng/ml**) documenta un azzeramento/nadir stabile ed una condizione di risposta completa di malattia in assenza di evidenze laboratoristiche di ripresa biochimica.

**RACCOMANDAZIONI:**
Si raccomanda prosecuzione del programma di monitoraggio clinico-laboratoristico mediante dosaggio del PSA sierico secondo cadenza temporale codificata e prosecuzione della presa in carico per l'ottimizzazione del recupero funzionale."""

        linfonodi_str = f"{pn_stage}"
        if "pN1" in pn_stage:
            linfonodi_str += f" ({linfonodi_pos}/{linfonodi_tot} linfonodi metastatici)"

        terapie_str = ", ".join(terapie_pregresse)

        referto_fu_finale = f"""# VERBALE MULTIDISCIPLINARE (DMT) - FOLLOW-UP POST-PROSTATECTOMIA RADICALE

**Paziente:** {nome_paziente}
**Data di Nascita:** {data_nascita.strftime('%d/%m/%Y')} ({eta} anni)
**Data Discussione:** {data_visita.strftime('%d/%m/%Y')}

---

### 1. QUADRO ANATOMO-PATOLOGICO E CHIRURGICO DEFINITIVO
* **Intervento Eseguito:** {tecnica_intervento} ({nerve_sparing})
* **Stadio Anatomo-Patologico Definitivo:** {pt_stage} {linfonodi_str} - {margini_r}
* **ISUP Group Definitivo:** {isup_postop}
* **Performance Status:** {ecog_ps_fu}
* **Trattamenti Pregressi Eseguiti:** {terapie_str}

---

### 2. BILANCIO CLINICO-LABORATORISTICO E FUNZIONALE
* **PSA Sierico Attuale:** **{psa_postop:.2f} ng/ml**
* **Stato Oncologico:** {status_oncologico}
* **Continenza Urinaria:** {continenza_status}
* **Funzione Erettile:** {potenza_status}

---

### 3. PARERE COLLEGIALE E RACCOMANDAZIONI DMT
{parere_dmt_fu}
"""
        st.code(referto_fu_finale, language="markdown")

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
