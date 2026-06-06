"""
Backtest du modèle V2 sur WC 2022 (64 matchs réels).
Métriques : Accuracy, Brier Score, RPS (Ranked Probability Score).
"""
import sys
import math
import json
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.predictor_v2 import MatchPredictorV2
from scrapers.elo import get_team_elo

# ─── RÉSULTATS WC 2022 (Qatar) ─────────────────────────────────────────────
WC2022 = [
    # Groupe A
    {"home": "Qatar",   "away": "Ecuador",  "result": "away",  "hg": 0, "ag": 2},
    {"home": "Senegal", "away": "Netherlands","result":"away",  "hg": 0, "ag": 2},
    {"home": "Qatar",   "away": "Senegal",  "result": "away",  "hg": 1, "ag": 3},
    {"home": "Netherlands","away":"Ecuador", "result": "draw",  "hg": 1, "ag": 1},
    {"home": "Ecuador", "away": "Senegal",  "result": "away",  "hg": 1, "ag": 2},
    {"home": "Netherlands","away":"Qatar",   "result": "home",  "hg": 2, "ag": 0},
    # Groupe B
    {"home": "England", "away": "Iran",     "result": "home",  "hg": 6, "ag": 2},
    {"home": "USA",     "away": "Wales",    "result": "draw",  "hg": 1, "ag": 1},
    {"home": "Wales",   "away": "Iran",     "result": "away",  "hg": 0, "ag": 2},
    {"home": "England", "away": "USA",      "result": "draw",  "hg": 0, "ag": 0},
    {"home": "Wales",   "away": "England",  "result": "away",  "hg": 0, "ag": 3},
    {"home": "Iran",    "away": "USA",      "result": "away",  "hg": 0, "ag": 1},
    # Groupe C
    {"home": "Argentina","away":"Saudi Arabia","result":"away", "hg": 1, "ag": 2},
    {"home": "Mexico",  "away": "Poland",   "result": "draw",  "hg": 0, "ag": 0},
    {"home": "Poland",  "away": "Saudi Arabia","result":"home", "hg": 2, "ag": 0},
    {"home": "Argentina","away":"Mexico",   "result": "home",  "hg": 2, "ag": 0},
    {"home": "Poland",  "away": "Argentina","result":"away",   "hg": 0, "ag": 2},
    {"home": "Saudi Arabia","away":"Mexico","result":"draw",    "hg": 1, "ag": 2},
    # Groupe D
    {"home": "France",  "away": "Australia","result": "home",  "hg": 4, "ag": 1},
    {"home": "Denmark", "away": "Tunisia",  "result": "draw",  "hg": 0, "ag": 0},
    {"home": "Tunisia", "away": "Australia","result": "draw",  "hg": 0, "ag": 1},
    {"home": "France",  "away": "Denmark",  "result": "home",  "hg": 2, "ag": 1},
    {"home": "Australia","away":"Denmark",  "result": "home",  "hg": 1, "ag": 0},
    {"home": "Tunisia", "away": "France",   "result": "home",  "hg": 1, "ag": 0},
    # Groupe E
    {"home": "Spain",   "away": "Costa Rica","result":"home",  "hg": 7, "ag": 0},
    {"home": "Germany", "away": "Japan",    "result": "away",  "hg": 1, "ag": 2},
    {"home": "Japan",   "away": "Costa Rica","result":"home",  "hg": 0, "ag": 1},
    {"home": "Spain",   "away": "Germany",  "result": "draw",  "hg": 1, "ag": 1},
    {"home": "Japan",   "away": "Spain",    "result": "home",  "hg": 2, "ag": 1},
    {"home": "Costa Rica","away":"Germany", "result": "away",  "hg": 2, "ag": 4},
    # Groupe F
    {"home": "Morocco", "away": "Croatia",  "result": "draw",  "hg": 0, "ag": 0},
    {"home": "Belgium", "away": "Canada",   "result": "home",  "hg": 1, "ag": 0},
    {"home": "Belgium", "away": "Morocco",  "result": "away",  "hg": 0, "ag": 2},
    {"home": "Croatia", "away": "Canada",   "result": "home",  "hg": 4, "ag": 1},
    {"home": "Croatia", "away": "Belgium",  "result": "home",  "hg": 0, "ag": 0},
    {"home": "Morocco", "away": "Canada",   "result": "home",  "hg": 2, "ag": 1},
    # Groupe G
    {"home": "Switzerland","away":"Cameroon","result":"home",   "hg": 1, "ag": 0},
    {"home": "Brazil",  "away": "Serbia",   "result": "home",  "hg": 2, "ag": 0},
    {"home": "Cameroon","away":"Serbia",    "result": "draw",  "hg": 3, "ag": 3},
    {"home": "Brazil",  "away": "Switzerland","result":"home", "hg": 1, "ag": 0},
    {"home": "Serbia",  "away": "Switzerland","result":"away", "hg": 2, "ag": 3},
    {"home": "Cameroon","away":"Brazil",    "result": "home",  "hg": 1, "ag": 0},
    # Groupe H
    {"home": "Uruguay", "away": "South Korea","result":"draw",  "hg": 0, "ag": 0},
    {"home": "Portugal","away":"Ghana",     "result": "home",  "hg": 3, "ag": 2},
    {"home": "South Korea","away":"Ghana",  "result": "home",  "hg": 2, "ag": 3},
    {"home": "Portugal","away":"Uruguay",   "result": "home",  "hg": 2, "ag": 0},
    {"home": "Ghana",   "away": "Uruguay",  "result": "away",  "hg": 0, "ag": 2},
    {"home": "South Korea","away":"Portugal","result":"away",   "hg": 1, "ag": 2},
    # Huitièmes
    {"home": "Netherlands","away":"USA",    "result": "home",  "hg": 3, "ag": 1, "phase":"R16"},
    {"home": "Argentina","away":"Australia","result":"home",    "hg": 2, "ag": 1, "phase":"R16"},
    {"home": "France",  "away": "Poland",   "result": "home",  "hg": 3, "ag": 1, "phase":"R16"},
    {"home": "England", "away": "Senegal",  "result": "home",  "hg": 3, "ag": 0, "phase":"R16"},
    {"home": "Japan",   "away": "Croatia",  "result": "away",  "hg": 1, "ag": 1, "phase":"R16"},  # AET
    {"home": "Brazil",  "away": "South Korea","result":"home", "hg": 4, "ag": 1, "phase":"R16"},
    {"home": "Morocco", "away": "Spain",    "result": "home",  "hg": 0, "ag": 0, "phase":"R16"},  # Morocco wins on PKs
    {"home": "Portugal","away":"Switzerland","result":"home",   "hg": 6, "ag": 1, "phase":"R16"},
    # Quarts
    {"home": "Croatia", "away": "Brazil",   "result": "home",  "hg": 1, "ag": 1, "phase":"QF"},
    {"home": "Netherlands","away":"Argentina","result":"away",  "hg": 2, "ag": 2, "phase":"QF"},
    {"home": "Morocco", "away": "Portugal", "result": "home",  "hg": 1, "ag": 0, "phase":"QF"},
    {"home": "England", "away": "France",   "result": "away",  "hg": 1, "ag": 2, "phase":"QF"},
    # Demis
    {"home": "Argentina","away":"Croatia",  "result": "home",  "hg": 3, "ag": 0, "phase":"SF"},
    {"home": "France",  "away": "Morocco",  "result": "home",  "hg": 2, "ag": 0, "phase":"SF"},
    # 3ème place
    {"home": "Croatia", "away": "Morocco",  "result": "home",  "hg": 2, "ag": 1, "phase":"3P"},
    # Finale
    {"home": "Argentina","away":"France",   "result": "home",  "hg": 3, "ag": 3, "phase":"Final"},  # Argentina wins on PKs
]


def compute_rps(pred_probs: list, actual_idx: int) -> float:
    """Ranked Probability Score (standard football prediction metric)."""
    cdf_pred = [sum(pred_probs[:i+1]) for i in range(len(pred_probs))]
    cdf_act  = [1.0 if i >= actual_idx else 0.0 for i in range(len(pred_probs))]
    return sum((cp - ca)**2 for cp, ca in zip(cdf_pred, cdf_act)) / (len(pred_probs) - 1)


def run_backtest(use_form: bool = False, verbose: bool = True) -> dict:
    """
    Backteste le modèle sur WC 2022.
    use_form=False → ELO pur
    use_form=True → ELO + forme (si données dispo)
    """
    pred = MatchPredictorV2()

    results = []
    correct = 0
    total_brier = 0.0
    total_rps   = 0.0
    n = len(WC2022)

    if verbose:
        print(f"\n{'='*60}")
        print(f"BACKTEST WC 2022 — {n} matchs")
        print(f"{'='*60}")

    for m in WC2022:
        # Prédiction avec ELO uniquement (pas de données historiques dispo au moment du match)
        prediction = pred.predict(m["home"], m["away"], {})

        actual = m["result"]
        p_home = prediction["p_home"] / 100
        p_draw = prediction["p_draw"] / 100
        p_away = prediction["p_away"] / 100

        # Outcome réel
        if actual == "home":   act_vec = [1, 0, 0]; act_idx = 0
        elif actual == "draw": act_vec = [0, 1, 0]; act_idx = 1
        else:                  act_vec = [0, 0, 1]; act_idx = 2

        pred_vec = [p_home, p_draw, p_away]

        # Brier Score
        brier = sum((p-a)**2 for p,a in zip(pred_vec, act_vec))

        # RPS
        rps = compute_rps(pred_vec, act_idx)

        # Accuracy
        winner_pred = max(["home","draw","away"], key=lambda x: prediction[f"p_{x}"])
        is_correct  = (winner_pred == actual)
        if is_correct:
            correct += 1

        total_brier += brier
        total_rps   += rps

        results.append({
            "match":    f"{m['home']} vs {m['away']}",
            "phase":    m.get("phase", "Group"),
            "actual":   actual,
            "pred":     winner_pred,
            "correct":  is_correct,
            "p_home":   round(p_home*100, 1),
            "p_draw":   round(p_draw*100, 1),
            "p_away":   round(p_away*100, 1),
            "brier":    round(brier, 4),
            "rps":      round(rps, 4),
        })

    # Métriques finales
    accuracy    = round(correct / n * 100, 1)
    avg_brier   = round(total_brier / n, 4)
    avg_rps     = round(total_rps / n, 4)

    # Benchmarks industry
    brier_grade = "🟢 Excellent" if avg_brier < 0.20 else \
                  "🟡 Bon" if avg_brier < 0.22 else \
                  "🟠 Moyen" if avg_brier < 0.25 else "🔴 Faible"
    rps_grade   = "🟢 Excellent" if avg_rps < 0.200 else \
                  "🟡 Bon" if avg_rps < 0.210 else \
                  "🟠 Moyen" if avg_rps < 0.220 else "🔴 Faible"
    acc_grade   = "🟢 Excellent" if accuracy >= 60 else \
                  "🟡 Bon" if accuracy >= 55 else \
                  "🟠 Moyen" if accuracy >= 50 else "🔴 Faible"

    metrics = {
        "n_matches":  n,
        "correct":    correct,
        "accuracy":   accuracy,
        "avg_brier":  avg_brier,
        "avg_rps":    avg_rps,
        "results":    results,
    }

    if verbose:
        print(f"\n{'─'*60}")
        print(f"RÉSULTATS")
        print(f"{'─'*60}")
        print(f"Accuracy     : {accuracy}%  {acc_grade}")
        print(f"Brier Score  : {avg_brier}  {brier_grade}  (target < 0.22)")
        print(f"RPS          : {avg_rps}  {rps_grade}  (target < 0.205)")
        print(f"\nComparaison benchmarks :")
        print(f"  Bookmakers : ~58% accuracy, Brier ~0.192, RPS ~0.190")
        print(f"  CatBoost best : ~56% accuracy, RPS 0.1925")
        print(f"  Poisson pur : ~50% accuracy, RPS ~0.230")
        print(f"  Notre modèle V2 : {accuracy}% accuracy, RPS {avg_rps}")

        # Matchs mal prédits (surprises)
        wrong = [r for r in results if not r["correct"]]
        print(f"\nMatchs mal prédits ({len(wrong)}/{n}):")
        for r in wrong[:10]:
            print(f"  [{r['phase'][:3]}] {r['match']}: prédit {r['pred']} | réel {r['actual']} | p={r['p_home']}/{r['p_draw']}/{r['p_away']}")

    return metrics


if __name__ == "__main__":
    metrics = run_backtest(verbose=True)

    # Sauvegarde
    out = Path(__file__).parent / "backtest_wc2022.json"
    with open(out, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n💾 Résultats sauvegardés : {out}")
