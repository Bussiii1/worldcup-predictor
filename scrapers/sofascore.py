import re

TEAM_IDS = {
    "France": ("france", 4481), "Brazil": ("brazil", 4750),
    "Argentina": ("argentina", 4759), "Spain": ("spain", 4698),
    "England": ("england", 4713), "Germany": ("germany", 4711),
    "Portugal": ("portugal", 4749), "Belgium": ("belgium", 4720),
    "Netherlands": ("netherlands", 4705), "Morocco": ("morocco", 4737),
    "USA": ("usa", 4679), "Mexico": ("mexico", 4735),
    "Japan": ("japan", 4756), "Croatia": ("croatia", 4722),
    "Uruguay": ("uruguay", 4764), "Denmark": ("denmark", 4716),
}

BASE_URL = "https://www.sofascore.com/team/football/{slug}/{id}"


def _ef(md: str, pat: str) -> float | None:
    m = re.search(pat, md, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1).replace(",", "."))
        except (ValueError, IndexError):
            return None
    return None


def _parse_sofascore(md: str, team: str) -> dict:
    d: dict = {"team": team, "source": "sofascore"}

    d["team_avg_rating_5games"] = _ef(md, r"Avg(?:erage)? [Rr]ating[^\d]*?([\d.]+)")
    d["goalkeeper_avg_rating"] = _ef(md, r"GK.*?[Rr]ating[^\d]*?([\d.]+)")

    # Best player
    m = re.search(r"(?:Best|Top) [Pp]layer[:\s]*([\w\s'-]+)", md)
    d["best_player_name"] = m.group(1).strip() if m else None
    d["best_player_avg_rating"] = _ef(md, r"(?:Best|Top) [Pp]layer.*?([\d.]{3,4})")

    # Momentum
    ratings = re.findall(r"(\d+\.\d+)", md)
    if len(ratings) >= 5:
        try:
            recent = [float(r) for r in ratings[:5]]
            if recent[-1] > recent[0] + 0.2:
                d["momentum_trend"] = "ascending"
            elif recent[-1] < recent[0] - 0.2:
                d["momentum_trend"] = "descending"
            else:
                d["momentum_trend"] = "stable"
        except Exception:
            d["momentum_trend"] = None
    else:
        d["momentum_trend"] = None

    # Games this month (fatigue proxy)
    d["games_this_month"] = None
    months = re.findall(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}", md, re.IGNORECASE)
    if months:
        from collections import Counter
        most_common = Counter(months).most_common(1)
        if most_common:
            d["games_this_month"] = most_common[0][1]

    d["key_passes_avg"] = _ef(md, r"Key [Pp]asses?[^\d]*?([\d.]+)")
    d["duels_won_pct"] = _ef(md, r"Duels [Ww]on[^\d]*?([\d.]+)%?")

    return d


async def get_sofascore(team: str, crawler) -> dict:
    try:
        info = TEAM_IDS.get(team)
        if not info:
            return {"team": team, "source": "sofascore", "error": "team_not_supported"}
        slug, team_id = info
        url = BASE_URL.format(slug=slug, id=team_id)
        md = await crawler.fetch(url)
        if not md:
            return {"team": team, "source": "sofascore", "error": "no_data"}
        return _parse_sofascore(md, team)
    except Exception as e:
        return {"team": team, "source": "sofascore", "error": str(e)}
