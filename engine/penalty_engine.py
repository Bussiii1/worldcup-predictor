"""
Penalty Engine — item 7.
Historique des tirs au but en Coupe du Monde et compétitions majeures.
Données statiques compilées depuis Wikipedia/RSSSF.
"""

# Format : team → {attempts, converted, success_rate, shootouts_won, shootouts_lost}
# Sources : Wikipedia "List of FIFA World Cup penalty shoot-outs" + UEFA/Copa Am.
WC_PENALTY_HISTORY = {
    "Germany":      {"attempts": 35, "converted": 29, "rate": 0.829, "won": 4, "lost": 2},
    "Argentina":    {"attempts": 30, "converted": 24, "rate": 0.800, "won": 5, "lost": 3},
    "France":       {"attempts": 18, "converted": 13, "rate": 0.722, "won": 2, "lost": 3},
    "Brazil":       {"attempts": 27, "converted": 19, "rate": 0.704, "won": 2, "lost": 3},
    "Spain":        {"attempts": 18, "converted": 14, "rate": 0.778, "won": 2, "lost": 2},
    "Netherlands":  {"attempts": 15, "converted": 10, "rate": 0.667, "won": 1, "lost": 2},
    "Portugal":     {"attempts": 20, "converted": 15, "rate": 0.750, "won": 3, "lost": 1},
    "England":      {"attempts": 30, "converted": 20, "rate": 0.667, "won": 2, "lost": 6},
    "Italy":        {"attempts": 28, "converted": 22, "rate": 0.786, "won": 3, "lost": 3},
    "Croatia":      {"attempts": 18, "converted": 15, "rate": 0.833, "won": 4, "lost": 1},
    "Switzerland":  {"attempts": 10, "converted":  8, "rate": 0.800, "won": 2, "lost": 1},
    "Mexico":       {"attempts": 15, "converted": 10, "rate": 0.667, "won": 1, "lost": 4},
    "Uruguay":      {"attempts": 20, "converted": 15, "rate": 0.750, "won": 3, "lost": 2},
    "Colombia":     {"attempts": 12, "converted":  9, "rate": 0.750, "won": 2, "lost": 1},
    "Japan":        {"attempts": 10, "converted":  7, "rate": 0.700, "won": 2, "lost": 2},
    "South Korea":  {"attempts": 10, "converted":  7, "rate": 0.700, "won": 2, "lost": 1},
    "Morocco":      {"attempts":  5, "converted":  4, "rate": 0.800, "won": 1, "lost": 0},
    "USA":          {"attempts":  8, "converted":  5, "rate": 0.625, "won": 1, "lost": 1},
    "Australia":    {"attempts":  5, "converted":  3, "rate": 0.600, "won": 1, "lost": 1},
    "Belgium":      {"attempts":  8, "converted":  5, "rate": 0.625, "won": 0, "lost": 2},
    "Senegal":      {"attempts":  5, "converted":  4, "rate": 0.800, "won": 1, "lost": 1},
    "Ecuador":      {"attempts":  3, "converted":  2, "rate": 0.667, "won": 0, "lost": 1},
    "Ghana":        {"attempts":  6, "converted":  3, "rate": 0.500, "won": 0, "lost": 2},
    "Cameroon":     {"attempts":  3, "converted":  2, "rate": 0.667, "won": 1, "lost": 0},
    "Turkey":       {"attempts":  3, "converted":  2, "rate": 0.667, "won": 0, "lost": 1},
    "Serbia":       {"attempts":  3, "converted":  2, "rate": 0.667, "won": 0, "lost": 1},
    "Denmark":      {"attempts":  8, "converted":  6, "rate": 0.750, "won": 1, "lost": 1},
    "Iran":         {"attempts":  3, "converted":  2, "rate": 0.667, "won": 0, "lost": 1},
    "Canada":       {"attempts":  0, "converted":  0, "rate": 0.720, "won": 0, "lost": 0},
    "Norway":       {"attempts":  0, "converted":  0, "rate": 0.720, "won": 0, "lost": 0},
    "Austria":      {"attempts":  0, "converted":  0, "rate": 0.720, "won": 0, "lost": 0},
}

# Taux moyen WC si pas de données
AVERAGE_PENALTY_RATE = 0.720
AVERAGE_SHOOTOUT_WIN_RATE = 0.500


def get_penalty_stats(team: str) -> dict:
    """
    Retourne les statistiques de penalty/tirs au but pour une équipe.
    """
    data = WC_PENALTY_HISTORY.get(team)

    if data:
        total_shootouts = data["won"] + data["lost"]
        shootout_win_rate = data["won"] / total_shootouts if total_shootouts > 0 else AVERAGE_SHOOTOUT_WIN_RATE

        return {
            "team":                  team,
            "penalty_rate":          data["rate"],
            "shootout_win_rate":     round(shootout_win_rate, 3),
            "shootouts_played":      total_shootouts,
            "penalty_data_quality":  "historical" if data["attempts"] > 0 else "estimated",
            "penalty_strength":      "strong" if data["rate"] > 0.76 else
                                     "weak"   if data["rate"] < 0.68 else "average",
        }
    else:
        return {
            "team":                  team,
            "penalty_rate":          AVERAGE_PENALTY_RATE,
            "shootout_win_rate":     AVERAGE_SHOOTOUT_WIN_RATE,
            "shootouts_played":      0,
            "penalty_data_quality":  "estimated",
            "penalty_strength":      "average",
        }


def get_ko_advantage(team_a: str, team_b: str) -> dict:
    """
    Compare les stats de TAB des deux équipes pour un éventuel match KO.
    Retourne un avantage relatif (-1 à +1) pour team_a.
    """
    a = get_penalty_stats(team_a)
    b = get_penalty_stats(team_b)

    rate_diff = a["penalty_rate"] - b["penalty_rate"]
    shootout_diff = a["shootout_win_rate"] - b["shootout_win_rate"]

    advantage = round(0.6 * rate_diff + 0.4 * shootout_diff, 4)

    return {
        "team_a":           team_a,
        "team_b":           team_b,
        "penalty_advantage": advantage,
        "advantage_team":   team_a if advantage > 0.02 else
                            (team_b if advantage < -0.02 else "equal"),
        "rate_a":           a["penalty_rate"],
        "rate_b":           b["penalty_rate"],
    }
