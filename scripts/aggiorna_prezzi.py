"""Aggiorna i prezzi self nel sito dai dati MIMIT (Osservaprezzi carburanti).

1. prova il CSV giornaliero prezzo_alle_8.csv (più tentativi, attesa lunga);
2. se non risponde, chiede i prezzi impianto per impianto al servizio Osservaprezzi.
Riscrive le righe `const PREZZI_DATA=...;` e `const PREZZI=...;` di index.html.
Se nessuna fonte risponde non tocca nulla."""
import csv, datetime as dt, json, re, sys, time, urllib.request, pathlib

CSV_URL = "https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv"
API_URL = "https://carburanti.mise.gov.it/ospzApi/registry/servicearea/{}"
UA = {"User-Agent": "Mozilla/5.0 (tpetrol-sito; aggiornamento prezzi)", "Accept": "*/*"}

p = pathlib.Path(__file__).resolve().parent.parent / "index.html"
html = p.read_text(encoding="utf-8")
ids = sorted(set(re.findall(r'"[A-Z0-9]+", "(\d{4,6})"\]', html)))
if len(ids) < 20:
    sys.exit(f"id impianti non trovati ({len(ids)})")


def get(url, timeout):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")


def from_csv():
    for attempt in range(3):
        try:
            raw = get(CSV_URL, 240)
            break
        except Exception as e:
            print(f"CSV tentativo {attempt + 1}: {e}")
            time.sleep(20)
    else:
        return None
    lines = raw.splitlines()
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", lines[0] if lines else "")
    if not m:
        return None
    sep = "|" if "|" in lines[1] else ";"
    P = {}
    for r in csv.reader(lines[2:], delimiter=sep):
        if len(r) < 5 or r[0] not in ids:
            continue
        try:
            v = float(r[2].replace(",", "."))
        except ValueError:
            continue
        P.setdefault(r[0], []).append([r[1], v, 1 if r[3].strip() == "1" else 0, r[4]])
    return f"{m.group(3)}/{m.group(2)}/{m.group(1)}", P


def from_api():
    P = {}
    for i in ids:
        try:
            d = json.loads(get(API_URL.format(i), 30))
        except Exception as e:
            print(f"API {i}: {e}")
            continue
        for f in d.get("fuels", []):
            try:
                v = float(f.get("price"))
            except (TypeError, ValueError):
                continue
            when = (f.get("insertDate") or "")[:19]
            try:
                when = dt.datetime.fromisoformat(when).strftime("%d/%m/%Y %H:%M:%S")
            except ValueError:
                pass
            P.setdefault(i, []).append([f.get("name", ""), v, 1 if f.get("isSelf") else 0, when])
        time.sleep(0.5)
    return dt.date.today().strftime("%d/%m/%Y"), P


res = from_csv()
if not res or len(res[1]) < len(ids) * 0.6:
    print("CSV non disponibile, provo il servizio impianto per impianto")
    res = from_api()
data, P = res
if len(P) < len(ids) * 0.6:
    sys.exit(f"troppi impianti senza prezzo ({len(P)}/{len(ids)}): sito non modificato")

new = re.sub(r'const PREZZI_DATA="[^"]*";', f'const PREZZI_DATA="{data}";', html, count=1)
new = re.sub(r"const PREZZI=\{.*?\};", "const PREZZI=" + json.dumps(P, separators=(",", ":"), ensure_ascii=False) + ";", new, count=1, flags=re.S)
if new != html:
    p.write_text(new, encoding="utf-8")
    print(f"prezzi aggiornati al {data}: {len(P)} impianti")
else:
    print("nessuna variazione")
