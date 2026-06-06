"""
News Engine — items 8 (sentiment coach) & 12 (facteurs psychologiques).
Source : Google News RSS + feedparser.
Analyse NLP étendue : blessures, tensions internes, confiance du staff.
"""
import feedparser
import re
from typing import Optional

RSS_BASE = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

INJURY_KEYWORDS = {
    "injured", "injury", "muscle", "hamstring", "knee", "ankle", "doubt",
    "doubtful", "out", "miss", "missing", "ruled out", "fitness concern",
    "late fitness test", "not training", "absent", "withdrew",
}
SUSPENSION_KEYWORDS = {
    "suspended", "suspension", "ban", "banned", "yellow card accumulation",
    "miss through suspension",
}
POSITIVE_KEYWORDS = {
    "confident", "ready", "strong", "excellent form", "training well",
    "fully fit", "sharp", "motivated", "united", "great", "perfect",
    "in form", "prepared", "belief", "determined", "cohesive",
}
NEGATIVE_KEYWORDS = {
    "crisis", "concern", "struggle", "poor form", "disorganized", "divided",
    "tension", "conflict", "row", "unhappy", "morale", "problems", "weakened",
    "depleted", "collapse", "worry", "worried",
}
INTERNAL_CONFLICT_KEYWORDS = {
    "dispute", "argument", "rift", "revolt", "unhappy", "dropped",
    "left out", "squad dispute", "bonus row", "contract dispute",
    "manager sacked", "axed", "benched", "fallout", "not selected",
    "training ground", "dressing room", "falling out",
}
COACH_CONFIDENCE_POSITIVE = {
    "we are ready", "full confidence", "believe we can", "our time",
    "we will win", "excited", "best squad", "fully prepared",
    "no injuries", "everyone available", "great spirit",
}
COACH_CONCERN_KEYWORDS = {
    "not at 100", "fitness doubt", "we'll see", "not sure", "wait and see",
    "a concern", "some issues", "not ideal", "far from ideal", "difficult",
    "struggle", "not training",
}
KNOWN_COACHES = {
    "France": ["Deschamps", "Didier"], "Brazil": ["Ancelotti", "Carlo"],
    "Argentina": ["Scaloni"], "England": ["Southgate", "Tuchel"],
    "Spain": ["de la Fuente", "Luis"], "Germany": ["Nagelsmann", "Julian"],
    "Portugal": ["Martinez", "Roberto"], "Netherlands": ["Koeman"],
    "Morocco": ["Regragui"], "Japan": ["Moriyasu"],
    "USA": ["Pochettino"], "Senegal": ["Aliou", "Cisse"],
}


def _kw_score(text, keywords):
    t = text.lower()
    return sum(1 for kw in keywords if kw in t)


def _tone(pos, neg):
    if pos > neg + 1:   return "positive"
    if neg > pos + 1:   return "negative"
    return "neutral"


def _extract_player_names(texts):
    combined = " ".join(texts)
    pattern = (r"([A-Z][a-zà-ÿ]+"
               r"(?:\s+[A-Z][a-zà-ÿ]+)+)"
               r"(?:\s+(?:is|was|has been|could|will|might|may))?"
               r"\s+(?:injured|out|miss|missing|suspended|banned|doubtful|unavailable)")
    names = re.findall(pattern, combined)
    return list(dict.fromkeys(names))[:8]


def _fetch_rss(query, max_items=6):
    try:
        url = RSS_BASE.format(query=query.replace(" ", "+"))
        feed = feedparser.parse(url)
        return [{"title": e.get("title",""), "summary": e.get("summary","")}
                for e in feed.entries[:max_items]]
    except Exception:
        return []


async def get_news(team1, team2):
    try:
        queries = [
            f'"{team1}" "{team2}" World Cup 2026',
            f'"{team1}" squad news injury 2026',
            f'"{team2}" squad news injury 2026',
            f'"{team1}" coach press conference World Cup',
            f'"{team2}" coach press conference World Cup',
        ]
        all_items = []
        for q in queries:
            all_items.extend(_fetch_rss(q, 5))

        all_texts = [f"{it['title']} {it['summary']}" for it in all_items]
        t1_texts  = [t for t in all_texts if team1.lower() in t.lower()]
        t2_texts  = [t for t in all_texts if team2.lower() in t.lower()]

        coaches1 = KNOWN_COACHES.get(team1, [])
        coaches2 = KNOWN_COACHES.get(team2, [])
        coach_t1 = [t for t in t1_texts if any(c.lower() in t.lower() for c in coaches1)]
        coach_t2 = [t for t in t2_texts if any(c.lower() in t.lower() for c in coaches2)]

        def coach_sent(texts):
            if not texts: return "neutral"
            return _tone(_kw_score(" ".join(texts), COACH_CONFIDENCE_POSITIVE),
                         _kw_score(" ".join(texts), COACH_CONCERN_KEYWORDS))

        conflict1 = _kw_score(" ".join(t1_texts), INTERNAL_CONFLICT_KEYWORDS)
        conflict2 = _kw_score(" ".join(t2_texts), INTERNAL_CONFLICT_KEYWORDS)

        pos1 = _kw_score(" ".join(t1_texts), POSITIVE_KEYWORDS)
        neg1 = _kw_score(" ".join(t1_texts), NEGATIVE_KEYWORDS)
        pos2 = _kw_score(" ".join(t2_texts), POSITIVE_KEYWORDS)
        neg2 = _kw_score(" ".join(t2_texts), NEGATIVE_KEYWORDS)

        def psych(pos, neg, conflict, coach):
            s = 0.5 + (pos - neg) * 0.03 - conflict * 0.04
            if coach == "positive": s += 0.05
            elif coach == "negative": s -= 0.05
            return round(max(0.1, min(s, 0.95)), 3)

        cs1, cs2 = coach_sent(coach_t1), coach_sent(coach_t2)

        return {
            f"injuries_{team1}":            _extract_player_names(t1_texts),
            f"injuries_{team2}":            _extract_player_names(t2_texts),
            f"suspension_flag_{team1}":     _kw_score(" ".join(t1_texts), SUSPENSION_KEYWORDS) > 0,
            f"suspension_flag_{team2}":     _kw_score(" ".join(t2_texts), SUSPENSION_KEYWORDS) > 0,
            f"coach_sentiment_{team1}":     cs1,
            f"coach_sentiment_{team2}":     cs2,
            f"internal_conflict_{team1}":   conflict1 >= 2,
            f"internal_conflict_{team2}":   conflict2 >= 2,
            f"conflict_score_{team1}":      conflict1,
            f"conflict_score_{team2}":      conflict2,
            f"tone_{team1}":                _tone(pos1, neg1),
            f"tone_{team2}":                _tone(pos2, neg2),
            f"psych_score_{team1}":         psych(pos1, neg1, conflict1, cs1),
            f"psych_score_{team2}":         psych(pos2, neg2, conflict2, cs2),
            "top5_headlines":               [it["title"] for it in all_items[:5]],
            "n_articles":                   len(all_items),
            "source":                       "google_news",
        }
    except Exception as e:
        return {
            "source": "google_news", "error": str(e),
            f"psych_score_{team1}": 0.5, f"psych_score_{team2}": 0.5,
            f"internal_conflict_{team1}": False, f"internal_conflict_{team2}": False,
            f"coach_sentiment_{team1}": "neutral", f"coach_sentiment_{team2}": "neutral",
        }
