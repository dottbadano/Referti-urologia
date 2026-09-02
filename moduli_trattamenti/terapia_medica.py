from datetime import datetime
import streamlit as st
from utils import genera_pdf_referto, salva_db_pazienti

def render_terapia_medica(paziente, db_attivo, codice_search):
    """Modulo dedicato alla gestione e follow-up della Terapia Medica (ormonale, ARSI, chemioterapia, PARPi, mCRPC e Bone Health)."""
    st.markdown("### 🟡 Protocollo di Terapia Medica Avanzata")
    st.info("Gestione della malattia metastatica o avanzata, definizione del volume tumorale (Criteri CHAARTED/STAMPEDE), transizione mCRPC, terapie sistemiche, mutazioni HRR/BRCA, salute ossea e monitoraggio di PSA e testosteronemia.")
    
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
        st.markdown("#### 🌍 Caratteristiche di Malattia e Volume (Criteri CHAARTED / STAMPEDE)")
        
        col_vol1, col_vol2 = st.columns(2)
        with col_vol1:
            presenza_metastasi = st.selectbox("Presenza di Metastasi", ["No (M0 / Ormonodipendente non metastatica)", "Sì (M1 / Malattia metastatica)"], key="tm_metastasi_check")
        with col_vol2:
            volume_malattia = st.selectbox("Volume di Malattia (Criteri CHAARTED/STAMPEDE)", ["Non applicabile (M0)", "Low Volume (Basso volume)", "High Volume (Alto volume: metastasi viscerali o >=4 lesioni ossee con almeno una extra-assiale/vertebrale)"], key="tm_volume")

        st.markdown("---")
        st.markdown("#### 🚨 Stato di Malattia e transizione mCRPC (Resistenza alla Castrazione - Linee Guida EAU/ESMO)")
        
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
                    ["Switch di ARSI", "Chemioterapia con Cabazitaxel", "Terapia Radiometabolica (177Lu-PSMA)", "Radio-223 (per metastasi ossee esclusive)"],
                    key="tm_strat_mcrpc"
                )
            else:
                st.info("Paziente in fase ormonosensibile.")

        st.markdown("---")
        st.markdown("#### 💉 Terapia Ormonale e ARSI")
        
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
            tipo_arsi_tm = st.selectbox("Molecola ARSI", ["Nessuna", "Apalutamide", "Darolutamide", "Enzalutamide", "Abiraterone"], key="tm_tipo_arsi")

        st.markdown("---")
        st.markdown("#### 💊 Chemioterapia, Target Therapy (PARPi) e Salute Ossea")
        
        col_chem1, col_chem2 = st.columns(2)
        with col_chem1:
            usa_chemio = st.selectbox("Chemioterapia associata?", ["No", "Sì"], key="tm_chemio_check")
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
            paziente["ultimo_psa"] = valore_psa_tm
            paziente["percorso_scelto"] = scelta_fine_visita

            dettagli_tm = (
                f"Controllo Terapia Medica Avanzata\n"
                f"• Stato: {presenza_metastasi} | Volume: {volume_malattia} | mCRPC: {stato_crpc} (Strategia: {opzione_mcrpc})\n"
                f"• LH-RH: {fatto_lhrh_tm} ({tipo_lhrh_tm}) | ARSI: {usa_arsi_tm} ({tipo_arsi_tm})\n"
                f"• Chemio: {usa_chemio} ({tipo_chemio}) | HRR/BRCA: {brca_mutato} (PARPi: {tipo_parpi})\n"
                f"• Bone Health: {terapia_osso} (Vit.D/Ca: {supp_vitd})\n"
                f"• Biochimica: PSA {valore_psa_tm} ng/mL | Testosterone {valore_testosterone} ng/dL ({target_castrazione})\n"
                f"• Decisione Fine Visita: {scelta_fine_visita}\n"
                f"• Note: {note_tm}"
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
            f"Stato mCRPC: {stato_crpc} ({opzione_mcrpc})",
            f"Terapia Sistemica: LHRH ({tipo_lhrh_tm}), ARSI ({tipo_arsi_tm}), PARPi ({tipo_parpi})",
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
