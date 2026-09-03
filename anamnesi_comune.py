from datetime import datetime
import random
import string
import streamlit as st

def genera_codice_univoco_organo(nome, cognome, organo_lettera="P"):
    n = nome.strip()
    c = cognome.strip()
    if len(n) < 2 or len(c) < 2:
        return ""
    
    return f"{n[0].upper()}{c[1].upper()}{c[0].upper()}{n[1].upper()}-{''.join(random.choices(string.digits, k=6))}-{organo_lettera.upper()[:1]}"

def stima_aspettativa_di_vita(eta, charlson_score, g8_score, ecog_str):
    """
    Calcola l'aspettativa di vita ponderando comorbilità (Charlson), 
    stato geriatrico (G8) e performance fisica (ECOG).
    """
    bonus_fitness = 0
    
    if "0" in ecog_str or "1" in ecog_str:
        bonus_fitness += 2
        
    if g8_score >= 14:
        bonus_fitness += 2
    elif g8_score >= 11:
        bonus_fitness += 1

    charlson_ponderato = max(0, charlson_score - bonus_fitness)
    
    aspettativa_maggiore_di_10 = True
    
    if eta >= 80 and charlson_ponderato >= 5:
        aspettativa_maggiore_di_10 = False
    elif charlson_ponderato >= 6 and g8_score < 11:
        aspettativa_maggiore_di_10 = False

    return aspettativa_maggiore_di_10, charlson_ponderato

def render_anagrafica_e_anamnesi_unificata(sigla_organo="P", prefix="gen"):
    st.markdown("### 📋 Anagrafica & Identificazione")
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        nome = st.text_input("Nome Paziente", key=f"input_nome_{prefix}")
    with col_b:
        cognome = st.text_input("Cognome Paziente", key=f"input_cognome_{prefix}")
    
    id_key = f"input_id_{prefix}"
    if id_key not in st.session_state:
        st.session_state[id_key] = ""
        
    nuovo_id = genera_codice_univoco_organo(nome, cognome, sigla_organo)
    if nuovo_id:
        st.session_state[id_key] = nuovo_id

    with col_c:
        codice_paziente = st.text_input("Codice Univoco / ID (Autogenerato)", key=id_key)

    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        data_nascita = st.date_input("Data di Nascita", datetime(1960, 1, 1), key=f"input_nascita_{prefix}")
    with col_d2:
        peso = st.number_input("Peso (kg)", min_value=30.0, max_value=250.0, value=75.0, step=0.5, key=f"input_peso_{prefix}")
    with col_d3:
        altezza = st.number_input("Altezza (cm)", min_value=100.0, max_value=250.0, value=175.0, step=1.0, key=f"input_altezza_{prefix}")

    altezza_m = altezza / 100.0
    bmi_valore = round(peso / (altezza_m ** 2), 1) if altezza_m > 0 else 0.0
    oggi = datetime.today().date()
    eta = oggi.year - data_nascita.year - ((oggi.month, oggi.day) < (data_nascita.month, data_nascita.day))
    
    st.info(f"📊 **Età Anagrafica:** {eta} anni | ⚖️ **BMI:** `{bmi_valore}`")

    st.markdown("---")
    st.markdown("### 🏃‍♂️ Performance Status")
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
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        adl = st.selectbox(
            "Scala ADL (Activities of Daily Living):",
            ["Non valutato", "Indipendente (6/6)", "Parzialmente dipendente (3-5/6)", "Fortemente dipendente (0-2/6)"],
            key=f"{prefix}_adl"
        )
    with col_p2:
        iadl = st.selectbox(
            "Scala IADL (Instrumental Activities of Daily Living):",
            ["Non valutato", "Indipendente (8/8)", "Parzialmente dipendente (4-7/8)", "Fortemente dipendente (0-3/8)"],
            key=f"{prefix}_iadl"
        )

    st.markdown("---")
    st.markdown("### 🧠 Valutazione Geriatrica (G8, GDS, Mini-Mental)")
    
    with st.expander("Screening G8 (Valutazione a 8 voci)", expanded=False):
        g8_pesi = [
            [("0 - Grave diminuzione", 0), ("1 - Moderata diminuzione", 1), ("2 - Nessuna diminuzione", 2)],
            [("0 - > 3 kg", 0), ("1 - Non sa", 1), ("2 - Tra 1 e 3 kg", 2), ("3 - Nessuna", 3)],
            [("0 - A letto/sedia", 0), ("1 - Esce ma limitato", 1), ("2 - Normale", 2)],
            [("0 - Sì", 0), ("2 - No", 2)],
            [("0 - Demenza/Depressione grave", 0), ("1 - Demenza lieve", 1), ("2 - Nessuno", 2)],
            [("0 - < 19", 0), ("1 - 19-21", 1), ("2 - 21-23", 2), ("3 - > 23", 3)],
            [("0 - Sì", 0), ("1 - No", 1)],
            [("0 - Peggiore", 0), ("0.5 - Non sa", 0.5), ("1 - Uguale", 1), ("2 - Migliore", 2)]
        ]
        g8_labels = [
            "1. Riduzione assunzione di cibo negli ultimi 3 mesi?",
            "2. Perdita di peso recente:",
            "3. Mobilità:",
            "4. Malattia acuta o stress psicologico recente?",
            "5. Problemi neuropsicologici:",
            "6. BMI:",
            "7. Assume più di 3 farmaci al giorno?",
            "8. Stato di salute percepito rispetto ai coetanei:"
        ]
        g8_score = sum(
            st.selectbox(g8_labels[i], g8_pesi[i], format_func=lambda x: x[0], key=f"{prefix}_g8_{i+1}")[1]
            for i in range(8)
        )

    st.info(f"📌 **Punteggio Totale G8:** `{g8_score}/17`")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        gds = st.selectbox(
            "Geriatric Depression Scale (GDS):",
            ["Non valutato", "Negativa (Assente)", "Positiva (Sospetta depressione / lieve-moderata)"],
            key=f"{prefix}_gds"
        )
    with col_g2:
        esegue_mmse = st.checkbox("Eseguito Mini-Mental State Examination (MMSE)", key=f"{prefix}_check_mmse")
        valore_mmse = st.text_input("Punteggio MMSE (es. 28/30)", key=f"{prefix}_valore_mmse") if esegue_mmse else ""

    st.markdown("---")
    st.markdown("### 📊 Charlson Comorbidity Index (CCI)")
    
    charlson_items = [
        ("Infarto miocardico pregresso (+1)", 1, "c_infarto"),
        ("Scompenso cardiaco congestizio (+1)", 1, "c_scompenso"),
        ("Malattia vascolare periferica (+1)", 1, "c_vascolare"),
        ("Malattia cerebrovascolare / TIA (+1)", 1, "c_cerebrovascolare"),
        ("Demenza (+1)", 1, "c_demenza"),
        ("Malattia polmonare cronica (BPCO) (+1)", 1, "c_bpco"),
        ("Malattia del tessuto connettivo / Reumatologica (+1)", 1, "c_connettivite"),
        ("Ulcera peptica (+1)", 1, "c_ulcera"),
        ("Malattia epatica lieve (+1)", 1, "c_fegato_l"),
        ("Diabete mellito (+1)", 1, "c_diabete"),
        ("Emiplegia o paraplegia (+2)", 2, "c_emiplegia"),
        ("Malattia renale cronica moderata-severa (+2)", 2, "c_renale"),
        ("Tumore solido localizzato (+2)", 2, "c_tumore"),
        ("Leucemia o Linfoma (+2)", 2, "c_leucemia"),
        ("Malattia epatica moderata-severa (+3)", 3, "c_fegato_g"),
        ("Tumore solido metastatico / Malattia disseminata (+6)", 6, "c_metastasi"),
        ("AIDS / HIV conclamato (+6)", 6, "c_aids")
    ]

    with st.expander("Seleziona comorbilità attive per calcolo Charlson", expanded=False):
        base_charlson = sum(
            weight if st.checkbox(label, key=f"{prefix}_{key}") else 0
            for label, weight, key in charlson_items
        )

    bonus_eta_charlson = 4 if eta >= 80 else (3 if eta >= 70 else (2 if eta >= 60 else (1 if eta >= 50 else 0)))
    charlson_totale = base_charlson + bonus_eta_charlson
    
    # Calcolo dell'aspettativa di vita ponderata
    aspettativa_ok, charlson_ponderato = stima_aspettativa_di_vita(eta, charlson_totale, g8_score, ecog)
    
    st.info(f"📈 **Charlson Comorbidity Index (Corretto per Età):** `{charlson_totale}` (Ponderato su Fitness: `{charlson_ponderato}`)")

    st.markdown("---")
    st.markdown("### 💊 Allergie, Tabagismo & Funzionalità Renale")
    ha_allergie = st.checkbox("Il paziente presenta allergie note", key=f"{prefix}_ha_allergie")
    specifica_allergie = st.text_input("Specificare allergie (es. farmaci, lattice, mdc)", key=f"{prefix}_specifica_allergie") if ha_allergie else ""

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        tabagismo = st.selectbox(
            "Tabagismo:",
            ["Non fumatore", "Ex fumatore", "Fumatore attivo"],
            key=f"{prefix}_tabagismo"
        )
        sig_die = st.number_input("Numero sigarette / die", min_value=1, max_value=100, value=10, step=1, key=f"{prefix}_sig_die") if tabagismo == "Fumatore attivo" else 0

    with col_t2:
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            creatinina = st.number_input("Creatinina (mg/dL)", min_value=0.2, max_value=15.0, value=0.9, step=0.1, key=f"{prefix}_creatinina")
        with col_r2:
            egfr = st.number_input("eGFR (mL/min)", min_value=5, max_value=150, value=90, step=1, key=f"{prefix}_egfr")

    st.markdown("---")
    st.markdown("### 🤝 Caregiver & Rete di Supporto")
    caregiver_supporto = st.selectbox(
        "Rete di supporto e Caregiver:",
        ["Non valutato", "Autonomo (Senza caregiver)", "Caregiver familiare presente", "Caregiver strutturato / Assistenza domiciliare", "Supporto sociosanitario carente"],
        key=f"{prefix}_caregiver"
    )

    st.markdown("### 🧬 Anamnesi Oncologica & Genetica")
    st.write("Familiarità oncologica per organi:")
    
    organi_fam = [("Prostata", "f_pros"), ("Seno", "f_seno"), ("Pancreas", "f_panc"), ("Fegato", "f_feg"),
                  ("Utero / Endometrio", "f_uter"), ("Testicolo", "f_test"), ("Polmone", "f_polm"), ("Colon-Retto", "f_colo")]
    cols = st.columns(4)
    famiglie_attive = []
    for idx, (label, key) in enumerate(organi_fam):
        if cols[idx % 4].checkbox(label, key=f"{prefix}_{key}"):
            famiglie_attive.append(label)

    st.write("Profilo Genetico / Mutazionale:")
    genetica_opts = [("HRD (Homologous Recombination Deficiency)", "f_hrd", "HRD Positivo"),
                     ("BRCA Mutation (1/2)", "f_brca", "BRCA Mutated"),
                     ("Sindrome di Lynch / MSI", "f_lynch", "Sindrome di Lynch / MSI")]
    cols_m = st.columns(3)
    genetica_attiva = []
    for idx, (label, key, val_name) in enumerate(genetica_opts):
        if cols_m[idx].checkbox(label, key=f"{prefix}_{key}"):
            genetica_attiva.append(val_name)

    st.markdown("---")
    st.markdown("### 📝 Anamnesi Chirurgica & Farmacologica")
    interventi = st.text_area("Anamnesi Chirurgica", key=f"{prefix}_interventi")
    farmacologica = st.text_area("Anamnesi Farmacologica", key=f"{prefix}_farmacologica")

    return {
        "nome": nome.strip(),
        "cognome": cognome.strip(),
        "id_univoco": codice_paziente.strip(),
        "data_nascita": str(data_nascita),
        "eta": eta,
        "peso": peso,
        "altezza": altezza,
        "bmi": bmi_valore,
        "ecog": ecog,
        "adl": adl,
        "iadl": iadl,
        "g8_score": g8_score,
        "gds": gds,
        "mmse_eseguito": esegue_mmse,
        "mmse_valore": valore_mmse.strip(),
        "charlson_score": charlson_totale,
        "charlson_ponderato": charlson_ponderato,
        "aspettativa_vita_maggiore_10_anni": aspettativa_ok,
        "ha_allergie": ha_allergie,
        "specifica_allergie": specifica_allergie.strip(),
        "tabagismo": tabagismo,
        "sig_die": sig_die,
        "creatinina": creatinina,
        "egfr": egfr,
        "caregiver": caregiver_supporto,
        "familiarita": famiglie_attive,
        "genetica": genetica_attiva,
        "interventi": interventi.strip(),
        "farmacologica": farmacologica.strip()
    }

def formatta_anamnesi_per_pdf_unificata(paziente_info):
    righe = [
        f"• Età: {paziente_info.get('eta', 'N/D')} anni | Peso: {paziente_info.get('peso', 'N/D')} kg | Altezza: {paziente_info.get('altezza', 'N/D')} cm | BMI: {paziente_info.get('bmi', 'N/D')}",
        f"• Performance Status (ECOG): {paziente_info.get('ecog', 'N/D')}"
    ]
    
    if (adl := paziente_info.get('adl')) and adl != "Non valutato":
        righe.append(f"• ADL: {adl}")
    if (iadl := paziente_info.get('iadl')) and iadl != "Non valutato":
        righe.append(f"• IADL: {iadl}")
        
    righe.append(f"• Screening G8: {paziente_info.get('g8_score', 'N/D')}/17")
    
    if (gds := paziente_info.get('gds')) and gds != "Non valutato":
        righe.append(f"• GDS: {gds}")
    if paziente_info.get('mmse_eseguito') and (mmse_val := paziente_info.get('mmse_valore')):
        righe.append(f"• MMSE: {mmse_val}")
        
    righe.append(f"• Charlson Comorbidity Index (corretto): {paziente_info.get('charlson_score', 'N/D')} (Ponderato su Fitness: {paziente_info.get('charlson_ponderato', 'N/D')})")
    
    if paziente_info.get('ha_allergie') and (spec_all := paziente_info.get('specifica_allergie')):
        righe.append(f"• Allergie Note: {spec_all}")
    else:
        righe.append("• Allergie: Nessuna nota/riferita")
        
    tabagismo_str = paziente_info.get('tabagismo', 'Non fumatore')
    if tabagismo_str == "Fumatore attivo":
        tabagismo_str += f" ({paziente_info.get('sig_die', 0)} sigarette/die)"
    righe.append(f"• Tabagismo: {tabagismo_str}")
    
    righe.append(f"• Funzionalità Renale: Creatinina {paziente_info.get('creatinina', 'N/D')} mg/dL | eGFR {paziente_info.get('egfr', 'N/D')} mL/min")
    
    if (caregiver := paziente_info.get('caregiver')) and caregiver != "Non valutato":
        righe.append(f"• Rete di Supporto / Caregiver: {caregiver}")
        
    if fam := paziente_info.get('familiarita', []):
        righe.append(f"• Familiarità Oncologica: {', '.join(fam)}")
        
    if gen := paziente_info.get('genetica', []):
        righe.append(f"• Profilo Genetico / Mutazionale: {', '.join(gen)}")
        
    if interventi := paziente_info.get('interventi', ''):
        righe.append(f"• Anamnesi Chirurgica: {interventi}")
        
    if farmacologica := paziente_info.get('farmacologica', ''):
        righe.append(f"• Terapia Farmacologica Attuale: {farmacologica}")
        
    return "\n".join(righe)
