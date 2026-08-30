import os
import json
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Elenco mesi per la selezione nelle app
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

def genera_pdf_referto(codice_paziente, dati_visita, percorso, note_raccomandazioni):
    """Genera un PDF in memoria pronto per il download su Streamlit."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1A365D'),
        spaceAfter=12
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
    
    # Intestazione
    story.append(Paragraph("<b>DSS UROLOGIA - REFERTO CLINICO</b>", title_style))
    story.append(Spacer(1, 10))
    
    # Info Paziente
    info_data = [
        [Paragraph("<b>Codice Paziente:</b>", normal_style), Paragraph(codice_paziente, normal_style)],
        [Paragraph("<b>Data Visita:</b>", normal_style), Paragraph(dati_visita.get("data", str(datetime.today().date())), normal_style)],
        [Paragraph("<b>Tipo Visita:</b>", normal_style), Paragraph(dati_visita.get("tipo", "-"), normal_style)],
        [Paragraph("<b>Percorso Clinical:</b>", normal_style), Paragraph(percorso, normal_style)]
    ]
    
    t_info = Table(info_data, colWidths=[130, 370])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 15))
    
    # Dettagli Clinici
    story.append(Paragraph("<b>Dettagli Clinici e Parametri</b>", heading_style))
    story.append(Paragraph(dati_visita.get("dettagli", "Nessun dettaglio inserito."), normal_style))
    story.append(Spacer(1, 15))
    
    # Raccomandazioni / Next Steps
    story.append(Paragraph("<b>Indicazioni e Indicazioni di Follow-up</b>", heading_style))
    if note_raccomandazioni:
        for nota in note_raccomandazioni:
            story.append(Paragraph(f"• {nota}", normal_style))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("Nessuna indicazione specifica.", normal_style))
        
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
