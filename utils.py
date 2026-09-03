import json
import os
from datetime import datetime
import streamlit as st

DB_FILE_PATH = "database_pazienti.json"

ELENCO_MESI = [
    "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
]

@st.cache_data
def carica_db_pazienti_cached():
    """
    Carica il database dei pazienti da file JSON con supporto di cache per massimizzare le performance.
    """
    if os.path.exists(DB_FILE_PATH):
        try:
            with open(DB_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def carica_db_pazienti():
    """
    Interfaccia di caricamento che interagisce direttamente con lo stato della sessione e il file system.
    """
    if "db_pazienti_cache" not in st.session_state:
        st.session_state["db_pazienti_cache"] = carica_db_pazienti_cached()
    return st.session_state["db_pazienti_cache"]

def salva_db_pazienti(db):
    """
    Salva il database aggiornato sul file JSON e pulisce la cache di Streamlit.
    """
    try:
        with open(DB_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
        st.cache_data.clear()
        st.session_state["db_pazienti_cache"] = db
        return True
    except Exception as e:
        st.error(f"Errore durante il salvataggio del database: {e}")
        return False

def salva_paziente_su_drive(nome, cognome, data_nascita, codice_univoco):
    """
    Funzione di servizio per la gestione della persistenza locale e tracciamento anagrafico.
    """
    cartella_base = "pazienti_archivio"
    if not os.path.exists(cartella_base):
        os.makedirs(cartella_base, exist_ok=True)
    
    info_paziente = {
        "nome": nome,
        "cognome": cognome,
        "data_nascita": str(data_nascita),
        "codice_univoco": codice_univoco,
        "data_registrazione": str(datetime.today().date())
    }
    
    file_path = os.path.join(cartella_base, f"{codice_univoco}.json")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(info_paziente, f, ensure_ascii=False, indent=4)
        return True
    except Exception:
        return False

def genera_o_aggiorna_registro(nome, cognome, data_nascita, codice_univoco):
    """
    Aggiorna il registro generale dei pazienti attivi nel sistema clinico.
    """
    registro_path = "registro_generale.json"
    registro = {}
    if os.path.exists(registro_path):
        try:
            with open(registro_path, "r", encoding="utf-8") as f:
                registro = json.load(f)
        except Exception:
            registro = {}
            
    registro[codice_univoco] = {
        "nome": nome,
        "cognome": cognome,
        "data_nascita": str(data_nascita),
        "ultimo_aggiornamento": str(datetime.today().date())
    }
    
    try:
        with open(registro_path, "w", encoding="utf-8") as f:
            json.dump(registro, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

def genera_pdf_referto(codice_paziente, ultima_visita, trattamento_scelto, note_list, nome="", cognome=""):
    """
    Generatore strutturato di referti medici in formato PDF basato su ReportLab.
    Restituisce i byte del file PDF generato.
    """
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    style_title = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=6
    )
    
    style_subtitle = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=12
    )
    
    style_body = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=8
    )

    story = []
    
    # Intestazione Reparto / Clinica
    story.append(Paragraph("CENTRO URO-ONCOLOGICO INTEGRATO", style_title))
    story.append(Paragraph(f"Referto Clinico Specialistico — Codice Paziente: {codice_paziente}", style_subtitle))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1A365D"), spaceAfter=15))
    
    # Dati Anagrafici
    if nome or cognome:
        story.append(Paragraph(f"<b>Paziente:</b> {cognome} {nome}", style_body))
    story.append(Paragraph(f"<b>Data Referto:</b> {ultima_visita.get('data', datetime.today().date())}", style_body))
    story.append(Paragraph(f"<b>Tipologia Visita:</b> {ultima_visita.get('tipo', 'Visita Specialistica')}", style_body))
    story.append(Spacer(1, 10))
    
    # Dettagli Clinici
    story.append(Paragraph("<b>Inquadramento e Dettagli Clinici:</b>", style_body))
    dettagli_testo = ultima_visita.get('dettagli', '').replace('\n', '<br/>')
    story.append(Paragraph(dettagli_testo, style_body))
    story.append(Spacer(1, 10))
    
    # Trattamento Selezionato
    story.append(Paragraph(f"<b>Percorso Terapeutico / Scelta:</b> {trattamento_scelto}", style_body))
    story.append(Spacer(1, 10))
    
    # Note e Considerazioni
    if note_list:
        story.append(Paragraph("<b>Considerazioni Cliniche e Linee Guida:</b>", style_body))
        for nota in note_list:
            nota_pulita = str(nota).replace('\n', '<br/>')
            story.append(Paragraph(f"• {nota_pulita}", style_body))
            
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
