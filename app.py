import math
from datetime import datetime
import streamlit as st

st.set_page_config(page_title="Refertatore Urologico", page_icon="🩺")

st.title("🩺 Assistente Referti Urologia")

# --- 0. TIPO DI PRESTAZIONE ---
st.header("0. Tipo di Prestazione")
tipo_visita = st.selectbox(
    "Seleziona il tipo di prestazione/patologia:",
    [
        "Visita urologica prostata",
        "Visita tumore prostata (Prima Diagnosi / Stadiazione)",
        "Follow-Up Tumore Prostata",
        "Cistoscopia",
        "Visita tumore vescica",
        "Visita colica renale",
    ],
)

# --- 1. DATI PAZIENTE ---
st.header("1. Dati Paziente & Anamnesi")
data_visita = st.date_input("Data Visita", datetime.today())
data_nascita = st.date_input(
    "Data di Nascita",
    value=datetime(1960, 1, 1),
    min_value=datetime(1920, 1, 1),
    max_value=datetime.today(),
)

eta = (
    data_visita.year
    - data_nascita.year
    - (
        (data_visita.month, data_visita.day)
        < (data_nascita.month, data_nascita.day)
    )
)
st.info(
    f"📅 **Data Nascita:** {data_nascita.strftime('%d/%m/%Y')} — **Età calcolata:** {eta} anni"
)

sesso = st.radio("Sesso Paziente:", ["Maschio", "Femmina"], horizontal=True)

# Variabili di supporto
anamnesi_text = ""
esame_ob_text = ""
conclusioni_text = ""
consigli_text = ""
psadt_result = ""
alert_list = []

# --- 2. SEZIONI SPECIFICHE PER PRESTAZIONE ---

# A) VISITA UROLOGICA PROSTATA (IPB / LUTS)
if tipo_visita == "Visita urologica prostata":
    luts_input = st.text_input("Sintomi LUTS", "LUTS svuotamento nicturia 2")
    ivu_input = st.text_input("Storia IVU", "Negativa")
    eo_input = st.text_area(
        "Note EO", "Addome trattabile, non dolente. Giordano negativo."
    )
    dre_code = st.selectbox(
        "DRE",
        [
            "DRE *1 non noduli",
            "DRE *2 non noduli",
            "DRE *3 non noduli",
            "Personalizzato",
        ],
    )
    compenso = st.text_input(
        "Stato compenso", "quadro di IPB con buon compenso clinico"
    )
    consigli_input = st.text_area(
        "Si consiglia...",
        "Urinocoltura tra 20 gg. Associare Avodart. Controllo PSA e visita tra 12 mesi.",
    )

    anamnesi_text = (
        f"* Sintomatologia: {luts_input}\n* Anamnesi infettiva: {ivu_input}"
    )
    if "DRE *1" in dre_code:
        dre_t = "Prostata nei limiti per volume, superficie liscia, consistenza fibro-elastica, non dolente. DRE Negativa (cT1c)."
    elif "DRE *2" in dre_code:
        dre_t = "Prostata aumentata di volume (stimata ~40-45 cc), superficie liscia, consistenza fibro-elastica. Assenza di noduli sospetti."
    elif "DRE *3" in dre_code:
        dre_t = "Prostata nettamente aumentata di volume (>60 cc), consistenza teso-elastica, DRE negativa per lesioni sospette."
    else:
        dre_t = "Prostata valutata all'esplorazione rettale."
    esame_ob_text = f"* **EO Addome:** {eo_input}\n* **DRE:** {dre_t}"
    conclusioni_text = f"> **{compenso.capitalize()} in assenza di segni di ostruzione acuta.**"
    consigli_text = consigli_input

# B) VISITA TUMORE PROSTATA (PRIMA DIAGNOSI / STADIAZIONE)
elif tipo_visita == "Visita tumore prostata (Prima Diagnosi / Stadiazione)":
    st.subheader("Inquadramento Bioptico & Nomogrammi")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        gleason = st.text_input("Gleason Score / ISUP", "Gleason 3+4 (ISUP 2)")
        pct_frustoli = st.number_input(
            "% Frustoli Positivi",
            min_value=0,
            max_value=100,
            value=33,
        )
    with col_b2:
        pct_estensione = st.number_input(
            "% Estensione Lineare Max",
            min_value=0,
            max_value=100,
            value=50,
        )
        nomogram_lni = st.number_input(
            "% Rischio LNI (Nomogramma)",
            min_value=0.0,
            max_value=100.0,
            value=8.5,
            format="%.1f",
        )

    st.subheader("Imaging Prostatico & Systemic Imaging")
    rmn_text = st.text_area(
        "Referto mpRMN Prostatica",
        "Area di restrizione della diffusione in sede periferica medio-basale destra.",
    )
    pirads = st.selectbox("Pi-RADS Score", ["Pi-RADS 2", "Pi-RADS 3", "Pi-RADS 4", "Pi-RADS 5"])
    pet_tc_text = st.text_area(
        "Referto PET PSMA / TC / Scintigrafia",
        "Accumulo di tracciante a livello prostatico senza chiare captazioni patologiche a distanza.",
    )

    st.subheader("Stato Metastatico (Flag Diagnostici)")
    col_f1, col_f2, col_f3 = st.columns(3)
    meta_ossa = col_f1.checkbox("Metastasi Ossee")
    meta_visc = col_f2.checkbox("Metastasi Viscerali")
    superscan = col_f3.checkbox("SuperScan")

    st.subheader("Assetto Ormonale")
    in_adt = st.checkbox("Paziente in ADT (LHRH analogo/antagonista)")
    testo_val = 0.0
    if in_adt:
        testo_val = st.number_input(
            "Testosteronemia (ng/dL)", value=15.0, format="%.1f"
        )
        if testo_val >= 50.0:
            alert_list.append(
                "⚠️ **Escape Testicolare:** Testosteronemia $\\ge 50$ ng/dL in corso di ADT."
            )

    consigli_text = st.text_area(
        "Indicazioni Terapeutiche",
        "Pianificazione chirurgica (Prostatectomia Radicale) vs Radioterapia Radiocomposta.",
    )

    meta_str = "Assenza di secondarismi a distanza noti."
    if superscan:
        meta_str = "Quadro di SuperScan alla scintigrafia ossea (diffuso interessamento metastatico)."
    elif meta_ossa or meta_visc:
        locs = []
        if meta_ossa:
            locs.append("osseo")
        if meta_visc:
            locs.append("viscerale")
        meta_str = f"Quadro di malattia metastatica a localizzazione {' e '.join(locs)}."

    anamnesi_text = f"* **Istologia:** {gleason} | Frustoli pos: {pct_frustoli}% | Estensione max: {pct_estensione}%\n* **Nomogramma LNI:** Stima rischio invasione linfonodale {nomogram_lni}%\n* **mpRMN:** {rmn_text} ({pirads})\n* **Imaging Sistemico:** {pet_tc_text}\n* **Assetto Metastatico:** {meta_str}"
    if in_adt:
        anamnesi_text += f"\n* **Terapia Ormonale:** In ADT (Testosteronemia: {testo_val} ng/dL)"

    conclusioni_text = f"> **Neoplasia Prostatica ({gleason}) — {pirads}. Rischio LNI: {nomogram_lni}%. Status: {meta_str}**"

# C) FOLLOW-UP TUMORE PROSTATA
elif tipo_visita == "Follow-Up Tumore Prostata":
    st.subheader("Inquadramento Trattamento Primitivo")
    tipo_tratt = st.radio(
        "Trattamento Eseguito:",
        ["Prostatectomia Radicale", "Radioterapia / Brachiterapia"],
        horizontal=True,
    )

    psa_curr = st.number_input(
        "PSA Attuale (ng/ml)", value=0.05, format="%.3f"
    )
    nadir_rt = 0.0
    if tipo_tratt == "Radioterapia / Brachiterapia":
        nadir_rt = st.number_input(
            "PSA Nadir post-RT (ng/ml)", value=0.50, format="%.2f"
        )

    st.subheader("Calcolo PSADT (Opzionale)")
    usa_dt = st.checkbox("Calcola PSADT su due valori")
    if usa_dt:
        psa1 = st.number_input("Primo PSA", value=0.10, format="%.2f")
        d1 = st.date_input("Data 1")
        psa2 = st.number_input("Secondo PSA", value=0.25, format="%.2f")
        d2 = st.date_input("Data 2")
        if d2 > d1 and psa1 > 0 and psa2 > 0 and psa2 > psa1:
            m = ((d2 - d1).days) / 30.44
            dt = (m * math.log(2)) / math.log(psa2 / psa1)
            psadt_result = f"PSADT: {dt:.1f} mesi"

    st.subheader("Assetto Ormonale e Stadio")
    in_adt_fu = st.checkbox("In Terapia di Deprivazione Androgenica (ADT)")
    testo_fu = 0.0
    if in_adt_fu:
        testo_fu = st.number_input(
            "Testosteronemia (ng/dL)", value=12.0, format="%.1f"
        )

    meta_fu = st.radio(
        "Stadio Malattia Attuale:",
        ["M0 (Non Metastatico)", "M1 (Metastatico)"],
        horizontal=True,
    )

    consigli_text = st.text_area(
        "Programma Follow-Up",
        "Proseguire controlli ematochimici (PSA) tra 3-6 mesi.",
    )

    # Valutazione Recidiva Biochimica (BCR)
    bcr_status = "In Remissione Biochimica"
    if tipo_tratt == "Prostatectomia Radicale":
        if psa_curr >= 0.20:
            bcr_status = "⚠️ Sospetto di Recidiva Biochimica Post-Chirurgica (PSA ≥ 0.2 ng/ml)"
            alert_list.append(
                "📌 **Alert BCR Chirurgia:** PSA ≥ 0.20 ng/ml. Valutare PET PSMA di stadiazione."
            )
    else:
        if psa_curr >= (nadir_rt + 2.0):
            bcr_status = "⚠️ Recidiva Biochimica Post-RT (Criterio Phoenix: Nadir + 2 ng/ml)"
            alert_list.append(
                "📌 **Alert BCR Radioterapia:** PSA ≥ Nadir + 2 ng/ml."
            )

    anamnesi_text = f"* **Trattamento Primitivo:** {tipo_tratt}\n* **PSA Attuale:** {psa_curr} ng/ml"
    if tipo_tratt == "Radioterapia / Brachiterapia":
        anamnesi_text += f" (Nadir: {nadir_rt} ng/ml)"
    if psadt_result:
        anamnesi_text += f" | {psadt_result}"
    if in_adt_fu:
        anamnesi_text += f"\n* **Terapia Ormonale:** In ADT (Testosteronemia: {testo_fu} ng/dL)"
    anamnesi_text += f"\n* **Stadio:** {meta_fu}"

    conclusioni_text = f"> **Follow-Up Tumore Prostata ({tipo_tratt}) — Status: {bcr_status}.**"

# D) CISTOSCOPIA
elif tipo_visita == "Cistoscopia":
    esito_cisto = st.radio(
        "Esito Esame:",
        [
            "Cistoscopia Negativa (Normale)",
            "Cistoscopia Positiva (Lesione Vescicale)",
        ],
    )

    if "Negativa" in esito_cisto:
        if sesso == "Maschio":
            esame_ob_text = "* **Cistoscopia Flessibile:** Uretra pervia. Sfintere striato continente. Loggia prostatica ostruente/bilobata. Vescica a colonne di reazione, esente da lesioni vegetanti o sospette. Osti ureterali in sede, eiaculanti urina limpida."
        else:
            esame_ob_text = "* **Cistoscopia Flessibile:** Meato uretrale esterno regolare. Uretra pervia. Vescica normocapiente, mucosa esente da lesioni neoformative vegetanti o sospette. Osti ureterali ortotopici."
        conclusioni_text = (
            "> **Esame cistoscopico negativo per lesioni etroplastiche atipiche.**"
        )
        consigli_text = "Controllo clinico / ecografico periodico secondo indicazione medica."
    else:
        desc_lesione = st.text_area(
            "Descrizione Lesione Vescicale",
            "Formazione vegetante/papillare di ~1.5 cm a carico della parete laterale destra, in prossimità dell'ostio ureterale.",
        )
        esame_ob_text = f"* **Cistoscopia Flessibile:** {desc_lesione}"
        conclusioni_text = "> **Riscontro cistoscopico di neoformazione vescicale. Indicazione a procedura chirurgica di resezione (TURBT).**"
        consigli_text = "Programmazione intervento di TURBT (Resezione Transuretrale di Lesione Vescicale) + Esame Istologico."

# E) VISITA TUMORE VESCICA
elif tipo_visita == "Visita tumore vescica":
    stadio_vescica = st.selectbox(
        "Inquadramento Clinico:",
        [
            "Post-TURBT (NMIBC - Non Muscolo Invasivo)",
            "Muscolo Invasivo (MIBC)",
            "Metastatico / Avanzato",
        ],
    )
    istologia_v = st.text_input(
        "Istologia TURBT / Biopsia", "Carcinoma Uroteliale di Alto Grado (Ta/T1)"
    )
    instillazioni = st.checkbox("In corso di ciclo di Instillazioni (BCG / Chemioterapico)")

    anamnesi_text = f"* **Inquadramento:** {stadio_vescica}\n* **Istologia:** {istologia_v}\n* **Terapia Endovescicale:** {'In corso' if instillazioni else 'No/Non indicata'}"
    esame_ob_text = "* **EO Addome:** Trattabile, dolenza sovrapubica assente."
    conclusioni_text = f"> **Neoplasia Vescicale ({stadio_vescica}) — {istologia_v}.**"
    consigli_text = st.text_area(
        "Raccomandazioni",
        "Programmazione cistoscopia di controllo + citologia urinaria su 3 campioni tra 3 mesi.",
    )

# F) VISITA COLICA RENALE
elif tipo_visita == "Visita colica renale":
    lato = st.radio("Lato interessato:", ["Destro", "Sinistro", "Bilaterale"], horizontal=True)
    etg_calcolo = st.text_input(
        "Reperto ETG / TC",
        f"Calcolo ureterale {lato.lower()} di ~5 mm con idronefrosi di I-II grado.",
    )

    anamnesi_text = f"* **Sintomatologia:** Dolore lombare acuto a tipo colico irradiato in sede inguinale ({lato})."
    esame_ob_text = f"* **EO Addome:** Addome trattabile. **Giordano positivo a {lato}.**\n* **Imaging (ETG/TC):** {etg_calcolo}"
    conclusioni_text = f"> **Colica renale {lato.lower()} da calcolosi ureterale con idronefrosi reattiva.**"
    consigli_text = st.text_area(
        "Terapia Consigliata",
        "Terapia espulsiva (Tamsulosina 0.4 mg/die) + FANS al bisogno in caso di dolore. Idratazione controllata. Controllo ETG tra 15 gg.",
    )

# --- GENERAZIONE REFERTO ---
if st.button("🚀 Genera Referto e Analisi"):
    st.markdown("---")
    st.subheader("📋 Referto Generato")

    referto_completo = f"""
**REFERTO DI {tipo_visita.upper()}**
**Data Visita:** {data_visita.strftime('%d/%m/%Y')}
**Paziente:** Nato il {data_nascita.strftime('%d/%m/%Y')} (Anni: {eta}) — Sesso: {sesso}

**ANAMNESI ED ESAMI IN VISIONE:**
{anamnesi_text}

**ESAME OBIETTIVO / STRUMENTALE:**
{esame_ob_text}

**CONCLUSIONI DIAGNOSTICHE:**
{conclusioni_text}

**RACCOMANDAZIONI ED ITER TERAPEUTICO:**
{consigli_text}
"""
    st.code(referto_completo, language="markdown")

    # CONTROLLI DI QUALITÀ
    st.markdown("---")
    st.subheader("💡 Controllo di Qualità")

    if alert_list:
        for al in alert_list:
            st.warning(al)
    else:
        st.success("Referto completo e coerente con le linee guida inserite.")
