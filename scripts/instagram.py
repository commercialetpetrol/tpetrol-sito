"""Prepara ig.json per il sito da instagram_raw.json (scritto ogni giorno da Claude con i dati Metricool).
instagram_raw.json: {"aggiornato": ISO, "post": [{"id","url","imageUrl","testo","data","like","commenti","tipo"}]}
Scarica le immagini in ig/<id>.jpg (le foto di Instagram scadono) e scrive ig.json con i percorsi locali.
Tiene i 12 post più recenti e cancella le immagini non più usate."""
import json, pathlib, re, urllib.request
root = pathlib.Path(__file__).resolve().parent.parent
raw = json.loads((root / "instagram_raw.json").read_text(encoding="utf-8"))
posts = sorted(raw.get("post", []), key=lambda p: p.get("data") or "", reverse=True)[:12]
igdir = root / "ig"; igdir.mkdir(exist_ok=True)
out, keep = [], set()
for p in posts:
    pid = re.sub(r"[^A-Za-z0-9_-]", "", str(p.get("id") or p.get("url") or ""))[-40:] or str(len(out))
    f = igdir / f"{pid}.jpg"
    if not f.exists() and p.get("imageUrl"):
        try:
            req = urllib.request.Request(p["imageUrl"], headers={"User-Agent": "Mozilla/5.0"})
            f.write_bytes(urllib.request.urlopen(req, timeout=60).read())
        except Exception as e:
            print("immagine non scaricata", pid, e)
    if not f.exists():
        continue
    keep.add(f.name)
    out.append({"url": p.get("url"), "img": f"ig/{f.name}", "testo": p.get("testo", ""), "data": p.get("data"),
                "like": p.get("like", 0), "commenti": p.get("commenti", 0), "tipo": p.get("tipo", "")})
for f in igdir.glob("*.jpg"):
    if f.name not in keep:
        f.unlink()
(root / "ig.json").write_text(json.dumps({"aggiornato": raw.get("aggiornato"), "post": out}, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"ig.json: {len(out)} post")
