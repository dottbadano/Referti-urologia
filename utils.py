def carica_db_pazienti():
    """Carica il database dei pazienti dal Foglio Google su Drive."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl=0)

        registro = {}
        if not df.empty and "codice" in df.columns:
            for _, row in df.iterrows():
                codice = str(row["codice"]).strip()
                if codice and codice != "nan":
                    # Recupera eventuali visite salvate in formato JSON se la colonna esiste
                    visite_raw = row.get("visite", "[]")
                    try:
                        visite_list = json.loads(visite_raw) if isinstance(visite_raw, str) else []
                    except Exception:
                        visite_list = []

                    registro[codice] = {
                        "nome": str(row.get("nome", "")),
                        "cognome": str(row.get("cognome", "")),
                        "data_nascita": str(row.get("data_nascita", "")),
                        "ultimo_aggiornamento": str(row.get("ultimo_aggiornamento", datetime.today().date())),
                        "organo": str(row.get("organo", "PROSTATA")),
                        "isup": int(row.get("isup", 1)) if pd.notna(row.get("isup")) else 1,
                        "rischio": str(row.get("rischio", "")),
                        "percorso_scelto": str(row.get("percorso_scelto", "")),
                        "ultimo_psa": float(row.get("ultimo_psa", 0.0)) if pd.notna(row.get("ultimo_psa")) else 0.0,
                        "data_ultimo_psa": str(row.get("data_ultimo_psa", "")),
                        "g8_score": int(row.get("g8_score", 0)) if pd.notna(row.get("g8_score")) else 0,
                        "visite": visite_list,
                    }
        return registro
    except Exception as e:
        print(f"Errore nella lettura del database su Google Sheets: {e}")
        return {}
