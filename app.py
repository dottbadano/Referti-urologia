import math
from datetime import datetime
import streamlit as st

st.set_page_config(page_title="Refertatore Urologico", page_icon="🩺")

st.title("🩺 Assistente Referti Urologia")

# --- 1. DATI PAZIENTE ---
st.header("1. Dati Paziente & Anamnesi")
nome = st.text_input("Nome Paziente", "Sig. ")
eta = st.number_input("Età", min_value=18, max_value=100, value=65)
data_visita = st.date_input("Data Visita", datetime.today())

luts_input = st.text_input("Sintomi LUTS", "LUTS svuotamento nicturia 2")
ivu_input = st.text_input("Storia IVU", "")

# --- 2. PSA E PSADT ---
st.header("2. Valori PSA e PSADT")
usa_psa = st.checkbox("Calcola PSADT")
psadt_result = ""
if usa_psa:
    psa1 = st.number_input("Primo PSA (ng/ml)", value=3.70, format="%.2f")
    data1 = st.date_input("Data primo PSA")
    psa2 = st.number_input("Secondo PSA (ng/ml)", value=4.31, format="%.2f")
    data2 = st.date_input("Data secondo PSA")

    if data2 > data1 and psa1 > 0 and psa2 > 0:
        giorni = (data2 - data1).days
        mesi = giorni / 30.44
        if psa2 > psa1:
            dt = (mesi * math.log(2)) / math.log(psa2 / psa1)
            psadt_result = f"PSA in incremento (da {psa1} a {psa2} in {int(mesi)} mesi). **PSADT: {dt:.1f} mesi.**"
        else:
            psadt_result = f"PSA stabile/in riduzione (da {psa1} a {psa2})."

# --- 3. ESAME OBIETTIVO ---
st.header("3. Esame Obiettivo")
eo_input = st.text_area(
    "Note EO", "Addome trattabile, non dolente. Giordano negativo."
)
dre_code = st.selectbox(
    "DRE",
    ["DRE *1 non noduli", "DRE *2 non noduli", "DRE *3 non noduli", "Personalizzato"],
)

# --- 4. CONCLUSIONI ---
st.header("4. Conclusioni e Prescrizioni")
compenso = st.text_input(
    "Stato compenso", "quadro di IPB con buon compenso clinico"
)
consigli_input = st.text_area(
    "Si consiglia...",
    "Urinocoltura tra 20 gg. Associare Avodart. Controllo PSA e visita tra 12 mesi.",
)

# --- GENERAZIONE ---
if st.button("🚀 Genera Referto e Analisi"):
    st.markdown("---")
    st.subheader("📋 Referto Generato")

    if "DRE *1" in dre_code:
        dre_text = "Prostata nei limiti per volume, superficie liscia, consistenza fibro-elastica, non dolente. DRE Negativa (cT1c)."
    elif "DRE *2" in dre_code:
        dre_text = "Prostata aumentata di volume (stimata ~40-45 cc), superficie liscia, consistenza fibro-elastica, solco interlobare conservato. Assenza di noduli sospetti (DRE Negativa / cT1c)."
    elif "DRE *3" in dre_code:
        dre_text = "Prostata nettamente aumentata di volume (>60 cc), a prevalente sviluppo adenomatoso, consistenza teso-elastica, DRE negativa per lesioni sospette (cT1c)."
    else:
        dre_text = "Prostata valutata all'esplorazione rettale."

    referto_finale = f"""
**REFERTO DI VISITA SPECIALISTICA UROLOGICA**
**Paziente:** {nome} (anni {eta}) — **Data:** {data_visita.strftime('%d/%m/%Y')}

**ANAMNESI ED ESAMI IN VISIONE:**
* Sintomatologia: {luts_input}
* Anamnesi infettiva: {ivu_input if ivu_input else 'Negativa per IVU recenti'}
* Inquadramento PSA: {psadt_result if psadt_result else 'PSA nei limiti / non specificato'}

**ESAME OBIETTIVO:**
* **Obiettività addominale/urologica:** {eo_input}
* **Esplorazione Rettale (DRE):** {dre_text}

**CONCLUSIONI DIAGNOSTICHE:**
> **{compenso.capitalize()} in assenza di segni di ostruzione acuta.**

**RACCOMANDAZIONI ED ITER TERAPEUTICO:**
{consigli_input}
"""
    st.code(referto_finale, language="markdown")

    # CONTROLLI
    st.markdown("---")
    st.subheader("💡 Controllo di Qualità")
    if "Avodart" in consigli_input or "Dutasteride" in consigli_input:
        st.warning(
            "⚠️ **Avvertenza PSA:** Ricordare che Avodart dimezzerà il PSA tra 6-12 mesi."
        )
    if "RPM" not in referto_finale and "Residuo" not in referto_finale:
        st.warning(
            "📌 **Omissione Strumentale:** Valutare l'inserimento della misurazione del Residuo Post-Minzionale (RPM)."
        )
    if "IVU" in ivu_input and "Urinocoltura" not in consigli_input:
        st.warning(
            "📌 **Controllo Infettivologico:** Inserire urinocoltura di controllo post-terapia."
        )
