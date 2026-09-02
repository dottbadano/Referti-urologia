    st.markdown("---")
    st.markdown("### 🔄 Registra Nuova Valutazione di Follow-up (Sorveglianza Attiva)")
    
    with st.form("form_nuova_valutazione_sa"):
        col_psa1, col_psa2, col_psa3 = st.columns(3)
        with col_psa1:
            mese_psa_a = st.selectbox("Mese Prelievo PSA", ELENCO_MESI, index=datetime.today().month - 1)
        with col_psa2:
            anno_psa_a = st.number_input("Anno Prelievo PSA", min_value=2000, max_value=2030, value=datetime.today().year)
        with col_psa3:
            psa_attuale = st.number_input("Valore PSA Attuale (ng/ml):", min_value=0.0, value=float(paziente.get("ultimo_psa", 0.0)), step=0.01)

        col_img1, col_img2 = st.columns(2)
        with col_img1:
            repertoprecise = st.selectbox(
                "Reperto RMN di Controllo (Punteggio PRECISE):",
                [
                    "Non Eseguita",
                    "PRECISE 1 - Regressione sostanziale",
                    "PRECISE 2 - Lieve regressione",
                    "PRECISE 3 - Stabile / Nessun cambiamento significativo",
                    "PRECISE 4 - Moderata evidenza di progressione",
                    "PRECISE 5 - Sostanziale evidenza di progressione"
                ]
            )
        with col_img2:
            dre_esito = st.selectbox(
                "Esplorazione Rettale (DRE):",
                ["Negativa", "Positiva (Sospetto locale / Modificazione)"]
            )

        note_cliniche_fu = st.text_area("Dettagli clinici della visita, sintomi o annotazioni:")

        scelta_fine_visita = st.selectbox(
            "Decisione presa a fine visita (Aggiornamento Percorso):",
            [
                "Prosegue Sorveglianza Attiva",
                "Chirurgia (Post-Prostatectomia)",
                "Radioterapia"
            ]
        )

        submitted = st.form_submit_button("💾 Salva Nuova Valutazione & Genera Referto PDF", type="primary")

        if submitted:
            num_mese_a = ELENCO_MESI.index(mese_psa_a) + 1
            data_psa_attuale = datetime(anno_psa_a, num_mese_a, 1).date()
            
            # Calcolo PSADT
            psadt_calcolato = calcola_psadt(paziente.get("ultimo_psa"), paziente.get("data_ultimo_psa"), psa_attuale, data_psa_attuale)

            paziente["ultimo_psa"] = psa_attuale
            paziente["data_ultimo_psa"] = str(data_psa_attuale)
            paziente["percorso_scelto"] = scelta_fine_visita
            
            dettagli_fu = (
                f"Controllo Follow-up (Sorveglianza Attiva)\n"
                f"• PSA: {psa_attuale:.2f} ng/ml ({mese_psa_a} {anno_psa_a})\n"
                f"• PSADT Calcolato: {psadt_calcolato if psadt_calcolato else 'Stabile / Non calcolabile'} mesi\n"
                f"• RMN Controllo (PRECISE): {repertoprecise}\n"
                f"• Esplorazione Rettale (DRE): {dre_esito}\n"
                f"• Decisione Finale: {scelta_fine_visita}"
            )
            if note_cliniche_fu:
                dettagli_fu += f"\n• Note Cliniche: {note_cliniche_fu}"

            dati_nuova_visita = {
                "data": str(datetime.today().date()),
                "tipo": f"Visita di Controllo ({scelta_fine_visita})",
                "dettagli": dettagli_fu
            }
            
            paziente["visite"].append(dati_nuova_visita)
            salva_db_pazienti(db_file)
            st.session_state["ultimo_paziente_fu_sa"] = codice_search
            st.success("✅ Nuova valutazione salvata correttamente nello storico del paziente!")

    # Gestione download referto aggiornato
    if st.session_state.get("ultimo_paziente_fu_sa") == codice_search and paziente["visite"]:
        ultima_visita = paziente["visite"][-1]
        note_pdf = [
            f"Valutazione RMN: {repertoprecise}",
            f"Esito DRE: {dre_esito}",
            f"Decisione di fine visita: {scelta_fine_visita}",
            note_cliniche_fu
        ]
        note_pdf = [n for n in note_pdf if n]
        
        pdf_bytes = genera_pdf_referto(
            codice_search, 
            ultima_visita, 
            scelta_fine_visita, 
            note_pdf, 
            nome=paziente.get('nome', ''), 
            cognome=paziente.get('cognome', '')
        )
        
        st.download_button(
            label="📄 Scarica Referto Aggiornato in PDF",
            data=pdf_bytes,
            file_name=f"Referto_Sorveglianza_Attiva_{codice_search}.pdf",
            mime="application/pdf",
            key="download_pdf_sa_aggiornato"
        )
