"""
Génère les prédictions V2 pour tous les 72 matchs de groupe.
Crée data/predictions_v2.json — chargé par index.html.
"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine.data_assembler import assemble_match_data
from engine.predictor_v2   import MatchPredictorV2

# Tous les matchs de groupe avec leurs stades
MATCHES = [
    # GROUPE A
    {"date":"2026-06-11","home":"Mexico",        "away":"South Africa",       "stadium":"Estadio Azteca",          "group":"A"},
    {"date":"2026-06-11","home":"South Korea",   "away":"Czechia",            "stadium":"Estadio Akron",           "group":"A"},
    {"date":"2026-06-18","home":"Czechia",        "away":"South Africa",       "stadium":"Mercedes-Benz Stadium",   "group":"A"},
    {"date":"2026-06-18","home":"Mexico",         "away":"South Korea",        "stadium":"Estadio Akron",           "group":"A"},
    {"date":"2026-06-24","home":"Czechia",        "away":"Mexico",             "stadium":"Estadio Azteca",          "group":"A"},
    {"date":"2026-06-24","home":"South Africa",  "away":"South Korea",        "stadium":"Estadio BBVA",            "group":"A"},
    # GROUPE B
    {"date":"2026-06-12","home":"Canada",         "away":"Bosnia-Herzegovina", "stadium":"BMO Field",               "group":"B"},
    {"date":"2026-06-13","home":"Qatar",          "away":"Switzerland",        "stadium":"Levi's Stadium",          "group":"B"},
    {"date":"2026-06-18","home":"Switzerland",    "away":"Bosnia-Herzegovina", "stadium":"SoFi Stadium",            "group":"B"},
    {"date":"2026-06-18","home":"Canada",         "away":"Qatar",              "stadium":"BC Place",                "group":"B"},
    {"date":"2026-06-24","home":"Switzerland",    "away":"Canada",             "stadium":"BC Place",                "group":"B"},
    {"date":"2026-06-24","home":"Bosnia-Herzegovina","away":"Qatar",           "stadium":"Lumen Field",             "group":"B"},
    # GROUPE C
    {"date":"2026-06-13","home":"Brazil",         "away":"Morocco",            "stadium":"MetLife Stadium",         "group":"C"},
    {"date":"2026-06-13","home":"Haiti",          "away":"Scotland",           "stadium":"Gillette Stadium",        "group":"C"},
    {"date":"2026-06-19","home":"Scotland",       "away":"Morocco",            "stadium":"Gillette Stadium",        "group":"C"},
    {"date":"2026-06-19","home":"Brazil",         "away":"Haiti",              "stadium":"Lincoln Financial Field", "group":"C"},
    {"date":"2026-06-24","home":"Scotland",       "away":"Brazil",             "stadium":"Hard Rock Stadium",       "group":"C"},
    {"date":"2026-06-24","home":"Morocco",        "away":"Haiti",              "stadium":"Mercedes-Benz Stadium",   "group":"C"},
    # GROUPE D
    {"date":"2026-06-12","home":"USA",            "away":"Paraguay",           "stadium":"SoFi Stadium",            "group":"D"},
    {"date":"2026-06-13","home":"Australia",      "away":"Turkey",             "stadium":"BC Place",                "group":"D"},
    {"date":"2026-06-19","home":"USA",            "away":"Australia",          "stadium":"Lumen Field",             "group":"D"},
    {"date":"2026-06-19","home":"Turkey",         "away":"Paraguay",           "stadium":"Levi's Stadium",          "group":"D"},
    {"date":"2026-06-25","home":"Turkey",         "away":"USA",                "stadium":"SoFi Stadium",            "group":"D"},
    {"date":"2026-06-25","home":"Paraguay",       "away":"Australia",          "stadium":"Levi's Stadium",          "group":"D"},
    # GROUPE E
    {"date":"2026-06-14","home":"Germany",        "away":"Curaçao",            "stadium":"NRG Stadium",             "group":"E"},
    {"date":"2026-06-14","home":"Ivory Coast",    "away":"Ecuador",            "stadium":"Lincoln Financial Field", "group":"E"},
    {"date":"2026-06-20","home":"Germany",        "away":"Ivory Coast",        "stadium":"BMO Field",               "group":"E"},
    {"date":"2026-06-20","home":"Ecuador",        "away":"Curaçao",            "stadium":"Arrowhead Stadium",       "group":"E"},
    {"date":"2026-06-25","home":"Ecuador",        "away":"Germany",            "stadium":"MetLife Stadium",         "group":"E"},
    {"date":"2026-06-25","home":"Curaçao",        "away":"Ivory Coast",        "stadium":"Lincoln Financial Field", "group":"E"},
    # GROUPE F
    {"date":"2026-06-14","home":"Netherlands",    "away":"Japan",              "stadium":"AT&T Stadium",            "group":"F"},
    {"date":"2026-06-14","home":"Sweden",         "away":"Tunisia",            "stadium":"Estadio BBVA",            "group":"F"},
    {"date":"2026-06-20","home":"Netherlands",    "away":"Sweden",             "stadium":"NRG Stadium",             "group":"F"},
    {"date":"2026-06-20","home":"Tunisia",        "away":"Japan",              "stadium":"Estadio BBVA",            "group":"F"},
    {"date":"2026-06-25","home":"Japan",          "away":"Sweden",             "stadium":"AT&T Stadium",            "group":"F"},
    {"date":"2026-06-25","home":"Tunisia",        "away":"Netherlands",        "stadium":"Arrowhead Stadium",       "group":"F"},
    # GROUPE G
    {"date":"2026-06-15","home":"Belgium",        "away":"Egypt",              "stadium":"Lumen Field",             "group":"G"},
    {"date":"2026-06-15","home":"Iran",           "away":"New Zealand",        "stadium":"SoFi Stadium",            "group":"G"},
    {"date":"2026-06-21","home":"Belgium",        "away":"Iran",               "stadium":"SoFi Stadium",            "group":"G"},
    {"date":"2026-06-21","home":"New Zealand",    "away":"Egypt",              "stadium":"BC Place",                "group":"G"},
    {"date":"2026-06-26","home":"Egypt",          "away":"Iran",               "stadium":"Lumen Field",             "group":"G"},
    {"date":"2026-06-26","home":"New Zealand",    "away":"Belgium",            "stadium":"BC Place",                "group":"G"},
    # GROUPE H
    {"date":"2026-06-15","home":"Spain",          "away":"Cape Verde",         "stadium":"Mercedes-Benz Stadium",   "group":"H"},
    {"date":"2026-06-15","home":"Saudi Arabia",   "away":"Uruguay",            "stadium":"Hard Rock Stadium",       "group":"H"},
    {"date":"2026-06-21","home":"Spain",          "away":"Saudi Arabia",       "stadium":"Mercedes-Benz Stadium",   "group":"H"},
    {"date":"2026-06-21","home":"Uruguay",        "away":"Cape Verde",         "stadium":"Hard Rock Stadium",       "group":"H"},
    {"date":"2026-06-26","home":"Cape Verde",     "away":"Saudi Arabia",       "stadium":"NRG Stadium",             "group":"H"},
    {"date":"2026-06-26","home":"Uruguay",        "away":"Spain",              "stadium":"Estadio Akron",           "group":"H"},
    # GROUPE I
    {"date":"2026-06-16","home":"France",         "away":"Senegal",            "stadium":"MetLife Stadium",         "group":"I"},
    {"date":"2026-06-16","home":"Iraq",           "away":"Norway",             "stadium":"Gillette Stadium",        "group":"I"},
    {"date":"2026-06-22","home":"France",         "away":"Iraq",               "stadium":"Lincoln Financial Field", "group":"I"},
    {"date":"2026-06-22","home":"Norway",         "away":"Senegal",            "stadium":"MetLife Stadium",         "group":"I"},
    {"date":"2026-06-26","home":"Norway",         "away":"France",             "stadium":"Gillette Stadium",        "group":"I"},
    {"date":"2026-06-26","home":"Senegal",        "away":"Iraq",               "stadium":"BMO Field",               "group":"I"},
    # GROUPE J
    {"date":"2026-06-16","home":"Argentina",      "away":"Algeria",            "stadium":"Arrowhead Stadium",       "group":"J"},
    {"date":"2026-06-16","home":"Austria",        "away":"Jordan",             "stadium":"Levi's Stadium",          "group":"J"},
    {"date":"2026-06-22","home":"Argentina",      "away":"Austria",            "stadium":"AT&T Stadium",            "group":"J"},
    {"date":"2026-06-22","home":"Jordan",         "away":"Algeria",            "stadium":"Levi's Stadium",          "group":"J"},
    {"date":"2026-06-27","home":"Algeria",        "away":"Austria",            "stadium":"Arrowhead Stadium",       "group":"J"},
    {"date":"2026-06-27","home":"Jordan",         "away":"Argentina",          "stadium":"AT&T Stadium",            "group":"J"},
    # GROUPE K
    {"date":"2026-06-17","home":"Portugal",       "away":"DR Congo",           "stadium":"NRG Stadium",             "group":"K"},
    {"date":"2026-06-17","home":"Uzbekistan",     "away":"Colombia",           "stadium":"Estadio Azteca",          "group":"K"},
    {"date":"2026-06-23","home":"Portugal",       "away":"Uzbekistan",         "stadium":"NRG Stadium",             "group":"K"},
    {"date":"2026-06-23","home":"Colombia",       "away":"DR Congo",           "stadium":"Estadio Akron",           "group":"K"},
    {"date":"2026-06-27","home":"Colombia",       "away":"Portugal",           "stadium":"Hard Rock Stadium",       "group":"K"},
    {"date":"2026-06-27","home":"DR Congo",       "away":"Uzbekistan",         "stadium":"Mercedes-Benz Stadium",   "group":"K"},
    # GROUPE L
    {"date":"2026-06-17","home":"England",        "away":"Croatia",            "stadium":"AT&T Stadium",            "group":"L"},
    {"date":"2026-06-17","home":"Ghana",          "away":"Panama",             "stadium":"BMO Field",               "group":"L"},
    {"date":"2026-06-23","home":"England",        "away":"Ghana",              "stadium":"Gillette Stadium",        "group":"L"},
    {"date":"2026-06-23","home":"Panama",         "away":"Croatia",            "stadium":"BMO Field",               "group":"L"},
    {"date":"2026-06-27","home":"Panama",         "away":"England",            "stadium":"MetLife Stadium",         "group":"L"},
    {"date":"2026-06-27","home":"Croatia",        "away":"Ghana",              "stadium":"Lincoln Financial Field", "group":"L"},
]


async def generate_all():
    predictor = MatchPredictorV2()
    results = []
    total = len(MATCHES)

    print(f"Generating predictions for {total} matches...")
    print("(This takes ~2 min for ELO + form + odds fetching)\n")

    for i, m in enumerate(MATCHES):
        try:
            print(f"[{i+1:02d}/{total}] {m['home']} vs {m['away']}...", end=" ", flush=True)
            data = await assemble_match_data(
                m["home"], m["away"], m["date"], m["stadium"], verbose=False
            )
            pred = predictor.predict(m["home"], m["away"], data)

            results.append({
                "home":    m["home"],
                "away":    m["away"],
                "date":    m["date"],
                "stadium": m["stadium"],
                "group":   m["group"],
                # Prédiction
                "p_home":  pred["p_home"],
                "p_draw":  pred["p_draw"],
                "p_away":  pred["p_away"],
                "winner":  pred["winner"],
                "score":   pred["best_score"],
                "xg_home": pred["lambda_a"],
                "xg_away": pred["lambda_b"],
                "over25":  pred["over25"],
                "btts":    pred["btts"],
                "avg_goals": pred["avg_goals"],
                "confidence_score": pred["confidence"]["score"],
                "confidence_level": pred["confidence"]["level"],
                "top_scores": pred["top_scores"][:4],
                "bayesian_blend": pred["bayesian_blend"],
                "signals": pred["signals_used"],
                # Experts
                "espn_winner":    data.get("expert_espn_winner"),
                "espn_score":     data.get("expert_espn_score"),
                "opta_fav":       data.get("expert_opta_favorite"),
                "opta_win_home":  data.get("expert_opta_win_home"),
                "opta_win_away":  data.get("expert_opta_win_away"),
                "opta_qual_home": data.get("expert_opta_qualify_home"),
                "opta_qual_away": data.get("expert_opta_qualify_away"),
                "consensus":      data.get("expert_consensus_aligned"),
                # Cotes
                "odds_home": data.get("odds_home"),
                "odds_draw": data.get("odds_draw"),
                "odds_away": data.get("odds_away"),
                "odds_ok":   data.get("odds_available", False),
                # Météo
                "weather_temp": data.get("weather_temp"),
                "weather_rain": data.get("weather_rain"),
                "weather_cond": data.get("weather_conditions"),
                # Forme
                "form_home": data.get(f"form_string_{m['home']}"),
                "form_away": data.get(f"form_string_{m['away']}"),
                # ELO
                "elo_home": data.get(f"elo_{m['home']}"),
                "elo_away": data.get(f"elo_{m['away']}"),
            })

            odds_tag = "📊" if data.get("odds_available") else "  "
            print(f"{pred['winner']} {pred['winner_prob']}% | {pred['best_score']} {odds_tag}")

        except Exception as e:
            print(f"ERROR: {e}")
            results.append({"home": m["home"], "away": m["away"],
                            "date": m["date"], "group": m["group"], "error": str(e)})

    out = {
        "generated_at": datetime.utcnow().isoformat(),
        "version": "v2",
        "total_matches": total,
        "matches_with_odds": sum(1 for r in results if r.get("odds_ok")),
        "matches": results,
    }

    out_path = Path(__file__).parent / "data" / "predictions_v2.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"\n✅ {total} prédictions générées")
    print(f"📊 {out['matches_with_odds']}/{total} avec cotes live")
    print(f"💾 {out_path}")
    return out_path


if __name__ == "__main__":
    asyncio.run(generate_all())
