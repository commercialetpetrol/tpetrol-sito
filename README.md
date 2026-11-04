# Sito T.Petrol – www.tpetrol.it

Sito statico pubblicato con GitHub Pages.

- **Prezzi self**: aggiornati ogni mattina in automatico dall'Osservaprezzi carburanti MIMIT
  (`.github/workflows/prezzi.yml` → `scripts/aggiorna_prezzi.py`).
- **Contatore rifornimenti** (in `index.html`, oggetto `LIVE`): si aggiorna ogni lunedì dopo la banca dati vendite.
  - `BASE` = 8.938.710 (stima fissa 2015–2020) + somma della colonna "Nr erogazioni" (Stato OK) di tutti i fogli
  - `BASE_DAL` = giorno successivo all'ultimo dato della banca dati
  - `MEDIA` = media giornaliera delle erogazioni delle ultime 4 settimane
- **Moduli**: inviano direttamente a commercialetpetrol@gmail.com tramite FormSubmit (se fallisce, apre una mail precompilata).
- **Privacy**: nessun cookie, font e immagini ospitati qui (`fonts/`, `logo.png`).
