import re
import json
import asyncio

TEAM_SLUGS = {
    "France": "France", "Brazil": "Brazil", "Argentina": "Argentina",
    "Spain": "Spain", "England": "England", "Germany": "Germany",
    "Portugal": "Portugal", "Belgium": "Belgium", "Netherlands": "Netherlands",
    "Morocco": "Morocco",
}

BASE_URL = "https://understat.com/team/{slug}/2025"


def _decode_js_var(html: str, var_name: str):
    pattern = rf"var {var_name}\s*=\s*JSON\.parse\('(.+?)'\)"
    m = re.search(pattern, html)
    if not m:
        return None
    try:
        raw = m.group(1)
        decoded = raw.encode("utf-8").decode("unicode_escape")
        return json.loads(decoded)
    except Exception:
        return None


def _parse_understat(html: str, team: str) -> dict:
    d: dict = {"team": team, "source": "understat"}

    dates_data = _decode_js_var(html, "datesData")
    stat_data = _decode_js_var(html, "statData")
    players_data = _decode_js_var(html, "playersData")

    if stat_data:
        try:
            stats = stat_data if isinstance(stat_data, dict) else {}
            d["xg_total_season"] = float(stats.get("xG", 0) or 0) or None
            d["xga_total_season"] = float(stats.get("xGA", 0) or 0) or None
            goals = float(stats.get("scored", 0) or 0)
            xg = d.get("xg_total_season") or 0
            d["xg_overperformance"] = round(goals - xg, 2) if xg else None
            conceded = float(stats.get("missed", 0) or 0)
            xga = d.get("xga_total_season") or 0
            d["xga_overperformance"] = round(xga - conceded, 2) if xga else None
        except Exception:
            pass

    d["xg_open_play"] = None
    d["xg_set_piece"] = None
    d["xg_counter"] = None
    d["shots_inside_box_pct"] = None
    d["shot_conversion_rate"] = None
    d["top5_xg_values"] = None
    d["top_creator_xa"] = None
    d["big_chances_created_per_game"] = None
    d["big_chances_missed_per_game"] = None
    d["xg_conceded_corners"] = None

    if dates_data and isinstance(dates_data, list):
        recent = dates_data[-5:]
        xg_vals = []
        for g in recent:
            try:
                xg_vals.append(float(g.get("xG", 0) or 0))
            except Exception:
                pass
        if len(xg_vals) >= 3:
            if xg_vals[-1] > xg_vals[0] + 0.2:
                d["xg_trend_direction"] = "ascending"
            elif xg_vals[-1] < xg_vals[0] - 0.2:
                d["xg_trend_direction"] = "descending"
            else:
                d["xg_trend_direction"] = "stable"
        else:
            d["xg_trend_direction"] = None
    else:
        d["xg_trend_direction"] = None

    if players_data and isinstance(players_data, list):
        try:
            sorted_p = sorted(players_data, key=lambda x: float(x.get("xA", 0) or 0), reverse=True)
            if sorted_p:
                top = sorted_p[0]
                d["top_creator_xa"] = float(top.get("xA", 0) or 0)
            top5 = sorted(players_data, key=lambda x: float(x.get("xG", 0) or 0), reverse=True)[:5]
            d["top5_xg_values"] = [{"name": p.get("player_name"), "xg": float(p.get("xG", 0) or 0)} for p in top5]
        except Exception:
            pass

    return d


async def get_understat_data(team: str, crawler) -> dict:
    try:
        slug = TEAM_SLUGS.get(team)
        if not slug:
            return {"team": team, "source": "understat", "error": "team_not_supported"}
        url = BASE_URL.format(slug=slug)
        html = await crawler.fetch_raw_html(url)
        if not html:
            return {"team": team, "source": "understat", "error": "no_data"}
        return _parse_understat(html, team)
    except Exception as e:
        return {"team": team, "source": "understat", "error": str(e)}
