from datetime import datetime
import random
import string
import streamlit as st

def genera_codice_univoco_organo(nome, cognome, organo_lettera="P"):
    """
    Genera codice univoco: 1ª nome, 2ª cognome, 1ª cognome, 2ª nome + 6 numeri + 1ª lettera organo.
    """
    n = nome.strip()
    c = cognome.strip()
    if len(n) < 2 or len(c) < 2:
        return ""
    
    l1_nom = n[0].upper()
    l2_cog = c[1].upper()
    l1_cog = c[0].upper()
    l2_nom = n[1].upper()
    
    rand_num = "".join(random.choices(string.digits, k=6))
    org = organo_lettera.upper()[:1]
    
    return f"{l1_nom}{l2_cog}{l1_cog}{l2_nom}-{rand_num}-{org}"

def render_anagrafica_e_anamnesi_unificata(sigla_organo="P", prefix="gen"):
    """
    Modulo unificato per Anagrafica, ID automatico, Charlson pesato per età,
    Allergie, G8, ADL, IADL, ECOG, Mini-Mental, Familiarità ed Anamnesi Chirurgica/Farmacologica.
    """
    st.markdown("### 📋 Anagrafica & Profilo Globale del Paziente")
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        nome = st.text_input("Nome Paziente", key=f"input_nome_{prefix}")
    with col_b:
        cognome = st.text_input("Cognome Paziente", key=f"input_cognome_{prefix}")
    
    # Generazione automatica ID in sessione
    id_key = f"id_generato_{prefix}"
    if id_key not in st.session_state:
        st.session_state[id_key] = ""
        
    if nome and cognome:
        st.session_state[id_key] = genera_codice_univoco_organo(nome, cognome, sigla_organo)

    with col_c:
        codice_paziente = st.text_input("Codice Univoco / ID (Autogenerato)", value=st.session_state[id_key], key=f"input_id_{prefix}")

    data_nascita = st.date_input("Data di Nascita", datetime(1960, 1, 1), key=f"input_nascita_{prefix}")
    
    # Calcolo automatico età
    oggi = datetime.today().date()
    eta = oggi.year - data_nascita.year - ((oggi.month, oggi.day) < (data_nascita.month, data_nascita.day))

    st.markdown("---")
    st.markdown("### 🏥 Comorbilità (Charlson Comorbidity Index)")
    
    with st.expander("Seleziona Patologie del Charlson Index", expanded=False):
        c1 = st.checkbox("Infarto miocardico pregresso (+1)", key=f"{prefix}_c_infarto")
        c2 = st.checkbox("Scompenso cardiaco congestizio (+1)", key=f"{prefix}_c_scompenso")
        c3 = st.checkbox("Malattia vascolare periferica (+1)", key=f"{prefix}_c_vascolare")
        c4 = st.checkbox("Malattia cerebrovascolare / TIA (+1)", key=f"{prefix}_c_cerebro")
        c5 = st.checkbox("Demenza (+1)", key=f"{prefix}_c_demenza")
        c6 = st.checkbox("Malattia polmonare cronica - BPCO (+1)", key=f"{prefix}_c_bpco")
        c7 = st.checkbox("Connettivopatia / Malattia reumatologica (+1)", key=f"{prefix}_c_connettivo")
        c8 = st.checkbox("Ulcera peptica (+1)", key=f"{prefix}_c_ulcera")
        c9 = st.checkbox("Epatopatia cronica lieve (+1)", key=f"{prefix}_c_epatica_lieve")
        c10 = st.checkbox("Diabete mellito senza danno d'organo (+1)", key=f"{prefix}_c_diabete_s")
        c11 = st.checkbox("Emiplegia o paraplegia (+2)", key=f"{prefix}_c_emiplegia")
        c12 = st.checkbox("Insufficienza renale da moderata a severa (+2)", key=f"{prefix}_c_renale")
        c13 = st.checkbox("Diabete mellito con danno d'organo (+2)", key=f"{prefix}_c_diabete_d")
        c14 = st.checkbox("Tumore solido localizzato (+2)", key=f"{prefix}_c_tumore_loc")
        c15 = st.checkbox("Leucemia o linfoma (+2)", key=f"{prefix}_c_emopatia")
        c16 = st.checkbox("Epatopatia cronica media o severa (+3)", key=f"{prefix}_c_epatica_sev")
        c17 = st.checkbox("Tumore solido metastatico (+6)", key=f"{prefix}_c_metastatico")
        c18 = st.checkbox("AIDS / HIV conclamato (+6)", key=f"{prefix}_c_aids")

    # Somma punti comorbilità base
    punti_charlson = (
        (1 if c1 else 0) + (1 if c2 else 0) + (1 if c3 else 0) + (1 if c4 else 0) +
        (1 if c5 else 0) + (1 if c6 else 0) + (1 if c7 else 0) + (1 if c8 else 0) +
        (1 if c9 else 0) + (1 if c10 else 0) + (2 if c11 else 0) + (2 if c12 else 0) +
        (2 if c13 else 0) + (2 if c14 else 0) + (2 if c15 else 0) + (3 if c16 else 0) +
        (6 if c17 else 0) + (6 if c18 else 0)
    )

    # Correzione età Charlson (+1 ogni decennio dai 50 anni)
    correzione_eta = 0
    if 50 <= eta < 60: correzione_eta = 1
    elif 60 <= eta < 70: correzione_eta = 2
    elif 70 <= eta < 80: correzione_eta = 3
    elif eta >= 80: correzione_eta = 4

    cci_totale = punti_charlson + correzione_eta
    st.info(f"📊 **Età Anagrafica:** {eta} anni | **Charlson Comorbidity Index (Corretto per Età):** `{cci_totale}`")

    st.markdown("---")
    st.markdown("### 💊 Allergie")
    ha_allergie = st.checkbox("Il paziente presenta allergie note", key=f"{prefix}_ha_allergie")
    specifica_allergie = ""
    if ha_allergie:
        specifica_allergie = st.text_input("Specificare allergie (es. farmaci, lattice, mezzi di contrasto)", key=f"{prefix}_specifica_allergie")

    st.markdown("---")
    st.markdown("### 🏃‍♂️ Riserva Biologica & Autonomia Funzionale (G8, ADL, IADL, ECOG)")
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        ecog = st.selectbox(
            "ECOG Performance Status:",
            [
                "0 - Pienamente attivo e autonomo",
                "1 - Sintomatico ma ambulante",
                "2 - Allettato <50% del giorno",
                "3 - Allettato >50% del giorno",
                "4 - Completamente allettato e dipendente"
            ],
            key=f"{prefix}_ecog"
        )
        adl = st.selectbox(
            "Scala ADL (Activities of Daily Living):",
            ["Non valutato", "Indipendente (6/6)", "Parzialmente dipendente (3-5/6)", "Fortemente dipendente (0-2/6)"],
            key=f"{prefix}_adl"
        )
    with col_r2:
        iadl = st.selectbox(
            "Scala IADL (Instrumental Activities of Daily Living):",
            ["Non valutato", "Indipendente (8/8)", "Parzialmente dipendente (4-7/8)", "Fortemente dipendente (0-3/8)"],
            key=f"{prefix}_iadl"
        )
        # G8 rapido integrato
        g8_score = st.slider("Punteggio Screening G8 (Geriatric 8 / max 17):", 0, 17, 15, key=f"{prefix}_g8")

    st.markdown("---")
    st.markdown("### 🧠 Valutazione Cognitiva (Opzionale)")
    esegue_mmse = st.checkbox("Eseguito Mini-Mental State Examination (MMSE)", key=f"{prefix}_check_mmse")
    valore_mmse = ""
    if esegue_mmse:
        valore_mmse = st.text_input("Punteggio MMSE (es. 28/30)", key=f"{prefix}_valore_mmse")

    st.markdown("---")
    st.markdown("### 🧬 Familiarità Oncologica (Multi-organo)")
    st.write("Selezionare gli organi con presenza di familiarità neoplastica:")
    
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        f_pros = st.checkbox("Prostata", key=f"{prefix}_f_pros")
        f_seno = st.checkbox("Seno", key=f"{prefix}_f_seno")
    with col_f2:
        f_panc = st.checkbox("Pancreas", key=f"{prefix}_f_panc")
        f_feg = st.checkbox("Fegato", key=f"{prefix}_f_feg")
    with col_f3:
        f_uter = st.checkbox("Utero / Endometrio", key=f"{prefix}_f_uter")
        f_test = st.checkbox("Testicolo", key=f"{prefix}_f_test")
    with col_f4:
        f_polm = st.checkbox("Polmone", key=f"{prefix}_f_polm")
        f_colo = st.checkbox("Colon-Retto", key=f"{prefix}_f_colo")

    st.markdown("---")
    st.markdown("### 📝 Anamnesi Chirurgica & Farmacologica")
    interventi = st.text_area("Anamnesi Chirurgica (Interventi passati)", key=f"{prefix}_interventi")
    farmacologica = st.text_area("Anamnesi Farmacologica (Terapie domiciliari in corso)", key=f"{prefix}_farmacologica")

    # Raccolta liste per stampa condizionale
    famiglie_attive = []
    if f_pros: famiglie_attive.append("Prostata")
    if f_seno: famiglie_attive.append("Seno")
    if f_panc: famiglie_attive.append("Pancreas")
    if f_feg: famiglie_attive.append("Fegato")
    if f_uter: famiglie_attive.append("Utero/Endometrio")
    if f_test: famiglie_attive.append("Testicolo")
    if f_polm: famiglie_attive.append("Polmone")
    if f_colo: famiglie_attive.append("Colon-Retto")

    comorb_attive = []
    if c1: comorb_attive.append("Infarto miocardico pregresso")
    if c2: comorb_attive.append("Scompenso cardiaco")
    if c3: comorb_attive.append("Malattia vascolare periferica")
    if c4: comorb_attive.append("Malattia cerebrovascolare")
    if c5: comorb_attive.append("Demenza")
    if c6: comorb_attive.append("BPCO")
    if c7: comorb_attive.append("Connettivopatia")
    if c8: comorb_attive.append("Ulcera peptica")
    if c9: comorb_attive.append("Epatopatia lieve")
    if c10: comorb_attive.append("Diabete senza danno d'organo")
    if c11: comorb_attive.append("Emiplegia/Paraplegia")
    if c12: comorb_attive.append("Insufficienza renale mod/sev")
    if c13: comorb_attive.append("Diabete con danno d'organo")
    if c14: comorb_attive.append("Tumore solido localizzato")
    if c15: comorb_attive.append("Leucemia/Linfoma")
    if c16: comorb_attive.append("Epatopatia media/sev")
    if c17: comorb_attive.append("Tumore metastatico")
    if c18: comorb_attive.append("AIDS")

    return {
        "nome": nome.strip(),
        "cognome": cognome.strip(),
        "id_univoco": codice_paziente.strip(),
        "data_nascita": str(data_nascita),
        "eta": eta,
        "charlson_score": cci_totale,
        "comorbidita_elenco": comorb_attive,
        "ha_allergie": ha_allergie,
        "specifica_allergie": specifica_allergie.strip(),
        "ecog": ecog,
        "adl": adl,
        "iadl": iadl,
        "g8_score": g8_score,
        "mmse_eseguito": esegue_mmse,
        "mmse_valore": valore_mmse.strip(),
        "familiarita": famiglie_attive,
        "interventi": interventi.strip(),
        "farmacologica": farmacologica.strip()
    }

def formatta_anamnesi_per_pdf_unificata(dati):
    """
    Formatta l'anamnesi stampando ESCLUSIVAMENTE i campi compilati o flaggati.
    """
    linee = []
    
    if dati.get("comorbidita_elenco"):
        linee.append(f"• Comorbilità (Charlson Score: {dati.get('charlson_score')}): {', '.join(dati['comorbidita_elenco'])}")
        
    if dati.get("ha_allergie") and dati.get("specifica_allergie"):
        linee.append(f"• Allergie: {dati['specifica_allergie']}")
    elif dati.get("ha_allergie"):
        linee.append("• Allergie: Presenti (Non specificate)")
        
    if dati.get("ecog") and "Non valutato" not in dati.get("ecog", ""):
        linee.append(f"• Performance Status (ECOG): {dati['ecog']}")
        
    if dati.get("g8_score") is not None:
        linee.append(f"• Screening G8 (Riserva Biologica): {dati['g8_score']}/17")
        
    if dati.get("adl") and "Non valutato" not in dati.get("adl", ""):
        linee.append(f"• Scala ADL: {dati['adl']}")
        
    if dati.get("iadl") and "Non valutato" not in dati.get("iadl", ""):
        linee.append(f"• Scala IADL: {dati['iadl']}")
        
    if dati.get("mmse_eseguito") and dati.get("mmse_valore"):
        linee.append(f"• Test Cognitivo MMSE: {dati['mmse_valore']}")
        
    if dati.get("familiarita"):
        linee.append(f"• Familiarità Oncologica: {', '.join(dati['familiarita'])}")
        
    if dati.get("interventi"):
        linee.append(f"• Anamnesi Chirurgica: {dati['interventi']}")
        
    if dati.get("farmacologica"):
        linee.append(f"• Anamnesi Farmacologica: {dati['farmacologica']}")
        
    return "\n".join(linee) if linee else ""
