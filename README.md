# Sito T.Petrol – www.tpetrol.it

Sito statico pubblicato con GitHub Pages.

- **Prezzi self**: aggiornati ogni mattina in automatico dall'Osservaprezzi carburanti MIMIT
  (`.github/workflows/prezzi.yml` → `scripts/aggiorna_prezzi.py`).
- **Contatore rifornimenti** (in `index.html`, oggetto `LIVE`): si aggiorna ogni lunedì dopo la banca dati vendite.
  - `BASE` = 8.938.710 (stima fissa 2015–2020) + somma della colonna "Nr erogazioni" (Stato OK) di tutti i fogli
  - `BASE_DAL` = giorno successivo all'ultimo dato della banca dati
  - `MEDIA` = media giornaliera delle erogazioni delle ultime 4 settimane
- **Moduli**: inviano direttamente a commercialetpetrol@gmail.com tramite Web3Forms (se fallisce, apre una mail precompilata).
- **Privacy**: nessun cookie, font e immagini ospitati qui (`fonts/`, `logo.png`).
- **Instagram**: ogni giorno un'attività di Claude scrive `instagram_raw.json` con gli ultimi post (da Metricool);
  l'automazione `.github/workflows/instagram.yml` scarica le foto in `ig/` e aggiorna `ig.json`, che la pagina legge.
- **Carte accettate** (sezione `#carte-accettate` in `index.html`, oggetti `CARTE` e `CARTA`; loghi in `carte/`): un riquadro per ogni carta
  con l'elenco degli impianti dove è accettata. Le carte flotta vengono dalla banca dati vendite (pagamenti negli ultimi 4 mesi,
  periodo in `CARTE_DAL`/`CARTE_AL`); American Express è aggiunta a mano su tutti gli impianti.
