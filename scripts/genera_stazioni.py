#!/usr/bin/env python3
"""Genera le pagine /stazioni/<slug>/ a partire dai dati della home (index.html).
I prezzi non sono scritti nelle pagine: ogni pagina li legge dalla home al caricamento,
quindi l'aggiornamento automatico del mattino vale anche qui.
Da rilanciare solo se cambiano stazioni, servizi, carte o foto."""
import urllib.parse
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
FOTO = {"22021": "casilina", "12021": "nomentana", "5687": "leonardo", "5522": "marconi-scheda", "5565": "bravetta-scheda", "49512": "sabaudia", "5580": "spoleto", "5229": "sant-egidio", "6413": "aprilia", "49513": "farfa-scheda", "49521": "circeo-scheda", "6414": "podgora-scheda", "49510": "arsoli-scheda", "CMD01": "comeda-scheda", "5579": "orte", "49511": "pontinia-scheda", "6415": "cisterna-scheda"}
GPL_PV = {"CMD01", "5580", "27465", "6413"}  # stazioni con GPL indicate nella scheda (confermate da Federico)
LK = {"brt": "BRT", "inpost": "InPost", "poste": "Poste Italiane + DHL"}
# Orari (comunicati da Federico, novembre 2026): il self service è aperto H24 in tutte le stazioni.
# Qui solo gli orari del servito con il gestore: (lunedì-venerdì, sabato, domenica); None = servito chiuso.
# Le stazioni non elencate sono solo self, senza servito.
_SPEZ = (["07:00-12:30", "15:00-19:00"], ["07:00-12:30"], None)
ORARI = {pv: _SPEZ for pv in ["49518", "5522", "5581", "49514", "6413", "6415", "6416", "5229"]}
ORARI.update({
    "49512": (["07:00-12:00", "15:00-19:00"], ["07:00-12:00"], None),  # Sabaudia
    "5580": (["07:00-13:00", "14:30-18:00"], None, None),               # Spoleto
    "CMD01": (["06:00-19:00"], ["06:00-19:00"], ["06:00-17:00"]),       # Aprilia Comeda
    "5579": (["06:00-18:00"], ["06:00-15:00"], ["06:00-18:00"]),        # Orte
    "27465": (["05:00-21:00"],) * 3,                                    # Bassano in Teverina
    "49515": (["05:00-12:00"], ["05:00-12:00"], None),                  # Roma Bufalini
})
def ora(t):
    h, m = t.split(":"); return str(int(h)) + ("" if m == "00" else ":" + m)
def fasce(r):
    return "chiuso" if not r else " e ".join(ora(a) + "–" + ora(b) for a, b in (x.split("-") for x in r))
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
@media (max-width:640px){.facts{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:16px 12px}.facts span{font-size:11px}}
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
.st-orari{border-collapse:collapse;margin-top:12px;min-width:min(100%,420px)}
.st-orari th,.st-orari td{text-align:left;padding:10px 16px 10px 0;border-bottom:1px solid var(--line)}
.st-orari th{font-weight:600}.st-orari td{font-variant-numeric:tabular-nums}
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
    if pv in GPL_PV: serv.append(("GPL", "Rifornimento di GPL in stazione."))
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
    nomi_serv = [t if t.startswith(("AdBlue", "GPL")) else t[0].lower() + t[1:] for t in nomi_serv]
    lead = ("Self service H24" + (", " + ", ".join(nomi_serv[:-1]) + (" ed " if nomi_serv[-1][0] in "eE" else " e ") + nomi_serv[-1] if len(nomi_serv) > 1 else (" e " + nomi_serv[0] if nomi_serv else ""))
            + f". Una stazione di servizio della rete T.Petrol a {x['city']}.")
    facts = [(B, "marchio"), ("H24", "self service"), (str(len(carte)), "carte flotta accettate")]
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
    ld["openingHoursSpecification"] = [{"@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], "opens": "00:00", "closes": "23:59"}]
    o = ORARI.get(pv)
    if o:
        righe = "".join(f"<tr><th scope=\"row\">{g}</th><td>{fasce(r)}</td></tr>" for g, r in zip(("Dal lunedì al venerdì", "Sabato", "Domenica"), o))
        servito = f'<h3 style="margin-top:28px">Servito con il gestore</h3><table class="st-orari"><tbody>{righe}</tbody></table><p class="intro" style="font-size:14px">Fuori da questi orari il rifornimento è sempre disponibile al self service.</p>'
    else:
        servito = '<p class="intro">Stazione completamente self service: nessun orario di chiusura.</p>'
    if pv in FOTO: ld["image"] = f"https://www.tpetrol.it/galleria/{FOTO[pv]}.jpg"
    bc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "T.Petrol", "item": "https://www.tpetrol.it/"},
        {"@type": "ListItem", "position": 2, "name": "Stazioni di servizio", "item": "https://www.tpetrol.it/stazioni/"},
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
      <a class="hide-m" href="../">Tutte le stazioni</a>
      <a class="hide-m" href="../../#contatti">Contatti</a>
      <a class="pill pill-sun" href="{MAPS}" target="_blank" rel="noopener">Indicazioni</a>
    </nav>
  </div>
</header>

<main>
  <section class="hero band">
    <div class="wrap">
      <p class="crumbs"><a href="../../">T.Petrol</a> › <a href="../">Stazioni di servizio</a> › {e(x['city'])}, {e(x['n'])}</p>
      <p class="kick">Stazione di servizio {e(B)} · {e(x['city'])} ({e(x['prov'])})</p>
      <h1>Distributore <b>{e(B)}</b> {prep} {e(x['city'])}, {e(x['n'])}</h1>
      <p class="lead">{e(lead)}</p>
      <div class="cta">
        <a class="pill pill-sun" href="{MAPS}" target="_blank" rel="noopener">Indicazioni stradali</a>
        <a class="pill pill-white" href="#prezzi">Prezzi di oggi</a>
        <a class="pill pill-white wa" href="https://wa.me/?text={urllib.parse.quote(f"Distributore {B} T.Petrol – {x['n']}, {x['city']} ({x['prov']}): {URL}")}" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true" style="margin-right:8px;color:#25d366"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.7.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.3-.4.7-1.4a.5.5 0 0 0 0-.5l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.7 11.9 11.9 0 0 0 4.6 4c1.7.7 2.4.8 3.2.6a2.8 2.8 0 0 0 1.8-1.3 2.3 2.3 0 0 0 .2-1.3c-.1-.1-.3-.2-.5-.3z"/></svg>Condividi su WhatsApp</a>
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

  <section class="sec band" id="orari" aria-labelledby="s5">
    <div class="wrap">
      <h2 id="s5">Orari</h2>
      <div class="cross"><div><b>Self service aperto 24 ore su 24</b><span>Tutti i giorni, festivi compresi</span></div></div>
      {servito}
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

# ---- pagina indice /stazioni/
ZONE = [("Roma", lambda x: x["c"] == "Roma (RM)"), ("Provincia di Roma", lambda x: x["prov"] == "RM"),
        ("Latina e provincia", lambda x: x["prov"] == "LT"), ("Provincia di Viterbo", lambda x: x["prov"] == "VT"),
        ("Provincia di Rieti", lambda x: x["prov"] == "RI"), ("Umbria", lambda x: x["prov"] == "PG"), ("Abruzzo", lambda x: x["prov"] == "TE")]
def zona(x): return next(i for i, (_, f) in enumerate(ZONE) if f(x))
def tags(x):
    pv = x["pv"]; t = []
    if pv in ADB: t.append("AdBlue")
    t += SERVIZI.get(pv, [])
    if pv == "6413": t.append("Autolavaggio H24")
    if LOCKER.get(pv): t.append("Locker H24")
    if pv in SOLARE: t.append("Fotovoltaico")
    return t
grp = ""
for i, (nome, _) in enumerate(ZONE):
    L = sorted([x for x in st if zona(x) == i], key=lambda x: (x["city"], x["n"]))
    if not L: continue
    items = ""
    for x in L:
        tg = "".join(f"<i>{e(t)}</i>" for t in tags(x))
        items += (f'<li><a href="{x["slug"]}/"><span class="sx-b">{e(BRAND[x["b"]])}</span><b>{e(x["city"])}</b><small>{e(x["n"])}</small>'
                  + (f'<span class="sx-t">{tg}</span>' if tg else "") + "</a></li>")
    grp += f'<h2 class="sx-h">{e(nome)} <span>{len(L)}</span></h2>\n      <ul class="sx-list">{items}</ul>\n      '
URLI = "https://www.tpetrol.it/stazioni/"
ld_i = {"@context": "https://schema.org", "@type": "ItemList", "name": "Stazioni di servizio T.Petrol", "numberOfItems": len(st),
        "itemListElement": [{"@type": "ListItem", "position": k + 1, "url": f"{URLI}{x['slug']}/", "name": f"{BRAND[x['b']]} {x['city']} – {x['n']}"} for k, x in enumerate(st)]}
pre_i = page(st[0]).split("<header")[0]
pre_i = re.sub(r"<title>.*?</title>", f"<title>Le nostre stazioni di servizio – {len(st)} distributori a Roma, Latina, Umbria e Abruzzo | T.Petrol</title>", pre_i, flags=re.S)
pre_i = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="Tutte le {len(st)} stazioni di servizio T.Petrol tra Roma, Latina e province, Viterbo, Rieti, Spoleto e Teramo: indirizzi, marchi, servizi e prezzi self di oggi.">', pre_i)
pre_i = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{URLI}">', pre_i)
pre_i = re.sub(r'<meta property="og:(title|description|url|image)" content="[^"]*">\n', "", pre_i)
pre_i = re.sub(r'<script type="application/ld\+json">.*?</script>', lambda m: '<script type="application/ld+json">' + json.dumps(ld_i, ensure_ascii=False) + "</script>", pre_i, flags=re.S)
pre_i = pre_i.replace('href="../../', 'href="../').replace("<style>", """<style>
.sx-h{margin:40px 0 0;font-size:clamp(22px,2.6vw,28px)}.sx-h:first-child{margin-top:0}.sx-h span{font-size:15px;color:var(--muted);font-weight:600;margin-left:6px}
.sx-list{list-style:none;margin:16px 0 0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.sx-list a{display:grid;gap:3px;height:100%;padding:16px 18px;border:1px solid var(--line);border-radius:18px;background:var(--bg);text-decoration:none;color:inherit;transition:border-color .15s,transform .15s}
.sx-list a:hover{border-color:#f67625;transform:translateY(-2px)}
.sx-b{font-size:12px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#b04a05}.sx-list b{font-size:18px}.sx-list small{color:var(--muted)}
.sx-t{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}.sx-t i{font-style:normal;font-size:11.5px;font-weight:700;padding:2px 8px;border-radius:999px;background:rgba(246,118,37,.14);color:#b04a05}
""", 1)
foot_i = footer.replace('href="../../', 'href="../').replace('src="../../', 'src="../')
html_i = pre_i + f'''<header class="top band">
  <div class="wrap">
    <a class="logo" href="../" aria-label="T.Petrol, vai alla home"><img src="../logo.png" alt="T.Petrol" width="161" height="38"></a>
    <nav aria-label="Navigazione">
      <a class="hide-m" href="../">Home</a>
      <a class="hide-m" href="../#prezzi">Prezzi di oggi</a>
      <a class="pill pill-sun" href="../#contatti">Contatti</a>
    </nav>
  </div>
</header>
<main>
  <section class="hero band">
    <div class="wrap">
      <p class="crumbs"><a href="../">T.Petrol</a> › Stazioni di servizio</p>
      <p class="kick">La rete T.Petrol</p>
      <h1>Le nostre <b>{len(st)} stazioni</b> di servizio</h1>
      <p class="lead">Distributori di carburante tra Roma, Latina e le loro province, Viterbo, Rieti, Spoleto e Teramo. Scegli una stazione per vedere indirizzo, servizi, carte accettate e prezzi self di oggi.</p>
      <div class="cta"><a class="pill pill-sun" href="../#rete">Apri la mappa</a><a class="pill pill-white" href="../#prezzi">Prezzi di oggi</a></div>
    </div>
  </section>
  <section class="sec band">
    <div class="wrap">
      {grp}
    </div>
  </section>
</main>

{foot_i}</body>
</html>
'''
(out / "index.html").write_text(html_i)
print("indice /stazioni/ generato")

# ---- C10: pagine per zona (solo zone con almeno 2 stazioni)
ZPAG = {0: ("distributori-roma", "Distributori di carburante a Roma", "a Roma", "nella città di Roma"),
        1: ("distributori-provincia-di-roma", "Distributori di carburante in provincia di Roma", "in provincia di Roma", "in provincia di Roma"),
        2: ("distributori-latina", "Distributori di carburante a Latina e provincia", "a Latina e provincia", "a Latina e in provincia"),
        3: ("distributori-viterbo", "Distributori di carburante in provincia di Viterbo", "in provincia di Viterbo", "in provincia di Viterbo")}
zone_links = {}
for i, (zs, h1t, dove, dove_l) in ZPAG.items():
    L = sorted([x for x in st if zona(x) == i], key=lambda x: (x["city"], x["n"]))
    if len(L) < 2:
        continue
    zone_links[i] = zs
    items = ""
    for x in L:
        tg = "".join(f"<i>{e(t)}</i>" for t in tags(x))
        items += (f'<li><a href="../{x["slug"]}/"><span class="sx-b">{e(BRAND[x["b"]])}</span><b>{e(x["city"])}</b><small>{e(x["n"])}</small>'
                  + (f'<span class="sx-t">{tg}</span>' if tg else "") + "</a></li>")
    marchi = sorted({BRAND[x["b"]] for x in L})
    comuni = sorted({x["city"] for x in L})
    URLZ = f"{URLI}{zs}/"
    ldz = [{"@context": "https://schema.org", "@type": "ItemList", "name": h1t + " – T.Petrol", "numberOfItems": len(L),
            "itemListElement": [{"@type": "ListItem", "position": k + 1, "url": f"{URLI}{x['slug']}/", "name": f"{BRAND[x['b']]} {x['city']} – {x['n']}"} for k, x in enumerate(L)]},
           {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
               {"@type": "ListItem", "position": 1, "name": "T.Petrol", "item": "https://www.tpetrol.it/"},
               {"@type": "ListItem", "position": 2, "name": "Stazioni di servizio", "item": URLI},
               {"@type": "ListItem", "position": 3, "name": ZONE[i][0], "item": URLZ}]}]
    pre_z = pre_i.replace('href="../', 'href="../../').replace('src="../', 'src="../../')
    pre_z = re.sub(r"<title>.*?</title>", f"<title>{e(h1t)} – {len(L)} stazioni T.Petrol, prezzi self di oggi</title>", pre_z, flags=re.S)
    pre_z = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{len(L)} stazioni di servizio T.Petrol {e(dove)} ({e(", ".join(marchi))}): indirizzi, servizi, carte accettate e prezzi self aggiornati ogni giorno.">', pre_z)
    pre_z = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{URLZ}">', pre_z)
    pre_z = re.sub(r'<script type="application/ld\+json">.*?</script>', lambda m: '<script type="application/ld+json">' + json.dumps(ldz, ensure_ascii=False) + "</script>", pre_z, flags=re.S)
    foot_z = foot_i.replace('href="../', 'href="../../').replace('src="../', 'src="../../')
    zona_nome = e(ZONE[i][0])
    h1h = e(h1t).replace("carburante", "<b>carburante</b>", 1)
    lead = f"{len(L)} stazioni di servizio T.Petrol {e(dove_l)} ({e(', '.join(comuni))}), con i marchi {e(', '.join(marchi))}. Apri una stazione per vedere indirizzo, servizi, carte accettate e prezzi self di oggi."
    html_z = (pre_z
        + '<header class="top band">\n  <div class="wrap">\n'
        + '    <a class="logo" href="../../" aria-label="T.Petrol, vai alla home"><img src="../../logo.png" alt="T.Petrol" width="161" height="38"></a>\n'
        + '    <nav aria-label="Navigazione">\n      <a class="hide-m" href="../../">Home</a>\n      <a class="hide-m" href="../">Tutte le stazioni</a>\n'
        + '      <a class="pill pill-sun" href="../../#contatti">Contatti</a>\n    </nav>\n  </div>\n</header>\n<main>\n'
        + '  <section class="hero band">\n    <div class="wrap">\n'
        + f'      <p class="crumbs"><a href="../../">T.Petrol</a> › <a href="../">Stazioni di servizio</a> › {zona_nome}</p>\n'
        + f'      <p class="kick">Stazioni di servizio {e(dove)}</p>\n'
        + f'      <h1>{h1h}</h1>\n'
        + f'      <p class="lead">{lead}</p>\n'
        + '      <div class="cta"><a class="pill pill-sun" href="../../#prezzi">Prezzi di oggi</a><a class="pill pill-white" href="../">Tutte le stazioni</a></div>\n'
        + '    </div>\n  </section>\n  <section class="sec band">\n    <div class="wrap">\n'
        + f'      <ul class="sx-list">{items}</ul>\n'
        + '    </div>\n  </section>\n</main>\n\n'
        + foot_z + '</body>\n</html>\n')
    (out / zs).mkdir(exist_ok=True)
    (out / zs / "index.html").write_text(html_z)
    print("zona", zs, len(L))

# link dalle intestazioni della pagina indice alle pagine per zona
html_i2 = (out / "index.html").read_text()
for i, zs in zone_links.items():
    nome = e(ZONE[i][0])
    html_i2 = html_i2.replace(f'<h2 class="sx-h">{nome} <span>', f'<h2 class="sx-h"><a href="{zs}/">{nome}</a> <span>', 1)
html_i2 = html_i2.replace(".sx-h span{", ".sx-h a{color:inherit;text-decoration-color:rgba(246,118,37,.6);text-underline-offset:5px}.sx-h span{", 1)
(out / "index.html").write_text(html_i2)
