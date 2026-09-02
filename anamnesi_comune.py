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
    Modulo unificato con inclusione del Charlson Comorbidity Index dopo la valutazione geriatrica.
    """
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

    # Calcolo automatico BMI e Età
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
        g8_1_opt = st.selectbox("1. Riduzione assunzione di cibo negli ultimi 3 mesi?", [("0 - Grave diminuzione", 0), ("1 - Moderata diminuzione", 1), ("2 - Nessuna diminuzione", 2)], format_func=lambda x: x[0], key=f"{prefix}_g8_1")[1]
        g8_2_opt = st.selectbox("2. Perdita di peso recente:", [("0 - > 3 kg", 0), ("1 - Non sa", 1), ("2 - Tra 1 e 3 kg", 2), ("3 - Nessuna", 3)], format_func=lambda x: x[0], key=f"{prefix}_g8_2")[1]
        g8_3_opt = st.selectbox("3. Mobilità:", [("0 - A letto/sedia", 0), ("1 - Esce ma limitato", 1), ("2 - Normale", 2)], format_func=lambda x: x[0], key=f"{prefix}_g8_3")[1]
        g8_4_opt = st.selectbox("4. Malattia acuta o stress psicologico recente?", [("0 - Sì", 0), ("2 - No", 2)], format_func=lambda x: x[0], key=f"{prefix}_g8_4")[1]
        g8_5_opt = st.selectbox("5. Problemi neuropsicologici:", [("0 - Demenza/Depressione grave", 0), ("1 - Demenza lieve", 1), ("2 - Nessuno", 2)], format_func=lambda x: x[0], key=f"{prefix}_g8_5")[1]
        g8_6_opt = st.selectbox("6. BMI:", [("0 - < 19", 0), ("1 - 19-21", 1), ("2 - 21-23", 2), ("3 - > 23", 3)], format_func=lambda x: x[0], key=f"{prefix}_g8_6")[1]
        g8_7_opt = st.selectbox("7. Assume più di 3 farmaci al giorno?", [("0 - Sì", 0), ("1 - No", 1)], format_func=lambda x: x[0], key=f"{prefix}_g8_7")[1]
        g8_8_opt = st.selectbox("8. Stato di salute percepito rispetto ai coetanei:", [("0 - Peggiore", 0), ("0.5 - Non sa", 0.5), ("1 - Uguale", 1), ("2 - Migliore", 2)], format_func=lambda x: x[0], key=f"{prefix}_g8_8")[1]

    g8_score = g8_1_opt + g8_2_opt + g8_3_opt + g8_4_opt + g8_5_opt + g8_6_opt + g8_7_opt + g8_8_opt
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
        valore_mmse = ""
        if esegue_mmse:
            valore_mmse = st.text_input("Punteggio MMSE (es. 28/30)", key=f"{prefix}_valore_mmse")

    st.markdown("---")
    st.markdown("### 📊 Charlson Comorbidity Index (CCI)")
    with st.expander("Seleziona comorbilità attive per calcolo Charlson", expanded=False):
        c_infarto = st.checkbox("Infarto miocardico pregresso (+1)", key=f"{prefix}_c_infarto")
        c_ scompenso = st.checkbox("Scompenso cardiaco congestizio (+1)", key=f"{prefix}_c_scompenso")
        c_vascolare = st.checkbox("Malattia vascolare periferica (+1)", key=f"{prefix}_c_vascolare")
        c_ cerebrovascolare = st.checkbox("Malattia cerebrovascolare / TIA (+1)", key=f"{prefix}_c_cerebrovascolare")
        c_demenza = st.checkbox("Demenza (+1)", key=f"{prefix}_c_demenza")
        c_bpco = st.checkbox("Malattia polmonare cronica (BPCO) (+1)", key=f"{prefix}_c_bpco")
        c_connettivite = st.checkbox("Malattia del tessuto connettivo / Reumatologica (+1)", key=f"{prefix}_c_connettivite")
        c_ ulcera = st.checkbox("Ulcera peptica (+1)", key=f"{prefix}_c_ulcera")
        c_fegato_l = st.checkbox("Malattia epatica lieve (+1)", key=f"{prefix}_c_fegato_l")
        c_diabete = st.checkbox("Diabete mellito (senza danno d'organo +1 / con danno d'organo +2)", key=f"{prefix}_c_diabete")
        c_emiplegia = st.checkbox("Emiplegia o paraplegia (+2)", key=f"{prefix}_c_emiplegia")
        c_renale = st.checkbox("Malattia renale cronica moderata-severa (+2)", key=f"{prefix}_c_renale")
        c_tumore = st.checkbox("Tumore solido localizzato (+2)", key=f"{prefix}_c_tumore")
        c_leucemia = st.checkbox("Leucemia o Linfoma (+2)", key=f"{prefix}_c_leucemia")
        c_fegato_g = st.checkbox("Malattia epatica moderata-severa (+3)", key=f"{prefix}_c_fegato_g")
        c_metastasi = st.checkbox("Tumore solido metastatico / Malattia disseminata (+6)", key=f"{prefix}_c_metastasi")
        c_aids = st.checkbox("AIDS / HIV conclamato (+6)", key=f"{prefix}_c_aids")

    # Calcolo base Charlson (pesi clinici standard)
    base_charlson = 0
    if c_infarto: base_charlson += 1
    if c_scompenso: base_charlson += 1
    if c_vascolare: base_charlson += 1
    if c_cerebrovascolare: base_charlson += 1
    if c_demenza: base_charlson += 1
    if c_bpco: base_charlson += 1
    if c_connettivite: base_charlson += 1
    if c_ulcera: base_charlson += 1
    if c_fegato_l: base_charlson += 1
    if c_diabete: base_charlson += 1 # standard base 1, aggiustabile se serve
    if c_emiplegia: base_charlson += 2
    if c_renale: base_charlson += 2
    if c_tumore: base_charlson += 2
    if c_leucemia: base_charlson += 2
    if c_fegato_g: base_charlson += 3
    if c_metastasi: base_charlson += 6
    if c_aids: base_charlson += 6

    # Aggiustamento età per Charlson (1 punto ogni decennio sopra i 50 anni)
    bonus_eta_charlson = 0
    if eta >= 50 and eta < 60: bonus_eta_charlson = 1
    elif eta >= 60 and eta < 70: bonus_eta_charlson = 2
    elif eta >= 70 and eta < 80: bonus_eta_charlson = 3
    elif eta >= 80: bonus_eta_charlson = 4

    charlson_totale = base_charlson + bonus_eta_charlson
    st.info(f"📈 **Charlson Comorbidity Index (Corretto per Età):** `{charlson_totale}` (Comorbilità: {base_charlson} + Età: {bonus_eta_charlson})")

    st.markdown("---")
    st.markdown("### 💊 Allergie, Tabagismo & Funzionalità Renale")
    ha_allergie = st.checkbox("Il paziente presenta allergie note", key=f"{prefix}_ha_allergie")
    specifica_allergie = ""
    if ha_allergie:
        specifica_allergie = st.text_input("Specificare allergie (es. farmaci, lattice, mdc)", key=f"{prefix}_specifica_allergie")

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        tabagismo = st.selectbox(
            "Tabagismo:",
            ["Non fumatore", "Ex fumatore", "Fumatore attivo"],
            key=f"{prefix}_tabagismo"
        )
        sig_die = 0
        if tabagismo == "Fumatore attivo":
            sig_die = st.number_input("Numero sigarette / die", min_value=1, max_value=100, value=10, step=1, key=f"{prefix}_sig_die")

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

    st.write("Profilo Genetico / Mutazionale:")
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        f_hrd = st.checkbox("HRD (Homologous Recombination Deficiency)", key=f"{prefix}_f_hrd")
    with col_m2:
        f_brca = st.checkbox("BRCA Mutation (1/2)", key=f"{prefix}_f_brca")
    with col_m3:
        f_lynch = st.checkbox("Sindrome di Lynch / MSI", key=f"{prefix}_f_lynch")

    st.markdown("---")
    st.markdown("### 📝 Anamnesi Chirurgica & Farmacologica")
    interventi = st.text_area("Anamnesi Chirurgica", key=f"{prefix}_interventi")
    farmacologica = st.text_area("Anamnesi Farmacologica", key=f"{prefix}_farmacologica")

    famiglie_attive = []
    if f_pros: famiglie_attive.append("Prostata")
    if f_seno: famiglie_attive.append("Seno")
    if f_panc: famiglie_attive.append("Pancreas")
    if f_feg: famiglie_attive.append("Fegato")
    if f_uter: famiglie_attive.append("Utero/Endometrio")
    if f_test: famiglie_attive.append("Testicolo")
    if f_polm: famiglie_attive.append("Polmone")
    if f_colo: famiglie_attive.append("Colon-Retto")

    genetica_attiva = []
    if f_hrd: genetica_attiva.append("HRD Positivo")
    if f_brca: genetica_attiva.append("BRCA Mutated")
    if f_lynch: genetica_attiva.append("Sindrome di Lynch / MSI")

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
