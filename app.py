"""
Flask server pour WorldCup Predictor V2.
Sert l'app web et expose /api/analyze pour l'analyse Gemini.

Usage local : python3 app.py
Prod (Render) : gunicorn app:app
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory
from dotenv import load_dotenv

load_dotenv()

BASE = Path(__file__).parent
app = Flask(__name__, static_folder=None)

# Crée le dossier output s'il n'existe pas (premier démarrage sur Render)
(BASE / "output").mkdir(exist_ok=True)
(BASE / "data").mkdir(exist_ok=True)


@app.route("/")
def index():
    return send_file(BASE / "index.html")


@app.route("/data/<path:filename>")
def data(filename):
    return send_from_directory(BASE / "data", filename)


@app.route("/output/<path:filename>")
def output(filename):
    return send_from_directory(BASE / "output", filename)


@app.route("/api/analyze", methods=["POST"])
def analyze():
    body = request.get_json(force=True)
    home    = body.get("home", "").strip()
    away    = body.get("away", "").strip()
    date    = body.get("date", "").strip()
    stadium = body.get("stadium", "").strip()
    phase   = body.get("phase", "Groupe").strip()

    if not all([home, away, date, stadium]):
        return jsonify({"error": "home, away, date, stadium requis"}), 400

    try:
        result = subprocess.run(
            [sys.executable, str(BASE / "pipeline.py"),
             "--home", home,
             "--away", away,
             "--date", date,
             "--stadium", stadium,
             "--phase", phase],
            capture_output=True, text=True, timeout=120, cwd=str(BASE)
        )
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timeout (120s) — pipeline trop lent"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Lire le fichier de sortie généré par pipeline.py
    slug = f"{home.lower().replace(' ', '-')}_vs_{away.lower().replace(' ', '-')}"
    out_file = BASE / "output" / f"{slug}_v2.json"
    if out_file.exists():
        return jsonify(json.loads(out_file.read_text()))

    stderr = (result.stderr or "")[-600:]
    return jsonify({"error": f"Fichier de sortie introuvable. stderr: {stderr}"}), 500


@app.route("/api/news")
def news():
    import feedparser, re
    from datetime import datetime, timezone
    from email.utils import parsedate_to_datetime

    import requests as req_lib
    HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; WC2026Bot/1.0)"}
    feeds = [
        {"url":"https://feeds.bbci.co.uk/sport/football/rss.xml","source":"BBC Sport","color":"#bb1919","icon":"🎙"},
        {"url":"https://www.espn.com/espn/rss/soccer/news","source":"ESPN FC","color":"#cc0000","icon":"🏈"},
        {"url":"https://www.theguardian.com/football/worldcup/rss","source":"The Guardian","color":"#005689","icon":"📰"},
        {"url":"https://www.skysports.com/rss/12040","source":"Sky Sports","color":"#0070cc","icon":"📡"},
        {"url":"https://www.goal.com/feeds/en/news","source":"Goal.com","color":"#00a651","icon":"⚽"},
    ]
    WC_KEYWORDS = ["world cup","worldcup","2026","coupe du monde","mundial","fifa","wc2026",
                   "mexico","south africa","france","argentina","brazil","england","spain","germany",
                   "portugal","netherlands","norway","colombia","kroatien","groupe"]

    def img_from_entry(e):
        # Try enclosure
        for enc in getattr(e, "enclosures", []):
            if enc.get("type","").startswith("image"): return enc.get("href","")
        # Try media_content
        for m in getattr(e, "media_content", []):
            if m.get("url",""): return m["url"]
        # Try media_thumbnail
        for t in getattr(e, "media_thumbnail", []):
            if t.get("url",""): return t["url"]
        # Try finding img in summary
        s = getattr(e, "summary", "") or ""
        m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', s)
        return m.group(1) if m else ""

    def parse_date(e):
        for f in ["published","updated","created"]:
            v = getattr(e, f, None)
            if v:
                try: return parsedate_to_datetime(v).astimezone(timezone.utc).isoformat()
                except: pass
        return ""

    articles = []
    for fi in feeds:
        try:
            r = req_lib.get(fi["url"], headers=HEADERS, timeout=8)
            feed = feedparser.parse(r.text)
            for e in feed.entries[:20]:
                title   = getattr(e,"title","") or ""
                summary = getattr(e,"summary","") or ""
                link    = getattr(e,"link","") or ""
                text    = (title + " " + summary).lower()
                if not any(k in text for k in WC_KEYWORDS):
                    continue
                # Clean HTML from summary
                clean = re.sub(r"<[^>]+>","",summary).strip()[:220]
                articles.append({
                    "title":   title,
                    "url":     link,
                    "summary": clean,
                    "source":  fi["source"],
                    "color":   fi["color"],
                    "icon":    fi["icon"],
                    "date":    parse_date(e),
                    "image":   img_from_entry(e),
                })
        except Exception:
            pass

    articles.sort(key=lambda x: x.get("date",""), reverse=True)
    return jsonify({"articles": articles[:40], "updated": datetime.now(timezone.utc).isoformat()})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_ENV") != "production"
    print(f"🚀  WorldCup Predictor V2 — http://localhost:{port}")
    app.run(debug=debug, port=port, use_reloader=False)
