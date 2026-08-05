#!/opt/ravenor/venv/bin/python3
"""Ravenor — OSINT feed collector."""
import hashlib, json, logging
from datetime import date, datetime, timezone
from pathlib import Path

import feedparser
import trafilatura

BASE      = Path("/opt/ravenor")
FEEDS     = BASE / "feeds.txt"
CORPUS    = BASE / "corpus"
SEEN      = BASE / "seen.txt"
LOG_FILE  = BASE / "logs" / "collector.log"

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


def process_feed(url, seen, run_dir):
    parsed = feedparser.parse(url)
    if not parsed.entries:
        return None
    saved = 0
    for e in parsed.entries:
        link = e.get("link")
        if not link or uid(link) in seen:
            continue
        art = article(url, e.get("title", ""), link,
                      e.get("published", ""), extract(link) or e.get("summary", ""))
        save(run_dir, art); mark_seen(art["id"]); seen.add(art["id"]); saved += 1
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
    seen, urls, total = load_seen(), load_feeds(), 0
    log.info("run start — %d sources, %d seen", len(urls), len(seen))
    for url in urls:
        try:
            n = process_feed(url, seen, run_dir)
            n = process_page(url, seen, run_dir) if n is None else n
            log.info("%s -> %d new", url, n); total += n
        except Exception as e:
            log.error("source failed %s: %s", url, e)
    log.info("run done — %d new in %s", total, run_dir)
    print(f"{total} new articles -> {run_dir}")

if __name__ == "__main__":
    main()
