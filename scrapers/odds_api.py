"""
Cotes bookmakers via The Odds API (the-odds-api.com).
Plan gratuit : 500 req/mois — suffisant pour toute la phase de groupes.
Clé gratuite sur : https://the-odds-api.com
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.the-odds-api.com/v4"
SPORT_KEY = "soccer_fifa_world_cup"

# Bookmakers de référence (fiabilité décroissante)
SHARP_BOOKS = ["pinnacle", "betfair", "bet365", "unibet", "williamhill"]


def get_match_odds(home: str, away: str) -> dict:
    """
    Récupère les cotes live pour un match WC 2026.
    Retourne un dict avec prob_home, prob_draw, prob_away normalisées.
    """
    api_key = os.environ.get("ODDS_API_KEY", "")
    if not api_key:
        return {"source": "odds_api", "error": "no_api_key",
                "odds_available": False}

    try:
        resp = requests.get(
            f"{BASE_URL}/sports/{SPORT_KEY}/odds",
            params={
                "apiKey":      api_key,
                "regions":     "eu,uk",
                "markets":     "h2h,totals",
                "oddsFormat":  "decimal",
                "bookmakers":  ",".join(SHARP_BOOKS),
            },
            timeout=10,
        )
        resp.raise_for_status()
        events = resp.json()

        # Cherche le match correspondant
        for event in events:
            h = event.get("home_team", "").lower()
            a = event.get("away_team", "").lower()
            if _team_match(home, h) and _team_match(away, a):
                return _parse_event(event, home, away)

        return {"source": "odds_api", "error": "match_not_found",
                "odds_available": False}

    except requests.exceptions.HTTPError as e:
        if "401" in str(e):
            return {"source": "odds_api", "error": "invalid_api_key",
                    "odds_available": False}
        return {"source": "odds_api", "error": str(e), "odds_available": False}
    except Exception as e:
        return {"source": "odds_api", "error": str(e), "odds_available": False}


def _team_match(name: str, api_name: str) -> bool:
    """Matching flexible des noms d'équipes."""
    n = name.lower().strip()
    a = api_name.lower().strip()
    if n == a:
        return True
    # Alias courants
    aliases = {
        "usa": ["united states", "us men", "usmnt", "u.s.a."],
        "dr congo": ["congo dr", "democratic republic of congo", "drc"],
        "ivory coast": ["côte d'ivoire", "cote d'ivoire", "cote divoire"],
        "south korea": ["korea republic", "republic of korea", "korea"],
        "czechia": ["czech republic", "czech"],
        "bosnia-herzegovina": ["bosnia and herzegovina", "bosnia & herzegovina", "bosnia"],
        "iran": ["ir iran"],
        "cape verde": ["cabo verde"],
        "curaçao": ["curacao"],
        "usa": ["united states", "us"],
    }
    for key, vals in aliases.items():
        if n == key or n in vals:
            if a == key or a in vals:
                return True
    # Fuzzy : un contient l'autre
    return n in a or a in n


def _parse_event(event: dict, home: str, away: str) -> dict:
    """Parse l'event Odds API et retourne les signaux."""
    h2h_home, h2h_draw, h2h_away = [], [], []
    over25_vals, under25_vals = [], []

    has_pinnacle = False
    for bk in event.get("bookmakers", []):
        if bk["key"] == "pinnacle":
            has_pinnacle = True
        for mkt in bk.get("markets", []):
            if mkt["key"] == "h2h":
                for outcome in mkt["outcomes"]:
                    n = outcome["name"].lower()
                    p = outcome["price"]
                    if "draw" in n:
                        h2h_draw.append(p)
                    elif _team_match(home, n):
                        h2h_home.append(p)
                    else:
                        h2h_away.append(p)
            elif mkt["key"] == "totals":
                for outcome in mkt["outcomes"]:
                    if outcome.get("point") == 2.5:
                        if outcome["name"] == "Over":
                            over25_vals.append(outcome["price"])
                        else:
                            under25_vals.append(outcome["price"])

    def avg(lst): return round(sum(lst)/len(lst), 3) if lst else None

    odds_h = avg(h2h_home)
    odds_d = avg(h2h_draw)
    odds_a = avg(h2h_away)
    odds_o25 = avg(over25_vals)
    odds_u25 = avg(under25_vals)

    # Probabilités implicites
    imp_h = (1/odds_h) if odds_h else None
    imp_d = (1/odds_d) if odds_d else None
    imp_a = (1/odds_a) if odds_a else None

    # Normalisation (retire la marge bookmaker)
    prob_h, prob_d, prob_a = None, None, None
    if all([imp_h, imp_d, imp_a]):
        total = imp_h + imp_d + imp_a
        prob_h = round(imp_h / total, 4)
        prob_d = round(imp_d / total, 4)
        prob_a = round(imp_a / total, 4)
        overround = round((total - 1) * 100, 2)  # marge bookmaker en %
    else:
        overround = None

    # xG implicites depuis les cotes (via formule empirique calibrée WC)
    xg_h = _odds_to_xg(odds_h, odds_a) if odds_h and odds_a else None
    xg_a = _odds_to_xg(odds_a, odds_h) if odds_h and odds_a else None

    return {
        "odds_home":        odds_h,
        "odds_draw":        odds_d,
        "odds_away":        odds_a,
        "odds_over25":      odds_o25,
        "odds_under25":     odds_u25,
        "prob_home":        prob_h,
        "prob_draw":        prob_d,
        "prob_away":        prob_a,
        "overround_pct":    overround,
        "xg_implied_home":  xg_h,
        "xg_implied_away":  xg_a,
        "bookmakers_count": len(event.get("bookmakers", [])),
        "has_pinnacle":     has_pinnacle,
        "odds_available":   True,
        "source":           "odds_api",
    }


def _odds_to_xg(odds_team: float, odds_opp: float) -> float:
    """
    Convertit les cotes en xG attendu.
    Formule calibrée sur données WC historiques.
    Base : 1.18 buts/équipe en WC, ajusté par force relative.
    """
    BASE = 1.18
    # P(victoire) sans le nul = force relative
    p = 1 / odds_team
    p_opp = 1 / odds_opp
    ratio = p / (p + p_opp)  # 0-1, 0.5 = équilibré
    factor = (ratio / 0.5) ** 1.2
    return round(BASE * factor, 3)


def get_all_wc_odds() -> list[dict]:
    """Récupère toutes les cotes WC disponibles."""
    api_key = os.environ.get("ODDS_API_KEY", "")
    if not api_key:
        return []
    try:
        resp = requests.get(
            f"{BASE_URL}/sports/{SPORT_KEY}/odds",
            params={"apiKey": api_key, "regions": "eu", "markets": "h2h",
                    "oddsFormat": "decimal"},
            timeout=10,
        )
        return resp.json()
    except Exception:
        return []


if __name__ == "__main__":
    import json
    print("Testing Odds API...")
    print("(Add ODDS_API_KEY to .env to get live odds)")
    result = get_match_odds("France", "Argentina")
    print(json.dumps(result, indent=2))

    # Test sans clé
    all_odds = get_all_wc_odds()
    print(f"\nMatches with odds available: {len(all_odds)}")
