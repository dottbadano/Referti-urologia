from datetime import datetime
import json
import random
import string
from io import BytesIO
import pandas as pd
import requests
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

ELENCO_MESI = [
    "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
]

@st.cache_data(ttl=60)
def carica_db_pazienti_cached():
    """Carica il database dei pazienti dal Foglio Google tramite esportazione CSV pubblica."""
    try:
        csv_url = "https://docs.google.com/spreadsheets/d/1DYM84MnzgSXQYNc8d6X0kJW101nRb4zG-IFSx6xuNiQ/export?format=csv&gid=0"
        df = pd.read_csv(csv_url)

        registro = {}
        if not df.empty and "codice" in df.columns:
            for _, row in df.iterrows():
                codice = str(row["codice"]).strip()
                if codice and codice != "nan":
                    visite_raw = row.get("visite", "[]")
                    try:
                        visite_list = json.loads(visite_raw) if isinstance(visite_raw, str) else []
                    except Exception:
                        visite_list = []

                    registro[codice] = {
                        "nome": str(row.get("nome", "")),
                        "cognome": str(row.get("cognome", "")),
                        "data_nascita": str(row.get("data_nascita", "")),
                        "ultimo_aggiornamento": str(row.get("ultimo_aggiornamento", datetime.today().date())),
                        "organo": str(row.get("organo", "PROSTATA")),
                        "isup": int(row.get("isup", 1)) if pd.notna(row.get("isup")) else 1,
                        "rischio": str(row.get("rischio", "")),
                        "percorso_scelto": str(row.get("percorso_scelto", "")),
                        "ultimo_psa": float(row.get("ultimo_psa", 0.0)) if pd.notna(row.get("ultimo_psa")) else 0.0,
                        "data_ultimo_psa": str(row.get("data_ultimo_psa", "")),
                        "g8_score": int(row.get("g8_score", 0)) if pd.notna(row.get("g8_score")) else 0,
                        "visite": visite_list,
                    }
        return registro
    except Exception as e:
        st.error(f"Errore nella lettura del database su Google Sheets: {e}")
        return {}

def carica_db_pazienti():
    """Interfaccia di caricamento sincronizzata con la sessione di Streamlit[cite: 2]."""
    if "db_pazienti_cache" not in st.session_state:
        st.session_state["db_pazienti_cache"] = carica_db_pazienti_cached()
    return st.session_state["db_pazienti_cache"]

def salva_db_pazienti(registro):
    """Funzione di compatibilità per il salvataggio completo[cite: 2]."""
    st.cache_data.clear()
    st.session_state["db_pazienti_cache"] = registro
    return True

def genera_codice_univoco(nome, cognome):
    """Genera un codice univoco basato sulle iniziali e numeri casuali[cite: 2]."""
    n_init = nome[:2].upper() if len(nome) >= 2 else nome.upper()
    c_init = cognome[:2].upper() if len(cognome) >= 2 else cognome.upper()
    rand_num = "".join(random.choices(string.digits, k=4))
    return f"{c_init}{n_init}-{rand_num}"

def salva_paziente_su_drive(nome, cognome, data_nascita, codice_univoco):
    """Invia i dati del paziente al Google Sheet tramite la Web App di Apps Script[cite: 2]."""
    url_web_app = "https://script.google.com/macros/s/AKfycbxMA61mMW_m_9C9xc9v2dziiZIlUseu9KGGI_Qt1r59DzcfL3idMOni9sn3Ja3LTjQ/exec"

    payload = {
        "nome": nome,
        "cognome": cognome,
        "data_nascita": str(data_nascita),
        "codice_univoco": codice_univoco,
    }

    try:
        risposta = requests.post(url_web_app, json=payload, timeout=10)
        return risposta.status_code == 200
    except Exception:
        return False

def genera_o_aggiorna_registro(nome, cognome, data_nascita, codice_univoco):
    """Salva o aggiorna il singolo paziente tramite Apps Script[cite: 2]."""
    successo = salva_paziente_su_drive(nome, cognome, data_nascita, codice_univoco)
    if successo:
        st.cache_data.clear()
        if "db_pazienti_cache" in st.session_state:
            st.session_state["db_pazienti_cache"] = carica_db_pazienti_cached()
        return True
    else:
        st.error("Errore nel salvataggio tramite Web App di Google Sheets.")
        return False

def render_anamnesi_generale(prefix="gen"):
    """Renderizza l'inquadramento clinico generale con campi facoltativi[cite: 2]."""
    st.markdown("#### 📋 Anamnesi Generale Paziente")

    col1, col2 = st.columns(2)

    with col1:
        ipertensione = st.checkbox("Ipertensione Arteriosa", key=f"{prefix}_ipertensione")
        cardiopatia = st.checkbox("Cardiopatia / Ischemia", key=f"{prefix}_cardiopatia")
        diabete = st.selectbox(
            "Diabete Mellito",
            ["No", "Diabete Tipo 1", "Diabete Tipo 2"],
            key=f"{prefix}_diabete",
        )

        insuff_renale = st.checkbox("Insufficienza Renale Cronica", key=f"{prefix}_insuff_renale")
        creatinina = ""
        if insuff_renale:
            creatinina = st.text_input(
                "Valore Creatinina (mg/dL)",
                placeholder="Es. 1.4 mg/dL",
                key=f"{prefix}_creatinina",
            )

    with col2:
        fumo = st.selectbox(
            "Abitudine Tabagica",
            ["Non fumatore", "Ex fumatore", "Fumatore attivo"],
            key=f"{prefix}_fumo",
        )

        ha_allergie = st.checkbox("Allergie", key=f"{prefix}_ha_allergie")
        specifica_allergie = ""
        if ha_allergie:
            specifica_allergie = st.text_input(
                "Specificare a cosa è allergico",
                placeholder="Es. Penicillina, Lattice...",
                key=f"{prefix}_specifica_allergie",
            )

    st.markdown("---")

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        scala_performance = st.selectbox(
            "Scala di Performance / Stato Generale (ECOG Performance Status)",
            [
                "Non valutato / Non applicabile",
                "0 - Pienamente attivo, capace di svolgere tutte le normali attività",
                "1 - Limitato nelle attività fisiche pesanti, ma deambulante",
                "2 - Deambulante e capace di cura personale, incapace di lavoro",
                "3 - Capace di limitata cura personale, confinato a letto/sedia (>50% del giorno)",
                "4 - Completamente disabile, confinato a letto o sedia",
            ],
            key=f"{prefix}_ecog",
        )
    with col_v2:
        esegue_mmse = st.checkbox(
            "Eseguito Mini-Mental State Examination (MMSE) / Test Cognitivo",
            key=f"{prefix}_check_mmse",
        )
        valore_mmse = ""
        if esegue_mmse:
            valore_mmse = st.text_input(
                "Punteggio MMSE / Test (es. 28/30)",
                placeholder="Punteggio ottenuto...",
                key=f"{prefix}_valore_mmse",
            )

    st.markdown("---")

    st.markdown("##### ⚖️ Stato Nutrizionale e Parametri Antropometrici")
    col_nut1, col_nut2, col_nut3 = st.columns(3)
    with col_nut1:
        peso = st.number_input(
            "Peso (kg)",
            min_value=0.0,
            max_value=300.0,
            value=0.0,
            step=0.5,
            key=f"{prefix}_peso",
        )
    with col_nut2:
        altezza = st.number_input(
            "Altezza (cm)",
            min_value=0.0,
            max_value=250.0,
            value=0.0,
            step=1.0,
            key=f"{prefix}_altezza",
        )
    with col_nut3:
        bmi_val = 0.0
        if peso > 0 and altezza > 0:
            alt_m = altezza / 100.0
            bmi_val = round(peso / (alt_m**2), 1)
        st.metric(
            "Indice di Massa Corporea (BMI)",
            f"{bmi_val} kg/m²" if bmi_val > 0 else "Non calcolabile",
        )

    st.markdown("---")

    st.markdown("##### 🚶 Autonomia Funzionale")
    col_aut1, col_aut2 = st.columns(2)
    with col_aut1:
        scala_adl = st.selectbox(
            "Scala ADL (Activities of Daily Living)",
            [
                "Non valutato",
                "Indipendente (6/6)",
                "Parzialmente dipendente (3-5/6)",
                "Fortemente dipendente (0-2/6)",
            ],
            key=f"{prefix}_adl",
        )
    with col_aut2:
        scala_iadl = st.selectbox(
            "Scala IADL (Instrumental Activities of Daily Living)",
            [
                "Non valutato",
                "Indipendente (8/8)",
                "Parzialmente dipendente (4-7/8)",
                "Fortemente dipendente (0-3/8)",
            ],
            key=f"{prefix}_iadl",
        )

    st.markdown("---")

    st.markdown("##### 🧬 Anamnesi Familiare Oncologica (Familiarità per Tumori)")
    st.write("Selezionare gli organi con stretta familiarità neoplastica nota:")
    col_fam1, col_fam2, col_fam3, col_fam4 = st.columns(4)
    with col_fam1:
        fam_prostata = st.checkbox("Prostata", key=f"{prefix}_fam_prostata")
        fam_seno = st.checkbox("Seno", key=f"{prefix}_fam_seno")
    with col_fam2:
        fam_utero = st.checkbox("Utero / Endometrio", key=f"{prefix}_fam_utero")
        fam_ovaio = st.checkbox("Ovaio", key=f"{prefix}_fam_ovaio")
    with col_fam3:
        fam_vescica = st.checkbox("Vescica / Urotelio", key=f"{prefix}_fam_vescica")
        fam_colon = st.checkbox("Colon-Retto", key=f"{prefix}_fam_colon")
    with col_fam4:
        fam_altro = st.checkbox("Altro / Negativa", key=f"{prefix}_fam_altro")

    st.markdown("---")

    st.markdown("##### 💉 Stato Vaccinale Principale")
    col_vac1, col_vac2 = st.columns(2)
    with col_vac1:
        vac_antinfluenzale = st.checkbox("Antinfluenzale (Ultima stagione)", key=f"{prefix}_vac_influenzale")
        vac_pneumococco = st.checkbox("Anti-Pneumococco", key=f"{prefix}_vac_pneumococco")
    with col_vac2:
        vac_zoster = st.checkbox("Anti-Herpes Zoster", key=f"{prefix}_vac_zoster")
        vac_covid = st.checkbox("Anti-COVID (Aggiornato)", key=f"{prefix}_vac_covid")

    st.markdown("---")
    interventi_chirurgici = st.text_area(
        "Anamnesi Interventi Chirurgici Subiti",
        placeholder="Elencare eventuali interventi precedenti...",
        key=f"{prefix}_interventi",
    )
    anamnesi_farmacologica = st.text_area(
        "Anamnesi Farmacologica (Terapia in corso)",
        placeholder="Farmaci assunti abitualmente...",
        key=f"{prefix}_farmacologica",
    )

    organi_fam = []
    if fam_prostata: organi_fam.append("Prostata")
    if fam_seno: organi_fam.append("Seno")
    if fam_utero: organi_fam.append("Utero")
    if fam_ovaio: organi_fam.append("Ovaio")
    if fam_vescica: organi_fam.append("Vescica")
    if fam_colon: organi_fam.append("Colon-Retto")
    if fam_altro: organi_fam.append("Altro/Negativa")
    str_fam = ", ".join(organi_fam) if organi_fam else ""

    vaccini = []
    if vac_antinfluenzale: vaccini.append("Antinfluenzale")
    if vac_pneumococco: vaccini.append("Anti-Pneumococco")
    if vac_zoster: vaccini.append("Anti-Herpes Zoster")
    if vac_covid: vaccini.append("Anti-COVID")
    str_vac = ", ".join(vaccini) if vaccini else ""

    return {
        "ipertensione": ipertensione,
        "cardiopatia": cardiopatia,
        "diabete": diabete,
        "fumo": fumo,
        "insuff_renale": insuff_renale,
        "creatinina": creatinina,
        "ha_allergie": ha_allergie,
        "specifica_allergie": specifica_allergie,
        "ecog_performance": scala_performance,
        "mmse_eseguito": esegue_mmse,
        "mmse_punteggio": valore_mmse,
        "peso": peso,
        "altezza": altezza,
        "bmi": bmi_val,
        "scala_adl": scala_adl,
        "scala_iadl": scala_iadl,
        "familiarita_oncologica": str_fam,
        "stato_vaccinale": str_vac,
        "interventi_chirurgici": interventi_chirurgici,
        "anamnesi_farmacologica": anamnesi_farmacologica,
    }

def formatta_anamnesi_per_pdf(anamnesi):
    """Genera una stringa pulita ed ordinata contenente SOLO i campi anamnestici flaggati o compilati[cite: 2]."""
    linee = []

    patologie = []
    if anamnesi.get("ipertensione"):
        patologie.append("Ipertensione Arteriosa")
    if anamnesi.get("cardiopatia"):
        patologie.append("Cardiopatia / Ischemia")
    if anamnesi.get("diabete") and anamnesi.get("diabete") != "No":
        patologie.append(f"Diabete: {anamnesi['diabete']}")
    if anamnesi.get("insuff_renale"):
        crea = anamnesi.get("creatinina", "").strip()
        patologie.append("Insufficienza Renale Cronica" + (f" (Creatinina: {crea} mg/dL)" if crea else ""))

    if patologie:
        linee.append(f"• Condizioni Cliniche: {', '.join(patologie)}")

    fumo = anamnesi.get("fumo")
    if fumo and fumo != "Non fumatore":
        linee.append(f"• Abitudine Tabagica: {fumo}")

    if anamnesi.get("ha_allergie"):
        spec = anamnesi.get("specifica_allergie", "").strip()
        linee.append(f"• Allergie: {spec if spec else 'Presenti'}")

    ecog = anamnesi.get("ecog_performance")
    if ecog and "Non valutato" not in ecog:
        linee.append(f"• ECOG Performance Status: {ecog}")

    if anamnesi.get("mmse_eseguito"):
        punteggio = anamnesi.get("mmse_punteggio", "").strip()
        linee.append(f"• Test Cognitivo MMSE: {punteggio}")

    peso = anamnesi.get("peso", 0)
    altezza = anamnesi.get("altezza", 0)
    bmi = anamnesi.get("bmi", 0)
    if peso > 0 and altezza > 0:
        linee.append(f"• Parametri Antropometrici: Peso {peso} kg, Altezza {altezza} cm, BMI {bmi} kg/m²")

    adl = anamnesi.get("scala_adl")
    if adl and "Non valutato" not in adl:
        linee.append(f"• Scala ADL: {adl}")

    iadl = anamnesi.get("scala_iadl")
    if iadl and "Non valutato" not in iadl:
        linee.append(f"• Scala IADL: {iadl}")

    fam = anamnesi.get("familiarita_oncologica")
    if fam:
        linee.append(f"• Familiarità Oncologica: {fam}")

    vac = anamnesi.get("stato_vaccinale")
    if vac:
        linee.append(f"• Stato Vaccinale: {vac}")

    interventi = anamnesi.get("interventi_chirurgici", "").strip()
    if interventi:
        linee.append(f"• Interventi Chirurgici: {interventi}")

    farmacologica = anamnesi.get("anamnesi_farmacologica", "").strip()
    if farmacologica:
        linee.append(f"• Terapia / Anamnesi Farmacologica: {farmacologica}")

    return "\n".join(linee) if linee else ""

def genera_pdf_referto(codice_paziente, dati_visita, percorso, note_raccomandazioni, nome, cognome):
    """Funzione di generazione PDF strutturata con SimpleDocTemplate per il ritorno a capo automatico[cite: 2]."""
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=50,
        rightMargin=50,
        topMargin=45,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()

    style_brand_title = ParagraphStyle(
        "BrandTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=20,
        textColor=colors.HexColor("#CC0000"),
    )
    style_brand_sub = ParagraphStyle(
        "BrandSub",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#666666"),
    )
    style_meta = ParagraphStyle(
        "MetaText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#222222"),
    )
    style_h2 = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#111111"),
        spaceBefore=10,
        spaceAfter=4,
    )
    style_body = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#333333"),
        spaceAfter=4,
    )

    story = []

    story.append(Paragraph("<b><font color='#CC0000'>2</font><font color='#1A1A1A'>gether</font></b>", style_brand_title))
    story.append(Paragraph("the answer is just next 2U", style_brand_sub))
    story.append(Spacer(1, 10))

    meta_lines = [
        f"<b>Data Controllo / Visita:</b> {dati_visita.get('data')}",
        f"<b>Paziente:</b> {cognome} {nome} (ID: {codice_paziente})",
        f"<b>Tipologia Protocollo:</b> {dati_visita.get('tipo')}",
    ]
    for ml in meta_lines:
        story.append(Paragraph(ml, style_meta))

    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CCCCCC"), spaceBefore=2, spaceAfter=10))

    dettagli_testo = dati_visita.get("dettagli", "")
    if dettagli_testo:
        story.append(Paragraph("Dettagli Clinici e Parametri di Follow-up:", style_h2))
        for line in dettagli_testo.split("\n"):
            if line.strip():
                story.append(Paragraph(line, style_body))
        story.append(Spacer(1, 6))

    if percorso:
        story.append(Paragraph("Percorso Clinico Impostato:", style_h2))
        story.append(Paragraph(f"• {percorso}", style_body))
        story.append(Spacer(1, 6))

    if note_raccomandazioni:
        story.append(Paragraph("Raccomandazioni e Note Mediche:", style_h2))
        if isinstance(note_raccomandazioni, list):
            for rec in note_raccomandazioni:
                if rec and str(rec).strip():
                    story.append(Paragraph(f"• {rec}", style_body))
                    story.append(Spacer(1, 4))
        else:
            story.append(Paragraph(str(note_raccomandazioni), style_body))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
