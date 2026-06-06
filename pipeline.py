"""
WorldCup Predictor V2 — Pipeline principal.
Orchestre : data_assembler + predictor_v2 + Gemini analyst.

Usage :
  python3 pipeline.py --home France --away Argentina --date 2026-07-14 --stadium "AT&T Stadium" --phase "Demi-finales"
  python3 pipeline.py --home France --away Senegal   --date 2026-06-16 --stadium "MetLife Stadium" --phase "Groupe I"
"""
import asyncio
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from engine.data_assembler import assemble_match_data
from engine.predictor_v2   import MatchPredictorV2


# ─── GEMINI ───────────────────────────────────────────────────────────────────
def call_gemini(data: dict, prediction: dict) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key or api_key == "your_gemini_key_here":
        return {"error": "GEMINI_API_KEY not set", "analysis": None}

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
    except ImportError:
        return {"error": "google-generativeai not installed", "analysis": None}

    home = data["_home"]
    away = data["_away"]

    # Construction du prompt — synthèse analytique, pas oracle
    prompt = f"""Tu es un analyste football de niveau mondial. Le modèle quantitatif a déjà produit une prédiction.
Ta mission : synthétiser en JSON les signaux que le modèle ne peut pas capturer.

═══ PRÉDICTION MODÈLE ═══
Match : {home} vs {away} | {data['_date']} | {data['_stadium']}
Vainqueur : {prediction['winner']} ({prediction['winner_prob']}%)
Score prédit : {prediction['best_score']}
Proba : {home} {prediction['p_home']}% / Nul {prediction['p_draw']}% / {away} {prediction['p_away']}%
xG : {prediction['lambda_a']:.2f} - {prediction['lambda_b']:.2f}
Over 2.5 : {prediction['over25']}% | BTTS : {prediction['btts']}%
Confiance modèle : {prediction['confidence']['level']} ({prediction['confidence']['score']}/100)

═══ SIGNAUX QUANTITATIFS ═══
ELO : {home}={data.get(f'elo_{home}')} / {away}={data.get(f'elo_{away}')}
Forme {home} : {data.get(f'form_string_{home}','?')} (score={data.get(f'form_score_{home}','?')}, trend={data.get(f'form_trend_{home}','?')})
Forme {away} : {data.get(f'form_string_{away}','?')} (score={data.get(f'form_score_{away}','?')}, trend={data.get(f'form_trend_{away}','?')})
xG offensif : {home}={data.get(f'xg_rolling_{home}','?')} / {away}={data.get(f'xg_rolling_{away}','?')}
H2H WC : {data.get('h2h_matches',0)} matchs | dominant={data.get('h2h_dominant','?')}
Cotes live : {home}={data.get('odds_home','?')} / Nul={data.get('odds_draw','?')} / {away}={data.get('odds_away','?')}
Météo : {data.get('weather_temp','?')}°C / {data.get('weather_rain','?')}mm / {data.get('weather_conditions','?')}
WC titres : {home}={data.get(f'wc_titles_{home}',0)} / {away}={data.get(f'wc_titles_{away}',0)}
Squad value : {home}=€{data.get(f'squad_value_{home}','?')}M / {away}=€{data.get(f'squad_value_{away}','?')}M
Blessés {home} : {data.get(f'n_injured_{home}',0)} ({data.get(f'stars_out_{home}',[])}) | {away} : {data.get(f'n_injured_{away}',0)} ({data.get(f'stars_out_{away}',[])})

═══ SIGNAUX TACTIQUES & PSYCHOLOGIQUES ═══
Style de pressing : {home}={data.get(f'pressing_level_{home}','?')} (score={data.get(f'pressing_score_{home}','?')}) / {away}={data.get(f'pressing_level_{away}','?')} (score={data.get(f'pressing_score_{away}','?')})
Fatigue {home} : {data.get(f'fatigue_level_{home}','?')} (matchs 30j={data.get(f'matches_30d_{home}',0)}) | {away} : {data.get(f'fatigue_level_{away}','?')} (matchs 30j={data.get(f'matches_30d_{away}',0)})
Distance voyage : {home}={data.get(f'travel_km_{home}','?')} km ({data.get(f'travel_level_{home}','?')}) | {away}={data.get(f'travel_km_{away}','?')} km ({data.get(f'travel_level_{away}','?')})
Score psychologique : {home}={data.get(f'psych_score_{home}','?')} | {away}={data.get(f'psych_score_{away}','?')}
Sentiment coach : {home}={data.get(f'coach_sentiment_{home}','neutral')} | {away}={data.get(f'coach_sentiment_{away}','neutral')}
Tensions internes : {home}={data.get(f'internal_conflict_{home}',False)} | {away}={data.get(f'internal_conflict_{away}',False)}
Arbitre (estimation) : style={data.get('ref_style','?')} conf={data.get('ref_confederation','?')}
Pénaltys TAB : {home}={data.get(f'penalty_rate_{home}','?')} ({data.get(f'shootout_winrate_{home}','?')} win TAB) | {away}={data.get(f'penalty_rate_{away}','?')} ({data.get(f'shootout_winrate_{away}','?')} win TAB)

═══ SIGNAUX EXPERTS ═══
Opta Supercomputer (25k simul.) : {home}={data.get('expert_opta_win_home',0)}% de titre / {away}={data.get('expert_opta_win_away',0)}% de titre
Opta qualifier {home} : {data.get('expert_opta_qualify_home','?')}% / {away} : {data.get('expert_opta_qualify_away','?')}%
ESPN Expert Pick : {data.get('expert_espn_winner','?')} ({data.get('expert_espn_score','?')})
Consensus ESPN/Opta alignés : {data.get('expert_consensus_aligned',False)}

═══ TA MISSION ═══
Réponds UNIQUEMENT en JSON valide. Structure exacte :

{{
  "verdict": "Une phrase directe sur le résultat probable (max 25 mots)",
  "cle_du_match": "L'élément TACTIQUE décisif : pressing vs bloc bas, transitions, duels physiques clés",
  "analyse_tactique": "2-3 phrases sur comment les styles s'affrontent : formations probables, zones de danger, matchups décisifs",
  "facteur_psychologique": "Impact des données psycho (confiance coach, tensions internes, fatigue, voyage) sur le résultat",
  "signal_divergent": "Si ESPN diverge d'Opta/modèle : explique pourquoi c'est intéressant (null sinon)",
  "joueurs_a_surveiller": [
    {{"nom": "...", "equipe": "...", "pourquoi": "impact attendu sur CE match spécifique compte tenu du contexte tactique"}}
  ],
  "risque_surprise": "Scénario crédible où le favori perd : quel événement déclencheur ? (probabilité en %)",
  "meteo_impact": "Impact concret des conditions météo sur les styles (pressing, long ball, vitesse) — null si neutre",
  "fatigue_impact": "Si une équipe est fatiguée ou a voyagé loin : comment ça se manifeste tactiquement en 2e mi-temps",
  "paris_value": [
    {{"marche": "...", "pick": "...", "edge": "pourquoi c'est potentiellement sous-côté", "confiance": "high|medium|low"}}
  ],
  "paris_ko_tab": {{"pick": "avantage TAB si match KO", "edge": "basé sur historique pénaltys", "confiance": "high|medium|low"}},
  "synthese_expert": "2-3 phrases : où convergent/divergent modèle quantitatif, Opta, ESPN, et données tactiques/psycho",
  "confiance_finale": "high|medium|low",
  "verdict_score": "Score exact le plus probable selon TON analyse (peut différer du modèle)"
}}"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Nettoyer markdown si présent
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.split("```")[0]
        return {"analysis": json.loads(text.strip()), "error": None}
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse: {e}", "raw": response.text[:300], "analysis": None}
    except Exception as e:
        return {"error": str(e), "analysis": None}


# ─── SAVE ─────────────────────────────────────────────────────────────────────
def save_output(home: str, away: str, data: dict, prediction: dict, gemini: dict) -> Path:
    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(exist_ok=True)

    slug = f"{home.lower().replace(' ','-')}_vs_{away.lower().replace(' ','-')}"
    out_path = out_dir / f"{slug}_v2.json"

    result = {
        "meta": {
            "home": home, "away": away,
            "date": data.get("_date"), "stadium": data.get("_stadium"),
            "generated_at": datetime.utcnow().isoformat(),
            "version": "v2",
            "sources_ok": data.get("_signals_ok"), "sources_total": data.get("_signals_total"),
        },
        "prediction": prediction,
        "gemini": gemini,
        "data_log": data.get("_data_log", []),
    }
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    return out_path


# ─── PRINT ────────────────────────────────────────────────────────────────────
def print_report(home: str, away: str, pred: dict, gemini: dict, out_path: Path, data: dict):
    print(f"\n{'═'*60}")
    print(f"  {home}  vs  {away}")
    print(f"{'═'*60}")
    print(f"  Proba     : {home} {pred['p_home']}%  |  Nul {pred['p_draw']}%  |  {away} {pred['p_away']}%")
    print(f"  Score     : {pred['best_score']}  (xG {pred['lambda_a']:.2f}–{pred['lambda_b']:.2f})")
    print(f"  Over 2.5  : {pred['over25']}%  |  BTTS : {pred['btts']}%")
    print(f"  Confiance : {pred['confidence']['level']} ({pred['confidence']['score']}/100)")

    # Experts
    espn = data.get("expert_espn_winner")
    if espn:
        aligned = "✓ consensus" if data.get("expert_consensus_aligned") else "⚡ diverge"
        print(f"\n  ESPN      : {espn} ({data.get('expert_espn_score')})  {aligned}")
    opta_h = data.get("expert_opta_win_home", 0)
    opta_a = data.get("expert_opta_win_away", 0)
    print(f"  Opta WC%  : {home} {opta_h}%  |  {away} {opta_a}%")

    # Gemini
    if gemini.get("analysis"):
        g = gemini["analysis"]
        print(f"\n{'─'*60}")
        print(f"  ANALYSE IA (Gemini)")
        print(f"{'─'*60}")
        print(f"  Verdict   : {g.get('verdict','—')}")
        print(f"  Clé match : {g.get('cle_du_match','—')}")
        if g.get("signal_divergent"):
            print(f"  ⚡ Diverge : {g['signal_divergent']}")
        if g.get("meteo_impact"):
            print(f"  🌤 Météo  : {g['meteo_impact']}")
        print(f"\n  Synthèse  : {g.get('synthese_expert','—')}")
        print(f"\n  Paris value :")
        for b in g.get("paris_value", [])[:3]:
            print(f"    [{b.get('confiance','?').upper()}] {b.get('marche','?')} → {b.get('pick','?')}")
            print(f"           Edge : {b.get('edge','?')}")
    elif gemini.get("error"):
        print(f"\n  Gemini    : {gemini['error']}")

    sources_ok = data.get("_signals_ok", 0)
    sources_total = data.get("_signals_total", 0)
    print(f"\n✅ {sources_ok}/{sources_total} sources OK")
    print(f"💾 {out_path}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────
async def main():
    parser = argparse.ArgumentParser(description="WorldCup Predictor V2")
    parser.add_argument("--home",    required=True)
    parser.add_argument("--away",    required=True)
    parser.add_argument("--date",    required=True, help="YYYY-MM-DD")
    parser.add_argument("--stadium", required=True)
    parser.add_argument("--phase",   default="Groupe")
    parser.add_argument("--no-gemini", action="store_true", help="Skip Gemini")
    args = parser.parse_args()

    print(f"\n🚀 WorldCup Predictor V2 — {args.home} vs {args.away}")
    print(f"   {args.date} · {args.stadium} · {args.phase}")

    # 1. Assembler les données
    data = await assemble_match_data(args.home, args.away, args.date, args.stadium)

    # 2. Prédiction quantitative
    predictor = MatchPredictorV2()
    prediction = predictor.predict(args.home, args.away, data)

    # 3. Analyse Gemini
    if args.no_gemini:
        gemini = {"analysis": None, "error": "skipped"}
    else:
        print("\n🤖 Calling Gemini analyst...")
        gemini = call_gemini(data, prediction)

    # 4. Save + Print
    out_path = save_output(args.home, args.away, data, prediction, gemini)
    print_report(args.home, args.away, prediction, gemini, out_path, data)


if __name__ == "__main__":
    asyncio.run(main())
