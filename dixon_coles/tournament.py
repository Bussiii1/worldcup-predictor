"""
Étape 3 — Structure du tournoi Coupe du Monde 2026.
12 groupes de 4 équipes → 2 premiers + 8 meilleurs 3e → KO 32.
"""
from __future__ import annotations
import numpy as np

# Tirage au sort officiel WC 2026 (48 équipes, 12 groupes)
GROUPS: dict[str, list[str]] = {
    "A": ["USA", "Panama", "Morocco", "New Zealand"],  # (approximatif, tirage non final)
    "B": ["Spain", "Uruguay", "Egypt", "Uzbekistan"],
    "C": ["Argentina", "Chile", "Nigeria", "Indonesia"],
    "D": ["France", "Ivory Coast", "Honduras", "Switzerland"],
    "E": ["Germany", "Japan", "South Africa", "DR Congo"],
    "F": ["Brazil", "Costa Rica", "Australia", "Senegal"],
    "G": ["England", "Serbia", "Colombia", "Algeria"],
    "H": ["Portugal", "Bolivia", "Saudi Arabia", "South Korea"],
    "I": ["Netherlands", "Mexico", "Canada", "Cameroon"],
    "J": ["Croatia", "Belgium", "Ecuador", "Iran"],
    "K": ["Turkey", "Ukraine", "Paraguay", "Jordan"],
    "L": ["Austria", "Denmark", "Jamaica", "Scotland"],
}

# 3 points victoire, 1 nul, 0 défaite
def _group_stage(group: list[str], model) -> list[dict]:
    """Simule une phase de groupes, retourne le classement."""
    stats = {t: {"pts": 0, "gf": 0, "ga": 0} for t in group}

    # Round-robin : 6 matchs
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            home, away = group[i], group[j]
            gh, ga = model.simulate_match(home, away, knockout=False)
            stats[home]["gf"] += gh; stats[home]["ga"] += ga
            stats[away]["gf"] += ga; stats[away]["ga"] += gh
            if gh > ga:
                stats[home]["pts"] += 3
            elif gh == ga:
                stats[home]["pts"] += 1; stats[away]["pts"] += 1
            else:
                stats[away]["pts"] += 3

    ranking = []
    for t, s in stats.items():
        ranking.append({
            "team": t,
            "pts": s["pts"],
            "gd": s["gf"] - s["ga"],
            "gf": s["gf"],
        })
    ranking.sort(key=lambda x: (x["pts"], x["gd"], x["gf"]), reverse=True)
    return ranking


def _ko_match(home: str, away: str, model) -> str:
    """Retourne le vainqueur d'un match KO (avec prolongations/tirs au but)."""
    gh, ga = model.simulate_match(home, away, knockout=True)
    return home if gh > ga else away


def simulate_tournament(model) -> dict:
    """
    Simule une Coupe du Monde complète.
    Retourne un dict {équipe: meilleur résultat atteint}.
    """
    results = {t: "group" for group in GROUPS.values() for t in group}

    # Phase de groupes
    all_group_results = {}
    third_place_teams = []

    for gname, group in GROUPS.items():
        ranking = _group_stage(group, model)
        all_group_results[gname] = ranking

        # 1er et 2e qualifiés directement
        results[ranking[0]["team"]] = "r16"
        results[ranking[1]["team"]] = "r16"

        # 3e avec ses stats (pour sélection des meilleurs 3e)
        third_place_teams.append({
            "team": ranking[2]["team"],
            "pts":  ranking[2]["pts"],
            "gd":   ranking[2]["gd"],
            "gf":   ranking[2]["gf"],
            "group": gname,
        })

    # 8 meilleurs 3e sur 12
    third_place_teams.sort(key=lambda x: (x["pts"], x["gd"], x["gf"]), reverse=True)
    best_thirds = [t["team"] for t in third_place_teams[:8]]
    for t in best_thirds:
        results[t] = "r16"

    # Huitièmes de finale (16 équipes)
    # On construit le bracket à partir des 1ers et 2e de chaque groupe + 8 meilleurs 3e
    qualified = []
    for gname, ranking in all_group_results.items():
        qualified.append(("1st_" + gname, ranking[0]["team"]))
        qualified.append(("2nd_" + gname, ranking[1]["team"]))
    for t in best_thirds:
        qualified.append(("3rd", t))

    # Simplification : bracket aléatoire des 32 qualifiés (sans fixture officielle)
    r16_teams = [t for label, t in qualified if results[t] == "r16"]
    np.random.shuffle(r16_teams)

    def run_ko_round(teams: list[str], stage_name: str) -> list[str]:
        winners = []
        for k in range(0, len(teams), 2):
            w = _ko_match(teams[k], teams[k + 1], model)
            winners.append(w)
            results[w] = stage_name
        return winners

    r8  = run_ko_round(r16_teams, "qf")
    r4  = run_ko_round(r8,        "sf")
    r2  = run_ko_round(r4,        "final")
    winner = _ko_match(r2[0], r2[1], model)
    results[winner] = "winner"

    return results


def simulate_n(model, n: int = 100_000, verbose: bool = True) -> dict[str, dict]:
    """
    Lance N simulations Monte Carlo.
    Retourne les compteurs : {équipe: {stage: count}}.
    """
    all_teams = [t for group in GROUPS.values() for t in group]
    stages = ["group", "r16", "qf", "sf", "final", "winner"]

    counts: dict[str, dict[str, int]] = {
        t: {s: 0 for s in stages} for t in all_teams
    }

    step = n // 10
    for i in range(n):
        if verbose and i % step == 0:
            print(f"  Simulation {i:>7} / {n}...")
        tour_result = simulate_tournament(model)
        for team, stage in tour_result.items():
            counts[team][stage] += 1

    return counts


def format_results(counts: dict, n: int) -> list[dict]:
    """Formate les résultats en pourcentages."""
    rows = []
    for team, c in counts.items():
        rows.append({
            "team":       team,
            "win_%":      round(c["winner"] / n * 100, 2),
            "final_%":    round((c["winner"] + c["final"]) / n * 100, 2),
            "semi_%":     round((c["winner"] + c["final"] + c["sf"]) / n * 100, 2),
            "quarter_%":  round((c["winner"] + c["final"] + c["sf"] + c["qf"]) / n * 100, 2),
            "r16_%":      round((c["winner"] + c["final"] + c["sf"] + c["qf"] + c["r16"]) / n * 100, 2),
        })
    rows.sort(key=lambda x: -x["win_%"])
    return rows
