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
- **Carte accettate** (sezione `#carte-accettate` in `index.html`, oggetti `CARTE` e `CARTA`; loghi in `carte/`): fila di loghi + mappa che accende gli impianti dove la carta scelta è accettata
  Le carte flotta vengono dalla banca dati vendite (pagamenti negli ultimi 4 mesi,
  periodo in `CARTE_DAL`/`CARTE_AL`); American Express è aggiunta a mano su tutti gli impianti.
- **Mappe**: la geografia (oggetto `GEO` in `index.html`) è già proiettata nel riquadro 560×740: regioni e province ISTAT (via openpolis/geojson-italy, CC BY), laghi e fiumi Natural Earth. Va rigenerata solo se cambia l'area della mappa.
- **Sostenibilità** (sezione `#sostenibilita`): `SOLARE` = per ogni codice PV le righe `[kW fotovoltaico, kWh accumulo, etichetta opzionale]`; `CER_NOVA` = stazioni aderenti a CER Nova ETS. L'elenco "Dove" si genera da solo.

## Restyling 2026 (livello C)
Approvato il 6 novembre 2026. Si somma allo stile e al codice esistenti senza modificarli:
- **Stile**: blocco `<style id="restyling">` subito dopo lo stile principale in `index.html`
  (parte A rifiniture, parte B struttura visiva, parte C valorizzazione dati). Le classi nuove iniziano con `rs-`.
- **Script**: blocco `<script id="restyling-js">` in fondo alla pagina. Legge i dati già presenti
  (`S`, `bestB`, `bestG`, `fmt`, `SOLARE`, `CER_NOVA`): se si rinominano queste costanti va aggiornato anche il blocco.
- **HTML aggiunto**: menu desktop e pulsante «Richiedi la carta» nella barra, prezzi di oggi e quattro numeri nell'apertura,
  righe «oggi» nel contatore (`live-today`, `live-rate`, calcolate dal codice del contatore), icone e azioni nei contatti, piè di pagina a colonne.
- **Privacy e Cookie**: pulsante «Torna al sito», piè di pagina, link leggibili.
- Le righe aggiornate dalle automazioni (`PREZZI_DATA`, `PREZZI`, `LIVE`, `CARTE`) non sono cambiate.
- Per tornare allo stile precedente: togliere i due blocchi `restyling` (o annullare il commit di unione del ramo `restyling`).

## Pagine per proprietari di impianti (novembre 2026)
Per farsi trovare su Google da chi vuole vendere un distributore o cerca consulenza:
- `vendere-distributore-carburanti/` → www.tpetrol.it/vendere-distributore-carburanti/ (acquisizione, convenzionamento o gestione diretta degli impianti, modulo «Proposta per il vostro impianto»)
- `consulenza-impianti-carburanti/` → www.tpetrol.it/consulenza-impianti-carburanti/ (costruzione, ristrutturazione, messa a norma, valutazioni e perizie, modulo «Richiesta di consulenza»)
- Stile comune in `pagine.css`, invio dei moduli in `moduli.js` (stesso Web3Forms della home, verso commercialetpetrol@gmail.com).
- Nella home: sezione `#impianti-gestori` (stile in `<style id="sezione-impianti">`), voci nel menu ☰ e nel piè di pagina.
- Ogni pagina ha titolo, descrizione, indirizzo canonico e dati strutturati (Organization, BreadcrumbList, FAQPage; Service per la consulenza).
  Le domande frequenti sono scritte sia nella pagina sia nei dati strutturati: se si cambia una risposta, va cambiata in tutti e due i punti.
- I numeri nelle pagine (29 impianti, 6 marchi) sono scritti a mano: aggiornarli se cambia la rete.
- La sezione «Ambito di intervento» raccoglie tipologie di impianti e province: sono le parole con cui le pagine vengono cercate.
- `sitemap.xml` e `robots.txt`: aggiungere qui ogni nuova pagina da far trovare su Google.
- Google Search Console: proprietà https://www.tpetrol.it/ (account commercialetpetrol@gmail.com), verificata con il file `google0f7155e32ee4327c.html`: non rimuoverlo.

## Orari delle stazioni (novembre 2026)
- In tutte le stazioni il self service è aperto H24. Gli orari del servito con il gestore sono nell'oggetto `ORARI`
  di `scripts/genera_stazioni.py` (lunedì–venerdì, sabato, domenica; `None` = chiuso). Le stazioni non elencate sono solo self.
- Ogni scheda stazione ha la sezione `#orari`; nei dati strutturati l'orario è 24/7 (self).
- Se cambia un orario: modificare `ORARI` e rilanciare `python3 scripts/genera_stazioni.py`.
