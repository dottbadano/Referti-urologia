from datetime import datetime
import streamlit as st

def calcola_indice_charlson_dettagliato(combilist):
    """
    Calcola l'indice di comorbilità di Charlson pesato in base alle patologie selezionate.
    """
    punteggio = 0
    pesi = {
        "Infarto miocardico acuto / Pregresso": 1,
        "Scompenso cardiaco congestizio": 1,
        "Vasculopatia periferica": 1,
        "Malattia cerebrovascolare (ictus / TIA)": 1,
        "Demenza": 1,
        "Malattia polmonare cronica (BPCO)": 1,
        "Connettivopatia / Malattia reumatologica": 1,
        "Ulcera peptica": 1,
        "Malattia epatica lieve": 1,
        "Diabete mellito (senza danno d'organo)": 1,
        "Emiplegia / Paraplegia": 2,
        "Malattia renale moderata o severa": 2,
        "Diabete mellito con danno d'organo": 2,
        "Tumore solido localizzato": 2,
        essa_leucemia_linfoma: 2, # Gestito dinamicamente se presente
        "Malattia epatica moderata o severa": 3,
        "Tumore solido metastatico": 6,
        "AIDS / HIV conclamato": 6
    }
    
    for patologia in combilist:
        # Assegnazione peso dinamico o standard
        if "Leucemia" in patologia or "Linfoma" in patologia:
            punteggio += 2
        else:
            punteggio += pesi.get(patologia, 1)
            
    return punteggio

def calcola_screening_g8(eta, app_to_eat, perdita_peso, mobilita, neuropsichico, bmi_val):
    """
    Calcola il punteggio G8 per lo screening geriatrico (range 0-17).
    """
    score = 0
    
    # 1. Riduzione dell'assunzione di cibo negli ultimi 3 mesi
    score += app_to_eat
    
    # 2. Perdita di peso recente (< 3 mesi)
    score += perdita_peso
    
    # 3. Mobilità
    score += mobilita
    
    # 4. Problemi neuropsicologici
    score += neuropsichico
    
    # 5. Indice di Massa Corporea (BMI)
    score += bmi_val
    
    # 6. Assunzione di più di 3 farmaci al giorno (valutato esternamente o di default)
    # 7. Età del paziente
    if eta < 80:
        score += 3
    elif 80 <= eta <= 85:
        score += 2
    else:
        score += 1
        
    return score

def render_anagrafica_e_anamnesi_unificata(sigla_organo="P", prefix="comune"):
    """
    Modulo unificato ottimizzato per Anagrafica, Anamnesi Patologica Remota, 
    Comorbilità (Charlson) e Screening Oncogeriatrico (G8).
     racchiuso in un'unica interfaccia pulita e strutturata.
    """
    st.subheader("Anagrafica e Identificazione Paziente")
    
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        cognome = st.text_input("Cognome", key=f"{prefix}_cognome")
    with col_a2:
        nome = st.text_input("Nome", key=f"{prefix}_nome")
    with col_a3:
        data_nascita = st.date_input(
            "Data di Nascita", 
            value=datetime(1955, 1, 1).date(), 
            min_value=datetime(1900, 1, 1).date(),
            max_value=datetime.today().date(),
            key=f"{prefix}_datanascita"
        )

    col_a4, col_a5 = st.columns(2)
    with col_a4:
        codice_fiscale = st.text_input("Codice Fiscale / ID Univoco", key=f"{prefix}_codice").strip().upper()
    with col_a5:
        recapito_tel = st.text_input("Recapito Telefonico", key=f"{prefix}_tel")

    st.markdown("---")
    st.subheader("Anamnesi Patologica Remota (APR) & Comorbilità")
    
    combilist_possibili = [
        "Infarto miocardico acuto / Pregresso",
        "Scompenso cardiaco congestizio",
        "Vasculopatia periferica",
        "Malattia cerebrovascolare (ictus / TIA)",
        "Demenza",
        "Malattia polmonare cronica (BPCO)",
        "Connettivopatia / Malattia reumatologica",
        "Ulcera peptica",
        "Malattia epatica lieve",
        "Diabete mellito (senza danno d'organo)",
        "Emiplegia / Paraplegia",
        "Malattia renale moderata o severa",
        "Diabete mellito con danno d'organo",
        "Tumore solido localizzato",
        "Leucemia o Linfoma",
        "Malattia epatica moderata o severa",
        "Tumore solido metastatico",
        "AIDS / HIV conclamato"
    ]
    
    combilist_selezionate = st.multiselect(
        "Seleziona patologie pregresse/concomitanti (per calcolo automatico Charlson Index):",
        combilist_possibili,
        key=f"{prefix}_combilist"
    )
    
    charlson_score = calcola_indice_charlson_dettagliato(combilist_selezionate)
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.info(f"**Indice di Charlson Calcolato:** {charlson_score}")
    with col_c2:
        fumo = st.selectbox("Anamnesi Tabagica:", ["Non Fumatore", "Ex Fumatore", "Fumatore Attivo"], key=f"{prefix}_fumo")

    st.markdown("---")
    st.subheader("Screening Oncogeriatrico (G8 & Parametri Funzionali)")
    
    eta_corrente = (datetime.today().date() - data_nascita).days // 365
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        app_to_eat = st.selectbox(
            "1. Riduzione assunzione cibo ultimi 3 mesi:",
            [
                (0, "Ha mangiato molto meno"),
                (1, "Ha mangiato un po' meno"),
                (2, "Ha mangiato normalmente")
            ],
            format_func=lambda x: x[1],
            key=f"{prefix}_g8_1"
        )[0]
        
        perdita_peso = st.selectbox(
            "2. Perdita di peso recente (< 3 mesi):",
            [
                (0, "Perdita > 3 kg"),
                (1, "Non sa"),
                (2, "Perdita tra 1 e 3 kg"),
                (3, "Nessuna perdita di peso")
            ],
            format_func=lambda x: x[1],
            key=f"{prefix}_g8_2"
        )[0]
        
        mobilita = st.selectbox(
            "3. Mobilità:",
            [
                (0, "Costretto a letto o in poltrona"),
                (1, "Capace di uscire ma non autosufficiente"),
                (2, "Autosufficiente nei movimenti")
            ],
            format_func=lambda x: x[1],
            key=f"{prefix}_g8_3"
        )[0]

    with col_g2:
        neuropsichico = st.selectbox(
            "4. Problemi neuropsicologici:",
            [
                (0, "Demenza o depressione severa"),
                (1, "Demenza o depressione lieve"),
                (2, "Nessun problema psicologico")
            ],
            format_func=lambda x: x[1],
            key=f"{prefix}_g8_4"
        )[0]
        
        bmi_scelta = st.selectbox(
            "5. Indice di Massa Corporea (BMI):",
            [
                (0, "BMI < 19"),
                (1, "19 <= BMI < 21"),
                (2, "21 <= BMI < 23"),
                (3, "BMI >= 23")
            ],
            format_func=lambda x: x[1],
            key=f"{prefix}_g8_5"
        )[0]

    totale_g8 = calcola_screening_g8(eta_corrente, app_to_eat, perdita_peso, mobilita, neuropsichico, bmi_scelta)
    
    st.markdown(f"### Punteggio G8 Totale: **{totale_g8} / 17**")
    if totale_g8 <= 14:
        st.warning("Screening G8 ≤ 14: Paziente a rischio geriatrico. Si raccomanda valutazione multidimensionale approfondita.")
    else:
        st.success("Screening G8 > 14: Profilo geriatrico favorevole.")

    return {
        "nome": nome,
        "cognome": cognome,
        "data_nascita": str(data_nascita),
        "id_univoco": codice_fiscale if codice_fiscale else f"{cognome.upper()}_{data_nascita.strftime('%Y%m%d')}",
        "telefono": recapito_tel,
        "charlson_score": charlson_score,
        "combilist": combilist_selezionate,
        "fumo": fumo,
        "g8_score": totale_g8
    }

def formatta_anamnesi_per_pdf_unificata(paziente_info):
    """
    Formatta l'anamnesi e i punteggi geriatrico-comorbidi in stringhe pulite pronte per la generazione del PDF.
    """
    comb_str = ", ".join(paziente_info.get("combilist", [])) if paziente_info.get("combilist") else "Nessuna comorbilità maggiore segnalata"
    
    testo = (
        f"Anagrafica: {paziente_info.get('cognome', '')} {paziente_info.get('nome', '')} "
        f"(Nato il: {paziente_info.get('data_nascita', '')}) - ID: {paziente_info.get('id_univoco', '')}\n"
        f"Recapito: {paziente_info.get('telefono', 'Non specificato')}\n"
        f"Anamnesi Patologica Remota & Comorbilità: {comb_str}\n"
        f"Indice di Comorbilità di Charlson: {paziente_info.get('charlson_score', 0)}\n"
        f"Anamnesi Tabagica: {paziente_info.get('fumo', 'Non specificato')}\n"
        f"Screening Oncogeriatrico G8: {paziente_info.get('g8_score', 0)} / 17"
    )
    return testo
