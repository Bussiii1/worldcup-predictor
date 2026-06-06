import re

TEAM_SLUGS = {
    "France": "france-national-team", "Brazil": "brazil-national-team",
    "Argentina": "argentina-national-team", "Spain": "spain-national-team",
    "England": "england-national-team", "Germany": "germany-national-team",
    "Portugal": "portugal-national-team", "Belgium": "belgium-national-team",
}

BASE_URL = "https://footystats.org/international/{slug}"


def _ef(md: str, pat: str) -> float | None:
    m = re.search(pat, md, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1).replace(",", "."))
        except (ValueError, IndexError):
            return None
    return None


def _parse_footystats(md: str, team: str) -> dict:
    d: dict = {"team": team, "source": "footystats"}

    d["over25_rate_pct"] = _ef(md, r"Over 2\.5[^\d]*?([\d.]+)%")
    d["over15_rate_pct"] = _ef(md, r"Over 1\.5[^\d]*?([\d.]+)%")
    d["btts_rate_pct"] = _ef(md, r"BTTS[^\d]*?([\d.]+)%")
    d["btts_home_rate_pct"] = _ef(md, r"BTTS.*?Home[^\d]*?([\d.]+)%")
    d["btts_away_rate_pct"] = _ef(md, r"BTTS.*?Away[^\d]*?([\d.]+)%")
    d["corners_over95_rate_pct"] = _ef(md, r"Corners Over 9\.5[^\d]*?([\d.]+)%")
    d["corners_over105_rate_pct"] = _ef(md, r"Corners Over 10\.5[^\d]*?([\d.]+)%")
    d["corners_avg_for"] = _ef(md, r"Corners For[^\d]*?([\d.]+)")
    d["corners_avg_against"] = _ef(md, r"Corners Against[^\d]*?([\d.]+)")
    d["cards_total_avg"] = _ef(md, r"Cards[^\d]*?([\d.]+)")
    d["yellow_cards_avg"] = _ef(md, r"Yellow Cards?[^\d]*?([\d.]+)")
    d["fouls_avg"] = _ef(md, r"Fouls?[^\d]*?([\d.]+)")

    return d


async def get_footystats(team: str, crawler) -> dict:
    try:
        slug = TEAM_SLUGS.get(team)
        if not slug:
            return {"team": team, "source": "footystats", "error": "team_not_supported"}
        url = BASE_URL.format(slug=slug)
        md = await crawler.fetch(url)
        if not md:
            return {"team": team, "source": "footystats", "error": "no_data"}
        return _parse_footystats(md, team)
    except Exception as e:
        return {"team": team, "source": "footystats", "error": str(e)}
