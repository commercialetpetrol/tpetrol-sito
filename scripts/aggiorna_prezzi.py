"""Aggiorna i prezzi self nel sito dai dati aperti MIMIT (Osservaprezzi carburanti).
Legge gli id MIMIT degli impianti da index.html, scarica prezzo_alle_8.csv e riscrive
le righe `const PREZZI_DATA=...;` e `const PREZZI=...;`. Se il download fallisce non tocca nulla."""
import csv, io, json, re, sys, urllib.request, pathlib
URL="https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv"
p=pathlib.Path(__file__).resolve().parent.parent/"index.html"
html=p.read_text(encoding="utf-8")
ids=set(re.findall(r'"[A-Z0-9]+", "(\d{4,6})"\]',html))
if len(ids)<20: sys.exit(f"id impianti non trovati ({len(ids)})")
req=urllib.request.Request(URL,headers={"User-Agent":"tpetrol-sito/1.0"})
try: raw=urllib.request.urlopen(req,timeout=90).read().decode("utf-8","replace")
except Exception as e: sys.exit(f"download MIMIT non riuscito: {e}")
lines=raw.splitlines()
m=re.search(r"(\d{4})-(\d{2})-(\d{2})",lines[0] if lines else "")
if not m: sys.exit("formato CSV inatteso")
data=f"{m.group(3)}/{m.group(2)}/{m.group(1)}"
sep="|" if "|" in lines[1] else ";"
P={}
for r in csv.reader(lines[2:],delimiter=sep):
    if len(r)<5 or r[0] not in ids: continue
    try: v=float(r[2].replace(",","."))
    except ValueError: continue
    P.setdefault(r[0],[]).append([r[1],v,1 if r[3].strip()=="1" else 0,r[4]])
if len(P)<len(ids)*0.6: sys.exit(f"troppi impianti senza prezzo ({len(P)}/{len(ids)})")
new=re.sub(r'const PREZZI_DATA="[^"]*";',f'const PREZZI_DATA="{data}";',html,count=1)
new=re.sub(r'const PREZZI=\{.*?\};',"const PREZZI="+json.dumps(P,separators=(",",":"),ensure_ascii=False)+";",new,count=1,flags=re.S)
if new!=html: p.write_text(new,encoding="utf-8"); print(f"prezzi aggiornati al {data}: {len(P)} impianti")
else: print("nessuna variazione")
