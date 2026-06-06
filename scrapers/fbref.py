"""
Stats offensives/défensives des équipes nationales.
Source principale : SofaScore JSON API (non-officielle mais stable).
Fallback : calcul depuis les données Dixon-Coles déjà entraînées.
"""
import re
import json
import requests
import time
from pathlib import Path
from typing import Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
}

# SofaScore team IDs pour équipes nationales
# Source: https://api.sofascore.com/api/v1/team/{id}
SOFASCORE_IDS = {
    "France":          4481,
    "Brazil":          4750,
    "Argentina":       4759,
    "Spain":           4698,
    "England":         4713,
    "Germany":         4711,
    "Portugal":        4749,
    "Belgium":         4720,
    "Netherlands":     4705,
    "Morocco":         4737,
    "USA":             4679,
    "Mexico":          4735,
    "Japan":           4756,
    "Croatia":         4722,
    "Uruguay":         4764,
    "Denmark":         4716,
    "Switzerland":     4676,
    "Colombia":        4753,
    "Ecuador":         4755,
    "South Korea":     4773,
    "Senegal":         4769,
    "Canada":          4716,
    "Austria":         4680,
    "Turkey":          4781,
    "Serbia":          4768,
    "Australia":       4750,
    "Iran":            4728,
    "Saudi Arabia":    4766,
    "Qatar":           4747,
    "Tunisia":         4779,
    "Ghana":           4722,
    "Cameroon":        4700,
    "Norway":          4743,
    "Scotland":        4767,
    "Paraguay":        4745,
    "Panama":          4744,
    "Algeria":         4675,
    "Egypt":           4709,
    "Ivory Coast":     4729,
    "DR Congo":        4706,
    "South Africa":    4772,
    "Nigeria":         4742,
    "Cape Verde":      4701,
    "Jordan":          4731,
    "Iraq":            4727,
    "Uzbekistan":      4785,
    "New Zealand":     4741,
    "Haiti":           4724,
    "Jamaica":         4730,
    "Bosnia-Herzegovina": 4692,
    "Czechia":         4704,
    "Curaçao":         4703,
    "Sweden":          4775,
    "Portugal":        4749,
}

# Cache des résultats pour éviter de re-fetcher
_CACHE: dict = {}

# Chargement du modèle DC pour fallback
_DC_PATH = Path(__file__).parent.parent / "data" / "dc_model.json"


def _load_dc() -> dict:
    if _DC_PATH.exists():
        try:
            return json.loads(_DC_PATH.read_text())
        except Exception:
            pass
    return {}


def _dc_xg_estimate(team: str, dc: dict) -> Optional[float]:
    """
    Estime le xG offensif depuis les paramètres Dixon-Coles.
    attack_i * mu = expected goals against average defense
    """
    attack = dc.get("attack", {}).get(team)
    mu = dc.get("mu", 1.18)
    if attack:
        # Contre une défense moyenne (=1.0), les buts attendus = attack * mu * WC_scale
        wc_scale = 1.18 / mu
        return round(attack * 1.0 * mu * wc_scale, 3)
    return None


def _dc_xga_estimate(team: str, dc: dict) -> Optional[float]:
    """
    Estime le xGA défensif : contre une attaque moyenne, buts concédés = defense * mu.
    Defense BASSE = bonne défense.
    """
    defense = dc.get("defense", {}).get(team)
    mu = dc.get("mu", 1.18)
    if defense:
        wc_scale = 1.18 / mu
        # Buts encaissés contre attaque moyenne (=1.0)
        return round(1.0 * defense * mu * wc_scale, 3)
    return None


def _fetch_sofascore(team_id: int) -> Optional[dict]:
    """
    Appelle l'API SofaScore pour récupérer les stats récentes d'une équipe.
    Endpoint : /api/v1/team/{id}/statistics/season/last
    """
    try:
        url = f"https://api.sofascore.com/api/v1/team/{team_id}/statistics/season/last"
        time.sleep(0.8)
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


def _parse_sofascore(data: dict, team: str) -> dict:
    """Extrait les stats pertinentes de la réponse SofaScore."""
    result: dict = {"team": team, "source": "sofascore"}
    if not data:
        return result

    stats = data.get("statistics", {}) or data.get("stats", {}) or {}

    # Buts
    result["goals_scored"]    = stats.get("goalsScored") or stats.get("goals")
    result["goals_conceded"]  = stats.get("goalsConceded") or stats.get("goalsAgainst")
    result["matches_played"]  = stats.get("matchesTotal") or stats.get("played")

    mp = result["matches_played"]
    if mp and mp > 0:
        if result["goals_scored"] is not None:
            result["xg_rolling"] = round(result["goals_scored"] / mp, 3)
        if result["goals_conceded"] is not None:
            result["xga_rolling"] = round(result["goals_conceded"] / mp, 3)

    # Rating moyen
    result["avg_rating"] = stats.get("avgRating") or stats.get("rating")

    return result


def get_team_xg(team: str) -> dict:
    """
    Retourne xG/xGA pour une équipe.
    Priorité : SofaScore → Dixon-Coles fallback.
    """
    if team in _CACHE:
        return _CACHE[team]

    result: dict = {"team": team, "source": "combined"}

    # 1. Essai SofaScore
    team_id = SOFASCORE_IDS.get(team)
    if team_id:
        raw = _fetch_sofascore(team_id)
        if raw:
            ss = _parse_sofascore(raw, team)
            result.update(ss)

    # 2. Fallback Dixon-Coles si pas de xG SofaScore
    dc = _load_dc()
    if not result.get("xg_rolling") and dc:
        xg_dc = _dc_xg_estimate(team, dc)
        if xg_dc:
            result["xg_rolling"] = xg_dc
            result["xg_source"] = "dixon_coles"

    if not result.get("xga_rolling") and dc:
        xga_dc = _dc_xga_estimate(team, dc)
        if xga_dc:
            result["xga_rolling"] = xga_dc
            result["xga_source"] = "dixon_coles"

    _CACHE[team] = result
    return result


def get_both(home: str, away: str) -> tuple[dict, dict]:
    h = get_team_xg(home)
    a = get_team_xg(away)
    return h, a
