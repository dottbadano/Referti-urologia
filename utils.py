import os
import json
import io
import random
import string
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import streamlit as st

ELENCO_MESI = [
    "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
]

DB_FILE = "db_pazienti.json"
REGISTRO_FILE = "registro_pazienti.json"

def carica_db_pazienti():
    """Carica il database locale dei pazienti se esiste."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def salva_db_pazienti(db_data):
    """Salva il database locale dei pazienti."""
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Errore nel salvataggio DB: {e}")

def genera_codice_univoco(nome, cognome):
    """Genera automaticamente un codice univoco basato su nome e cognome."""
    if nome and cognome:
        iniziali = f"{nome[0].upper()}{cognome[0].upper()}"
        rand_num = ''.join(random.choices(string.digits, k=4))
        return f"ID-{iniziali}-{rand_num}"
    return f"ID-PAT-{''.join(random.choices(string.digits, k=6))}"

def render_anamnesi_generale():
    """Crea la sezione riutilizzabile dell'anamnesi generale con i fattori di rischio."""
    st.markdown("### 📋 Anamnesi Generale e Fattori di Rischio")
    
    if "anamnesi_comune" not in st.session_state:
        st.session_state["anamnesi_comune"] = {
            "ipertensione": False,
            "diabete": "No",
            "fumo": "Non fumatore",
            "familiarita_organi": []
        }
    
    col1, col2 = st.columns(2)
    
    with col1:
        ipertensione = st.checkbox("Ipertensione arteriosa", value=st.session_state["anamnesi_comune"]["ipertensione"])
        
        diabete_opts = ["No", "Sì (Terapia Orale)", "Sì (Terapia Insulinica)"]
        curr_diabete = st.session_state["anamnesi_comune"]["diabete"]
        diabete_idx = diabete_opts.index(curr_diabete) if curr_diabete in diabete_opts else 0
        diabete = st.selectbox("Diabete Mellito", diabete_opts, index=diabete_idx, key="glob_diabete")
        
    with col2:
        fumo_opts = ["Non fumatore", "Ex fumatore", "Fumatore attivo"]
        curr_fumo = st.session_state["anamnesi_comune"]["fumo"]
        fumo_idx = fumo_opts.index(curr_fumo) if curr_fumo in fumo_opts else 0
        fumo = st.selectbox("Abitudine Tabagica", fumo_opts, index=fumo_idx, key="glob_fumo")
        
    st.markdown("**Familiarità per Tumori (Organi Interessati):**")
    organi_list = ["Prostata", "Vescica", "Rene", "Testicolo", "Polmone", "Colon", "Utero", "Ovaio", "Seno", "Fegato", "Pancreas"]
    
    cols = st.columns(4)
    familiarita_selezionata = []
    for idx, organo in enumerate(organi_list):
        col_idx = idx % 4
        with cols[col_idx]:
            val_precedente = organo in st.session_state["anamnesi_comune"]["familiarita_organi"]
            if st.checkbox(f"{organo}", value=val_precedente, key=f"fam_{organo}"):
                familiarita_selezionata.append(organo)
                
    dati_anamnesi = {
        "ipertensione": ipertensione,
        "diabete": diabete,
        "fumo": fumo,
        "familiarita_organi": familiarita_selezionata
    }
    st.session_state["anamnesi_comune"] = dati_anamnesi
    
    return dati_anamnesi

def genera_o_aggiorna_registro(nome, cognome, data_nascita, codice_paziente):
    """Mantiene un registro anagrafico base."""
    registro = {}
    if os.path.exists(REGISTRO_FILE):
        try:
            with open(REGISTRO_FILE, "r", encoding="utf-8") as f:
                registro = json.load(f)
        except Exception:
            registro = {}
    
    registro[codice_paziente] = {
        "nome": nome,
        "cognome": cognome,
        "data_nascita": str(data_nascita)
    }
    
    try:
        with open(REGISTRO_FILE, "w", encoding="utf-8") as f:
            json.dump(registro, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Errore nel salvataggio registro: {e}")

def genera_pdf_referto(codice_paziente, dati_visita, percorso, note_raccomandazioni, nome=None, cognome=None):
    """Genera un PDF in memoria pronto per il download con brand 2gether e anagrafica completa."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    
    brand_title_style = ParagraphStyle(
        'BrandTitle',
        parent=styles['Heading1'],
        fontSize=24,
        leading=28,
        alignment=1,
        spaceAfter=2
    )
    brand_subtitle_style = ParagraphStyle(
        'BrandSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        textColor=colors.HexColor('#555555'),
        alignment=1,
        spaceAfter=15
    )
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1A365D'),
        spaceAfter=10
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#2B6CB0'),
        spaceBefore=10,
        spaceAfter=6
    )
    normal_style = styles['Normal']
    
    # Intestazione 2gether con il 2 in rosso e la frase sotto
    story.append(Paragraph('<font color="red" size="28"><b>2</b></font><font size="24"><b>gether</b></font>', brand_title_style))
    story.append(Paragraph('<i>the answer is just next 2U</i>', brand_subtitle_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>REFERTO CLINICO</b>", title_style))
    story.append(Spacer(1, 10))
    
    nome_paziente = nome or "-"
    cognome_paziente = cognome or "-"
    
    if (not nome or not cognome) and os.path.exists(REGISTRO_FILE):
        try:
            with open(REGISTRO_FILE, "r", encoding="utf-8") as f:
                reg_data = json.load(f)
                if codice_paziente in reg_data:
                    nome_paziente = nome_paziente if nome_paziente != "-" else reg_data[codice_paziente].get("nome", "-")
                    cognome_paziente = cognome_paziente if cognome_paziente != "-" else reg_data[codice_paziente].get("cognome", "-")
        except Exception:
            pass

    # Tabella Info Paziente
    info_data = [
        [Paragraph("<b>Nome:</b>", normal_style), Paragraph(nome_paziente, normal_style)],
        [Paragraph("<b>Cognome:</b>", normal_style), Paragraph(cognome_paziente, normal_style)],
        [Paragraph("<b>Codice Univoco:</b>", normal_style), Paragraph(codice_paziente, normal_style)],
        [Paragraph("<b>Data Visita:</b>", normal_style), Paragraph(dati_visita.get("data", str(datetime.today().date())), normal_style)],
        [Paragraph("<b>Tipo Visita:</b>", normal_style), Paragraph(dati_visita.get("tipo", "-"), normal_style)],
        [Paragraph("<b>Percorso Clinico:</b>", normal_style), Paragraph(percorso, normal_style)]
    ]
    
    t_info = Table(info_data, colWidths=[130, 370])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 15))
    
    # Dettagli Clinici
    story.append(Paragraph("<b>Dettagli Clinici e Parametri</b>", heading_style))
    story.append(Paragraph(dati_visita.get("dettagli", "Nessun dettaglio inserito."), normal_style))
    story.append(Spacer(1, 15))
    
    # Raccomandazioni / Follow-up
    story.append(Paragraph("<b>Indicazioni e Follow-up</b>", heading_style))
    if note_raccomandazioni:
        for nota in note_raccomandazioni:
            story.append(Paragraph(f"• {nota}", normal_style))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("Nessuna indicazione specifica.", normal_style))
        
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
