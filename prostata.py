from datetime import datetime
import math
import streamlit as st
from utils import (
    carica_db_pazienti,
    salva_db_pazienti,
    genera_o_aggiorna_registro,
    genera_pdf_referto,
    salva_paziente_su_drive,
    ELENCO_MESI
)
from anamnesi_comune import (
    render_anagrafica_e_anamnesi_unificata,
    formatta_anamnesi_per_pdf_unificata
)

# Import corretti dai singoli file all'interno della cartella moduli_trattamenti
from moduli_trattamenti.sorveglianza import render_followup_sorveglianza_avanzato
from moduli_trattamenti.prostatectomia import render_followup_chirurgia_avanzato
from moduli_trattamenti.radioterapia import render_followup_radioterapia_avanzato
from moduli_trattamenti.terapia_medica import render_terapia_medica
