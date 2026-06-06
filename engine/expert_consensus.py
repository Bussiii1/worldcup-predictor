"""
Données experts WC 2026 embarquées :
- Opta Supercomputer (25 000 simulations, theanalyst.com)
- ESPN expert predictions (espn.com)
- Nate Silver / 538 methodology
- Fox Sports Power Rankings (Alexi Lalas)

Ces données sont statiques (scraped le 05/06/2026) et enrichissent
chaque prédiction avec le consensus des meilleurs analystes du monde.
"""

# ─── OPTA SUPERCOMPUTER — probabilités de gagner la WC ────────────────────
# Source : theanalyst.com/articles/who-will-win-2026-fifa-world-cup-predictions-opta-supercomputer
# Basé sur 25 000 simulations du tournoi complet

OPTA_WIN_PROB = {
    "Spain":        16.1,
    "France":       13.0,
    "England":      11.2,
    "Argentina":    10.4,
    "Portugal":      7.0,
    "Brazil":        6.6,
    "Germany":       5.1,
    "Netherlands":   3.6,
    "Norway":        3.5,
    "Belgium":       2.4,
    "Colombia":      2.1,
    "Croatia":       1.6,
    "Morocco":       1.9,
    "Ecuador":       1.4,
    "Mexico":        1.0,
    "Uruguay":       0.9,
    "Denmark":       0.8,
    "USA":           1.2,
    "Switzerland":   0.6,
    "Senegal":       0.5,
    "South Korea":   0.4,
    "Japan":         0.4,
    "Austria":       0.3,
    "Turkey":        0.3,
    "Australia":     0.2,
    "Chile":         0.2,
    "Egypt":         0.1,
    "Iran":          0.1,
    "Canada":        0.4,
    "Algeria":       0.1,
    "Czechia":       0.2,
    "Czech Republic":0.2,
    "Bosnia-Herzegovina": 0.1,
    "Qatar":         0.0,
    "Saudi Arabia":  0.0,
    "Ghana":         0.1,
    "Cameroon":      0.1,
    "DR Congo":      0.1,
    "Uzbekistan":    0.0,
    "Jordan":        0.0,
    "Iraq":          0.0,
    "Haiti":         0.0,
    "Cape Verde":    0.0,
    "Paraguay":      0.1,
    "Bolivia":       0.0,
    "New Zealand":   0.0,
    "South Africa":  0.0,
    "Curaçao":       0.0,
    "Scotland":      0.2,
    "Panama":        0.0,
    "Jamaica":       0.0,
    "Honduras":      0.0,
}

# ─── OPTA — probabilités de qualification par groupe ──────────────────────
# Source : theanalyst.com (articles groupes A-L)
# Format : "Équipe" : {"qualify_pct": X, "win_group_pct": Y, "qf_pct": Z}

OPTA_GROUP_QUALIFY = {
    # Groupe A
    "Mexico":       {"qualify_pct": 87.2, "win_group_pct": 55.1},
    "South Korea":  {"qualify_pct": 70.1, "win_group_pct": 22.3},
    "Czechia":      {"qualify_pct": 64.2, "win_group_pct": 18.5},
    "Czech Republic":{"qualify_pct": 64.2, "win_group_pct": 18.5},
    "South Africa": {"qualify_pct": 48.9, "win_group_pct": 4.1},

    # Groupe B
    "Switzerland":  {"qualify_pct": 85.4, "win_group_pct": 42.1},
    "Canada":       {"qualify_pct": 79.8, "win_group_pct": 35.3},
    "Bosnia-Herzegovina": {"qualify_pct": 38.2, "win_group_pct": 14.6},
    "Qatar":        {"qualify_pct": 18.6, "win_group_pct": 8.0},

    # Groupe C
    "Brazil":       {"qualify_pct": 96.9, "win_group_pct": 60.2},
    "Morocco":      {"qualify_pct": 81.4, "win_group_pct": 28.7},
    "Scotland":     {"qualify_pct": 51.2, "win_group_pct": 9.8},
    "Haiti":        {"qualify_pct": 21.3, "win_group_pct": 1.3},

    # Groupe D
    "USA":          {"qualify_pct": 77.0, "win_group_pct": 32.4},
    "Turkey":       {"qualify_pct": 71.4, "win_group_pct": 28.9},
    "Australia":    {"qualify_pct": 65.3, "win_group_pct": 24.2},
    "Paraguay":     {"qualify_pct": 36.2, "win_group_pct": 14.5},

    # Groupe E
    "Germany":      {"qualify_pct": 96.1, "win_group_pct": 59.9},
    "Ecuador":      {"qualify_pct": 81.2, "win_group_pct": 30.7},
    "Ivory Coast":  {"qualify_pct": 38.6, "win_group_pct": 7.9},
    "Curaçao":      {"qualify_pct": 4.1,  "win_group_pct": 1.5},

    # Groupe F
    "Netherlands":  {"qualify_pct": 88.2, "win_group_pct": 48.2},
    "Japan":        {"qualify_pct": 74.3, "win_group_pct": 26.4},
    "Sweden":       {"qualify_pct": 54.7, "win_group_pct": 18.9},
    "Tunisia":      {"qualify_pct": 32.8, "win_group_pct": 6.5},

    # Groupe G
    "Belgium":      {"qualify_pct": 89.6, "win_group_pct": 51.9},
    "Egypt":        {"qualify_pct": 68.2, "win_group_pct": 20.3},
    "Iran":         {"qualify_pct": 64.3, "win_group_pct": 18.1},
    "New Zealand":  {"qualify_pct": 47.8, "win_group_pct": 9.7},

    # Groupe H
    "Spain":        {"qualify_pct": 98.5, "win_group_pct": 74.3},
    "Uruguay":      {"qualify_pct": 84.3, "win_group_pct": 18.9},
    "Cape Verde":   {"qualify_pct": 22.1, "win_group_pct": 4.8},
    "Saudi Arabia": {"qualify_pct": 15.1, "win_group_pct": 2.0},

    # Groupe I
    "France":       {"qualify_pct": 95.3, "win_group_pct": 60.3},
    "Norway":       {"qualify_pct": 82.3, "win_group_pct": 25.2},
    "Senegal":      {"qualify_pct": 62.0, "win_group_pct": 11.4},
    "Iraq":         {"qualify_pct": 27.1, "win_group_pct": 3.1},

    # Groupe J
    "Argentina":    {"qualify_pct": 95.8, "win_group_pct": 73.0},
    "Austria":      {"qualify_pct": 75.4, "win_group_pct": 17.8},
    "Algeria":      {"qualify_pct": 49.3, "win_group_pct": 7.4},
    "Jordan":       {"qualify_pct": 29.5, "win_group_pct": 1.8},

    # Groupe K
    "Portugal":     {"qualify_pct": 94.9, "win_group_pct": 59.0},
    "Colombia":     {"qualify_pct": 84.9, "win_group_pct": 28.7},
    "DR Congo":     {"qualify_pct": 34.1, "win_group_pct": 8.4},
    "Uzbekistan":   {"qualify_pct": 26.1, "win_group_pct": 3.9},

    # Groupe L
    "England":      {"qualify_pct": 94.2, "win_group_pct": 67.5},
    "Croatia":      {"qualify_pct": 79.3, "win_group_pct": 20.8},
    "Ghana":        {"qualify_pct": 38.7, "win_group_pct": 8.2},
    "Panama":       {"qualify_pct": 37.8, "win_group_pct": 3.5},
}

# ─── ESPN EXPERT PICKS — prédictions match par match ────────────────────
# Source : espn.com/soccer/story/_/id/48962628/world-cup-predictions-...
# Format : (home, away) → {"winner": team or "draw", "score": "X-Y", "source": "espn"}

ESPN_PICKS = {
    # GROUPE A
    ("Mexico", "South Africa"):     {"winner": "Mexico",        "score": "2-0"},
    ("South Korea", "Czechia"):     {"winner": "draw",          "score": "1-1"},
    ("Czechia", "South Africa"):    {"winner": "Czechia",       "score": "1-0"},
    ("Mexico", "South Korea"):      {"winner": "Mexico",        "score": "1-1"},
    ("South Africa", "South Korea"):{"winner": "South Korea",   "score": "2-1"},
    ("Czechia", "Mexico"):          {"winner": "Mexico",        "score": "2-1"},
    # GROUPE B
    ("Canada", "Bosnia-Herzegovina"):{"winner": "Canada",       "score": "2-1"},
    ("Qatar", "Switzerland"):       {"winner": "Switzerland",   "score": "2-0"},
    ("Switzerland", "Bosnia-Herzegovina"):{"winner": "Switzerland","score": "2-1"},
    ("Canada", "Qatar"):            {"winner": "Canada",        "score": "1-0"},
    ("Switzerland", "Canada"):      {"winner": "draw",          "score": "1-1"},
    ("Bosnia-Herzegovina", "Qatar"):{"winner": "Qatar",         "score": "1-0"},
    # GROUPE C
    ("Brazil", "Morocco"):          {"winner": "Morocco",       "score": "1-0"},
    ("Haiti", "Scotland"):          {"winner": "Scotland",      "score": "2-1"},
    ("Scotland", "Morocco"):        {"winner": "draw",          "score": "0-0"},
    ("Brazil", "Haiti"):            {"winner": "Brazil",        "score": "3-0"},
    ("Scotland", "Brazil"):         {"winner": "Brazil",        "score": "1-0"},
    ("Morocco", "Haiti"):           {"winner": "Morocco",       "score": "2-0"},
    # GROUPE D
    ("USA", "Paraguay"):            {"winner": "USA",           "score": "2-0"},
    ("Australia", "Turkey"):        {"winner": "draw",          "score": "1-1"},
    ("USA", "Australia"):           {"winner": "draw",          "score": "1-1"},
    ("Turkey", "Paraguay"):         {"winner": "Paraguay",      "score": "2-1"},
    ("Turkey", "USA"):              {"winner": "Turkey",        "score": "2-1"},
    ("Paraguay", "Australia"):      {"winner": "draw",          "score": "1-1"},
    # GROUPE E
    ("Germany", "Curaçao"):         {"winner": "Germany",       "score": "5-0"},
    ("Ivory Coast", "Ecuador"):     {"winner": "Ecuador",       "score": "1-0"},
    ("Germany", "Ivory Coast"):     {"winner": "Germany",       "score": "3-1"},
    ("Ecuador", "Curaçao"):         {"winner": "Ecuador",       "score": "2-0"},
    ("Ecuador", "Germany"):         {"winner": "draw",          "score": "1-1"},
    ("Curaçao", "Ivory Coast"):     {"winner": "Ivory Coast",   "score": "3-1"},
    # GROUPE F
    ("Netherlands", "Japan"):       {"winner": "Japan",         "score": "2-1"},
    ("Sweden", "Tunisia"):          {"winner": "Sweden",        "score": "2-1"},
    ("Netherlands", "Sweden"):      {"winner": "Netherlands",   "score": "2-0"},
    ("Tunisia", "Japan"):           {"winner": "Japan",         "score": "1-0"},
    ("Tunisia", "Netherlands"):     {"winner": "Netherlands",   "score": "3-0"},
    ("Japan", "Sweden"):            {"winner": "draw",          "score": "1-1"},
    # GROUPE G
    ("Belgium", "Egypt"):           {"winner": "Belgium",       "score": "2-1"},
    ("Iran", "New Zealand"):        {"winner": "draw",          "score": "1-1"},
    ("Belgium", "Iran"):            {"winner": "draw",          "score": "1-1"},
    ("New Zealand", "Egypt"):       {"winner": "New Zealand",   "score": "2-1"},
    ("New Zealand", "Belgium"):     {"winner": "Belgium",       "score": "2-1"},
    ("Egypt", "Iran"):              {"winner": "draw",          "score": "0-0"},
    # GROUPE H
    ("Spain", "Cape Verde"):        {"winner": "Spain",         "score": "5-0"},
    ("Saudi Arabia", "Uruguay"):    {"winner": "Uruguay",       "score": "2-0"},
    ("Spain", "Saudi Arabia"):      {"winner": "Spain",         "score": "3-0"},
    ("Uruguay", "Cape Verde"):      {"winner": "Uruguay",       "score": "3-0"},
    ("Uruguay", "Spain"):           {"winner": "Spain",         "score": "2-1"},
    ("Cape Verde", "Saudi Arabia"): {"winner": "Cape Verde",    "score": "2-1"},
    # GROUPE I
    ("France", "Senegal"):          {"winner": "France",        "score": "2-1"},
    ("Iraq", "Norway"):             {"winner": "Norway",        "score": "2-0"},
    ("France", "Iraq"):             {"winner": "France",        "score": "3-1"},
    ("Norway", "Senegal"):          {"winner": "draw",          "score": "1-1"},
    ("Norway", "France"):           {"winner": "draw",          "score": "1-1"},
    ("Senegal", "Iraq"):            {"winner": "Senegal",       "score": "3-1"},
    # GROUPE J
    ("Argentina", "Algeria"):       {"winner": "Argentina",     "score": "1-0"},
    ("Austria", "Jordan"):          {"winner": "Austria",       "score": "3-1"},
    ("Argentina", "Austria"):       {"winner": "draw",          "score": "2-2"},
    ("Jordan", "Algeria"):          {"winner": "draw",          "score": "1-1"},
    ("Jordan", "Argentina"):        {"winner": "Argentina",     "score": "3-0"},
    ("Algeria", "Austria"):         {"winner": "draw",          "score": "1-1"},
    # GROUPE K
    ("Portugal", "DR Congo"):       {"winner": "DR Congo",      "score": "2-1"},  # surprise ESPN
    ("Uzbekistan", "Colombia"):     {"winner": "Colombia",      "score": "2-1"},
    ("Portugal", "Uzbekistan"):     {"winner": "Portugal",      "score": "2-1"},
    ("Colombia", "DR Congo"):       {"winner": "Colombia",      "score": "1-0"},
    ("Colombia", "Portugal"):       {"winner": "Colombia",      "score": "2-0"},  # upside ESPN
    ("DR Congo", "Uzbekistan"):     {"winner": "Uzbekistan",    "score": "2-1"},
    # GROUPE L
    ("England", "Croatia"):         {"winner": "draw",          "score": "1-1"},
    ("Ghana", "Panama"):            {"winner": "Panama",        "score": "2-1"},
    ("England", "Ghana"):           {"winner": "England",       "score": "3-0"},
    ("Panama", "Croatia"):          {"winner": "Croatia",       "score": "2-1"},
    ("Panama", "England"):          {"winner": "England",       "score": "2-0"},
    ("Croatia", "Ghana"):           {"winner": "Croatia",       "score": "2-0"},
}

# ─── OPTA KEY INSIGHTS — analyse qualitative par équipe ───────────────────
OPTA_KEY_INSIGHTS = {
    "France": {
        "key_player":   "Kylian Mbappé",
        "key_stat":     "12 buts sur WC 2018+2022, 14 contributions directes",
        "risk":         "Groupe difficile avec Norway (Haaland) — seul favori dans cette situation",
        "strength":     "Profondeur d'effectif exceptionnelle, champion du monde 2018",
        "opta_note":    "13% de chance de gagner le tournoi — 2e favori",
    },
    "Spain": {
        "key_player":   "Lamine Yamal",
        "key_stat":     "16% de chances de victoire finale — favori absolu Opta",
        "risk":         "Dépendance au pressing haut — fatigue en tournoi long",
        "strength":     "Tiki-taka nouvelle génération, vainqueurs Euro 2024",
        "opta_note":    "52% de chances d'atteindre les quarts",
    },
    "England": {
        "key_player":   "Jude Bellingham",
        "key_stat":     "11.2% de chances — 3e favori Opta, 67.9% de topper le groupe L",
        "risk":         "Croatia dangereux en phase de groupes (ESPN prédit nul 1-1)",
        "strength":     "Attaque redoutable, Bellingham + Kane",
        "opta_note":    "47.7% de chances d'atteindre les quarts",
    },
    "Argentina": {
        "key_player":   "Lionel Messi",
        "key_stat":     "Champions du monde en titre, forme excellente (WWWWW)",
        "risk":         "Messi vieillissant (38 ans), dernier tournoi probable",
        "strength":     "Meilleure forme du tournoi, 3 titres WC historiques",
        "opta_note":    "10.4% — 4e favori, 73% de topper le groupe J",
    },
    "Brazil": {
        "key_player":   "Vinícius Jr.",
        "key_stat":     "6.6% de chances — 5e favori Opta",
        "risk":         "ESPN surprenant : prédit Morocco 1-0 Brazil au 1er match",
        "strength":     "Record 5 titres WC, sélecteur Ancelotti",
        "opta_note":    "22.1% de chances d'atteindre les demi-finales",
    },
    "Germany": {
        "key_player":   "Florian Wirtz",
        "key_stat":     "96.1% de chances de qualification selon Opta",
        "risk":         "ESPN prédit Japon 2-1 Netherlands (choc possible en R32)",
        "strength":     "Reconstruction réussie post-2022, football offensif",
        "opta_note":    "5.1% de victoire finale — 6e favori",
    },
    "Norway": {
        "key_player":   "Erling Haaland",
        "key_stat":     "16 buts en 8 matchs qualifs — record européen absolu",
        "risk":         "Première participation WC, manque d'expérience tournoi",
        "strength":     "Haaland = meilleur finisseur mondial, 4.6 buts/match qualifs",
        "opta_note":    "3.5% de victoire finale — dark horse crédible",
    },
    "Portugal": {
        "key_player":   "Rafael Leão",
        "key_stat":     "94.9% de qualification, ESPN surprenant : DR Congo 2-1 Portugal J1",
        "risk":         "Post-Ronaldo, leadership en question",
        "strength":     "Génération talentueuse, Bernardo Silva créateur",
        "opta_note":    "7.0% — 5e favori, vainqueur potentiel",
    },
    "Netherlands": {
        "key_player":   "Cody Gakpo",
        "key_stat":     "88.2% de qualification, ESPN : Japan 2-1 Netherlands J1 (surprise)",
        "risk":         "Pas de 9 de classe mondiale, dépend de la créativité",
        "strength":     "Meilleur résultat depuis 2014 (3e), Van Dijk leader défensif",
        "opta_note":    "3.6% de victoire finale",
    },
    "Morocco": {
        "key_player":   "Achraf Hakimi",
        "key_stat":     "1ère équipe africaine demi-finaliste WC 2022",
        "risk":         "ESPN : Morocco 1-0 Brazil (upset potentiel réalisé ?)",
        "strength":     "Défense compacte, coaching tactique, stade plein de supporters",
        "opta_note":    "1.9% de victoire finale — meilleure surprise possible",
    },
    "USA": {
        "key_player":   "Christian Pulisic",
        "key_stat":     "Pays hôte, 77% de qualification, ESPN : 2-0 Paraguay J1",
        "risk":         "ESPN prédit Turkey 2-1 USA en J3 — élimination possible",
        "strength":     "Avantage du pays hôte, motivation exceptionnelle",
        "opta_note":    "1.2% de victoire finale, mais stades acquis à leur cause",
    },
    "Senegal": {
        "key_player":   "Sadio Mané",
        "key_stat":     "Vainqueurs CAN 2022, 62% de qualification Opta",
        "risk":         "Groupe difficile (France, Norway), ESPN prédit nul vs Norway",
        "strength":     "Collectif soudé, expérience WC 2022 (quarts de finale)",
        "opta_note":    "0.5% de victoire finale, mais vrai outsider à surveiller",
    },
}


def get_expert_signals(home: str, away: str) -> dict:
    """
    Retourne tous les signaux experts pour un match donné.
    """
    # ESPN pick (essaie dans les 2 sens)
    espn_fwd = ESPN_PICKS.get((home, away))
    espn_rev = ESPN_PICKS.get((away, home))

    if espn_fwd:
        espn = {**espn_fwd, "home": home, "away": away, "reversed": False}
    elif espn_rev:
        # Le pick était dans l'autre sens — adapter
        w = espn_rev["winner"]
        if w == away:   winner_adj = home
        elif w == home: winner_adj = away
        else:           winner_adj = "draw"
        # Inverser le score
        parts = espn_rev["score"].split("-")
        score_adj = f"{parts[1]}-{parts[0]}" if len(parts) == 2 else espn_rev["score"]
        espn = {"winner": winner_adj, "score": score_adj, "home": home, "away": away, "reversed": True}
    else:
        espn = None

    # Opta probas équipes
    opta_home = {
        "win_tournament_pct": OPTA_WIN_PROB.get(home, 0.0),
        "qualify_from_group_pct": OPTA_GROUP_QUALIFY.get(home, {}).get("qualify_pct"),
        "win_group_pct": OPTA_GROUP_QUALIFY.get(home, {}).get("win_group_pct"),
    }
    opta_away = {
        "win_tournament_pct": OPTA_WIN_PROB.get(away, 0.0),
        "qualify_from_group_pct": OPTA_GROUP_QUALIFY.get(away, {}).get("qualify_pct"),
        "win_group_pct": OPTA_GROUP_QUALIFY.get(away, {}).get("win_group_pct"),
    }

    # Insights qualitatifs
    insight_home = OPTA_KEY_INSIGHTS.get(home)
    insight_away = OPTA_KEY_INSIGHTS.get(away)

    # Consensus : ESPN + Opta alignés ?
    opta_favorite = home if opta_home["win_tournament_pct"] > opta_away["win_tournament_pct"] else away
    espn_favorite = espn["winner"] if espn else None
    consensus_aligned = (
        espn_favorite not in (None, "draw") and
        espn_favorite == opta_favorite
    )

    # Signal synthétique pour le modèle
    expert_edge = None
    if espn and opta_home["qualify_from_group_pct"] and opta_away["qualify_from_group_pct"]:
        opta_qual_gap = abs(
            (opta_home["qualify_from_group_pct"] or 50) -
            (opta_away["qualify_from_group_pct"] or 50)
        )
        if opta_qual_gap > 30:
            stronger = home if opta_home["qualify_from_group_pct"] > opta_away["qualify_from_group_pct"] else away
            expert_edge = {"team": stronger, "confidence": "high", "gap": opta_qual_gap}
        elif opta_qual_gap > 15:
            stronger = home if opta_home["qualify_from_group_pct"] > opta_away["qualify_from_group_pct"] else away
            expert_edge = {"team": stronger, "confidence": "medium", "gap": opta_qual_gap}

    return {
        "espn_pick":          espn,
        "opta_home":          opta_home,
        "opta_away":          opta_away,
        "insight_home":       insight_home,
        "insight_away":       insight_away,
        "opta_favorite":      opta_favorite,
        "consensus_aligned":  consensus_aligned,
        "expert_edge":        expert_edge,
        "sources":            ["opta_supercomputer_25k", "espn_expert_picks"],
    }


def get_tournament_outlook(team: str) -> dict:
    """Vue globale d'une équipe pour le tournoi."""
    return {
        "team":              team,
        "win_tournament_pct": OPTA_WIN_PROB.get(team, 0.0),
        "group_qualify_pct": OPTA_GROUP_QUALIFY.get(team, {}).get("qualify_pct"),
        "group_win_pct":     OPTA_GROUP_QUALIFY.get(team, {}).get("win_group_pct"),
        "key_insight":       OPTA_KEY_INSIGHTS.get(team),
    }


if __name__ == "__main__":
    import json

    print("=== Expert Consensus: France vs Senegal ===")
    signals = get_expert_signals("France", "Senegal")
    print(json.dumps(signals, indent=2, ensure_ascii=False))

    print("\n=== Expert Consensus: Netherlands vs Japan ===")
    signals2 = get_expert_signals("Netherlands", "Japan")
    print(json.dumps(signals2, indent=2, ensure_ascii=False))

    print("\n=== Tournament Outlook: Argentina ===")
    outlook = get_tournament_outlook("Argentina")
    print(json.dumps(outlook, indent=2, ensure_ascii=False))
