"""
World Football ELO Ratings via eloratings.net (national teams).
TSV format per row: year, month, day, home_code, away_code, home_goals, away_goals,
tournament, neutral, elo_change, home_elo_after, away_elo_after, ...
"""
import requests
from datetime import datetime, timedelta

BASE_URL = "https://www.eloratings.net/{team}.tsv"

# URL slug → (tsv_2letter_code) mapping
TEAM_SLUGS = {
    "France": ("France", "FR"), "Brazil": ("Brazil", "BR"),
    "Argentina": ("Argentina", "AR"), "Spain": ("Spain", "ES"),
    "England": ("England", "EN"), "Germany": ("Germany", "DE"),
    "Portugal": ("Portugal", "PT"), "Belgium": ("Belgium", "BE"),
    "Netherlands": ("Netherlands", "NL"), "Morocco": ("Morocco", "MA"),
    "USA": ("United_States", "US"), "Mexico": ("Mexico", "MX"),
    "Japan": ("Japan", "JP"), "Croatia": ("Croatia", "HR"),
    "Uruguay": ("Uruguay", "UY"), "Denmark": ("Denmark", "DK"),
    "Switzerland": ("Switzerland", "CH"), "Poland": ("Poland", "PL"),
    "Serbia": ("Serbia", "SE"), "South-Korea": ("South_Korea", "KR"),
    "South Korea": ("South_Korea", "KR"),
    "Senegal": ("Senegal", "SN"), "Ecuador": ("Ecuador", "EC"),
    "Canada": ("Canada", "CA"), "Australia": ("Australia", "AU"),
    "Qatar": ("Qatar", "QA"), "Saudi-Arabia": ("Saudi_Arabia", "SA"),
    "Iran": ("Iran", "IR"), "Wales": ("Wales", "WA"),
    "Tunisia": ("Tunisia", "TU"), "Ghana": ("Ghana", "GH"),
    "Cameroon": ("Cameroon", "CM"), "Costa-Rica": ("Costa_Rica", "CS"),
}


def _fetch_tsv(team: str) -> list[dict]:
    slug, _ = TEAM_SLUGS.get(team, (team.replace(" ", "_"), "??"))
    url = BASE_URL.format(team=slug)
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    rows = []
    for line in resp.text.strip().split("\n"):
        parts = line.split("\t")
        if len(parts) < 11:
            continue
        try:
            rows.append({
                "year": int(parts[0]),
                "month": int(parts[1]),
                "day": int(parts[2]),
                "home": parts[3].strip(),
                "away": parts[4].strip(),
                "home_elo_after": float(parts[10]),
                "away_elo_after": float(parts[11]) if len(parts) > 11 else None,
            })
        except (ValueError, IndexError):
            continue
    return rows


def _get_elo_for_team(rows: list[dict], team_code: str) -> tuple[float | None, float | None]:
    """Return (current_elo, elo_30d_ago) for the team from sorted match history."""
    today = datetime.today()
    thirty_ago = today - timedelta(days=30)

    current_elo = None
    past_elo = None

    # Walk backwards — find most recent match, then one ~30 days ago
    for row in reversed(rows):
        try:
            match_date = datetime(row["year"], row["month"], row["day"])
        except (ValueError, KeyError):
            continue

        is_home = row["home"] == team_code
        is_away = row["away"] == team_code

        if not is_home and not is_away:
            continue

        elo = row["home_elo_after"] if is_home else row["away_elo_after"]
        if elo is None:
            continue

        if current_elo is None and match_date <= today:
            current_elo = elo

        if past_elo is None and match_date <= thirty_ago:
            past_elo = elo

        if current_elo is not None and past_elo is not None:
            break

    return current_elo, past_elo


def get_team_elo(team: str) -> dict:
    try:
        rows = _fetch_tsv(team)
        _, tsv_code = TEAM_SLUGS.get(team, ("??", team[:2].upper()))

        current, past = _get_elo_for_team(rows, tsv_code)

        trend = None
        if current is not None and past is not None:
            trend = round(current - past, 1)

        return {
            "team": team,
            "current_elo": current,
            "elo_30d_ago": past,
            "elo_trend_30d": trend,
            "elo_world_rank": None,
            "source": "eloratings",
        }
    except Exception as e:
        return {
            "team": team, "current_elo": None, "elo_30d_ago": None,
            "elo_trend_30d": None, "elo_world_rank": None,
            "source": "eloratings", "error": str(e),
        }


def _win_probability(elo_a: float, elo_b: float) -> float:
    return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))


def compare_elo(team1: str, team2: str) -> dict:
    d1 = get_team_elo(team1)
    d2 = get_team_elo(team2)

    elo_a = d1.get("current_elo")
    elo_b = d2.get("current_elo")

    if elo_a and elo_b:
        win_prob = round(_win_probability(elo_a, elo_b) * 100, 1)
        d1["elo_win_probability_pct"] = win_prob
        d2["elo_win_probability_pct"] = round(100 - win_prob, 1)
    else:
        d1["elo_win_probability_pct"] = None
        d2["elo_win_probability_pct"] = None

    return {team1: d1, team2: d2}


# Quick test when run directly
if __name__ == "__main__":
    print("Testing World Football ELO Ratings (eloratings.net)...")
    result = compare_elo("France", "Brazil")
    for team, data in result.items():
        print(f"\n{team}:")
        for k, v in data.items():
            print(f"  {k}: {v}")
