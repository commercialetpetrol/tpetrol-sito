#!/usr/bin/env python3
"""Genera le pagine /stazioni/<slug>/ a partire dai dati della home (index.html).
I prezzi non sono scritti nelle pagine: ogni pagina li legge dalla home al caricamento,
quindi l'aggiornamento automatico del mattino vale anche qui.
Da rilanciare solo se cambiano stazioni, servizi, carte o foto."""
import re, json, math, pathlib, unicodedata, html
from urllib.parse import quote
R = pathlib.Path(__file__).resolve().parent.parent
s = (R / "index.html").read_text()

def obj(name):
    t = re.search(r"const " + name + r"=(\{.*?\});", s, re.S).group(1)
    t = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', t)
    return json.loads(t)
BRAND, CARTA, CARTE, SERVIZI, LOCKER, GPLACE, GFID, SOLARE = (obj(n) for n in
    ["BRAND", "CARTA", "CARTE", "SERVIZI", "LOCKER", "GPLACE", "GFID", "SOLARE"])
ADB = set(json.loads(re.search(r"const ADBLUE=new Set\((\[.*?\])\)", s).group(1)))
CER = set(json.loads(re.search(r"const CER_NOVA=new Set\((\[.*?\])\)", s).group(1)))
blk = s[s.index("const S=["):s.index("].map(([b,n,c,la,lo,pv,mid]")]
ROWS = [json.loads(l.strip().rstrip(",")) for l in blk.splitlines()[1:] if l.strip().startswith("[")]
LD = {x["@id"].split("#pv-")[1]: x for x in json.loads(re.search(r'id="ld-stazioni">(.*?)</script>', s, re.S).group(1))["@graph"]}
FOTO = {"22021": "casilina", "12021": "nomentana", "5687": "leonardo", "5522": "marconi", "5565": "bravetta", "49512": "sabaudia", "5580": "spoleto"}
LK = {"brt": "BRT", "inpost": "InPost", "poste": "Poste Italiane + DHL"}
SLUG_FISSI = {"6413": "q8-aprilia-selciatella", "5580": "q8-spoleto-flaminia", "5579": "q8-orte-ortana",
              "27465": "enilive-bassano-in-teverina", "CMD01": "comeda-aprilia-pontina", "6416": "q8-latina-via-della-stazione",
              "6414": "q8-latina-borgo-podgora", "49512": "ip-sabaudia-borgo-vodice", "49521": "ip-san-felice-circeo"}

def slugify(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")
STOP = {"via", "viale", "piazza", "largo", "loc", "dei", "di", "della", "delle", "del", "ss", "sp", "s", "km", "p", "l"}

def slug_for(b, n, c, pv):
    if pv in SLUG_FISSI: return SLUG_FISSI[pv]
    city = slugify(re.sub(r" \(..\)$", "", c))
    words = [w for w in slugify(n).split("-") if w not in STOP and not re.search(r"\d", w) and len(w) > 1]
    return "-".join([slugify(BRAND[b]), city] + words[:3])

st = []
for b, n, c, la, lo, pv, mid in ROWS:
    st.append(dict(b=b, n=n, c=c, city=re.sub(r" \(..\)$", "", c), prov=c[-3:-1], la=la, lo=lo, pv=pv, mid=mid, slug=slug_for(b, n, c, pv)))
seen = {}
for x in st:  # nomi doppi (es. due T24 sulla Casilina): aggiungo il civico
    if x["slug"] in seen:
        for y in (seen[x["slug"]], x):
            num = re.search(r"\d+", y["n"]); y["slug"] = y["slug"] + "-" + (num.group(0) if num else y["pv"].lower())
    seen[x["slug"]] = x
assert len({x["slug"] for x in st}) == len(st)

def maps(x):
    if x["pv"] in GFID: return f"https://www.google.com/maps/place//data=!4m2!3m1!1s{GFID[x['pv']]}"
    if x["pv"] in GPLACE: return f"https://www.google.com/maps/search/?api=1&query={quote(BRAND[x['b']]+' '+x['n']+', '+x['c'])}&query_place_id={GPLACE[x['pv']]}"
    return f"https://www.google.com/maps/search/?api=1&query={x['la']}%2C{x['lo']}"
def dist(a, b):
    k = math.cos(math.radians((a["la"] + b["la"]) / 2))
    return math.hypot((a["la"] - b["la"]) * 111, (a["lo"] - b["lo"]) * 111 * k)
a_ad = lambda city: "ad" if city[0].lower() == "a" else "a"
e = html.escape

tpl = (R / "autolavaggio-aprilia" / "index.html").read_text()
footer = tpl[tpl.index("<footer"):tpl.index("</body>")].replace('href="../', 'href="../../').replace('src="../', 'src="../../')
font_pre = re.search(r'<link rel="preload"[^>]*>', tpl).group(0).replace('href="../', 'href="../../')

CSS = """<style>
.st-prices{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:14px;margin-top:22px}
.st-p{background:#00142b;color:#f2f5f9;border-radius:20px;padding:18px 20px}
.st-p span{display:block;font-size:13px;letter-spacing:.1em;text-transform:uppercase;opacity:.75}
.st-p strong{display:block;margin-top:6px;font-size:40px;line-height:1;color:#f67625;font-variant-numeric:tabular-nums;white-space:nowrap}
.st-p strong em{font-style:normal;font-size:16px;color:#f2f5f9;opacity:.8;margin-left:4px}
.st-p small{display:block;margin-top:6px;opacity:.7;font-size:13px}
.st-load{color:var(--muted)}
.st-cards{list-style:none;margin:22px 0 0;padding:0;display:flex;flex-wrap:wrap;gap:12px}
.st-cards li{display:flex;align-items:center;gap:10px;padding:10px 14px;border:1px solid var(--line);border-radius:14px;background:var(--bg);font-weight:600}
.st-cards img{height:30px;width:auto}
.st-foto{margin:0;border-radius:24px;overflow:hidden;box-shadow:var(--sh-1)}.st-foto img{display:block;width:100%;height:auto;max-height:520px;object-fit:cover}
.st-foto figcaption{padding:10px 14px;font-size:13px;color:var(--muted);background:var(--bg)}
.st-near{list-style:none;margin:18px 0 0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px}
.st-near a{display:block;padding:14px 16px;border:1px solid var(--line);border-radius:16px;background:var(--bg);text-decoration:none;color:inherit}
.st-near a b{display:block}.st-near a small{color:var(--muted)}
</style>
"""
JS = """<script>
(function(){var box=document.getElementById("st-prices"),dt=document.getElementById("pz-data"),MID=box.getAttribute("data-mid");
fetch("../../",{cache:"no-store"}).then(function(r){return r.text()}).then(function(h){
 var m=h.match(/const PREZZI=(\\{.*?\\});/s),d=h.match(/const PREZZI_DATA="([^"]*)"/);if(!m)throw 0;
 var P=JSON.parse(m[1])[MID]||[];var f=function(v){return v.toFixed(3).replace(".",",")};
 var rows=P.filter(function(e){return e[2]===1});if(!rows.length)rows=P;if(!rows.length)throw 0;
 box.innerHTML=rows.map(function(e){return '<div class="st-p"><span>'+e[0]+(e[2]===1?' · self':' · servito')+'</span><strong>'+f(e[1])+'<em>€/lt</em></strong><small>Aggiornato '+e[3].slice(0,16)+'</small></div>'}).join("");
 if(d)dt.textContent="Prezzi self service del "+d[1]+", come comunicati all'Osservaprezzi carburanti del Ministero delle Imprese.";
}).catch(function(){box.innerHTML='<p class="st-load">Prezzi non disponibili in questo momento: <a href="../../#prezzi">consultali nella home</a>.</p>'})})();
</script>
"""

def page(x):
    B = BRAND[x["b"]]; URL = f"https://www.tpetrol.it/stazioni/{x['slug']}/"; MAPS = e(maps(x))
    pv = x["pv"]; prep = a_ad(x["city"])
    serv = []
    if pv in ADB: serv.append(("AdBlue", "Disponibile in stazione per i veicoli diesel con sistema SCR."))
    for t in SERVIZI.get(pv, []):
        serv.append((t, "Nell'area di servizio." if t == "Bar tabacchi" else "Per gli autisti dei mezzi pesanti, nell'area di servizio."))
    if pv == "6413": serv.append(("Autolavaggio self H24", 'Portale WashTec, acqua a ciclo chiuso, pagamento con carta o contanti e fattura dalla cassa self. <a href="../../autolavaggio-aprilia/">Scopri l\'autolavaggio</a>.'))
    if LOCKER.get(pv): serv.append(("Locker pacchi H24", "Ritiro e spedizione con " + ", ".join(LK[k] for k in LOCKER[pv]) + ", a qualsiasi ora. <a href=\"../../#locker\">Tutti i locker</a>."))
    if pv in SOLARE:
        kw = sum(r[0] for r in SOLARE[pv]); kwh = sum(r[1] for r in SOLARE[pv])
        serv.append(("Energia dal sole", f"Impianto fotovoltaico da {kw} kW con {kwh} kWh di batterie di accumulo." + (" La stazione fa parte della comunità energetica rinnovabile CER Nova ETS." if pv in CER else "")))
    serv.append(("Fattura elettronica", 'Fattura del rifornimento anche in self service o con l\'app gratuita fattura1click. <a href="../../#fattura">Come funziona</a>.'))
    serv.append(("Carta carburante T.Petrol", 'Per aziende e professionisti, su tutta la rete. <a href="../../#carta">Richiedila online</a>.'))
    carte = [k for k in CARTE.get(pv, []) + ["amex"] if k in CARTA]
    cards = "".join(f'<li><img src="../../{CARTA[k][1]}" alt="" loading="lazy"><span>{e(CARTA[k][0])}</span></li>' for k in carte)
    nomi_serv = [t for t, _ in serv if t not in ("Fattura elettronica", "Carta carburante T.Petrol")]
    nomi_serv = [t if t.startswith("AdBlue") else t[0].lower() + t[1:] for t in nomi_serv]
    lead = ("Self service" + (", " + ", ".join(nomi_serv[:-1]) + " e " + nomi_serv[-1] if len(nomi_serv) > 1 else (" e " + nomi_serv[0] if nomi_serv else ""))
            + f". Una stazione di servizio della rete T.Petrol a {x['city']}.")
    facts = [(B, "marchio"), (str(len(carte)), "carte flotta accettate")]
    if LOCKER.get(pv): facts.append(("H24", "locker pacchi"))
    if pv in SOLARE: facts.append((f"{sum(r[0] for r in SOLARE[pv])} kW", "di fotovoltaico"))
    near = sorted((y for y in st if y is not x), key=lambda y: dist(x, y))[:3]
    near_html = "".join(f'<li><a href="../{y["slug"]}/"><b>{e(BRAND[y["b"]])} · {e(y["city"])}</b><small>{e(y["n"])} · {dist(x, y):.0f} km</small></a></li>' for y in near)
    foto = ""
    if pv in FOTO:
        foto = f'''  <section class="sec band" aria-label="Foto della stazione">
    <div class="wrap">
      <figure class="st-foto"><img src="../../galleria/{FOTO[pv]}.jpg" alt="Stazione {e(B)} {e(x['n'])}, {e(x['city'])}" loading="lazy"><figcaption>I prezzi visibili nella foto risalgono al momento dello scatto e non rappresentano i prezzi attuali.</figcaption></figure>
    </div>
  </section>
'''
    title = f"Distributore {B} {x['city']}, {x['n']} – prezzi e servizi | T.Petrol"
    desc = f"Stazione di servizio {B} T.Petrol {prep} {x['city']} ({x['prov']}), {x['n']}: prezzi self di oggi" + (", " + ", ".join(nomi_serv) if nomi_serv else "") + " e carte carburante accettate."
    ld = dict(LD[pv]); ld["@context"] = "https://schema.org"; ld["url"] = URL; ld["mainEntityOfPage"] = URL
    if pv in FOTO: ld["image"] = f"https://www.tpetrol.it/galleria/{FOTO[pv]}.jpg"
    bc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "T.Petrol", "item": "https://www.tpetrol.it/"},
        {"@type": "ListItem", "position": 2, "name": "Stazioni di servizio", "item": "https://www.tpetrol.it/#rete"},
        {"@type": "ListItem", "position": 3, "name": f"{B} {x['city']} – {x['n']}", "item": URL}]}
    cards_serv = "".join(f'<article class="card"><h3>{e(t)}</h3><p>{d}</p></article>' for t, d in serv)
    facts_html = "".join(f"<li><strong>{e(a)}</strong><span>{e(b)}</span></li>" for a, b in facts)
    return f'''<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{URL}">
<link rel="icon" href="../../logo.png">
<meta name="theme-color" content="#00142b">
<meta property="og:type" content="website">
<meta property="og:locale" content="it_IT">
<meta property="og:site_name" content="T.Petrol">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{URL}">
<meta property="og:image" content="https://www.tpetrol.it/{('galleria/'+FOTO[pv]+'.jpg') if pv in FOTO else 'og.jpg'}">
{font_pre}
<link rel="stylesheet" href="../../pagine.css">
<script type="application/ld+json">{json.dumps([ld, bc], ensure_ascii=False)}</script>
{CSS}</head>
<body>
<header class="top band">
  <div class="wrap">
    <a class="logo" href="../../" aria-label="T.Petrol, vai alla home"><img src="../../logo.png" alt="T.Petrol" width="161" height="38"></a>
    <nav aria-label="Navigazione">
      <a class="hide-m" href="../../">Home</a>
      <a class="hide-m" href="../../#rete">Tutte le stazioni</a>
      <a class="hide-m" href="../../#contatti">Contatti</a>
      <a class="pill pill-sun" href="{MAPS}" target="_blank" rel="noopener">Indicazioni</a>
    </nav>
  </div>
</header>

<main>
  <section class="hero band">
    <div class="wrap">
      <p class="crumbs"><a href="../../">T.Petrol</a> › <a href="../../#rete">Stazioni di servizio</a> › {e(x['city'])}, {e(x['n'])}</p>
      <p class="kick">Stazione di servizio {e(B)} · {e(x['city'])} ({e(x['prov'])})</p>
      <h1>Distributore <b>{e(B)}</b> {prep} {e(x['city'])}, {e(x['n'])}</h1>
      <p class="lead">{e(lead)}</p>
      <div class="cta">
        <a class="pill pill-sun" href="{MAPS}" target="_blank" rel="noopener">Indicazioni stradali</a>
        <a class="pill pill-white" href="#prezzi">Prezzi di oggi</a>
      </div>
      <ul class="facts" aria-label="La stazione in breve">{facts_html}</ul>
    </div>
  </section>

{foto}  <section class="sec band" id="prezzi" aria-labelledby="s1">
    <div class="wrap">
      <h2 id="s1">Prezzi di oggi</h2>
      <p class="intro" id="pz-data">Prezzi self service comunicati all'Osservaprezzi carburanti del Ministero delle Imprese.</p>
      <div class="st-prices" id="st-prices" data-mid="{x['mid']}"><p class="st-load">Caricamento dei prezzi…</p></div>
      <p class="intro" style="font-size:14px">Confronta con le altre stazioni: <a href="../../#prezzi">tutti i prezzi della rete T.Petrol</a>.</p>
    </div>
  </section>

  <section class="sec band soft" aria-labelledby="s2">
    <div class="wrap">
      <h2 id="s2">Servizi in stazione</h2>
      <div class="grid g3">{cards_serv}</div>
    </div>
  </section>

  <section class="sec band" aria-labelledby="s3">
    <div class="wrap">
      <h2 id="s3">Pagamenti e carte accettate</h2>
      <p class="intro">Contanti, carte di credito e PagoBANCOMAT, più queste carte carburante e flotta:</p>
      <ul class="st-cards">{cards}</ul>
    </div>
  </section>

  <section class="sec band soft" aria-labelledby="s4">
    <div class="wrap">
      <h2 id="s4">Dove si trova</h2>
      <div class="cross"><div><b>{e(B)} T.Petrol · {e(x['n'])}, {e(x['c'])}</b><span>Coordinate {x['la']}, {x['lo']}</span></div><a class="pill pill-sun" href="{MAPS}" target="_blank" rel="noopener">Apri in Google Maps</a></div>
      <h3 style="margin-top:34px">Altre stazioni T.Petrol vicine</h3>
      <ul class="st-near">{near_html}</ul>
    </div>
  </section>
</main>

{footer}{JS}</body>
</html>
'''

out = R / "stazioni"
for x in st:
    d = out / x["slug"]; d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(page(x))
(out / "elenco.json").write_text(json.dumps({x["pv"]: x["slug"] for x in st}, ensure_ascii=False, indent=1))
print(len(st), "pagine generate")
for x in st: print(x["pv"], x["slug"])
