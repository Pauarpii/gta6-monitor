import json, os, re, time, urllib.request, urllib.parse
import xml.etree.ElementTree as ET

TOKEN = os.environ["TELEGRAM_TOKEN"]
UA = {"User-Agent": "Mozilla/5.0 (gta6-monitor)"}
FEEDS = {
    "Reddit r/GTA6": "https://www.reddit.com/r/GTA6/new/.rss",
    "GTAForum": "https://gtaforum.org/articles.html/3_gaming-news/?d=1&rss=1",
    "RockstarINTEL": "https://rockstarintel.com/feed/",
    "YouTube Rockstar": "https://www.youtube.com/feeds/videos.xml?user=rockstargames",
    "Google News ES": "https://news.google.com/rss/search?q=GTA+6&hl=es&gl=ES&ceid=ES:es",
    "Google News EN": "https://news.google.com/rss/search?q=GTA+6+when:2d&hl=en-US&gl=US&ceid=US:en",
}

OFFICIAL = {"YouTube Rockstar"}
BLOCK = re.compile(r"casino|betting|sportsbook|free spins|\bsponsor\b|#ad\b|gambl|slots?\b", re.I)

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
seen_list = json.load(open(seen_file)) if not first else []
seen = set(seen_list)

items = []
for n, (name, url) in enumerate(FEEDS.items()):
    if n:
        time.sleep(3)
    try:
        items += parse(name, get(url))
    except Exception as e:
        print("fallo", name, e)

new = [i for i in items if i[2] and i[2] not in seen and not BLOCK.search(i[1])]
cid = chat_id()

if first:
    tg("sendMessage", chat_id=cid, text=f"Monitor GTA 6 activado. {len(new)} items previos registrados; a partir de ahora solo novedades.")
else:
    for name, title, link in new[:15]:
        tag = "OFICIAL" if name in OFFICIAL else "RUMOR/SIN CONFIRMAR"
        tg("sendMessage", chat_id=cid, text=f"[{tag}] [{name}] {title}\n{link}")

for i in items:
    if i[2] and i[2] not in seen:
        seen.add(i[2])
        seen_list.append(i[2])
json.dump(seen_list[-3000:], open(seen_file, "w"))
