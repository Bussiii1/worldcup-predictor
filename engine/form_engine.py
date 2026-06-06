"""
Moteur de forme pondérée avec décroissance exponentielle.
Source des matchs : eloratings.net (TSV) — déjà utilisé dans scrapers/elo.py
"""
import requests
import re
from datetime import datetime, timedelta
from typing import Optional

DECAY = 0.75        # chaque match passé vaut 75% du précédent
MIN_MATCHES = 4     # minimum pour avoir un score fiable
MAX_MATCHES = 10    # on regarde jusqu'à 10 matchs en arrière

# Poids par compétition
COMP_WEIGHTS = {
    "WC":  2.5,   # Coupe du Monde
    "WCQ": 2.0,   # Qualifs WC
    "WCF": 2.5,   # Finale WC
    "CG":  2.0,   # Copa America / Euros / AFCON groupe
    "CGF": 2.5,   # Copa America / Euros finale
    "NL":  1.8,   # Nations League
    "NLF": 2.0,   # Nations League finale
    "F":   0.8,   # Amical officiel
    "FR":  0.6,   # Amical non officiel
    "ECT": 2.0,   # Éliminatoires continentales
}

# Slugs eloratings.net
ELO_SLUGS = {
    "France": "France", "Spain": "Spain", "Argentina": "Argentina",
    "England": "England", "Brazil": "Brazil", "Portugal": "Portugal",
    "Germany": "Germany", "Netherlands": "Netherlands", "Croatia": "Croatia",
    "Belgium": "Belgium", "Mexico": "Mexico", "USA": "USA",
    "Uruguay": "Uruguay", "Colombia": "Colombia", "Ecuador": "Ecuador",
    "Denmark": "Denmark", "Switzerland": "Switzerland", "Austria": "Austria",
    "Turkey": "Turkey", "Norway": "Norway", "Sweden": "Sweden",
    "South Korea": "South_Korea", "Japan": "Japan", "Australia": "Australia",
    "Morocco": "Morocco", "Senegal": "Senegal", "Nigeria": "Nigeria",
    "Ivory Coast": "Ivory_Coast", "Egypt": "Egypt", "Ghana": "Ghana",
    "Cameroon": "Cameroon", "DR Congo": "DR_Congo",
    "Iran": "Iran", "Saudi Arabia": "Saudi_Arabia", "Iraq": "Iraq",
    "Qatar": "Qatar", "Uzbekistan": "Uzbekistan",
    "Canada": "Canada", "Panama": "Panama",
    "Chile": "Chile", "Paraguay": "Paraguay", "Bolivia": "Bolivia",
    "Algeria": "Algeria", "Tunisia": "Tunisia",
    "Scotland": "Scotland", "Bosnia-Herzegovina": "Bosnia-Herzegovina",
    "Czech Republic": "Czech_Republic", "Czechia": "Czech_Republic",
    "New Zealand": "New_Zealand", "Haiti": "Haiti",
    "Jordan": "Jordan", "Cape Verde": "Cape_Verde",
    "Curaçao": "Curacao", "South Africa": "South_Africa",
    "Honduras": "Honduras",
}

# Codes pays eloratings.net (colonnes home/away dans le TSV)
ELO_COUNTRY_CODES = {
    "France": "FR", "Spain": "ES", "Argentina": "AR", "England": "EN",
    "Brazil": "BR", "Portugal": "PT", "Germany": "DE", "Netherlands": "NE",
    "Croatia": "CR", "Belgium": "BE", "Mexico": "MX", "USA": "US",
    "Uruguay": "UR", "Colombia": "CO", "Ecuador": "EC", "Denmark": "DA",
    "Switzerland": "SW", "Austria": "AU", "Turkey": "TU", "Norway": "NO",
    "Sweden": "SE", "South Korea": "KO", "Japan": "JP", "Australia": "OA",
    "Morocco": "MA", "Senegal": "SN", "Nigeria": "NI", "Ivory Coast": "CI",
    "Egypt": "EG", "Ghana": "GH", "Cameroon": "CM", "DR Congo": "ZA",
    "Iran": "IR", "Saudi Arabia": "SA", "Iraq": "IQ", "Qatar": "QA",
    "Uzbekistan": "UZ", "Canada": "CA", "Panama": "PA", "Chile": "CL",
    "Paraguay": "PY", "Bolivia": "BO", "Algeria": "DZ", "Tunisia": "TS",
    "Scotland": "SC", "Bosnia-Herzegovina": "BO",
    "Czech Republic": "CZ", "Czechia": "CZ",
    "New Zealand": "NZ", "Haiti": "HA", "Jordan": "JO", "Cape Verde": "CV",
    "Curaçao": "CW", "South Africa": "ZF", "Honduras": "HO",
}


def _fetch_tsv_rows(team: str) -> list[dict]:
    """Récupère l'historique des matchs depuis eloratings.net"""
    slug = ELO_SLUGS.get(team, team.replace(" ", "_"))
    url = f"https://www.eloratings.net/{slug}.tsv"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        rows = []
        for line in r.text.strip().split("\n"):
            parts = line.split("\t")
            if len(parts) < 11:
                continue
            try:
                rows.append({
                    "year":     int(parts[0]),
                    "month":    int(parts[1]),
                    "day":      int(parts[2]),
                    "home":     parts[3].strip(),
                    "away":     parts[4].strip(),
                    "home_g":   int(parts[5]),
                    "away_g":   int(parts[6]),
                    "comp":     parts[7].strip(),
                    "neutral":  parts[8].strip() == "1",
                    "elo_home": float(parts[10]) if len(parts) > 10 and parts[10] else None,
                    "elo_away": float(parts[11]) if len(parts) > 11 and parts[11] else None,
                })
            except (ValueError, IndexError):
                continue
        return rows
    except Exception:
        return []


def get_recent_form(team: str, as_of_date: Optional[str] = None) -> dict:
    """
    Calcule la forme pondérée d'une équipe sur les N derniers matchs.
    as_of_date : "YYYY-MM-DD" (défaut = aujourd'hui)
    """
    rows = _fetch_tsv_rows(team)
    if not rows:
        return {"team": team, "form_score": None, "error": "no_data"}

    country_code = ELO_COUNTRY_CODES.get(team)
    if not country_code:
        return {"team": team, "form_score": None, "error": "unknown_country_code"}

    cutoff = datetime.strptime(as_of_date, "%Y-%m-%d") if as_of_date else datetime.today()

    # Filtrer les matchs joués avant la date limite
    past = []
    for r in rows:
        try:
            md = datetime(r["year"], r["month"], r["day"])
        except ValueError:
            continue
        if md >= cutoff:
            continue

        is_home = (r["home"] == country_code)
        is_away = (r["away"] == country_code)
        if not is_home and not is_away:
            continue

        gf = r["home_g"] if is_home else r["away_g"]
        ga = r["away_g"] if is_home else r["home_g"]
        result = "W" if gf > ga else ("D" if gf == ga else "L")

        past.append({
            "date":   md,
            "result": result,
            "gf":     gf,
            "ga":     ga,
            "comp":   r["comp"],
            "is_home": is_home,
            "elo_after": r["elo_home"] if is_home else r["elo_away"],
        })

    if not past:
        return {"team": team, "form_score": None, "error": "no_past_matches"}

    # Trier du plus récent au plus ancien
    past.sort(key=lambda x: x["date"], reverse=True)
    recent = past[:MAX_MATCHES]

    # Calcul de la forme pondérée
    form_num    = 0.0
    gf_num      = 0.0
    ga_num      = 0.0
    total_w     = 0.0
    elo_vals    = []

    for i, m in enumerate(recent):
        time_w = DECAY ** i
        comp_w = COMP_WEIGHTS.get(m["comp"], 1.0)
        w = time_w * comp_w
        total_w += w

        pts = {"W": 3, "D": 1, "L": 0}[m["result"]]
        form_num += pts * w
        gf_num   += m["gf"] * w
        ga_num   += m["ga"] * w
        if m["elo_after"]:
            elo_vals.append(m["elo_after"])

    form_score = round(form_num / (total_w * 3), 3)  # 0 à 1
    xg_proxy   = round(gf_num / total_w, 3)          # buts marqués pondérés (proxy xG)
    xga_proxy  = round(ga_num / total_w, 3)

    # Trend : comparer 1ère moitié vs 2ème moitié des matchs
    mid = len(recent) // 2
    if mid >= 2:
        recent_gf = sum(m["gf"] for m in recent[:mid]) / mid
        old_gf    = sum(m["gf"] for m in recent[mid:]) / max(len(recent)-mid, 1)
        trend = "ascending" if recent_gf > old_gf + 0.3 else \
                "descending" if recent_gf < old_gf - 0.3 else "stable"
    else:
        trend = "stable"

    # ELO trend sur les matchs récents
    elo_trend = None
    if len(elo_vals) >= 3:
        elo_trend = round(elo_vals[0] - elo_vals[-1], 1)

    # Form string (ex: "WWDLW")
    form_string = "".join(m["result"] for m in recent[:5])

    # Clean sheet rate
    cs_rate = round(sum(1 for m in recent if m["ga"] == 0) / len(recent), 3)

    # Score goal en 1ère / 2ème mi-temps proxy (via buts totaux)
    high_scoring = sum(1 for m in recent if m["gf"] >= 2) / len(recent)

    return {
        "team":             team,
        "form_score":       form_score,        # 0-1 (principal signal)
        "form_string":      form_string,
        "goals_scored_avg": xg_proxy,          # proxy xG
        "goals_conceded_avg": xga_proxy,
        "clean_sheet_rate": cs_rate,
        "high_scoring_rate": round(high_scoring, 3),
        "form_trend":       trend,
        "elo_trend_recent": elo_trend,
        "matches_analyzed": len(recent),
        "last_match_date":  recent[0]["date"].strftime("%Y-%m-%d") if recent else None,
        "source":           "eloratings",
    }


if __name__ == "__main__":
    import json
    print("Testing form engine...")
    for team in ["France", "Spain", "Brazil", "Argentina"]:
        result = get_recent_form(team)
        print(f"\n{team}: form={result.get('form_score')} | string={result.get('form_string')} | trend={result.get('form_trend')}")
