from datetime import datetime
import streamlit as st
from anamnesi_comune_2 import render_anagrafica_e_anamnesi_unificata, formatta_anamnesi_per_pdf_unificata
from utils import genera_pdf_referto

def render_modulo_prostata():
    st.subheader("🏥 Modulo Clinico Urologico - Tumore della Prostata")
    
    # 1. Anamnesi comune unificata con calcolo della fitness ponderata
    paziente = render_anagrafica_e_anamnesi_unificata(sigla_organo="P", prefix="prostata")
    
    st.markdown("---")
    st.markdown("### 🔬 Parametri Oncologici specifici (Prostata)")
    
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        psa = st.number_input("Valore PSA (ng/mL)", min_value=0.0, max_value=1000.0, value=7.5, step=0.1, key="prostata_psa")
    with col_p2:
        isup = st.selectbox("Grade Group / ISUP", [1, 2, 3, 4, 5], key="prostata_isup")
    with col_p3:
        stadio_c = st.selectbox("Stadio Clinico cT", ["cT1c", "cT2a", "cT2b", "cT2c", "cT3a", "cT3b", "cT4"], key="prostata_stadio")

    st.markdown("---")
    st.markdown("### 📋 Valutazione di Idoneità ai Trattamenti Radicali")

    # CONTROLLO CLINICO PONDERATO (Usa il flag calcolato nell'anamnesi invece del solo Charlson grezzo)
    if not paziente.get("aspettativa_vita_maggiore_10_anni", True):
        st.error(
            f"⚠️ **ATTENZIONE CLINICA CRITICA**\n\n"
            f"**Aspettativa di Vita Stimata:** < 10 Anni | **Età:** {paziente.get('eta')} aa, "
            f"**Charlson Ponderato:** {paziente.get('charlson_ponderato')} (Grezzo: {paziente.get('charlson_score')}), "
            f"**ECOG:** {paziente.get('ecog')[0]}, **G8:** {paziente.get('g8_score')}/17\n\n"
            "L'aspettativa di vita residua stimata, tenendo conto della comorbilità globale e della riserva funzionale, "
            "risulta inferiore a 10 anni. In conformità alle Linee Guida oncologiche internazionali, **NON SUSSISTE "
            "INDICAZIONE A TRATTAMENTI CHIRURGICI AGGRESSIVI O A FINALITÀ RADICALE** (es. Prostatectomia Radicale)."
        )
        percorso_scelto = "Sorveglianza Attiva / Terapia Conservativa o Palliativa (Non candidato a radicalità)"
    else:
        st.success(
            f"✅ **Paziente Idoneo alla Valutazione per Trattamenti Radicali**\n\n"
            f"Nonostante le comorbilità (Charlson grezzo: {paziente.get('charlson_score')}), l'ottimo stato di forma fisica "
            f"({paziente.get('ecog')}) e la riserva geriatrica (G8: {paziente.get('g8_score')}/17) portano un **Charlson Ponderato "
            f"di {paziente.get('charlson_ponderato')**, garantendo un'aspettativa di vita ampiamente superiore a 10 anni."
        )
        
        percorso_scelto = st.selectbox(
            "Seleziona Percorso Clinico / Trattamento Proposto:",
            [
                "Sorveglianza Attiva (Active Surveillance)",
                "Prostatectomia Radicale (Chirurgia)",
                "Radioterapia Esterna (+/- Ormonoterapia)",
                "Brachiterapia",
                "Terapia Focale (HIFU / Elettroporazione)"
            ],
            key="prostata_percorso"
        )

    st.markdown("---")
    st.markdown("### 📝 Note e Raccomandazioni Mediche")
    note_raccomandazioni = st.text_area("Note cliniche, prescrizioni o raccomandazioni per il paziente", key="prostata_note")

    # Generazione Referto PDF
    if st.button("📄 Genera Referto PDF Urologia (Prostata)", type="primary"):
        if not paziente["nome"] or not paziente["cognome"]:
            st.warning("Inserire Nome e Cognome del paziente prima di generare il referto.")
        else:
            dati_visita = {
                "data": datetime.today().strftime("%d/%m/%Y"),
                "tipo": "Visita Urologica - Follow-up / Stadiazione Prostata",
                "dettagli": f"PSA: {psa} ng/mL | ISUP: {isup} | Stadio: {stadio_c}\n\n" + formatta_anamnesi_per_pdf_unificata(paziente)
            }
            
            pdf_bytes = genera_pdf_referto(
                codice_paziente=paziente["id_univoco"],
                dati_visita=dati_visita,
                percorso=percorso_scelto,
                note_raccomandazioni=note_raccomandazioni,
                nome=paziente["nome"],
                cognome=paziente["cognome"]
            )
            
            st.download_button(
                label="📥 Scarica Referto PDF",
                data=pdf_bytes,
                file_name=f"Referto_Prostata_{paziente['cognome']}_{paziente['nome']}.pdf",
                mime="application/pdf"
            )

if __name__ == "__main__":
    render_modulo_prostata()
