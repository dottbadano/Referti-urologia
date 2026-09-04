import streamlit as st
from datetime import datetime
from utils import salva_db_pazienti, genera_pdf_referto

def render_terapia_medica(paziente, db_attivo, codice_search):
    st.subheader("Gestione Terapia Medica / Ormonale (ADT e Nuovi Ormonofarmaci)")
    
    st.markdown(f"**Paziente in trattamento medico:** {paziente.get('cognome', '')} {paziente.get('nome', '')}")
    
    with st.form(key="form_terapia_medica"):
        st.markdown("### Aggiornamento Stato Clinico e Tossicità")
        
        tipo_trattamento_medico = st.selectbox(
            "Schema Terapeutico in Corso:",
            [
                "ADT Monoterapia (Analoghi/Antagonista LHRH)",
                "ADT + ARPI (Inibitore del Recettore degli Androgeni es. Enzalutamide, Darolutamide, Apalutamide)",
                "ADT + Chemioterapia (es. Docetaxel)",
                "Terapia di Seconda Linea / Altro"
            ]
        )
        
        valore_psa_attuale = st.number_input("Valore PSA Attuale (ng/ml):", min_value=0.0, step=0.1, value=float(paziente.get("ultimo_psa", 0.0)))
        
        st.markdown("---")
        st.markdown("**Monitoraggio Tossicità ed Effetti Collaterali (FATIGUE, VAMPATE, METABOLICO)**")
        
        col1, col2 = st.columns(2)
        with col1:
            vampate = st.selectbox("Vampate di calore (Vampate vasomotorie):", ["Assenti", "Lieve (gestibile)", "Moderata", "Severa"])
            astenia = st.selectbox("Astenia / Fatigue:", ["Assente", "Grado 1 (Lieve)", "Grado 2 (Moderata)", "Grado 3 (Severa)"])
        with col2:
            sintomi_metabolici = st.multiselect(
                "Effetti Metabolici / Ossei / Cardiovascolari:",
                ["Aumento ponderale / Massa grassa", "Riduzione massa muscolare", "Osteopenia / Osteoporosi", "Alterazioni lipidiche / Glicemiche", "Ipertensione arteriosa"]
            )
            
        note_cliniche = st.text_area("Note Cliniche, Esami Strumentali di Controllo o Variazioni della Terapia:")
        
        submitted = st.form_submit_button("Salva Visita Terapia Medica e Genera Report", type="primary")
        
        if submitted:
            data_visita = str(datetime.today().date())
            dettagli_visita = (
                f"Schema: {tipo_trattamento_medico}\n"
                f"PSA Attuale: {valore_psa_attuale} ng/ml\n"
                f"Tossicità / Effetti collaterali:\n"
                f"- Vampate: {vampate}\n"
                f"- Astenia: {astenia}\n"
                f"- Metabolici/Altro: {', '.join(sintomi_metabolici) if sintomi_metabolici else 'Nessuno'}\n"
                f"Note: {note_cliniche}"
            )
            
            nuova_visita = {
                "data": data_visita,
                "tipo": "Follow-up Terapia Medica / Ormonale",
                "dettagli": dettagli_visita
            }
            
            if "visite" not in paziente:
                paziente["visite"] = []
                
            paziente["visite"].append(nuova_visita)
            paziente["ultimo_psa"] = valore_psa_attuale
            paziente["data_ultimo_psa"] = data_visita
            
            db_attivo[codice_search] = paziente
            salva_db_pazienti(db_attivo)
            st.session_state["db_pazienti"] = db_attivo
            
            st.success("Dati di follow-up medico salvati correttamente nel database!")
            
            note_pdf = [
                f"Schema Terapeutico: {tipo_trattamento_medico}",
                f"Valore PSA di controllo: {valore_psa_attuale} ng/ml",
                f"Stato Tossicità: Astenia ({astenia}), Vampate ({vampate})",
                f"Note cliniche: {note_cliniche}"
            ]
            
            pdf_bytes = genera_pdf_referto(
                codice_search,
                nuova_visita,
                "Terapia Medica / Ormonale",
                note_pdf,
                nome=paziente.get('nome', ''),
                cognome=paziente.get('cognome', '')
            )
            
            st.download_button(
                label="Scarica Referto Follow-up Medico PDF",
                data=pdf_bytes,
                file_name=f"FollowUp_Medico_{paziente.get('cognome', '')}_{codice_search}.pdf",
                mime="application/pdf"
            )
