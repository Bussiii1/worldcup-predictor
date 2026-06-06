"""
Télécharge les 27 datasets de la Fjelstul World Cup Database
(github.com/jfjelstul/worldcup) — 1930 à 2022, 1.58M data points.
"""
import os
import requests
import pandas as pd
from pathlib import Path

BASE_URL = "https://raw.githubusercontent.com/jfjelstul/worldcup/master/data-csv/"
OUT_DIR  = Path(__file__).parent / "wc_history"

DATASETS = {
    "matches":           "matches.csv",
    "team_appearances":  "team_appearances.csv",
    "goals":             "goals.csv",
    "bookings":          "bookings.csv",
    "group_standings":   "group_standings.csv",
    "squads":            "squads.csv",
    "players":           "players.csv",
    "tournaments":       "tournaments.csv",
    "qualified_teams":   "qualified_teams.csv",
    "tournament_stages": "tournament_stages.csv",
    "substitutions":     "substitutions.csv",
}

# Normalisation des noms d'équipes vers nos slugs
TEAM_MAP = {
    "West Germany":         "Germany",
    "German DR":            "Germany",
    "Soviet Union":         "Russia",
    "Yugoslavia":           "Serbia",
    "Czechoslovakia":       "Czech Republic",
    "Republic of Ireland":  "Republic of Ireland",
    "Korea Republic":       "South Korea",
    "Korea DPR":            "North Korea",
    "USA":                  "USA",
    "United States":        "USA",
    "IR Iran":              "Iran",
    "Côte d'Ivoire":        "Ivory Coast",
    "Saudi Arabia":         "Saudi Arabia",
    "Cape Verde Islands":   "Cape Verde",
    "Bosnia Herzegovina":   "Bosnia-Herzegovina",
}


def normalize_team(name: str) -> str:
    return TEAM_MAP.get(name, name)


def download_all():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    downloaded = []

    for name, filename in DATASETS.items():
        out_path = OUT_DIR / f"{name}.parquet"
        if out_path.exists():
            print(f"  ✓ {name} (cached)")
            downloaded.append(name)
            continue

        url = BASE_URL + filename
        print(f"  ↓ Downloading {name}...", end=" ")
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            df = pd.read_csv(pd.io.common.StringIO(r.text))

            # Normaliser les noms d'équipes si les colonnes existent
            for col in ["home_team_name", "away_team_name", "team_name",
                        "country_name", "birth_country"]:
                if col in df.columns:
                    df[col] = df[col].map(lambda x: normalize_team(str(x)) if pd.notna(x) else x)

            df.to_parquet(out_path, index=False)
            print(f"✓ ({len(df)} rows)")
            downloaded.append(name)
        except Exception as e:
            print(f"✗ {e}")

    return downloaded


def load(name: str) -> pd.DataFrame:
    path = OUT_DIR / f"{name}.parquet"
    if not path.exists():
        download_all()
    return pd.read_parquet(path)


if __name__ == "__main__":
    print("Downloading Fjelstul World Cup Database...")
    result = download_all()
    print(f"\nDone: {len(result)}/{len(DATASETS)} datasets")

    # Quick check
    matches = load("matches")
    print(f"\nMatches loaded: {len(matches)} rows")
    print(f"Columns: {list(matches.columns)[:10]}")
    print(f"WC editions: {sorted(matches['tournament_id'].unique()) if 'tournament_id' in matches.columns else 'N/A'}")
