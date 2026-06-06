"""
Features extraites de l'historique World Cup (Fjelstul DB).
Calcule les stats long-terme de chaque équipe en WC.
"""
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from functools import lru_cache

sys.path.insert(0, str(Path(__file__).parent.parent))
from data.load_wc_history import load, normalize_team


@lru_cache(maxsize=None)
def _get_matches() -> pd.DataFrame:
    return load("matches")

@lru_cache(maxsize=None)
def _get_team_appearances() -> pd.DataFrame:
    return load("team_appearances")

@lru_cache(maxsize=None)
def _get_goals() -> pd.DataFrame:
    return load("goals")

@lru_cache(maxsize=None)
def _get_bookings() -> pd.DataFrame:
    return load("bookings")

@lru_cache(maxsize=None)
def _get_group_standings() -> pd.DataFrame:
    return load("group_standings")


def get_team_wc_stats(team: str) -> dict:
    """Stats globales d'une équipe dans toute l'histoire de la WC."""
    try:
        matches = _get_matches()
        ta = _get_team_appearances()

        # Filtre sur l'équipe
        team_n = normalize_team(team)

        # Dans matches, les colonnes peuvent varier selon la version du dataset
        home_col = "home_team_name" if "home_team_name" in matches.columns else "home_team_code"
        away_col = "away_team_name" if "away_team_name" in matches.columns else "away_team_code"

        home_m = matches[matches[home_col] == team_n].copy()
        away_m = matches[matches[away_col] == team_n].copy()
        all_m  = pd.concat([home_m, away_m])

        if len(all_m) == 0:
            return _empty_wc_stats(team)

        # Buts marqués / concédés
        home_m["gf"] = pd.to_numeric(home_m.get("home_team_score", pd.Series()), errors="coerce")
        home_m["ga"] = pd.to_numeric(home_m.get("away_team_score", pd.Series()), errors="coerce")
        away_m["gf"] = pd.to_numeric(away_m.get("away_team_score", pd.Series()), errors="coerce")
        away_m["ga"] = pd.to_numeric(away_m.get("home_team_score", pd.Series()), errors="coerce")

        combined = pd.concat([home_m[["gf","ga"]], away_m[["gf","ga"]]]).dropna()

        if len(combined) == 0:
            return _empty_wc_stats(team)

        total_m = len(combined)
        wins    = int(((combined["gf"] > combined["ga"])).sum())
        draws   = int(((combined["gf"] == combined["ga"])).sum())
        losses  = int(((combined["gf"] < combined["ga"])).sum())
        gf_avg  = round(combined["gf"].mean(), 3)
        ga_avg  = round(combined["ga"].mean(), 3)
        cs_pct  = round((combined["ga"] == 0).mean(), 3)

        # Phases KO uniquement (stage_name contient "Round of", "Quarter", "Semi", "Final")
        ko_stages = ["Round of 16", "Quarter-finals", "Semi-finals",
                     "Third-place match", "Final", "Round of 32"]
        stage_col = "stage_name" if "stage_name" in matches.columns else None

        ko_wins, ko_total = 0, 0
        if stage_col:
            ko_home = home_m[home_m[stage_col].str.contains("|".join(ko_stages), na=False)]
            ko_away = away_m[away_m[stage_col].str.contains("|".join(ko_stages), na=False)]

            for _, r in ko_home.iterrows():
                gf = pd.to_numeric(r.get("home_team_score"), errors="coerce")
                ga = pd.to_numeric(r.get("away_team_score"), errors="coerce")
                if pd.notna(gf) and pd.notna(ga):
                    ko_total += 1
                    if gf > ga: ko_wins += 1

            for _, r in ko_away.iterrows():
                gf = pd.to_numeric(r.get("away_team_score"), errors="coerce")
                ga = pd.to_numeric(r.get("home_team_score"), errors="coerce")
                if pd.notna(gf) and pd.notna(ga):
                    ko_total += 1
                    if gf > ga: ko_wins += 1

        ko_win_rate = round(ko_wins / max(ko_total, 1), 3)

        # Nombre d'éditions disputées (expérience)
        appearances_col = "tournament_id" if "tournament_id" in matches.columns else None
        n_editions = len(all_m[appearances_col].unique()) if appearances_col else 0

        # Tournois gagnés
        finalists = _get_finalists()
        n_titles  = finalists.get(team_n, {}).get("titles", 0)
        n_finals  = finalists.get(team_n, {}).get("finals", 0)

        return {
            "team": team,
            "wc_appearances":    n_editions,
            "wc_titles":         n_titles,
            "wc_finals":         n_finals,
            "wc_total_matches":  total_m,
            "wc_win_rate":       round(wins / total_m, 3),
            "wc_draw_rate":      round(draws / total_m, 3),
            "wc_loss_rate":      round(losses / total_m, 3),
            "wc_goals_scored_avg":   gf_avg,
            "wc_goals_conceded_avg": ga_avg,
            "wc_clean_sheet_pct":    cs_pct,
            "wc_ko_win_rate":    ko_win_rate,
            "wc_ko_matches":     ko_total,
            # Scoring momentum en WC
            "wc_experience_score": round(
                0.3 * min(n_editions / 10, 1) +
                0.3 * ko_win_rate +
                0.2 * (wins / total_m) +
                0.2 * min(n_titles / 3, 1),
                3
            ),
            "source": "fjelstul_worldcup",
        }
    except Exception as e:
        return {**_empty_wc_stats(team), "error": str(e)}


def get_h2h_stats(team_a: str, team_b: str) -> dict:
    """H2H complet entre deux équipes dans toute l'histoire de la WC."""
    try:
        matches = _get_matches()
        ta = normalize_team(team_a)
        tb = normalize_team(team_b)

        home_col = "home_team_name" if "home_team_name" in matches.columns else "home_team_code"
        away_col = "away_team_name" if "away_team_name" in matches.columns else "away_team_code"

        h2h = matches[
            ((matches[home_col] == ta) & (matches[away_col] == tb)) |
            ((matches[home_col] == tb) & (matches[away_col] == ta))
        ].copy()

        if len(h2h) == 0:
            return _empty_h2h(team_a, team_b)

        wins_a, wins_b, draws = 0, 0, 0
        goals_a_list, goals_b_list = [], []

        for _, r in h2h.iterrows():
            h_score = pd.to_numeric(r.get("home_team_score"), errors="coerce")
            a_score = pd.to_numeric(r.get("away_team_score"), errors="coerce")
            if pd.isna(h_score) or pd.isna(a_score):
                continue

            is_home_a = (r[home_col] == ta)
            gf_a = h_score if is_home_a else a_score
            gf_b = a_score if is_home_a else h_score

            goals_a_list.append(gf_a)
            goals_b_list.append(gf_b)

            if gf_a > gf_b:   wins_a += 1
            elif gf_a < gf_b: wins_b += 1
            else:              draws  += 1

        n = wins_a + wins_b + draws
        if n == 0:
            return _empty_h2h(team_a, team_b)

        avg_a  = round(np.mean(goals_a_list), 2) if goals_a_list else None
        avg_b  = round(np.mean(goals_b_list), 2) if goals_b_list else None
        avg_tt = round((avg_a or 0) + (avg_b or 0), 2)

        dominant = team_a if wins_a > wins_b else (team_b if wins_b > wins_a else "even")

        return {
            "team_a": team_a, "team_b": team_b,
            "h2h_matches":       n,
            "h2h_wins_a":        wins_a,
            "h2h_wins_b":        wins_b,
            "h2h_draws":         draws,
            "h2h_win_rate_a":    round(wins_a / n, 3),
            "h2h_win_rate_b":    round(wins_b / n, 3),
            "h2h_draw_rate":     round(draws / n, 3),
            "h2h_avg_goals_a":   avg_a,
            "h2h_avg_goals_b":   avg_b,
            "h2h_avg_total_goals": avg_tt,
            "h2h_over25_rate":   round(sum(1 for a,b in zip(goals_a_list,goals_b_list) if a+b>2.5)/n, 3),
            "h2h_dominant":      dominant,
            "source": "fjelstul_worldcup",
        }
    except Exception as e:
        return {**_empty_h2h(team_a, team_b), "error": str(e)}


def _get_finalists() -> dict:
    """Palmarès historique de la WC."""
    # Source : FIFA officiel (hardcodé pour robustesse)
    return {
        "Brazil":    {"titles": 5, "finals": 7},
        "Germany":   {"titles": 4, "finals": 8},
        "Italy":     {"titles": 4, "finals": 6},
        "Argentina": {"titles": 3, "finals": 5},
        "France":    {"titles": 2, "finals": 3},
        "Uruguay":   {"titles": 2, "finals": 3},
        "England":   {"titles": 1, "finals": 1},
        "Spain":     {"titles": 1, "finals": 1},
    }


def _empty_wc_stats(team: str) -> dict:
    return {
        "team": team, "wc_appearances": 0, "wc_titles": 0, "wc_finals": 0,
        "wc_total_matches": 0, "wc_win_rate": None, "wc_draw_rate": None,
        "wc_loss_rate": None, "wc_goals_scored_avg": None, "wc_goals_conceded_avg": None,
        "wc_clean_sheet_pct": None, "wc_ko_win_rate": None, "wc_ko_matches": 0,
        "wc_experience_score": 0, "source": "fjelstul_worldcup",
    }


def _empty_h2h(a: str, b: str) -> dict:
    return {
        "team_a": a, "team_b": b, "h2h_matches": 0,
        "h2h_wins_a": 0, "h2h_wins_b": 0, "h2h_draws": 0,
        "h2h_win_rate_a": None, "h2h_win_rate_b": None, "h2h_draw_rate": None,
        "h2h_avg_goals_a": None, "h2h_avg_goals_b": None, "h2h_avg_total_goals": None,
        "h2h_over25_rate": None, "h2h_dominant": "unknown",
        "source": "fjelstul_worldcup",
    }


if __name__ == "__main__":
    print("Testing WC features...")
    print("\n--- France WC Stats ---")
    import json
    stats = get_team_wc_stats("France")
    print(json.dumps(stats, indent=2))

    print("\n--- France vs Brazil H2H ---")
    h2h = get_h2h_stats("France", "Brazil")
    print(json.dumps(h2h, indent=2))
