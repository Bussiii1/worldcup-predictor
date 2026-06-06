"""
Fatigue Engine — items 5 & 6.
5. Densité de matchs (matchs joués dans les 30/60 derniers jours).
6. Performance à domicile neutre (stades neutres historique).
Source : eloratings.net TSV (déjà utilisé dans form_engine).
"""
import requests
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Optional

ELO_BASE = "https://www.eloratings.net/{slug}.tsv"
HEADERS  = {"User-Agent": "worldcup-predictor/2.0"}

ELO_SLUGS = {
    "France": "France", "Spain": "Spain", "Argentina": "Argentina",
    "England": "England", "Brazil": "Brazil", "Portugal": "Portugal",
    "Germany": "Germany", "Netherlands": "Netherlands", "Croatia": "Croatia",
    "Belgium": "Belgium", "Mexico": "Mexico", "USA": "United_States",
    "Uruguay": "Uruguay", "Colombia": "Colombia", "Ecuador": "Ecuador",
    "Denmark": "Denmark", "Switzerland": "Switzerland", "Austria": "Austria",
    "Turkey": "Turkey", "Norway": "Norway", "Sweden": "Sweden",
    "South Korea": "South_Korea", "Japan": "Japan", "Australia": "Australia",
    "Morocco": "Morocco", "Senegal": "Senegal", "Ivory Coast": "Ivory_Coast",
    "Egypt": "Egypt", "Ghana": "Ghana", "Cameroon": "Cameroon",
    "DR Congo": "DR_Congo", "Algeria": "Algeria", "Tunisia": "Tunisia",
    "South Africa": "South_Africa", "Nigeria": "Nigeria",
    "Iran": "Iran", "Saudi Arabia": "Saudi_Arabia", "Iraq": "Iraq",
    "Qatar": "Qatar", "Uzbekistan": "Uzbekistan",
    "Canada": "Canada", "Panama": "Panama", "Haiti": "Haiti",
    "Paraguay": "Paraguay", "Bolivia": "Bolivia",
    "Scotland": "Scotland", "Bosnia-Herzegovina": "Bosnia-Herzegovina",
    "Czechia": "Czech_Republic", "Jordan": "Jordan",
    "Cape Verde": "Cape_Verde", "Curaçao": "Curacao",
    "New Zealand": "New_Zealand", "Jamaica": "Jamaica",
}

ELO_CODES = {
    "France": "FR", "Spain": "ES", "Argentina": "AR", "England": "EN",
    "Brazil": "BR", "Portugal": "PT", "Germany": "DE", "Netherlands": "NE",
    "Croatia": "CR", "Belgium": "BE", "Mexico": "MX", "USA": "US",
    "Uruguay": "UR", "Colombia": "CO", "Ecuador": "EC", "Denmark": "DA",
    "Switzerland": "SW", "Austria": "AU", "Turkey": "TU", "Norway": "NO",
    "Sweden": "SW", "South Korea": "SK", "Japan": "JA", "Australia": "AS",
    "Morocco": "MO", "Senegal": "SN", "Ivory Coast": "CI", "Egypt": "EG",
    "Ghana": "GH", "Cameroon": "CM", "DR Congo": "CD", "Algeria": "AL",
    "Tunisia": "TU", "South Africa": "ZA", "Nigeria": "NG", "Iran": "IR",
    "Saudi Arabia": "SA", "Iraq": "IQ", "Qatar": "QA", "Uzbekistan": "UZ",
    "Canada": "CA", "Panama": "PM", "Haiti": "HA", "Paraguay": "PY",
    "Scotland": "SC", "Bosnia-Herzegovina": "BA", "Czechia": "CZ",
    "Jordan": "JO", "Cape Verde": "CV", "New Zealand": "NZ", "Jamaica": "JM",
    "Curaçao": "CW",
}

_CACHE: dict = {}


def _fetch_tsv(slug: str) -> list[dict]:
    try:
        r = requests.get(ELO_BASE.format(slug=slug), headers=HEADERS, timeout=12)
        r.raise_for_status()
        rows = []
        for line in r.text.strip().split("\n"):
            parts = line.split("\t")
            if len(parts) < 8:
                continue
            try:
                rows.append({
                    "year":    int(parts[0]),
                    "month":   int(parts[1]),
                    "day":     int(parts[2]),
                    "home":    parts[3].strip(),
                    "away":    parts[4].strip(),
                    "neutral": len(parts) > 8 and parts[8].strip() == "1",
                    "tournament": parts[7].strip() if len(parts) > 7 else "",
                })
            except (ValueError, IndexError):
                continue
        return rows
    except Exception:
        return []


def get_fatigue_and_neutral(team: str, match_date: str) -> dict:
    """
    Retourne :
    - matches_last_14d / 30d / 60d  (densité de matchs)
    - fatigue_score                  (0-1, plus c'est haut plus c'est fatigué)
    - neutral_win_rate               (% victoires sur terrain neutre depuis 2018)
    - neutral_matches                (nb matchs neutres)
    """
    cache_key = f"{team}_{match_date}"
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    slug = ELO_SLUGS.get(team)
    code = ELO_CODES.get(team)
    if not slug or not code:
        result = {"team": team, "fatigue_score": 0.0, "neutral_win_rate": None}
        _CACHE[cache_key] = result
        return result

    rows = _fetch_tsv(slug)
    if not rows:
        result = {"team": team, "fatigue_score": 0.0, "neutral_win_rate": None, "error": "fetch_failed"}
        _CACHE[cache_key] = result
        return result

    try:
        ref_date = datetime.strptime(match_date, "%Y-%m-%d")
    except ValueError:
        ref_date = datetime.today()

    d14 = ref_date - timedelta(days=14)
    d30 = ref_date - timedelta(days=30)
    d60 = ref_date - timedelta(days=60)

    n14 = n30 = n60 = 0
    neutral_wins = neutral_total = 0

    for row in rows:
        if row["home"] != code and row["away"] != code:
            continue
        try:
            rdate = datetime(row["year"], row["month"], row["day"])
        except ValueError:
            continue

        # Fatigue : matchs avant le match WC
        if d14 <= rdate < ref_date:
            n14 += 1
        if d30 <= rdate < ref_date:
            n30 += 1
        if d60 <= rdate < ref_date:
            n60 += 1

        # Terrain neutre depuis 2018
        if row["neutral"] and row["year"] >= 2018 and rdate < ref_date:
            neutral_total += 1
            # On ne peut pas savoir W/D/L sans le score dans ce TSV simplifié
            # → on skip le win_rate depuis le TSV (pas de score ici)

    # Score de fatigue : pondéré par la récence
    # Idéalement < 3 matchs en 30j, > 6 = surmenage
    fatigue_raw = n14 * 1.5 + (n30 - n14) * 0.8 + (n60 - n30) * 0.3
    fatigue_score = round(min(fatigue_raw / 12, 1.0), 3)

    result = {
        "team":             team,
        "matches_last_14d": n14,
        "matches_last_30d": n30,
        "matches_last_60d": n60,
        "fatigue_score":    fatigue_score,
        "fatigue_level":    "high" if fatigue_score > 0.6 else "medium" if fatigue_score > 0.3 else "low",
        "neutral_matches":  neutral_total,
        "neutral_win_rate": None,   # nécessiterait le score dans le TSV
    }
    _CACHE[cache_key] = result
    return result
