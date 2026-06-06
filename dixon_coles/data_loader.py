"""
Étape 1 — Récupération et filtrage des données.
Source : martj42/international_results (CSV public GitHub)
~3500 matchs pour les 48 équipes qualifiées, depuis 2018.
"""
import io
import requests
import pandas as pd
import numpy as np
from datetime import date

URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"

# 48 équipes qualifiées au Mondial 2026
QUALIFIED = {
    # CONMEBOL (6)
    "Argentina", "Brazil", "Colombia", "Ecuador", "Uruguay", "Paraguay",
    # UEFA (16)
    "Spain", "England", "France", "Germany", "Portugal", "Netherlands",
    "Belgium", "Croatia", "Austria", "Switzerland", "Denmark", "Turkey",
    "Serbia", "Ukraine", "Slovakia", "Scotland",
    # CONCACAF (6)
    "USA", "Mexico", "Canada", "Panama", "Honduras", "Jamaica",
    # CAF (9)
    "Morocco", "Senegal", "Nigeria", "Egypt", "Ivory Coast", "Cameroon",
    "South Africa", "DR Congo", "Algeria",
    # AFC (8)
    "Japan", "South Korea", "Iran", "Australia", "Saudi Arabia",
    "Uzbekistan", "Jordan", "Indonesia",
    # OFC (1)
    "New Zealand",
    # CONCACAF extra
    "Costa Rica", "Trinidad and Tobago", "Cuba", "Haiti",
    # Quelques alternatives de noms
    "Cape Verde", "Curaçao", "Bolivia", "Chile",
}

# Noms alternatifs → noms canoniques
NAME_MAP = {
    "United States":             "USA",
    "Korea Republic":            "South Korea",
    "Republic of Ireland":       "Ireland",
    "Czech Republic":            "Czechia",
    "Bosnia and Herzegovina":    "Bosnia-Herzegovina",
    "Côte d'Ivoire":             "Ivory Coast",
    "DR Congo":                  "DR Congo",
    "Democratic Republic of Congo": "DR Congo",
    "Congo DR":                  "DR Congo",
    "Trinidad & Tobago":         "Trinidad and Tobago",
}

# Poids par compétition
COMPETITION_WEIGHTS = {
    "FIFA World Cup":                  2.5,   # WC réel = signal max
    "FIFA World Cup qualification":    1.8,   # qualifs récentes = très prédictif
    "UEFA Euro":                       1.6,
    "UEFA Euro qualification":         1.3,
    "Copa América":                    1.5,
    "Africa Cup of Nations":           1.4,
    "Gold Cup":                        1.3,
    "AFC Asian Cup":                   1.4,
    "Friendly":                        0.4,   # amicaux = signal faible
    "UEFA Nations League":             1.2,
    "CONCACAF Nations League":         1.1,
}

# Boost supplémentaire pour les matchs 2024-2025 (qualifs WC 2026 récentes)
RECENT_BOOST_CUTOFF = 2024   # matchs depuis 2024 reçoivent un multiplicateur
RECENT_BOOST_FACTOR = 1.35   # +35% de poids pour les matchs très récents


def _competition_weight(tournament: str) -> float:
    for key, w in COMPETITION_WEIGHTS.items():
        if key.lower() in tournament.lower():
            return w
    return 0.8  # compétition inconnue = légèrement en dessous d'une qualification


def _time_weight(match_date: date, reference: date = date(2026, 6, 11)) -> float:
    """Décroissance exponentielle : demi-vie ≈ 2 ans.
    Boost supplémentaire pour les matchs 2024-2025 (qualifs WC 2026)."""
    days = (reference - match_date).days
    base = np.exp(-days / 730)   # 730 jours ≈ 2 ans (demi-vie réduite)
    # Boost récence pour qualifs WC 2026
    if match_date.year >= RECENT_BOOST_CUTOFF:
        base *= RECENT_BOOST_FACTOR
    return base


def load_matches(cutoff_year: int = 2018) -> pd.DataFrame:
    """
    Télécharge et filtre l'historique international.
    Retourne un DataFrame avec colonnes :
      home_team, away_team, home_goals, away_goals, weight
    """
    print(f"Téléchargement des résultats internationaux depuis GitHub...")
    resp = requests.get(URL, timeout=30, verify=False)
    resp.raise_for_status()
    raw = resp.text

    df = pd.read_csv(io.StringIO(raw), parse_dates=["date"])
    print(f"  {len(df)} matchs chargés au total")

    # Normalisation des noms d'équipes
    df["home_team"] = df["home_team"].replace(NAME_MAP)
    df["away_team"] = df["away_team"].replace(NAME_MAP)

    # Filtre : depuis cutoff_year
    df = df[df["date"].dt.year >= cutoff_year].copy()

    # Filtre : au moins une des deux équipes doit être qualifiée
    mask = df["home_team"].isin(QUALIFIED) | df["away_team"].isin(QUALIFIED)
    df = df[mask].copy()

    print(f"  {len(df)} matchs après filtrage (depuis {cutoff_year}, au moins 1 équipe qualifiée)")

    # Poids compétition
    df["comp_weight"] = df["tournament"].apply(_competition_weight)

    # Poids récence
    ref = date(2026, 6, 11)
    df["time_weight"] = df["date"].dt.date.apply(lambda d: _time_weight(d, ref))

    # Poids final = compétition × récence
    df["weight"] = df["comp_weight"] * df["time_weight"]

    # Colonnes finales
    df = df.rename(columns={
        "home_score": "home_goals",
        "away_score": "away_goals",
    })

    # Supprimer les matchs avec scores manquants
    df = df.dropna(subset=["home_goals", "away_goals"])
    df["home_goals"] = df["home_goals"].astype(int)
    df["away_goals"] = df["away_goals"].astype(int)

    print(f"  {len(df)} matchs utilisables avec scores")
    return df[["date", "home_team", "away_team", "home_goals", "away_goals",
               "tournament", "comp_weight", "time_weight", "weight"]].reset_index(drop=True)


if __name__ == "__main__":
    df = load_matches()
    print(df.sort_values("weight", ascending=False).head(10).to_string())
    print(f"\nEquipes présentes : {sorted(df['home_team'].unique())[:10]} ...")
