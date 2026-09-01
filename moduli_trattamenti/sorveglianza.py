import streamlit as st
from datetime import datetime
import pandas as pd

def render_sorveglianza_attiva(paziente, db_attivo, codice_search):
    """Modulo dedicato alla gestione e follow-up del protocollo di Sorveglianza Attiva con inserimento sequenziale del PSA, calcolo automatico del PSADT, grafico storico, mpRMN e biopsia confirmatoria."""
    st.markdown("### 🟢 Protocollo di Sorveglianza Attiva")
    st.info("Gestione clinica per pazienti in monitoraggio attivo: controllo del PSA a 6 mesi, rivalutazione a 12 mesi con mpRMN e biopsia confirmatoria, inserimento dati storici e grafico dell'andamento.")

    if "cronologia_psa" not in paziente:
        paziente["cronologia_psa"] = []

    st.markdown("#### 📈 Inserimento Nuovo Controllo PSA")
    with st.form(key="form_aggiungi_psa_sa"):
        col_psa1, col_psa2, col_psa3 = st.columns(3)
        with col_psa1:
            nuovo_valore_psa = st.number_input("Valore PSA (ng/mL)", min_value=0.0, max_value=100.0, value=0.0, step=0.1, key="sa_nuovo_psa")
        with col_psa2:
            mese_psa = st.selectbox("Mese Prelievo", ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"], key="sa_nuovo_mese")
        with col_psa3:
            anno_psa = st.number_input("Anno Prelievo", min_value=2000, max_value=2100, value=datetime.today().year, step=1, key="sa_nuovo_anno")

        btn_aggiungi_psa = st.form_submit_button("➕ Aggiungi PSA alla Cronologia")

        if btn_aggiungi_psa:
            if nuovo_valore_psa > 0:
                paziente["cronologia_psa"].append({
                    "valore": nuovo_valore_psa,
                    "mese": mese_psa,
                    "anno": anno_psa,
                    "data_registrazione": str(datetime.today().date())
                })
                from utils import salva_db_pazienti
                salva_db_pazienti(db_attivo)
                st.success(f"PSA di {nuovo_valore_psa} ng/mL ({mese_psa} {anno_psa}) aggiunto con successo!")
                st.rerun()
            else:
                st.error("Inserisci un valore di PSA valido maggiore di 0.")

    if paziente.get("cronologia_psa"):
        st.markdown("---")
        st.markdown("#### 📊 Andamento Temporale del PSA")
        df_psa = pd.DataFrame(paziente["cronologia_psa"])
        df_psa['etichetta_tempo'] = df_psa['mese'] + " " + df_psa['anno'].astype(str)
        
        st.line_chart(df_psa.set_index('etichetta_tempo')['valore'])

    st.markdown("---")
    st.markdown("#### 🩻 Imaging di Controllo (mpRMN) e Biopsia Confirmatoria")
    
    with st.form(key="form_quadro_clinico_sa"):
        col_diag1, col_diag2 = st.columns(2)
        with col_diag1:
            referto_rmn = st.text_area("Referto mpRMN / PI-RADS di Controllo", placeholder="Descrivere esito della risonanza di confronto...", key="sa_referto_rmn")
        with col_diag2:
            biopsia_conf = st.text_area("Esito Biopsia Confirmatoria (es. a 12 mesi)", placeholder="Riscontro istologico, ISUP e Gleason...", key="sa_biopsia_conf")

        stato_clinico_sa = st.selectbox(
            "Valutazione Criteri di Permanenza in Sorveglianza", 
            [
                "Criteri soddisfatti / Prosegue Sorveglianza (ogni 6 mesi)", 
                "Cinetica accelerata / Controllo ravvicinato (PSA ogni 3 mesi)", 
                "Criteri superati / Indicazione a trattamento radicale (Chirurgia/RT)"
            ], 
            key="sa_stato_clinico"
        )
        note_sa = st.text_area("Note cliniche generali di follow-up:", key="sa_note_generali")
        
        submit_sa = st.form_submit_button("💾 Salva Aggiornamento e Genera Referto", type="primary")
        
        if submit_sa:
            ultimi_valori = paziente["cronologia_psa"][-2:] if len(paziente["cronologia_psa"]) >= 2 else paziente["cronologia_psa"]
            stringa_cronologia = " | ".join([f"{item['valore']} ng/mL ({item['mese']} {item['anno']})" for item in ultimi_valori])
            
            dettagli_sa = (
                f"Sorveglianza Attiva - Ultimi controlli PSA: {stringa_cronologia}\n"
                f"Referto mpRMN: {referto_rmn}\n"
                f"Biopsia Confirmatoria: {biopsia_conf}\n"
                f"Stato Protocollo: {stato_clinico_sa}\nNote: {note_sa}"
            )
            dati_v_sa = {
                "data": str(datetime.today().date()),
                "tipo": "Controllo Sorveglianza Attiva",
                "dettagli": dettagli_sa
            }
            if "visite" not in paziente:
                paziente["visite"] = []
            paziente["visite"].append(dati_v_sa)
            
            from utils import salva_db_pazienti, genera_pdf_referto
            salva_db_pazienti(db_attivo)
            
            note_pdf = [stato_clinico_sa, referto_rmn, biopsia_conf, note_sa]
            pdf_bytes = genera_pdf_referto(codice_search, dati_v_sa, "Sorveglianza Attiva", note_pdf, nome=paziente.get('nome',''), cognome=paziente.get('cognome',''))
            
            st.success("Aggiornamento di Sorveglianza Attiva salvato correttamente!")
            st.download_button(
                label="📄 Scarica Referto Follow-up Sorveglianza PDF",
                data=pdf_bytes,
                file_name=f"SorveglianzaAttiva_{codice_search}.pdf",
                mime="application/pdf"
            )
