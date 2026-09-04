from datetime import datetime
import streamlit as st
from utils import genera_pdf_referto, salva_db_pazienti

def render_terapia_medica(paziente, db_attivo, codice_search):
    """Modulo dedicato alla gestione e follow-up della Terapia Medica (ormonale, ARSI, chemioterapia, PARPi, mCRPC e Bone Health) con supporto decisionale basato su stadiazione TNM, carico lesionale e comorbilità."""
    st.markdown("### 🟡 Protocollo di Terapia Medica Avanzata & Supporto Decisionale")
    st.info("Gestione della malattia avanzata, stratificazione del volume tumorale (Criteri CHAARTED/STAMPEDE da cTNM e lesioni ossee), analisi guidata delle comorbilità per la scelta dell'ARSI e prevenzione SRE.")
    
    # Visualizzazione dello Storico
    with st.expander("📂 Visualizza Storico Visite e Controlli Terapia Medica Precedenti", expanded=False):
        visite = paziente.get("visite", [])
        if not visite:
            st.write("Nessuna visita registrata nello storico.")
        for idx, v in enumerate(visite, 1):
            st.markdown(f"**Controllo {idx} — Data: {v.get('data')} | Tipo: {v.get('tipo')}**")
            st.text(v.get('dettagli', 'Nessun dettaglio'))
            st.markdown("---")

    st.markdown("---")
    st.markdown("### 🔄 Nuova Valutazione / Controllo Terapia Medica")

    with st.form(key="form_terapia_medica_aggiornato"):
        st.markdown("#### 🌍 Caratteristiche di Stadiazione (cTNM) e Carico Lesionale")
        
        col_tnm1, col_tnm2, col_tnm3 = st.columns(3)
        with col_tnm1:
            stad_t = st.selectbox("Stadio Clinico T", ["T1", "T2", "T3", "T4"], key="tm_stadio_t")
        with col_tnm2:
            stad_n = st.selectbox("Stadio Linfonodale N", ["N0", "N1"], key="tm_stadio_n")
        with col_tnm3:
            stad_m = st.selectbox("Stadio Metastatico M", ["M0 (Non metastatica)", "M1a (Linfonodi non regionali)", "M1b (Ossa)", "M1c (Viscerali o altro)"], key="tm_stadio_m")

        col_les1, col_les2 = st.columns(2)
        with col_les1:
            num_lesioni_osseec = st.number_input("Numero di Lesioni Ossee stimate", min_value=0, max_value=50, value=0, step=1, key="tm_num_lesioni")
        with col_les2:
            # Calcolo automatico orientativo del volume CHAARTED/STAMPEDE
            is_high_volume = ("M1c" in stad_m) or (num_lesioni_osseec >= 4)
            volume_stimato = "High Volume (Alto volume)" if is_high_volume else ("Low Volume (Basso volume)" if "M1" in stad_m else "Non applicabile (M0)")
            st.text_input("Volume di Malattia Stimato (CHAARTED/STAMPEDE)", value=volume_stimato, disabled=True, key="tm_vol_stimato")

        st.markdown("---")
        st.markdown("#### 🩺 Profilo di Comorbilità e Parametri Metabolico-Ossei")
        
        col_com1, col_com2, col_com3 = st.columns(3)
        with col_com1:
            flag_ipertensione = st.checkbox("Ipertensione severa / Scompenso CV", key="tm_flag_cv")
            flag_diabete = st.checkbox("Diabete / Difficoltà con Cortisonici", key="tm_flag_diabete")
        with col_com2:
            flag_neurologico = st.checkbox("Patologie Neurologiche / Epilessia / Rischio Cadute", key="tm_flag_neuro")
            flag_fragile = st.checkbox("Paziente Fragile / Politrattato", key="tm_flag_fragile")
        with col_com3:
            flag_osteopenia = st.checkbox("Osteopenia / Osteoporosi (Indicazione Bone Health)", key="tm_flag_osteopenia")

        # Motore di Supporto Decisionale basato sui flag e sulle evidenze scientifiche
        with st.expander("💡 Consiglio Clinico Basato su Evidenze (Trial Clinici & Tollerabilità)", expanded=True):
            sconsiglia_abi = flag_ipertensione or flag_diabete
            sconsiglia_enza = flag_neurologico or flag_fragile
            
            if "M1" in stad_m:
                if is_high_volume:
                    st.markdown("📍 **Setting: Malattia Metastatica ad Alto Volume (mHSPC)**")
                    st.markdown("• *Studio ARASENS*: Considerare la **Tripletta** (ADT + Docetaxel + **Darolutamide**), che garantisce il massimo vantaggio di OS con un ottimo profilo di tollerabilità.")
                else:
                    st.markdown("📍 **Setting: Malattia Metastatica a Basso Volume (mHSPC)**")
                    st.markdown("• *Studio TITAN / ARASENS / SPARTAN logic*: Preferire la **Doppietta** con un ARSI moderno evitando la chemio iniziale.")
                
                if sconsiglia_abi:
                    st.warning("⚠️ **Nota Abiraterone**: Sconsigliato per la necessaria co-somministrazione di prednisone/prednisolone in pazienti con ipertensione o diabete.")
                if sconsiglia_enza:
                    st.warning("⚠️ **Nota Enzalutamide**: Richiede cautela per la penetrazione a livello del SNC in pazienti con fragilità o storia neurologica.")
                if not sconsiglia_abi and not sconsiglia_enza:
                    st.success("✅ **Opzioni valide**: Darolutamide, Apalutamide, Enzalutamide o Abiraterone valutabili in base alle preferenze prescrittive.")
            else:
                st.markdown("📍 **Setting: Malattia Non Metastatica (nmCRPC / M0)**")
                st.markdown("• *Studio SPARTAN*: Valutare Apalutamide o molecole affini per ritardare la comparsa di metastasi.")

            if flag_osteopenia:
                st.info("🦴 **Protezione Ossea Consigliata**: Valutare l'avvio di Denosumab o Acido Zoledronico con supplementazione di Vitamina D/Calcemia per prevenire SRE.")

        st.markdown("---")
        st.markdown("#### 🚨 Stato di Malattia e transizione mCRPC (Linee Guida EAU/ESMO)")
        
        col_crpc1, col_crpc2 = st.columns(2)
        with col_crpc1:
            stato_crpc = st.selectbox(
                "Stato di Resistenza alla Castrazione", 
                ["No (Sensibile agli androgeni / mHSPC)", "Sì (mCRPC - Resistente alla castrazione con testosterone in target)"], 
                key="tm_crpc_check"
            )
        with col_crpc2:
            opzione_mcrpc = "Non applicabile"
            if "Sì (mCRPC" in stato_crpc:
                opzione_mcrpc = st.selectbox(
                    "Strategia di Linea Successiva (mCRPC)",
                    ["Switch di ARSI", "Chemioterapia con Cabazitaxel", "Terapia Radiometabolica (177Lu-PSMA)", "Radio-223 (per metastasi ossee esclusive - Studio PEACE-3)"],
                    key="tm_strat_mcrpc"
                )
            else:
                st.info("Paziente in fase ormonosensibile.")

        st.markdown("---")
        st.markdown("#### 💉 Terapia Ormonale e Scelta ARSI Guidata")
        
        col_LHRH1, col_LHRH2, col_LHRH3 = st.columns(3)
        with col_LHRH1:
            fatto_lhrh_tm = st.selectbox("Terapia LH-RH in corso?", ["No", "Sì"], key="tm_lhrh_check")
        with col_LHRH2:
            tipo_lhrh_tm = st.selectbox("Molecola LH-RH", ["Nessuna", "Triptorelina", "Leuprorelina", "Relugolix"], key="tm_tipo_lhrh")
        with col_LHRH3:
            data_inizio_lhrh_tm = st.date_input("Data di inizio LH-RH", value=datetime.today(), key="tm_lhrh_data")

        col_arsi1, col_arsi2 = st.columns(2)
        with col_arsi1:
            usa_arsi_tm = st.selectbox("Associazione con ARSI?", ["No", "Sì"], key="tm_arsi_check")
        with col_arsi2:
            tipo_arsi_tm = st.selectbox("Molecola ARSI scelta", ["Nessuna", "Darolutamide", "Apalutamide", "Enzalutamide", "Abiraterone"], key="tm_tipo_arsi")

        st.markdown("---")
        st.markdown("#### 💊 Chemioterapia, Target Therapy (PARPi) e Salute Ossea")
        
        col_chem1, col_chem2 = st.columns(2)
        with col_chem1:
            usa_chemio = st.selectbox("Chemioterapia associata (es. Tripletta ARASENS)?", ["No", "Sì"], key="tm_chemio_check")
        with col_chem2:
            tipo_chemio = st.selectbox("Molecola Chemioterapica", ["Nessuna", "Docetaxel", "Cabazitaxel"], key="tm_tipo_chemio")

        st.markdown("##### 🧬 Profilo Mutazionale HRR / BRCA e PARP Inibitori")
        col_parp1, col_parp2 = st.columns(2)
        with col_parp1:
            brca_mutato = st.checkbox("Paziente con mutazione BRCA1/2 o HRR (Homologous Recombination Repair esteso)", key="tm_brca_check")
        with col_parp2:
            tipo_parpi = st.selectbox("Scelta PARP Inibitore (PARPi)", ["Nessuno", "Olaparib", "Niraparib", "Talazoparib"], key="tm_tipo_parpi")

        st.markdown("##### 🦴 Protezione Ossea (Bone Health - Prevenzione SRE)")
        col_bone1, col_bone2 = st.columns(2)
        with col_bone1:
            terapia_osso = st.selectbox("Terapia Osteoprotettiva Associata", ["Nessuna", "Acido Zoledronico", "Denosumab"], key="tm_bone_med")
        with col_bone2:
            supp_vitd = st.checkbox("Inclusa supplementazione Calcemia / Vitamina D", key="tm_vitd_check")

        st.markdown("---")
        st.markdown("#### 📈 Monitoraggio Biochimico (PSA e Testosteronemia)")
        
        col_bio1, col_bio2, col_bio3 = st.columns(3)
        with col_bio1:
            valore_psa_tm = st.number_input("Valore PSA Attuale (ng/mL)", min_value=0.0, max_value=1000.0, value=float(paziente.get("ultimo_psa", 0.0)), step=0.1, key="tm_psa_val")
        with col_bio2:
            valore_testosterone = st.number_input("Testosteronemia (ng/dL)", min_value=0.0, max_value=1500.0, value=0.0, step=1.0, key="tm_testosterone")
        with col_bio3:
            target_castrazione = st.selectbox("Target Testosterone di Castrazione (< 50 ng/dL)?", ["Raggiunto (< 50 ng/dL)", "Non raggiunto (>= 50 ng/dL - Fuga biochimica)"], key="tm_target_test")

        if "Non raggiunto" in target_castrazione:
            st.error("⚠️ **ATTENZIONE**: Il livello di testosterone non rientra nel range di castrazione (< 50 ng/dL). Valutare la compliance o l'efficacia del blocco androgenico.")
        else:
            st.success("✅ Livello di testosteronemia in target di castrazione.")

        st.markdown("---")
        scelta_fine_visita = st.selectbox(
            "Decisione presa a fine visita (Aggiornamento Percorso):",
            [
                "Prosegue Terapia Medica in corso",
                "Switch terapeutico / Modifica Linea Sistemica",
                "Avvio percorso di cure palliative / supportive"
            ],
            key="tm_scelta_fine"
        )

        note_tm = st.text_area("Note cliniche, tollerabilità e raccomandazioni di terapia medica:", key="tm_note")
        
        submit_tm = st.form_submit_button("💾 Salva Nuova Valutazione & Genera Referto PDF", type="primary")
        
        if submit_tm:
            # Logica condizionale per la conclusione clinica automatica
            is_prima_visita = len(paziente.get("visite", [])) == 0
            conclusione_clinica_testo = ""
            
            if is_prima_visita:
                gleason_inserito = paziente.get("gleason_score", "7 (3+4)")
                descrizione_m = f"M{stad_m.split()[0][1:]}" if "M1" in stad_m else "M0 (assenti)"
                descrizione_n = f"N{stad_n}"
                
                conclusione_clinica_testo = (
                    f"\n\nConclusione clinica: Quadro di Adenocarcinoma prostatico (Gleason Score {gleason_inserito}) "
                    f"con secondarismi ({descrizione_n}, {descrizione_m}) che configura un quadro "
                    f"di carcinoma metastatico a {volume_stimato.lower()} per cui, sulla base delle "
                    f"linee guida, delle più recenti evidenze scientifiche e sulla storia clinica "
                    f"personale del paziente, si avvia terapia con {tipo_lhrh_tm} associato a {tipo_arsi_tm} "
                    f"{'e ' + tipo_chemio if usa_chemio == 'Sì' else ''}."
                )
            else:
                psa_precedente = float(paziente.get("ultimo_psa", valore_psa_tm))
                if valore_psa_tm < psa_precedente:
                    andamento_psa = "diminuzione del PSA"
                    stato_clinico = "miglioramento"
                elif valore_psa_tm > psa_precedente:
                    andamento_psa = "rising del PSA"
                    stato_clinico = "peggioramento"
                else:
                    andamento_psa = "stabilità del PSA"
                    stato_clinico = "stabile"

                if "Prosegue" in scelta_fine_visita:
                    consiglio_terapeutico = "proseguire terapia in atto"
                elif "Switch" in scelta_fine_visita:
                    consiglio_terapeutico = f"switch terapeutico a {tipo_arsi_tm if tipo_arsi_tm != 'Nessuna' else opzione_mcrpc}"
                else:
                    consiglio_terapeutico = "avviare percorso di cure palliative / supportive"

                conclusione_clinica_testo = (
                    f"\n\nConclusione clinica: Quadro clinico in {stato_clinico} con {andamento_psa} "
                    f"(PSA attuale: {valore_psa_tm} ng/mL), per cui si consiglia di {consiglio_terapeutico}."
                )

            paziente["ultimo_psa"] = valore_psa_tm
            paziente["percorso_scelto"] = scelta_fine_visita

            dettagli_tm = (
                f"Controllo Terapia Medica Avanzata\n"
                f"• Stadiazione: cT{stad_t} N{stad_n} M{stad_m} | Lesioni ossee: {num_lesioni_osseec} ({volume_stimato})\n"
                f"• Comorbilità/Flag: Ipertensione/CV: {flag_ipertensione}, Diabete: {flag_diabete}, Neuro: {flag_neurologico}, Fragile: {flag_fragile}\n"
                f"• mCRPC: {stato_crpc} (Strategia: {opzione_mcrpc})\n"
                f"• LH-RH: {fatto_lhrh_tm} ({tipo_lhrh_tm}) | ARSI Scelta: {usa_arsi_tm} ({tipo_arsi_tm})\n"
                f"• Chemio: {usa_chemio} ({tipo_chemio}) | HRR/BRCA: {brca_mutato} (PARPi: {tipo_parpi})\n"
                f"• Bone Health: {terapia_osso} (Vit.D/Ca: {supp_vitd})\n"
                f"• Biochimica: PSA {valore_psa_tm} ng/mL | Testosterone {valore_testosterone} ng/dL ({target_castrazione})\n"
                f"• Decisione Fine Visita: {scelta_fine_visita}\n"
                f"• Note: {note_tm}"
                f"{conclusione_clinica_testo}"
            )
            
            dati_v_tm = {
                "data": str(datetime.today().date()),
                "tipo": f"Follow-up Terapia Medica ({scelta_fine_visita})",
                "dettagli": dettagli_tm
            }
            
            if "visite" not in paziente:
                paziente["visite"] = []
            paziente["visite"].append(dati_v_tm)
            salva_db_pazienti(db_attivo)
            st.session_state["ultimo_paziente_fu_tm"] = codice_search
            st.success("✅ Nuova valutazione di terapia medica salvata correttamente nello storico!")

    # Gestione download referto aggiornato
    if st.session_state.get("ultimo_paziente_fu_tm"] == codice_search and paziente.get("visite"):
        ultima_visita = paziente["visite"][-1]
        
        note_pdf = [
            f"Stadiazione e Volume: cT{stad_t}N{stad_n}M{stad_m} ({volume_stimato}, {num_lesioni_osseec} lesioni ossee)",
            f"Stato mCRPC: {stato_crpc} ({opzione_mcrpc})",
            f"Terapia Sistemica: LHRH ({tipo_lhrh_tm}), ARSI ({tipo_arsi_tm}), Chemio ({tipo_chemio}), PARPi ({tipo_parpi})",
            f"Bone Health: {terapia_osso} (Suppl. Vit D/Ca: {supp_vitd})",
            f"Decisione di fine visita: {scelta_fine_visita}",
            note_tm
        ]
        note_pdf = [n for n in note_pdf if n]

        pdf_bytes = genera_pdf_referto(
            codice_search, 
            ultima_visita, 
            percorso="Terapia Medica Avanzata", 
            note_raccomandazioni=note_pdf, 
            nome=paziente.get('nome', ''), 
            cognome=paziente.get('cognome', '')
        )
        
        st.download_button(
            label="📄 Scarica Referto Terapia Medica in PDF",
            data=pdf_bytes,
            file_name=f"Referto_TerapiaMedica_{codice_search}.pdf",
            mime="application/pdf",
            key="download_pdf_tm_aggiornato"
        )
