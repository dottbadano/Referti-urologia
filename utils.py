import streamlit as st
import os
import json
import random
import string
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

def carica_db_pazienti():
    """Carica il database dei pazienti dal file JSON."""
    if os.path.exists("registro_pazienti.json"):
        try:
            with open("registro_pazienti.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def genera_codice_univoco(nome, cognome):
    """Genera un codice univoco basato sulle iniziali e numeri casuali."""
    n_init = nome[:2].upper() if len(nome) >= 2 else nome.upper()
    c_init = cognome[:2].upper() if len(cognome) >= 2 else cognome.upper()
    rand_num = ''.join(random.choices(string.digits, k=4))
    return f"{c_init}{n_init}-{rand_num}"

def genera_o_aggiorna_registro(nome, cognome, data_nascita, codice_univoco):
    """Salva o aggiorna il registro pazienti in un file JSON locale."""
    registro = carica_db_pazienti()
            
    registro[codice_univoco] = {
        "nome": nome,
        "cognome": cognome,
        "data_nascita": str(data_nascita),
        "ultimo_aggiornamento": str(datetime.today().date())
    }
    
    with open("registro_pazienti.json", "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=4)

def render_anamnesi_generale(prefix="gen"):
    """Renderizza l'inquadramento clinico generale con campi facoltativi."""
    st.markdown("#### 📋 Anamnesi Generale Paziente")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ipertensione = st.checkbox("Ipertensione Arteriosa", key=f"{prefix}_ipertensione")
        cardiopatia = st.checkbox("Cardiopatia / Ischemia", key=f"{prefix}_cardiopatia")
        diabete = st.selectbox("Diabete Mellito", ["No", "Diabete Tipo 1", "Diabete Tipo 2"], key=f"{prefix}_diabete")
        
        insuff_renale = st.checkbox("Insufficienza Renale Cronica", key=f"{prefix}_insuff_renale")
        creatinina = ""
        if insuff_renale:
            creatinina = st.text_input("Valore Creatinina (mg/dL)", placeholder="Es. 1.4 mg/dL", key=f"{prefix}_creatinina")
            
    with col2:
        fumo = st.selectbox("Abitudine Tabagica", ["Non fumatore", "Ex fumatore", "Fumatore attivo"], key=f"{prefix}_fumo")
        
        ha_allergie = st.checkbox("Allergie", key=f"{prefix}_ha_allergie")
        specifica_allergie = ""
        if ha_allergie:
            specifica_allergie = st.text_input("Specificare a cosa è allergico", placeholder="Es. Penicillina, Lattice...", key=f"{prefix}_specifica_allergie")

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
                "4 - Completamente disabile, confinato a letto o sedia"
            ],
            key=f"{prefix}_ecog"
        )
    with col_v2:
        esegue_mmse = st.checkbox("Eseguito Mini-Mental State Examination (MMSE) / Test Cognitivo", key=f"{prefix}_check_mmse")
        valore_mmse = ""
        if esegue_mmse:
            valore_mmse = st.text_input("Punteggio MMSE / Test (es. 28/30)", placeholder="Punteggio ottenuto...", key=f"{prefix}_valore_mmse")

    st.markdown("---")

    st.markdown("##### ⚖️ Stato Nutrizionale e Parametri Antropometrici")
    col_nut1, col_nut2, col_nut3 = st.columns(3)
    with col_nut1:
        peso = st.number_input("Peso (kg)", min_value=0.0, max_value=300.0, value=0.0, step=0.5, key=f"{prefix}_peso")
    with col_nut2:
        altezza = st.number_input("Altezza (cm)", min_value=0.0, max_value=250.0, value=0.0, step=1.0, key=f"{prefix}_altezza")
    with col_nut3:
        bmi_val = 0.0
        if peso > 0 and altezza > 0:
            alt_m = altezza / 100.0
            bmi_val = round(peso / (alt_m ** 2), 1)
        st.metric("Indice di Massa Corporea (BMI)", f"{bmi_val} kg/m²" if bmi_val > 0 else "Non calcolabile")

    st.markdown("---")

    st.markdown("##### 🚶 Autonomia Funzionale")
    col_aut1, col_aut2 = st.columns(2)
    with col_aut1:
        scala_adl = st.selectbox(
            "Scala ADL (Activities of Daily Living)",
            ["Non valutato", "Indipendente (6/6)", "Parzialmente dipendente (3-5/6)", "Fortemente dipendente (0-2/6)"],
            key=f"{prefix}_adl"
        )
    with col_aut2:
        scala_iadl = st.selectbox(
            "Scala IADL (Instrumental Activities of Daily Living)",
            ["Non valutato", "Indipendente (8/8)", "Parzialmente dipendente (4-7/8)", "Fortemente dipendente (0-3/8)"],
            key=f"{prefix}_iadl"
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
    interventi_chirurgici = st.text_area("Anamnesi Interventi Chirurgici Subiti", placeholder="Elencare eventuali interventi precedenti...", key=f"{prefix}_interventi")
    anamnesi_farmacologica = st.text_area("Anamnesi Farmacologica (Terapia in corso)", placeholder="Farmaci assunti abitualmente...", key=f"{prefix}_farmacologica")
        
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
        "anamnesi_farmacologica": anamnesi_farmacologica
    }

def formatta_anamnesi_per_pdf(anamnesi):
    """Genera una stringa pulita ed ordinata contenente SOLO i campi anamnestici flaggati o compilati, senza spazi vuoti."""
    linee = []
    
    patologie = []
    if anamnesi.get("ipertensione"): patologie.append("Ipertensione Arteriosa")
    if anamnesi.get("cardiopatia"): patologie.append("Cardiopatia / Ischemia")
    if anamnesi.get("diabete") and anamnesi.get("diabete") != "No": patologie.append(f"Diabete: {anamnesi['diabete']}")
    if anamnesi.get("insuff_renale"): 
        crea = anamnesi.get('creatinina', '').strip()
        patologie.append(f"Insufficienza Renale Cronica" + (f" (Creatinina: {crea} mg/dL)" if crea else ""))
        
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
    """Funzione di generazione PDF di base integrata."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Intestazione
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Decision Support System - Referto Clinico")
    
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, f"Data: {dati_visita.get('data')}")
    c.drawString(50, height - 85, f"Paziente: {cognome} {nome} (ID: {codice_paziente})")
    c.drawString(50, height - 100, f"Tipologia: {dati_visita.get('tipo')}")
    
    c.line(50, height - 110, width - 50, height - 110)
    
    # Contenuti Dettagli / Anamnesi
    y = height - 130
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Dettagli Clinici e Anamnesi:")
    y -= 20
    
    c.setFont("Helvetica", 10)
    dettagli_testo = dati_visita.get('dettagli', '')
    for line in dettagli_testo.split('\n'):
        if y < 100:
            c.showPage()
            y = height - 50
        c.drawString(60, y, line)
        y -= 15
        
    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Percorso Clinico Impostato:")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(60, y, f"• {percorso}")
    y -= 25
    
    if note_raccomandazioni:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Raccomandazioni e Note:")
        y -= 20
        c.setFont("Helvetica", 10)
        for rec in note_raccomandazioni:
            if y < 100:
                c.showPage()
                y = height - 50
            c.drawString(60, y, f"- {rec}")
            y -= 15
            
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
