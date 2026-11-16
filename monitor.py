import json, os, re, urllib.request, urllib.parse
import xml.etree.ElementTree as ET

TOKEN = os.environ["TELEGRAM_TOKEN"]
UA = {"User-Agent": "Mozilla/5.0 (gta6-monitor)"}
FEEDS = {
    "Google News ES": "https://news.google.com/rss/search?q=GTA+6&hl=es&gl=ES&ceid=ES:es",
    "Google News EN": "https://news.google.com/rss/search?q=GTA+6+when:2d&hl=en-US&gl=US&ceid=US:en",
    "Rockstar (web)": "https://news.google.com/rss/search?q=site:rockstargames.com+GTA+VI&hl=en-US&gl=US&ceid=US:en",
    "Reddit r/GTA6": "https://www.reddit.com/r/GTA6/new/.rss",
}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=30).read()

def parse(name, xml):
    root = ET.fromstring(xml)
    out = []
    for it in root.iter("item"):
        out.append((name, (it.findtext("title") or "").strip(), (it.findtext("link") or "").strip()))
    ns = "{http://www.w3.org/2005/Atom}"
    for e in root.iter(ns + "entry"):
        l = e.find(ns + "link")
        out.append((name, (e.findtext(ns + "title") or "").strip(), l.get("href") if l is not None else ""))
    return out

def tg(method, **data):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    body = urllib.parse.urlencode(data).encode()
    return json.load(urllib.request.urlopen(url, body, timeout=30))

def chat_id():
    cid = os.environ.get("TELEGRAM_CHAT_ID")
    if cid:
        return cid
    for u in tg("getUpdates").get("result", []):
        m = u.get("message")
        if m:
            return str(m["chat"]["id"])
    raise SystemExit("Escribe un mensaje a tu bot y vuelve a ejecutar")

seen_file = "seen.json"
first = not os.path.exists(seen_file)
seen = set(json.load(open(seen_file))) if not first else set()

items = []
for name, url in FEEDS.items():
    try:
        items += parse(name, get(url))
    except Exception as e:
        print("fallo", name, e)

new = [i for i in items if i[2] and i[2] not in seen]
cid = chat_id()

if first:
    tg("sendMessage", chat_id=cid, text=f"Monitor GTA 6 activado. {len(new)} items previos registrados; a partir de ahora solo novedades.")
else:
    for name, title, link in new[:15]:
        tg("sendMessage", chat_id=cid, text=f"[{name}] {title}\n{link}")

seen |= {i[2] for i in items if i[2]}
json.dump(sorted(seen)[-3000:], open(seen_file, "w"))
