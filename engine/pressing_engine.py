"""
Pressing Engine — item 4.
Proxy PPDA (Passes Per Defensive Action) calculé depuis les données
de forme disponibles + paramètres Dixon-Coles.
PPDA bas = pressing intense = style offensif agressif.
Source : eloratings TSV + DC model.
"""
import json
import math
from pathlib import Path
from typing import Optional

DC_PATH = Path(__file__).parent.parent / "data" / "dc_model.json"

# Style de pressing connu pour les équipes ayant un style très identifié
# Échelle 0-1 : 0 = bloc bas, 1 = pressing intense
KNOWN_PRESSING = {
    # Équipes connues pour leur pressing haut
    "Germany":     0.78,
    "Spain":       0.82,
    "Portugal":    0.72,
    "Belgium":     0.70,
    "Netherlands": 0.74,
    "France":      0.68,
    "Japan":       0.80,
    "Morocco":     0.65,
    "England":     0.70,
    "Brazil":      0.72,
    "Argentina":   0.65,
    "USA":         0.72,
    "Canada":      0.68,
    "South Korea": 0.75,
    "Ecuador":     0.62,
    "Colombia":    0.64,
    "Mexico":      0.60,
    "Senegal":     0.60,
    "Australia":   0.66,
    "Denmark":     0.72,
    "Switzerland": 0.68,
    "Croatia":     0.62,
    "Uruguay":     0.58,
    "Austria":     0.70,
    "Turkey":      0.62,
    "Norway":      0.66,
    "Serbia":      0.60,
    "Scotland":    0.65,
    "Sweden":      0.64,
    "Iran":        0.52,
    "Saudi Arabia":0.54,
    "Algeria":     0.55,
    "Tunisia":     0.53,
    "Egypt":       0.55,
    "Ghana":       0.58,
    "Cameroon":    0.57,
    "Ivory Coast": 0.60,
    "Nigeria":     0.60,
    "Qatar":       0.45,
    "Curaçao":     0.42,
    "Haiti":       0.48,
    "Cape Verde":  0.52,
    "Uzbekistan":  0.55,
    "Jordan":      0.50,
    "New Zealand": 0.55,
    "Panama":      0.50,
    "Paraguay":    0.55,
    "DR Congo":    0.58,
    "South Africa":0.55,
    "Morocco":     0.65,
    "Iraq":        0.52,
    "Bosnia-Herzegovina": 0.58,
    "Czechia":     0.62,
}


def _load_dc() -> dict:
    if DC_PATH.exists():
        try:
            return json.loads(DC_PATH.read_text())
        except Exception:
            pass
    return {}


def _dc_pressing_proxy(team: str, dc: dict) -> Optional[float]:
    """
    Proxy pressing depuis DC : faible defense_i = bonne défense (bloc bas)
    ou attaque élevée = équipe qui prend des risques (pressing).
    attack / defense ratio est une approximation du style offensif.
    """
    attack  = dc.get("attack", {}).get(team)
    defense = dc.get("defense", {}).get(team)
    if attack and defense:
        # Normalise sur 0-1 : log(attack/defense) centré sur 0
        ratio = math.log(attack / defense)
        # Mapping : -2 → 0.2, 0 → 0.5, +2 → 0.8
        normalized = 0.5 + ratio * 0.15
        return round(max(0.1, min(normalized, 0.95)), 3)
    return None


def get_pressing_stats(team: str) -> dict:
    """
    Retourne le style de pressing estimé pour l'équipe.
    pressing_score : 0 (bloc bas) → 1 (pressing très intense)
    """
    dc = _load_dc()

    # Priorité 1 : données connues
    if team in KNOWN_PRESSING:
        base = KNOWN_PRESSING[team]
        dc_proxy = _dc_pressing_proxy(team, dc)
        # Blend 70/30 connu vs DC
        if dc_proxy:
            score = round(0.70 * base + 0.30 * dc_proxy, 3)
        else:
            score = base
    else:
        # Uniquement DC
        score = _dc_pressing_proxy(team, dc) or 0.55

    level = "high" if score > 0.70 else "medium" if score > 0.55 else "low"

    return {
        "team":           team,
        "pressing_score": score,
        "pressing_level": level,
        # Impact sur lambda : équipe pressante → plus de chances créées
        # mais aussi plus de risques défensifs
        "press_attack_mult":  round(1.0 + (score - 0.55) * 0.12, 4),
        "press_defense_mult": round(1.0 - (score - 0.55) * 0.06, 4),
    }
