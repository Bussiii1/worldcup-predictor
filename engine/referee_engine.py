"""
Referee Engine — item 9.
Tendances arbitrales par confédération et profil d'arbitre.
Impact sur le style de jeu (physicalité autorisée, pénaltys, cartons).
Données statiques basées sur les statistiques WC historiques.
"""
from typing import Optional

# Profil arbitral par confédération de l'arbitre
# Source : statistiques FIFA WC 2018 + 2022 + UEFA/CONMEBOL averages
REFEREE_CONFEDERATIONS = {
    "UEFA":     {"cards_per_game": 3.8, "penalties_per_game": 0.28, "style": "strict"},
    "CONMEBOL": {"cards_per_game": 3.2, "penalties_per_game": 0.32, "style": "permissive"},
    "CAF":      {"cards_per_game": 2.9, "penalties_per_game": 0.22, "style": "permissive"},
    "AFC":      {"cards_per_game": 3.1, "penalties_per_game": 0.25, "style": "moderate"},
    "CONCACAF": {"cards_per_game": 3.4, "penalties_per_game": 0.30, "style": "moderate"},
    "OFC":      {"cards_per_game": 2.8, "penalties_per_game": 0.20, "style": "permissive"},
}

# Équipes qui bénéficient/souffrent selon le style arbitral
# physical : préfèrent un arbitre permissif (jeu physique)
# technical : préfèrent un arbitre strict (protège leur jeu technique)
TEAM_STYLE_PREFERENCE = {
    # Équipes techniques → meilleur avec arbitre strict
    "Spain":       "technical",
    "Germany":     "technical",
    "Netherlands": "technical",
    "Portugal":    "technical",
    "Japan":       "technical",
    "South Korea": "technical",
    "Belgium":     "technical",
    "France":      "balanced",
    "Brazil":      "technical",
    "Argentina":   "balanced",
    "England":     "physical",
    "Uruguay":     "physical",
    "Croatia":     "physical",
    "Turkey":      "physical",
    "Senegal":     "physical",
    "Morocco":     "physical",
    "Nigeria":     "physical",
    "Iran":        "physical",
    "USA":         "physical",
    "Canada":      "physical",
    "Mexico":      "technical",
    "Colombia":    "technical",
    "Ecuador":     "balanced",
    "Switzerland": "balanced",
    "Denmark":     "balanced",
    "Austria":     "balanced",
    "Norway":      "physical",
    "Sweden":      "physical",
    "Serbia":      "physical",
    "Australia":   "physical",
    "Scotland":    "physical",
    "Ghana":       "physical",
    "Cameroon":    "physical",
    "Ivory Coast": "physical",
    "DR Congo":    "physical",
    "Egypt":       "balanced",
    "Algeria":     "balanced",
    "Tunisia":     "balanced",
    "South Africa":"physical",
}

# Correspondance confédération → pays arbitres typiques en WC
# (rotation institutionnelle FIFA pour éviter conflits d'intérêt)
STADIUM_REFEREE_PROFILE = {
    # USA : arbitres souvent UEFA ou CONMEBOL
    "MetLife Stadium":          "UEFA",
    "AT&T Stadium":             "UEFA",
    "SoFi Stadium":             "CONMEBOL",
    "Rose Bowl":                "AFC",
    "Levi's Stadium":           "UEFA",
    "Hard Rock Stadium":        "CONMEBOL",
    "NRG Stadium":              "UEFA",
    "Gillette Stadium":         "CAF",
    "Arrowhead Stadium":        "UEFA",
    "Lumen Field":              "CONMEBOL",
    "Mercedes-Benz Stadium":    "CAF",
    "Lincoln Financial Field":  "AFC",
    "BMO Field":                "UEFA",
    # Mexico
    "Estadio Azteca":           "CONMEBOL",
    "Estadio Akron":            "UEFA",
    "Estadio BBVA":             "AFC",
}

WC_AVG_CARDS       = 3.2   # cartons par match moyen WC
WC_AVG_PENALTIES   = 0.26  # pénaltys par match moyen WC


def get_referee_impact(team_a: str, team_b: str, stadium: str) -> dict:
    """
    Estime l'impact arbitral sur le match.
    Retourne un ajustement de probabilité basé sur le style
    et les préférences des équipes.
    """
    conf = STADIUM_REFEREE_PROFILE.get(stadium, "UEFA")
    ref_profile = REFEREE_CONFEDERATIONS.get(conf, REFEREE_CONFEDERATIONS["UEFA"])

    style_a = TEAM_STYLE_PREFERENCE.get(team_a, "balanced")
    style_b = TEAM_STYLE_PREFERENCE.get(team_b, "balanced")

    # Un arbitre strict avantage les équipes techniques
    # Un arbitre permissif avantage les équipes physiques
    def advantage(team_style: str, ref_style: str) -> float:
        if ref_style == "strict":
            return 0.03 if team_style == "technical" else (
                -0.02 if team_style == "physical" else 0.0)
        elif ref_style == "permissive":
            return 0.02 if team_style == "physical" else (
                -0.01 if team_style == "technical" else 0.0)
        return 0.0

    adv_a = advantage(style_a, ref_profile["style"])
    adv_b = advantage(style_b, ref_profile["style"])

    return {
        "stadium":              stadium,
        "referee_confederation": conf,
        "ref_style":            ref_profile["style"],
        "cards_per_game_est":   ref_profile["cards_per_game"],
        "penalties_per_game_est": ref_profile["penalties_per_game"],
        "style_team_a":         style_a,
        "style_team_b":         style_b,
        "ref_advantage_a":      adv_a,   # + = avantage team_a
        "ref_advantage_b":      adv_b,   # + = avantage team_b
        "high_card_risk":       ref_profile["cards_per_game"] > WC_AVG_CARDS,
        "high_penalty_risk":    ref_profile["penalties_per_game"] > WC_AVG_PENALTIES,
    }
