#!/opt/ravenor/venv/bin/python3
# Sanctum Auspicium · Acolyte · v1.1 (starting anchor; history via git)
"""Ravenor — OSINT feed collector."""
import hashlib, json, logging, re
from datetime import date, datetime, timezone
from pathlib import Path

import feedparser
import trafilatura

BASE       = Path("/opt/ravenor")
FEEDS      = BASE / "feeds.txt"
CORPUS     = BASE / "corpus"
SEEN       = BASE / "seen.txt"
SEEN_TITLES = BASE / "seen_titles.txt"          # NEW
LOG_FILE   = BASE / "logs" / "collector.log"

MIN_TITLE_LEN = 15                              # NEW: below this, don't title-dedup
SUFFIX_SEPARATORS = (" - ", " | ", " — ")       # NEW: GNews appends outlet after these

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ravenor")


def load_feeds():
    return [l.strip() for l in FEEDS.read_text().splitlines()
            if l.strip() and not l.strip().startswith("#")]

def load_seen():
    return set(SEEN.read_text().split()) if SEEN.exists() else set()

def mark_seen(did):
    with SEEN.open("a") as f: f.write(did + "\n")

def uid(url):
    return hashlib.sha256(url.encode()).hexdigest()


# --- NEW: title-based dedup (catches cross-feed Google News duplicates) ---
def load_seen_titles():
    return set(SEEN_TITLES.read_text().split("\n")) - {""} if SEEN_TITLES.exists() else set()

def mark_seen_title(tkey):
    with SEEN_TITLES.open("a") as f: f.write(tkey + "\n")

def normalize_title(title):
    if not title:
        return ""
    t = title.strip()
    for sep in SUFFIX_SEPARATORS:
        if sep in t:
            parts = t.split(sep)
            if len(parts[-1]) <= 40:            # trailing segment looks like an outlet name
                t = sep.join(parts[:-1])
    t = t.lower()
    t = re.sub(r"[^a-z0-9 ]+", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def title_key(title):
    norm = normalize_title(title)
    if len(norm) < MIN_TITLE_LEN:
        return None                             # too generic to trust — let URL-hash decide alone
    return hashlib.sha256(norm.encode()).hexdigest()
# --- end new block ---


def extract(url):
    try:
        dl = trafilatura.fetch_url(url)
        return (trafilatura.extract(dl, include_comments=False) or "") if dl else ""
    except Exception as e:
        log.warning("extract failed %s: %s", url, e); return ""

def save(run_dir, art):
    (run_dir / f"{art['id'][:16]}.json").write_text(
        json.dumps(art, indent=2, ensure_ascii=False))

def article(source, title, url, published, text):
    return {"id": uid(url), "source": source, "title": title.strip(),
            "url": url, "published": published,
            "collected": datetime.now(timezone.utc).isoformat(), "text": text}


def process_feed(url, seen, seen_titles, run_dir):
    parsed = feedparser.parse(url)
    if not parsed.entries:
        return None
    saved = 0
    for e in parsed.entries:
        link = e.get("link")
        if not link or uid(link) in seen:
            continue
        # NEW: title gate — skip if this headline was already stored via another feed
        tkey = title_key(e.get("title", ""))
        if tkey and tkey in seen_titles:
            continue
        art = article(url, e.get("title", ""), link,
                      e.get("published", ""), extract(link) or e.get("summary", ""))
        save(run_dir, art); mark_seen(art["id"]); seen.add(art["id"])
        if tkey:                                # NEW: remember the title too
            mark_seen_title(tkey); seen_titles.add(tkey)
        saved += 1
    return saved

def process_page(url, seen, run_dir):
    if uid(url) in seen:
        return 0
    text = extract(url)
    if not text:
        log.warning("no text %s", url); return 0
    art = article(url, "", url, "", text)
    save(run_dir, art); mark_seen(art["id"]); seen.add(art["id"])
    return 1


def main():
    run_dir = CORPUS / date.today().isoformat()
    run_dir.mkdir(parents=True, exist_ok=True)
    seen, seen_titles, urls, total = load_seen(), load_seen_titles(), load_feeds(), 0
    log.info("run start — %d sources, %d seen, %d seen-titles", len(urls), len(seen), len(seen_titles))
    for url in urls:
        try:
            n = process_feed(url, seen, seen_titles, run_dir)
            n = process_page(url, seen, run_dir) if n is None else n
            log.info("%s -> %d new", url, n); total += n
        except Exception as e:
            log.error("source failed %s: %s", url, e)
    log.info("run done — %d new in %s", total, run_dir)
    print(f"{total} new articles -> {run_dir}")

if __name__ == "__main__":
    main()
