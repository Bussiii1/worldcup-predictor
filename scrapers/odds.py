import re
import asyncio

BASE_URL = "https://www.oddsportal.com/search/results/{t1}-{t2}/"


def _parse_odds(md: str) -> dict:
    d = {
        "avg_odds_home": None,
        "avg_odds_draw": None,
        "avg_odds_away": None,
        "implied_prob_home_pct": None,
        "implied_prob_away_pct": None,
        "source": "oddsportal",
    }

    odds_matches = re.findall(r"([\d.]+)\s*[|\-]\s*([\d.]+)\s*[|\-]\s*([\d.]+)", md)
    if odds_matches:
        try:
            home_vals, draw_vals, away_vals = [], [], []
            for h, dr, a in odds_matches[:10]:
                home_vals.append(float(h))
                draw_vals.append(float(dr))
                away_vals.append(float(a))
            d["avg_odds_home"] = round(sum(home_vals) / len(home_vals), 2)
            d["avg_odds_draw"] = round(sum(draw_vals) / len(draw_vals), 2)
            d["avg_odds_away"] = round(sum(away_vals) / len(away_vals), 2)

            imp_h = 1 / d["avg_odds_home"]
            imp_d = 1 / d["avg_odds_draw"]
            imp_a = 1 / d["avg_odds_away"]
            total = imp_h + imp_d + imp_a
            d["implied_prob_home_pct"] = round(imp_h / total * 100, 1)
            d["implied_prob_away_pct"] = round(imp_a / total * 100, 1)
        except Exception:
            pass

    return d


async def get_odds(team1: str, team2: str, crawler) -> dict:
    try:
        t1 = team1.lower().replace(" ", "-")
        t2 = team2.lower().replace(" ", "-")
        url = BASE_URL.format(t1=t1, t2=t2)
        md = await crawler.fetch(url)
        if not md:
            return {
                "avg_odds_home": None, "avg_odds_draw": None, "avg_odds_away": None,
                "implied_prob_home_pct": None, "implied_prob_away_pct": None,
                "source": "oddsportal", "error": "no_data",
            }
        return _parse_odds(md)
    except Exception as e:
        return {
            "avg_odds_home": None, "avg_odds_draw": None, "avg_odds_away": None,
            "implied_prob_home_pct": None, "implied_prob_away_pct": None,
            "source": "oddsportal", "error": str(e),
        }
