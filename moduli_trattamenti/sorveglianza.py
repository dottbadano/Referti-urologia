import streamlit as st
from datetime import datetime
import pandas as pd
import math

def calcola_psadt_preciso(data_prec_str, psa_prec, data_att_str, psa_att):
    """Calcola il tempo di raddoppio del PSA (PSADT) in mesi tra due rilevazioni."""
    if not data_prec_str or not data_att_str or psa_prec is None or psa_att is None:
        return None
    try:
        dt_prec = datetime.strptime(data_prec_str, "%Y-%m-%d").date()
        dt_att = datetime.strptime(data_att_str, "%Y-%m-%d").date()
        giorni = (dt_att - dt_prec).days
        if giorni <= 0 or psa_prec <= 0 or psa_att <= psa_prec:
            return None
        psadt_giorni = (math.log(2) * giorni) / math.log(psa_att / psa_prec)
        return round(psadt_giorni / 30.4375, 1)
    except Exception:
        return None

def render_sorveglianza_attiva(paziente, db_attivo, codice_search):
    """Modulo strutturato per la Sorveglianza Attiva: II Visita (6 mesi + PSADT + mpRMN), Controllo Confirmatorio (Biopsia + ISUP) e Follow-up PSA continuo con grafico e PSADT automatico."""
    st.markdown("### 🟢 Protocollo di Sorveglianza Attiva - Gestione Clinica")

    if "cronologia_psa" not in paziente:
        paziente["cronologia_psa"] = []

    fase_sa = st.radio(
        "Seleziona Fase del Protocollo di Sorveglianza:",
        [
            "1. Seconda Visita (Controllo a 6 Mesi & mpRMN)",
            "2. Controllo Confirmatorio (Biopsia & Istologia)",
            "3. Follow-up Continuo (Inserimento PSA & Cinetica)"
        ],
        horizontal=True
    )

    st.divider()

    if fase_sa == "1. Seconda Visita (Controllo a 6 Mesi & mpRMN)":
        st.subheader("📅 Seconda Visita: Rivalutazione a 6 Mesi")
        st.info("Inserire il primo controllo del PSA a 6 mesi (confrontato con il basale) e l'esito della mpRMN di controllo.")

        psa_basale_storico = paziente.get("ultimo_psa", 0.0)
        data_basale_storico = paziente.get("data_ultimo_psa", str(datetime.today().date()))

        with st.form(key="form_seconda_visita_sa"):
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                psa_6m = st.number_input("Valore PSA a 6 Mesi (ng/mL)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
            with col_s2:
                mese_6m = st.selectbox("Mese Prelievo", ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"], key="m_6m")
            with col_s3:
                anno_6m = st.number_input("Anno Prelievo", min_value=2000, max_value=2100, value=datetime.today().year, step=1, key="a_6m")

            num_m_6m = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"].index(mese_6m) + 1
            data_corrente_6m = datetime(int(anno_6m), num_m_6m, 1).date()

            # Calcolo automatico PSADT rispetto al basale
            psadt_stimato = calcola_psadt_preciso(data_basale_storico, psa_basale_storico, str(data_corrente_6m), psa_6m)
            
            if psadt_stimato is not None:
                st.warning(f"📈 **PSA Doubling Time (PSADT) stimato rispetto al basale:** `{psadt_stimato} mesi`")
            else:
                st.info("📈 PSADT non ancora calcolabile o valori stabili/in calo.")

            st.markdown("---")
            esito_rmn_6m = st.selectbox(
                "Esito Referto mpRMN di Controllo",
                ["Non valutabile", "Regressione", "Stabilità", "Progressione"]
            )
            note_sv2 = st.text_area("Note cliniche della seconda visita:")

            btn_salva_sv2 = st.form_submit_button("💾 Salva Seconda Visita", type="primary")

            if btn_salva_sv2:
                if psa_6m > 0:
                    # Registra in cronologia se non già presente
                    paziente["cronologia_psa"].append({
                        "valore": psa_6m,
                        "mese": mese_6m,
                        "anno": anno_6m,
                        "data_registrazione": str(data_corrente_6m)
                    })
                    paziente["ultimo_psa"] = psa_6m
                    paziente["data_ultimo_psa"] = str(data_corrente_6m)

                    dettagli_testo = f"Seconda Visita (6 Mesi) - PSA: {psa_6m} ng/mL ({mese_6m} {anno_6m}) | PSADT: {psadt_stimato if psadt_stimato else 'N/D'} mesi\nmpRMN: {esito_rmn_6m}\nNote: {note_sv2}"
                    
                    if "visite" not in paziente:
                        paziente["visite"] = []
                    paziente["visite"].append({"data": str(datetime.today().date()), "tipo": "Seconda Visita Sorveglianza", "dettagli": dettagli_testo})
                    
                    from utils import salva_db_pazienti
                    salva_db_pazienti(db_attivo)
                    st.success("Seconda visita salvata con successo!")
                    st.rerun()
                else:
                    st.error("Inserisci un valore di PSA valido.")

    elif fase_sa == "2. Controllo Confirmatorio (Biopsia & Istologia)":
        st.subheader("🔬 Controllo Confirmatorio: Biopsia Prostatica")
        st.info("Registrazione dei dati relativi alla biopsia confirmatoria e all'istologia definitiva.")

        with st.form(key="form_biopsia_confirmatoria"):
            fatta_biopsia = st.checkbox("Il paziente ha eseguito la biopsia confirmatoria?")
            
            isup_conf = st.selectbox(
                "Gruppo ISUP Bioptico",
                ["ISUP 1 (Gleason 3+3)", "ISUP 2 (Gleason 3+4)", "ISUP 3 (Gleason 4+3)", "ISUP 4 (Gleason 4+4)", "ISUP 5 (Gleason 9-10)"]
            )
            pct_prelievi = st.number_input("Percentuale di prelievi positivi (%)", min_value=0, max_value=100, value=10, step=5)
            note_bx = st.text_area("Note anatomopatologiche:")

            btn_salva_bx = st.form_submit_button("💾 Salva Dati Biopsia Confirmatoria", type="primary")

            if btn_salva_bx:
                stato_bx_str = f"Eseguita Biopsia Confirmatoria: {'Sì' if fatta_biopsia else 'No'} | {isup_conf} | Prelievi positivi: {pct_prelievi}% | Note: {note_bx}"
                if "visite" not in paziente:
                    paziente["visite"] = []
                paziente["visite"].append({"data": str(datetime.today().date()), "tipo": "Controllo Confirmatorio Biopsia", "dettagli": stato_bx_str})
                
                from utils import salva_db_pazienti
                salva_db_pazienti(db_attivo)
                st.success("Dati della biopsia confirmatoria salvati correttamente!")

    elif fase_sa == "3. Follow-up Continuo (Inserimento PSA & Cinetica)":
        st.subheader("📊 Follow-up Continuo e Monitoraggio Cinetica PSA")
        st.info("Inserisci i controlli periodici successivi. Il sistema calcolerà automaticamente il PSADT rispetto al prelievo precedente e aggiornerà il grafico storico.")

        with st.form(key="form_aggiungi_psa_continuo"):
            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1:
                nuovo_psa = st.number_input("Nuovo Valore PSA (ng/mL)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
            with col_c2:
                mese_nc = st.selectbox("Mese Prelievo", ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"], key="m_nc")
            with col_c3:
                anno_nc = st.number_input("Anno Prelievo", min_value=2000, max_value=2100, value=datetime.today().year, step=1, key="a_nc")

            btn_aggiungi_nc = st.form_submit_button("➕ Aggiungi PSA alla Cronologia", type="primary")

            if btn_aggiungi_nc:
                if nuovo_psa > 0:
                    num_m_nc = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"].index(mese_nc) + 1
                    data_nc = datetime(int(anno_nc), num_m_nc, 1).date()

                    paziente["cronologia_psa"].append({
                        "valore": nuovo_psa,
                        "mese": mese_nc,
                        "anno": anno_nc,
                        "data_registrazione": str(data_nc)
                    })
                    paziente["ultimo_psa"] = nuovo_psa
                    paziente["data_ultimo_psa"] = str(data_nc)

                    from utils import salva_db_pazienti
                    salva_db_pazienti(db_attivo)
                    st.success(f"PSA di {nuovo_psa} ng/mL ({mese_nc} {anno_nc}) memorizzato con successo!")
                    st.rerun()
                else:
                    st.error("Inserisci un valore di PSA valido maggiore di 0.")

        if paziente.get("cronologia_psa"):
            st.markdown("---")
            st.markdown("#### 📈 Storico PSA, Cinetica e Andamento Grafico")

            cronologia = sorted(paziente["cronologia_psa"], key=lambda x: datetime.strptime(x["data_registrazione"], "%Y-%m-%d"))
            
            dati_tabella = []
            psa_precedente = None
            data_precedente = None

            for item in cronologia:
                val = item["valore"]
                data_str = item["data_registrazione"]
                etich = f"{item['mese']} {item['anno']}"
                
                psadt_calc = "Valore Iniziale / Baseline"
                if psa_precedente is not None and data_precedente is not None:
                    risultato_psadt = calcola_psadt_preciso(data_precedente, psa_precedente, data_str, val)
                    if risultato_psadt is not None:
                        psadt_calc = f"{risultato_psadt} mesi"
                    else:
                        psadt_calc = "Stabile / Non incrementale"

                dati_tabella.append({
                    "Periodo": etich,
                    "Valore PSA (ng/mL)": val,
                    "PSADT (vs precedente)": psadt_calc
                })

                psa_precedente = val
                data_precedente = data_str

            df_psa = pd.DataFrame(dati_tabella)
            st.dataframe(df_psa, use_container_width=True)

            st.markdown("##### Grafico Andamento Temporale")
            df_chart = pd.DataFrame(cronologia)
            df_chart['etichetta_tempo'] = df_chart['mese'] + " " + df_chart['anno'].astype(str)
            st.line_chart(df_chart.set_index('etichetta_tempo')['valore'])
