import csv
from datetime import datetime
import hashlib
import io
import json
import math
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
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
# GESTIONE SALVATAGGIO LOCALE / PERMANENTE
# ==============================================================================
REGISTRO_LOCALE_PATH = "Registro_Chiave_Pazienti.csv"
DB_JSON_PATH = "db_pazienti.json"


def carica_db_pazienti():
    if os.path.exists(DB_JSON_PATH):
        try:
            with open(DB_JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def salva_db_pazienti(db):
    with open(DB_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)


def genera_o_aggiorna_registro(nome, cognome, data_nascita, codice_paziente):
    file_exists = os.path.exists(REGISTRO_LOCALE_PATH)
    with open(REGISTRO_LOCALE_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Nome", "Cognome", "Data_Nascita", "Codice_Paziente"])
        writer.writerow([nome, cognome, str(data_nascita), codice_paziente])


if "db_pazienti" not in st.session_state:
    st.session_state["db_pazienti"] = carica_db_pazienti()

ELENCO_MESI = [
    "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
]

# ==============================================================================
# MOTORE GENERAZIONE PDF UNIFICATO (Con Footer Normativo Obbligatorio)
# ==============================================================================
def genera_pdf_referto(codice_paziente, dati_visita, esito_percorso, note_esami):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=10
    )
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=5
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2D3748")
    )
    footer_style = ParagraphStyle(
        'FooterStyleCustom',
        parent=styles['Normal'],
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#718096"),
        alignment=1
    )

    story.append(Paragraph("<b>2GETAPP - CLINICAL DECISION SUPPORT UROLOGIA</b>", title_style))
    story.append(Paragraph("<i>Report Clinico DSS & Percorso Terapeutico Integrato (Prostata & Vescica)</i>", body_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1A365D"), spaceAfter=15))

    dati_tabella = [
        [Paragraph("<b>Codice Univoco Paziente:</b>", body_style), Paragraph(codice_paziente, body_style)],
        [Paragraph("<b>Data Documento:</b>", body_style), Paragraph(datetime.now().strftime("%d/%m/%Y"), body_style)],
        [Paragraph("<b>Tipo di Visita / Fase:</b>", body_style), Paragraph(dati_visita.get("tipo", "N/D"), body_style)],
        [Paragraph("<b>Esito / Percorso:</b>", body_style), Paragraph(f"<b>{esito_percorso}</b>", body_style)],
    ]
    t_info = Table(dati_tabella, colWidths=[160, 360])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 15))

    story.append(Paragraph("<b>QUADRO CLINICO E PARAMETRI VALUTATI</b>", h2_style))
    story.append(Paragraph(dati_visita.get("dettagli", "-"), body_style))
    story.append(Spacer(1, 15))

    story.append(Paragraph("<b>RACCOMANDAZIONI & PIANO DECISIONALE</b>", h2_style))
    for rec in note_esami:
        story.append(Paragraph(f"• {rec}", body_style))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 25))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E0"), spaceAfter=10))
    
    footer_text = (
        "Documento prodotto automaticamente dal Sistema di Supporto Decisionale 2gether™ secondo le Linee Guida Urologiche Internazionali e Nazionali.<br/>"
        "Riferimenti Ufficiali: <b>EAU</b> (European Association of Urology) | <b>AUA</b> (American Urological Association) | "
        "<b>AIOM</b> (Associazione Italiana di Oncologia Medica) | <b>NCCN</b> (National Comprehensive Cancer Network)"
    )
    story.append(Paragraph(footer_text, footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ==============================================================================
# FUNZIONI SCIENTIFICHE (PROSTATA)
# ==============================================================================
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
    if isup_num >= 4 or psa > 20 or ct_stage in ["cT3a", "cT3b", "cT4"] or is_terziario_alto:
        return ("Alto / Molto Alto Rischio", True, "Indicata Stadiatura Sistemica (PET/TC PSMA oppure TC + Scintigrafia).")
    elif isup_num in [2, 3] or (10 <= psa <= 20) or ct_stage == "cT2b-cT2c":
        if isup_num == 3 or (isup_num == 2 and psa > 10):
            return ("Rischio Intermedio Sfavorevole", True, "Indicata Stadiatura Sistemica (Preferibile PET/TC PSMA).")
        else:
            return ("Rischio Intermedio Favorevole", False, "Stadiatura sistemica NON indicata di routine.")
    else:
        return ("Basso Rischio", False, "Stadiatura sistemica NON indicata. Candidato per Sorveglianza Attiva.")


def calcola_timing_controllo(percorso, dati):
    if percorso == "Sorveglianza Attiva":
        isup = dati.get("isup", 1)
        psadt = dati.get("psadt")
        if (psadt is not None and psadt < 36) or isup > 1:
            return {
                "rec_psa": "PSA Sierico tra 3 Mesi (Monitoraggio stretto per cinetica rapida / PSADT < 36m).",
                "rec_rmn": "⚠️ Programmare mpRMN Prostatica urgente (entro 3 mesi).",
                "rec_bx": "⚠️ Ripetere Biopsia Prostatica di Riconferma/Re-stadiatura.",
                "alert": "⚠️ ATTENZIONE: PSADT accelerato o ISUP > 1. Valutare l'uscita dalla Sorveglianza Attiva.",
            }
        else:
            return {
                "rec_psa": "PSA Sierico ogni 6 Mesi + Visita Clinica.",
                "rec_rmn": "Programmare mpRMN Prostatica a 12 mesi dall'inizio della SA (o di controllo annuale).",
                "rec_bx": "Programmare Biopsia Prostatica di Riconferma tra i 12 e i 24 mesi.",
                "alert": "🟢 Cinetica del PSA nei limiti. Proseguire Sorveglianza Attiva.",
            }
    elif percorso == "Chirurgia (Post-Prostatectomia)":
        psa = dati.get("psa", 0.0)
        mesi_op = dati.get("mesi_post_op", 0)
        if psa >= 0.20:
            return {
                "rec_psa": "PSA Sierico Ultrasensibile di riconferma a 30 giorni.",
                "rec_imaging": "⚠️ PET/TC PSMA tempestiva per restaging.",
                "rec_azione": "Valutazione Radioterapica per Radioterapia di Salvataggio Precoce ± ADT.",
                "alert": "🚨 RECIDIVA BIOCHIMICA CONFERMATA (PSA ≥ 0.20 ng/ml).",
            }
        m = 3 if mesi_op <= 12 else (6 if mesi_op <= 36 else 12)
        return {
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
                "rec_psa": "PSA Sierico di riconferma a 30 giorni.",
                "rec_imaging": "⚠️ Programmare PET/TC PSMA e TC Torace-Addome di Restaging.",
                "rec_azione": "Discussione DMT per Terapia di Salvataggio o Sistemica.",
                "alert": "🚨 RECIDIVA BIOCHIMICA CRITERI PHOENIX (Nadir + 2.0 ng/ml).",
            }
        m = 3 if mesi_rt <= 24 else (6 if mesi_rt <= 60 else 12)
        return {
            "rec_psa": f"PSA Sierico tra {m} mesi + Visita Radioterapica / Oncologica.",
            "rec_imaging": "Imaging non indicato di routine in assenza di incremento sospetto.",
            "rec_azione": "Proseguire monitoraggio del Nadir.",
            "alert": "🟢 Cinetica del PSA stabile / post-attinica regolare.",
        }
    return {"rec_psa": "PSA + Visita tra 6 Mesi.", "alert": "Info standard."}

# ==============================================================================
# BARRA LATERALE PRINCIPALE
# ==============================================================================
st.sidebar.title("⚕️ 2getapp")
st.sidebar.caption("Clinical Decision Support in Uro-Oncologia")

organo_selezionato = st.sidebar.selectbox(
    "Seleziona Organo / Patologia:",
    ["🧬 PROSTATA", "💧 VESCICA & UTUC", "🫘 RENE (RCC)", "🥚 TESTICOLO & PENE"]
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

    if modalita == "1. Prima Visita: Inquadramento Bioptico & Rischio":
        st.subheader("📋 Inserimento Anagrafica Paziente")
        col_a, col_b = st.columns(2)
        with col_a:
            nome_p = st.text_input("Nome Paziente", key="pros_nome")
            data_nascita_p = st.date_input("Data di Nascita", datetime(1960, 1, 1), key="pros_nascita")
        with col_b:
            cognome_p = st.text_input("Cognome Paziente", key="pros_cognome")
            hash_id = hashlib.md5(f"{nome_p}{cognome_p}{data_nascita_p}".encode()).hexdigest()[:6]
            codice_paziente = f"2GET-PROS-{hash_id.upper()}"
            st.info(f"🔑 **Codice Univoco Generato:** `{codice_paziente}`")

        st.markdown("---")
        st.subheader("🔬 Dati Bioptici, Clinici e Imaging Iniziale (mpRMN)")

        col1, col2, col3 = st.columns(3)
        with col1:
            isup_basale = st.selectbox(
                "ISUP Group Bioptico:",
                ["ISUP 1 (Gleason 3+3)", "ISUP 2 (Gleason 3+4)", "ISUP 3 (Gleason 4+3)", "ISUP 4 (Gleason 4+4)", "ISUP 5 (Gleason 9-10)"],
                key="pros_isup"
            )
            isup_num = int(isup_basale.split()[1])
            gleason_terziario = st.selectbox("Gleason Pattern Terziario:", ["Assente", "Pattern 4 Terziario", "Pattern 5 Terziario"], key="pros_gleason")

            col_m, col_y = st.columns(2)
            with col_m:
                mese_psa_b = st.selectbox("Mese PSA", ELENCO_MESI, index=datetime.today().month - 1, key="pros_mese_psa")
            with col_y:
                anno_psa_b = st.number_input("Anno PSA", min_value=2000, max_value=2030, value=datetime.today().year, key="pros_anno_psa")

            num_mese_b = ELENCO_MESI.index(mese_psa_b) + 1
            data_psa_basale = datetime(anno_psa_b, num_mese_b, 1).date()
            psa_basale = st.number_input("PSA Basale (ng/ml)", value=6.5, step=0.1, key="pros_psa_basale")

        with col2:
            ct_stage = st.selectbox(
                "Stadio T Clinico:",
                ["cT1c (Inapprezzabile)", "cT2a (≤ metade di un lobo)", "cT2b (> metade di un lobo)", "cT2c (Entrambi i lobi)", "cT3a (Extracapsulare)", "cT3b (Vescicole)", "cT4 (Fissato/Adiacenti)"],
                key="pros_ct_stage"
            )
            rmn_pirads = st.selectbox("Reperto mpRMN Prostatica:", ["PI-RADS 3", "PI-RADS 4", "PI-RADS 5", "ECE / SVI Sospetta alla RMN", "Non Eseguita"], key="pros_rmn")

        with col3:
            st.markdown("🎯 **Valutazione Rischio & Stadiatura**")
            gruppo_rischio, necessita_stadiatura, motivazione_stadiatura = calcola_gruppo_rischio_eau(isup_num, psa_basale, ct_stage, gleason_terziario)
            st.write(f"**Classe di Rischio:** `{gruppo_rischio}`")
            if necessita_stadiatura:
                st.error("⚠️ **STADIATURA SISTEMICA INDICATA**")
            else:
                st.success("✅ **STADIATURA NON INDICATA AB INITIO**")

        st.markdown("---")
        scelta_trattamento = st.selectbox("Trattamento Concordato / Scelto:", ["Sorveglianza Attiva", "Chirurgia (Post-Prostatectomia)", "Radioterapia"], key="pros_trattamento") if not necessita_stadiatura else "In attesa di Stadiatura (DMT II)"

        if st.button("💾 Salvataggio & Genera Report PDF (Prostata)", key="pros_btn_save"):
            if not nome_p or not cognome_p:
                st.error("Inserire Nome e Cognome del paziente.")
            else:
                dati_v = {
                    "data": str(datetime.today().date()),
                    "tipo": "Visita I - Inquadramento Bioptico",
                    "dettagli": f"ISUP {isup_num} | Gleason Terziario: {gleason_terziario} | PSA: {psa_basale} ({mese_psa_b} {anno_psa_b}) | {ct_stage} | Rischio: {gruppo_rischio}"
                }
                st.session_state["db_pazienti"][codice_paziente] = {
                    "organo": "PROSTATA",
                    "isup": isup_num,
                    "rischio": gruppo_rischio,
                    "percorso_scelto": scelta_trattamento,
                    "ultimo_psa": psa_basale,
                    "data_ultimo_psa": str(data_psa_basale),
                    "visite": [dati_v]
                }
                salva_db_pazienti(st.session_state["db_pazienti"])
                genera_o_aggiorna_registro(nome_p, cognome_p, data_nascita_p, codice_paziente)
                
                pdf_bytes = genera_pdf_referto(codice_paziente, dati_v, scelta_trattamento, [motivazione_stadiatura, f"Percorso assegnato: {scelta_trattamento}"])
                st.success(f"Paziente salvato con successo! Codice: `{codice_paziente}`")
                
                st.download_button(
                    label="📄 Scarica Referto PDF Stampabile",
                    data=pdf_bytes,
                    file_name=f"Referto_PROSTATA_{codice_paziente}.pdf",
                    mime="application/pdf",
                    key="pros_dl"
                )

    elif modalita == "2. Seconda Visita / DMT: Referto Stadiatura & Decisione":
        st.subheader("📑 Seconda Visita / Inquadramento DMT")
        st.info("Fase per l'integrazione di PET/TC PSMA e discussione in Multidisciplinare.")

    elif modalita == "3. Controllo Successivo / Follow-up PSA":
        st.subheader("🔍 Richiama Paziente per Follow-up")
        codice_search = st.text_input("Inserisci Codice Univoco Paziente:", key="pros_search_code").strip().upper()

        if codice_search in st.session_state["db_pazienti"]:
            paziente = st.session_state["db_pazienti"][codice_search]
            st.success(f"Paziente Trovato! ID: {codice_search}")
            percorso_attuale = paziente.get("percorso_scelto", "Sorveglianza Attiva")

            st.markdown("---")
            col_psa1, col_psa2, col_psa3 = st.columns(3)
            with col_psa1:
                mese_psa_a = st.selectbox("Mese Prelievo PSA", ELENCO_MESI, index=datetime.today().month - 1, key="pros_fu_mese")
            with col_psa2:
                anno_psa_a = st.number_input("Anno Prelievo PSA", min_value=2000, max_value=2030, value=datetime.today().year, key="pros_fu_anno")
            with col_psa3:
                psa_attuale = st.number_input("Valore PSA Sierico (ng/ml):", min_value=0.0, value=float(paziente.get("ultimo_psa", 0.0)), step=0.01, key="pros_fu_psa")

            num_mese_a = ELENCO_MESI.index(mese_psa_a) + 1
            data_psa_attuale = datetime(anno_psa_a, num_mese_a, 1).date()
            psadt_calcolato = calcola_psadt(paziente.get("ultimo_psa"), paziente.get("data_ultimo_psa"), psa_attuale, data_psa_attuale)

            if percorso_attuale == "Sorveglianza Attiva":
                res_fu = calcola_timing_controllo("Sorveglianza Attiva", {"isup": paziente.get("isup", 1), "psadt": psadt_calcolato})
            elif percorso_attuale == "Chirurgia (Post-Prostatectomia)":
                res_fu = calcola_timing_controllo("Chirurgia (Post-Prostatectomia)", {"psa": psa_attuale, "mesi_post_op": 6})
            else:
                res_fu = calcola_timing_controllo("Radioterapia", {"psa": psa_attuale, "psa_nadir": 0.1, "mesi_post_rt": 12})

            st.info(f"**Indicazioni:** {res_fu['rec_psa']}")

            if st.button("💾 Salvataggio Visita & Genera PDF Controllo", key="pros_fu_save"):
                paziente["ultimo_psa"] = psa_attuale
                paziente["data_ultimo_psa"] = str(data_psa_attuale)
                
                dati_v = {
                    "data": str(datetime.today().date()),
                    "tipo": f"Follow-up ({percorso_attuale})",
                    "dettagli": f"PSA: {psa_attuale:.2f} ({mese_psa_a} {anno_psa_a}) | PSADT: {psadt_calcolato} mesi"
                }
                paziente["visite"].append(dati_v)
                salva_db_pazienti(st.session_state["db_pazienti"])
                
                note_pdf = [res_fu.get("rec_psa"), res_fu.get("rec_rmn"), res_fu.get("rec_bx"), res_fu.get("rec_imaging")]
                note_pdf = [n for n in note_pdf if n]
                
                pdf_bytes = genera_pdf_referto(codice_search, dati_v, percorso_attuale, note_pdf)
                st.success("Controllo registrato!")
                st.download_button(
                    label="📄 Scarica Referto Follow-up PDF",
                    data=pdf_bytes,
                    file_name=f"FollowUp_PROSTATA_{codice_search}.pdf",
                    mime="application/pdf",
                    key="pros_fu_dl"
                )

# ==============================================================================
# MODULO 2: VESCICA & UTUC (Integrato con correzione tasti ed esecuzione protetta)
# ==============================================================================
elif organo_selezionato == "💧 VESCICA & UTUC":
    st.title("💧 Carcinoma Uroteliale Vescicale & UTUC")

    fase_vescica = st.radio(
        "Seleziona Fase Diagnostica/Clinica:",
        [
            "1. Prima Cistoscopia & Diagnosi Iniziale",
            "2. Seconda Visita Post-TURBT (Istologia & Re-TURB)",
            "3. MIBC (≥T2) & Criteri di Elegibilità Chemioterapia"
        ],
        horizontal=True,
        key="vescica_fase_radio"
    )

    # --------------------------------------------------------------------------
    # FASE 1: PRIMA CISTOSCOPIA
    # --------------------------------------------------------------------------
    if fase_vescica == "1. Prima Cistoscopia & Diagnosi Iniziale":
        st.subheader("📋 1. Anagrafica e Primo Snodo Diagnostico")
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            nome_p = st.text_input("Nome Paziente", key="vescica_nome")
            data_nascita_p = st.date_input("Data di Nascita", datetime(1960, 1, 1), key="vescica_nascita")
        with col_b:
            cognome_p = st.text_input("Cognome Paziente", key="vescica_cognome")
            sesso = st.selectbox("Sesso del Paziente:", ["Maschio", "Femmina"], key="vescica_sesso")
        with col_c:
            hash_id = hashlib.md5(f"{nome_p}{cognome_p}{data_nascita_p}".encode()).hexdigest()[:6]
            codice_paziente = f"2GET-VESC-{hash_id.upper()}"
            st.info(f"🔑 **Codice Univoco:** `{codice_paziente}`")

        st.markdown("---")
        st.subheader("🔍 2. Indicazione ed Esito Cistoscopia")

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            motivo_cistoscopia = st.selectbox(
                "Motivo della Cistoscopia:",
                [
                    "Ematuria Macroscopica",
                    "Ematuria Microscopica Persistente",
                    "LUTS Irritativi / Urgenza Mictionale non spiegata",
                    "Reperto Incidentale Ecografico (Sospetta formazione)",
                    "Citologia Urinaria Positiva / Sospetta (Atypical/HGUC)",
                    "Sorveglianza / Rischio Professionale (Fumo, Amine Aromatiche)"
                ],
                key="vescica_motivo"
            )
        with col_d2:
            esito_cistoscopia = st.selectbox(
                "Esito della Cistoscopia:",
                [
                    "NEGATIVA (Assenza di neoformazioni sospette)",
                    "POSITIVA (Riscontro di neoformazione/i o aree sospette)"
                ],
                key="vescica_esito"
            )

        if "NEGATIVA" in esito_cistoscopia:
            st.success("🟢 **CISTOSCOPIA NEGATIVA**: Non si evidenziano neoformazioni vegetanti o lesioni sospette.")
            
            if sesso == "Maschio":
                template_negativo = (
                    "L'esame cistoscopico condotto con strumento flessibile evidenzia:\n"
                    "- Uretra anteriore e membranosa: pervia, mucosa regolare.\n"
                    "- Uretra prostatica: canale pervio, lobi prostatici non ostruenti.\n"
                    "- Cavità vescicale: mucosa normoelastica, esente da lesioni vegetanti sospette. Meati ureterali ortotopici ed eiaculanti urine limpide.\n"
                    "- CONCLUSIONI: Cistoscopia negativa per lesioni uroteliali evolutive."
                )
            else:
                template_negativo = (
                    "L'esame cistoscopico condotto con strumento flessibile evidenzia:\n"
                    "- Uretra: breve e pervia.\n"
                    "- Cavità vescicale: mucosa esente da lesioni vegetanti o alterazioni sospette. Meati ureterali ortotopici ed eiaculanti urine limpide.\n"
                    "- CONCLUSIONI: Cistoscopia negativa per lesioni uroteliali evolutive."
                )

            referto_testo = st.text_area("Testo del Referto Cistoscopico (Modificabile):", value=template_negativo, height=180, key="testo_negativo")
            raccomandazione_neg = st.selectbox(
                "Indicazione / Follow-up:",
                [
                    "Nessun ulteriore accertamento urologico immediato (Follow-up clinico)",
                    "Esecuzione Citologia Urinaria su 3 campioni di controllo",
                    "Rivalutazione ecografica a 6-12 mesi",
                    "Approfondimento vie urinarie superiori (TC Urografia) per ematuria non spiegata"
                ],
                key="racc_neg"
            )

            if st.button("💾 Salvataggio & Genera PDF Cistoscopia Negativa", key="btn_save_neg"):
                if not nome_p or not cognome_p:
                    st.error("Inserire Nome e Cognome del paziente.")
                else:
                    dati_v = {
                        "data": str(datetime.today().date()),
                        "tipo": f"Cistoscopia Diagnostica Negativa ({sesso})",
                        "dettagli": referto_testo
                    }
                    st.session_state["db_pazienti"][codice_paziente] = {
                        "organo": "VESCICA",
                        "sesso": sesso,
                        "esito": "Negativa",
                        "visite": [dati_v]
                    }
                    salva_db_pazienti(st.session_state["db_pazienti"])
                    genera_o_aggiorna_registro(nome_p, cognome_p, data_nascita_p, codice_paziente)

                    pdf_bytes = genera_pdf_referto(
                        codice_paziente,
                        dati_v,
                        "CISTOSCOPIA NEGATIVA",
                        [f"Raccomandazione: {raccomandazione_neg}"]
                    )
                    st.success(f"Referto stampato! Il percorso del paziente `{codice_paziente}` termina qui.")
                    st.download_button(
                        label="📄 Scarica Referto PDF Cistoscopia Negativa",
                        data=pdf_bytes,
                        file_name=f"Referto_Cistoscopia_NEG_{codice_paziente}.pdf",
                        mime="application/pdf",
                        key="dl_neg"
                    )

        else:
            st.error("⚠️ **CISTOSCOPIA POSITIVA**: Indicazione chirurgica a TURBT.")

            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                aspetto_lesione = st.selectbox(
                    "Morfologia Neoformazione:",
                    [
                        "Papillare / Peduncolata (Esofitica, apparentemente non infiltrante)",
                        "Sessile / Solida / Piatta (Apparentemente Infiltrante)",
                        "Area Eritematosa / Vellutata (Sospetto CIS)",
                        "Lesioni Multiple Papillari Multifocali"
                    ],
                    key="morfologia_lesione"
                )
            with col_p2:
                sede_lesione = st.selectbox(
                    "Sede Lesione:",
                    ["Parete Laterale Destra", "Parete Laterale Sinistra", "Parete Posteriore", "Fondo / Cupola", "Trigono Vescicale", "Collo Vescicale / Meati", "Uretra Prostatica (Uomo)"],
                    key="sede_lesione"
                )
            with col_p3:
                dimensione_stimata = st.selectbox(
                    "Dimensione Stimata:",
                    ["< 1 cm", "1 - 3 cm", "> 3 cm (Grande massa vescicale)"],
                    key="dim_lesione"
                )

            st.markdown("---")
            snodo_turbt = st.selectbox(
                "Programmazione Chirurgica (SNODO UNICO TURBT):",
                [
                    "TURBT (Transurethral Resection of Bladder Tumor)",
                    "TURBT + mpRMN Vescicale Pre-operatoria (Score VI-RADS)",
                    "TURBT + Biopsie Prostatiche/Uretrali Mappate (Uomo)",
                    "TURBT + Biopsie Vescicali Multiple (Sospetto CIS)"
                ],
                key="snodo_turbt"
            )

            note_guida = [f"Indicazione Chirurgica: {snodo_turbt}"]
            if "Sessile" in aspetto_lesione or "> 3 cm" in dimensione_stimata:
                st.warning("⚠️ **RISCHIO INVASIONE MUSCOLARE (≥pT2)**: Consigliata mpRMN Vescicale Pre-operatoria (VI-RADS) prima della TURBT.")
                if "mpRMN" not in snodo_turbt:
                    note_guida.append("Sospetta infiltrazione muscolare: raccomandata mpRMN Vescicale (VI-RADS) pre-TURBT.")

            if sesso == "Maschio":
                note_guida.append("Uomo: Valutare uretra prostatica durante TURBT.")
            else:
                note_guida.append("Donna: Valutare parete vescicale anteriore e piano vaginale.")

            template_positivo = (
                f"L'esame cistoscopico evidenzia in corrispondenza della {sede_lesione.lower()} neoformazione {aspetto_lesione.lower()} di circa {dimensione_stimata}.\n"
                f"- RACCOMANDAZIONE: Indicazione ad intervento di TURBT (Resezione Transuretrale di Tumore Vescicale)."
            )

            referto_testo_pos = st.text_area("Testo del Referto Cistoscopico Positivo:", value=template_positivo, height=160, key="testo_positivo")

            if st.button("💾 Salvataggio & Genera PDF Cistoscopia Positiva (TURBT)", key="btn_save_pos"):
                if not nome_p or not cognome_p:
                    st.error("Inserire Nome e Cognome del paziente.")
                else:
                    dati_v = {
                        "data": str(datetime.today().date()),
                        "tipo": f"Cistoscopia Diagnostica POSITIVA ({sesso})",
                        "dettagli": referto_testo_pos
                    }
                    st.session_state["db_pazienti"][codice_paziente] = {
                        "organo": "VESCICA",
                        "sesso": sesso,
                        "esito": "Positiva",
                        "morfologia": aspetto_lesione,
                        "sede": sede_lesione,
                        "percorso_scelto": snodo_turbt,
                        "visite": [dati_v]
                    }
                    salva_db_pazienti(st.session_state["db_pazienti"])
                    genera_o_aggiorna_registro(nome_p, cognome_p, data_nascita_p, codice_paziente)

                    pdf_bytes = genera_pdf_referto(
                        codice_paziente,
                        dati_v,
                        "CISTOSCOPIA POSITIVA (INDICAZIONE TURBT)",
                        note_guida
                    )
                    st.success(f"Referto salvato con indicazione a TURBT! Codice Paziente: `{codice_paziente}`.")
                    st.download_button(
                        label="📄 Scarica Referto PDF Cistoscopia Positiva (TURBT)",
                        data=pdf_bytes,
                        file_name=f"Referto_Cistoscopia_TURBT_{codice_paziente}.pdf",
                        mime="application/pdf",
                        key="dl_pos"
                    )

    # --------------------------------------------------------------------------
    # FASE 2: SECONDA VISITA POST-TURBT
    # --------------------------------------------------------------------------
    elif fase_vescica == "2. Seconda Visita Post-TURBT (Istologia & Re-TURB)":
        st.subheader("📑 Seconda Visita Post-TURBT: Valutazione Istologica e Decisionale")

        db_pazienti_memoria = st.session_state.get("db_pazienti", {})
        codici_esistenti = list(db_pazienti_memoria.keys()) if isinstance(db_pazienti_memoria, dict) else []
        
        if codici_esistenti:
            cod_sel = st.selectbox("Seleziona Codice Paziente esistente:", ["-- Seleziona o Inserisci nuovo --"] + codici_esistenti, key="vescica_sel_esistente")
        else:
            cod_sel = "-- Seleziona o Inserisci nuovo --"

        if cod_sel != "-- Seleziona o Inserisci nuovo --":
            codice_paziente = cod_sel
            st.info(f"Paziente Selezionato: `{codice_paziente}`")
        else:
            codice_paziente = st.text_input("Inserisci Codice Univoco Paziente (es. 2GET-VESC-XXXXXX):", key="vescica_manual_code")

        st.markdown("---")
        st.subheader("🔬 1. Esame Istologico Post-TURBT (CAMPI OBBLIGATORI)")

        col_ist1, col_ist2, col_ist3 = st.columns(3)

        with col_ist1:
            st_pT = st.selectbox(
                "Stadio T (pT) *[OBBLIGATORIO]*:",
                [
                    "-- Seleziona pT --",
                    "pTa (Non Invasivo)",
                    "pT1 (Invasione della Lamina Propria)",
                    "pTis (Carcinoma in Situ isolato o associato)",
                    "≥ pT2 (Invasione della Muscolare Propria - MIBC)"
                ],
                key="vescica_st_pt"
            )

        with col_ist2:
            st_grado = st.selectbox(
                "Grado OMS (LG / HG) *[OBBLIGATORIO]*:",
                [
                    "-- Seleziona Grado --",
                    "LG (Low Grade / Basso Grado)",
                    "HG (High Grade / Alto Grado)"
                ],
                key="vescica_st_grado"
            )

        with col_ist3:
            presenza_muscolo = st.selectbox(
                "Presenza di Tonaca Muscolare nel Preparato:",
                [
                    "Presente e Indenne (Muscolare Propria Negativa)",
                    "Assente (Non valutabile la muscolare)",
                    "Infiltrata (pT2)"
                ],
                key="vescica_muscolo"
            )

        st.markdown("---")
        st.subheader("🫲 2. Integrazione RMN Pre-TURBT / VI-RADS (se disponibile)")

        rmn_eseguita = st.radio(
            "RMN Vescicale Eseguita?",
            ["No / Non disponibile", "Sì - RMN Certifica Malattia Superficiale (VI-RADS ≤ 2)", "Sì - RMN Sospetta Infiltrazione Muscolare (VI-RADS ≥ 3)"],
            horizontal=True,
            key="vescica_rmn_eseguita"
        )

        if "VI-RADS ≤ 2" in rmn_eseguita:
            st.success("✅ **RMN CERTIFICA MALATTIA NON MUSCOLO-INVASIVA (VI-RADS ≤ 2)**: L'esame RMN conferma l'assenza di invasione della tonaca muscolare.")
        elif "VI-RADS ≥ 3" in rmn_eseguita:
            st.warning("⚠️ **RMN SOSTENE INFILTRAZIONE (VI-RADS ≥ 3)**: Correlare attentamente con l'esame istologico.")

        st.markdown("---")
        st.subheader("⚖️ 3. Indicazioni Cliniche & Avviso Re-TURB")

        indicazioni_visita = []
        richiede_returb = False

        if st_pT == "-- Seleziona pT --" or st_grado == "-- Seleziona Grado --":
            st.error("⛔ **ATTENZIONE**: I campi **pT** e **Grado (LG/HG)** sono **OBBLIGATORI** per procedere con il DSS e la stampa del referto.")
        else:
            if "pT1" in st_pT:
                richiede_returb = True
                motivo_returb = "Stadio pT1 (Tutti i pT1 richiedono Re-TURB a 2-6 settimane)."
            elif "HG" in st_grado and "Assente" in presenza_muscolo:
                richiede_returb = True
                motivo_returb = "Resezione High Grade (HG) priva di tonaca muscolare nel preparato."
            elif "Incompleta" in presenza_muscolo:
                richiede_returb = True
                motivo_returb = "Resezione primaria incompleta."

            if richiede_returb:
                st.error(f"⚠️ **INDICAZIONE A RE-TURB (Second Look)**\n\n**Motivazione:** {motivo_returb}\n\n👉 **INVITO CLINICO:** Discutere l'indicazione alla Re-TURB direttamente con il paziente (benefici stadiativi e terapeutici).")
                indicazioni_visita.append(f"INDIRIZZO CLINICO: Eventuale Re-TURB indicata e discussa con il paziente ({motivo_returb}).")
            else:
                st.info("ℹ️ Re-TURB non routinariamente indicata. Procedere con terapia endovescicale (BCG/Chemioterapia) o sorveglianza in base alla classe di rischio.")
                indicazioni_visita.append("Re-TURB non necessaria. Procedere con protocollo di sorveglianza/instillazioni.")

            if "VI-RADS ≤ 2" in rmn_eseguita:
                indicazioni_visita.append("RMN pre-operatoria certifica lesione non muscolo-invasiva (VI-RADS ≤ 2).")

            testo_post_turb = (
                f"VISITA POST-TURBT - VALUTAZIONE ISTOLOGICA\n"
                f"- Istotipo e Stadio: {st_pT}, {st_grado}\n"
                f"- Valutazione Tonaca Muscolare: {presenza_muscolo}\n"
                f"- RMN Vescicale: {rmn_eseguita}\n"
                f"- DECISIONE CLINICA: " + ("Inviata/Discussa eventuale Re-TURB con il paziente." if richiede_returb else "Programmata gestione/follow-up standard.")
            )

            referto_post = st.text_area("Testo del Referto II Visita Post-TURBT:", value=testo_post_turb, height=160, key="vescica_testo_post")

            if st.button("💾 Salvataggio & Genera PDF II Visita", key="vescica_btn_save_ii"):
                if not codice_paziente:
                    st.error("Inserire un codice paziente valido.")
                else:
                    dati_v = {
                        "data": str(datetime.today().date()),
                        "tipo": "Seconda Visita Post-TURBT",
                        "dettagli": referto_post
                    }
                    if codice_paziente not in st.session_state["db_pazienti"]:
                        st.session_state["db_pazienti"][codice_paziente] = {"visite": []}

                    if "visite" not in st.session_state["db_pazienti"][codice_paziente]:
                        st.session_state["db_pazienti"][codice_paziente]["visite"] = []

                    st.session_state["db_pazienti"][codice_paziente]["visite"].append(dati_v)
                    st.session_state["db_pazienti"][codice_paziente]["istologia"] = {
                        "pT": st_pT,
                        "grado": st_grado,
                        "re_turb_indicata": richiede_returb
                    }
                    salva_db_pazienti(st.session_state["db_pazienti"])

                    pdf_bytes = genera_pdf_referto(
                        codice_paziente,
                        dati_v,
                        f"Istologia: {st_pT} - {st_grado}",
                        indicazioni_visita
                    )
                    st.success(f"II Visita registrata con successo per il paziente `{codice_paziente}`!")
                    st.download_button(
                        label="📄 Scarica Referto PDF II Visita",
                        data=pdf_bytes,
                        file_name=f"Referto_PostTURBT_{codice_paziente}.pdf",
                        mime="application/pdf",
                        key="vescica_dl_ii"
                    )

    elif fase_vescica == "3. MIBC (≥T2) & Criteri di Elegibilità Chemioterapia":
        st.subheader("🩺 3. Carcinoma Muscolo-Invasivo (MIBC ≥ T2)")
        st.info("Fase per la valutazione dell'elegibilità a Cisplatino (Cisplatin-eligible vs. Ineligible) e stadiatura TC/PET.")

# ==============================================================================
# MODULI IN COSTRUZIONE
# ==============================================================================
elif organo_selezionato == "🫘 RENE (RCC)":
    st.title("🫘 Carcinoma Renale (RCC)")
    st.info("Modulo in fase di sviluppo.")

elif organo_selezionato == "🥚 TESTICOLO & PENE":
    st.title("🥚 Tumori del Testicolo e del Pene")
    st.info("Modulo in fase di sviluppo.")
