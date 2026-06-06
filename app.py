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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_ENV") != "production"
    print(f"🚀  WorldCup Predictor V2 — http://localhost:{port}")
    app.run(debug=debug, port=port, use_reloader=False)
