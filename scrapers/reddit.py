import requests

HEADERS = {"User-Agent": "worldcup-predictor/1.0 (by /u/worldcup_bot)"}
BASE_URL = "https://www.reddit.com/r/soccer/search.json"

POSITIVE_WORDS = {"great", "win", "amazing", "brilliant", "strong", "favorite", "favourite", "confident"}
NEGATIVE_WORDS = {"lose", "weak", "poor", "overrated", "worried", "concern", "injury", "doubt"}


def _assess_sentiment(posts: list[dict]) -> str:
    texts = " ".join(
        p.get("data", {}).get("title", "") + " " + p.get("data", {}).get("selftext", "")
        for p in posts
    ).lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in texts)
    neg = sum(1 for w in NEGATIVE_WORDS if w in texts)
    if pos > neg + 1:
        return "positive"
    elif neg > pos + 1:
        return "negative"
    return "neutral"


async def get_reddit_sentiment(team1: str, team2: str) -> dict:
    try:
        query = f"{team1} {team2} World Cup"
        params = {"q": query, "sort": "hot", "limit": 10, "type": "link"}
        resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        posts = data.get("data", {}).get("children", [])
        total_score = sum(p.get("data", {}).get("score", 0) for p in posts)
        total_comments = sum(p.get("data", {}).get("num_comments", 0) for p in posts)

        return {
            "active_threads_count": len(posts),
            "total_engagement_score": total_score + total_comments,
            "dominant_sentiment": _assess_sentiment(posts),
            "source": "reddit",
        }
    except Exception as e:
        return {
            "active_threads_count": None,
            "total_engagement_score": None,
            "dominant_sentiment": None,
            "source": "reddit",
            "error": str(e),
        }
