"""
Étape 4 — Validation sur WC 2022 (comme dans la vidéo).
Calibre le modèle sur les données AVANT le 21 nov 2022 (1er match WC 2022).
Lance 100 000 simulations du tournoi 2022.
Compare avec les vrais résultats.
"""
import sys
import json
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))

from dixon_coles.data_loader import load_matches, QUALIFIED
from dixon_coles.model import DixonColesModel

# Équipes WC 2022 et groupes officiels
GROUPS_2022: dict[str, list[str]] = {
    "A": ["Qatar",    "Ecuador",      "Senegal",      "Netherlands"],
    "B": ["England",  "Iran",         "USA",          "Wales"],
    "C": ["Argentina","Saudi Arabia", "Mexico",       "Poland"],
    "D": ["France",   "Australia",    "Denmark",      "Tunisia"],
    "E": ["Spain",    "Costa Rica",   "Germany",      "Japan"],
    "F": ["Belgium",  "Canada",       "Morocco",      "Croatia"],
    "G": ["Brazil",   "Serbia",       "Switzerland",  "Cameroon"],
    "H": ["Portugal", "Ghana",        "Uruguay",      "South Korea"],
}

# Vainqueur réel de chaque phase
REAL_WINNER = "Argentina"
REAL_FINAL  = {"Argentina", "France"}
REAL_SEMI   = {"Argentina", "France", "Croatia", "Morocco"}
REAL_QUARTER= {"Argentina", "France", "Croatia", "Morocco", "Netherlands", "England", "Brazil", "Portugal"}

WC2022_TEAMS = {t for g in GROUPS_2022.values() for t in g}


def _group_stage_2022(group, model):
    stats = {t: {"pts": 0, "gf": 0, "ga": 0} for t in group}
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            home, away = group[i], group[j]
            gh, ga = model.simulate_match(home, away, knockout=False)
            stats[home]["gf"] += gh; stats[home]["ga"] += ga
            stats[away]["gf"] += ga; stats[away]["ga"] += gh
            if gh > ga:   stats[home]["pts"] += 3
            elif gh == ga: stats[home]["pts"] += 1; stats[away]["pts"] += 1
            else:          stats[away]["pts"] += 3
    ranking = [{"team": t, "pts": s["pts"], "gd": s["gf"] - s["ga"], "gf": s["gf"]}
               for t, s in stats.items()]
    ranking.sort(key=lambda x: (x["pts"], x["gd"], x["gf"]), reverse=True)
    return ranking


def simulate_wc2022(model) -> str:
    """Simule WC 2022, retourne le vainqueur."""
    import numpy as np

    r16_teams = []
    for gname, group in GROUPS_2022.items():
        ranking = _group_stage_2022(group, model)
        r16_teams.append(ranking[0]["team"])
        r16_teams.append(ranking[1]["team"])

    def ko_round(teams):
        winners = []
        for k in range(0, len(teams), 2):
            gh, ga = model.simulate_match(teams[k], teams[k+1], knockout=True)
            winners.append(teams[k] if gh > ga else teams[k+1])
        return winners

    r8 = ko_round(r16_teams)
    r4 = ko_round(r8)
    r2 = ko_round(r4)
    gh, ga = model.simulate_match(r2[0], r2[1], knockout=True)
    return r2[0] if gh > ga else r2[1]


def simulate_wc2022_full(model) -> dict:
    """Simule WC 2022 complet, retourne le résultat par étape."""
    import numpy as np

    results = {t: "group" for t in WC2022_TEAMS}
    r16_teams = []
    for gname, group in GROUPS_2022.items():
        ranking = _group_stage_2022(group, model)
        r16_teams.append(ranking[0]["team"])
        r16_teams.append(ranking[1]["team"])
        results[ranking[0]["team"]] = "r16"
        results[ranking[1]["team"]] = "r16"

    def ko_round(teams, stage):
        winners = []
        for k in range(0, len(teams), 2):
            gh, ga = model.simulate_match(teams[k], teams[k+1], knockout=True)
            w = teams[k] if gh > ga else teams[k+1]
            winners.append(w)
            results[w] = stage
        return winners

    r8 = ko_round(r16_teams, "qf")
    r4 = ko_round(r8, "sf")
    r2 = ko_round(r4, "final")
    gh, ga = model.simulate_match(r2[0], r2[1], knockout=True)
    winner = r2[0] if gh > ga else r2[1]
    results[winner] = "winner"
    return results


def run_backtest(n: int = 100_000, cutoff_year: int = 2018):
    print("=" * 60)
    print("BACKTEST WC 2022 (process exact de la vidéo)")
    print("Calibration sur données avant le 21/11/2022")
    print("=" * 60)

    # Données jusqu'au 20 nov 2022
    df = load_matches(cutoff_year=cutoff_year)
    cutoff_date = date(2022, 11, 20)
    df = df[df["date"].dt.date <= cutoff_date].copy()
    print(f"  {len(df)} matchs utilisés (avant le 21/11/2022)")

    # Filtrer sur les équipes WC 2022
    # On garde uniquement les équipes WC 2022 pour la calibration
    mask = df["home_team"].isin(WC2022_TEAMS) & df["away_team"].isin(WC2022_TEAMS)
    df = df[mask].copy()
    print(f"  {len(df)} matchs entre équipes WC 2022")

    model = DixonColesModel()
    model.fit(df)

    print(f"\n=== Top équipes selon le modèle (avant WC 2022) ===")
    rankings = [r for r in model.rankings() if r["team"] in WC2022_TEAMS]
    for i, r in enumerate(rankings[:10], 1):
        print(f"  {i:2}. {r['team']:<20} strength={r['strength']:.3f}")

    # Monte Carlo
    print(f"\n=== {n:,} simulations du WC 2022 ===")
    stages = ["group", "r16", "qf", "sf", "final", "winner"]
    counts = {t: {s: 0 for s in stages} for t in WC2022_TEAMS}

    step = n // 10
    for i in range(n):
        if i % step == 0:
            print(f"  Simulation {i:>7} / {n}...")
        result = simulate_wc2022_full(model)
        for team, stage in result.items():
            counts[team][stage] += 1

    # Résultats
    rows = []
    for t in WC2022_TEAMS:
        c = counts[t]
        rows.append({
            "team":    t,
            "win_%":   round(c["winner"] / n * 100, 2),
            "final_%": round((c["winner"] + c["final"]) / n * 100, 2),
            "semi_%":  round((c["winner"] + c["final"] + c["sf"]) / n * 100, 2),
        })
    rows.sort(key=lambda x: -x["win_%"])

    print(f"\n{'='*60}")
    print(f"PRÉDICTIONS DU MODÈLE POUR LE WC 2022")
    print(f"{'='*60}")
    print(f"{'Rang':<5} {'Équipe':<22} {'Gagne':>7} {'Finale':>8} {'Demi':>7}")
    print("-" * 55)
    for i, r in enumerate(rows[:16], 1):
        flag = ""
        if r["team"] == REAL_WINNER:       flag = " ← VAINQUEUR RÉEL"
        elif r["team"] in REAL_FINAL:      flag = " ← finaliste réel"
        elif r["team"] in REAL_SEMI:       flag = " ← demi-finaliste réel"
        print(f"  {i:2}. {r['team']:<22} {r['win_%']:>6.1f}%  {r['final_%']:>6.1f}%  {r['semi_%']:>6.1f}%{flag}")

    # Analyse
    top8_pred = {r["team"] for r in rows[:8]}
    top8_real = REAL_QUARTER
    overlap    = top8_pred & top8_real
    print(f"\nÉquipes vraiment en quart de finale prédites dans le top 8 : {len(overlap)}/8")
    print(f"  Prédites : {', '.join(sorted(overlap))}")
    print(f"  Manquées : {', '.join(sorted(top8_real - top8_pred))}")

    winner_rank = next(i+1 for i, r in enumerate(rows) if r["team"] == REAL_WINNER)
    print(f"\nRang de l'Argentine (vainqueur réel) : {winner_rank}e")

    # Sauvegarde
    out = Path(__file__).parent.parent / "output" / "backtest_wc2022_dixon.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"n": n, "results": rows}, indent=2))
    print(f"\nSauvegardé : {out}")

    return rows


if __name__ == "__main__":
    run_backtest(n=100_000)
