"""
Moteur de prédiction V2.
- Skellam distribution (meilleure que Poisson pour le football)
- Fusion pondérée : ELO + xG rolling + Forme + Cotes
- Ajustement bayésien avec les cotes bookmakers
- Score de confiance composite
"""
import sys
import math
import json
from pathlib import Path
from typing import Optional

# Scipy optionnel (fallback sur Poisson si non installé)
try:
    from scipy.stats import skellam as _skellam, poisson as _poisson
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

sys.path.insert(0, str(Path(__file__).parent.parent))

# ─── Chargement du modèle Dixon-Coles (si disponible) ──────────────────────
_DC_PATH = Path(__file__).parent.parent / "data" / "dc_model.json"

def _load_dc_model():
    if _DC_PATH.exists():
        try:
            d = json.loads(_DC_PATH.read_text())
            return d.get("attack", {}), d.get("defense", {}), d.get("mu", 1.18)
        except Exception:
            pass
    return {}, {}, 1.18

DC_ATTACK, DC_DEFENSE, DC_MU = _load_dc_model()


# ─── ELO de base (World Football ELO Ratings, juin 2026) ───────────────────
ELO_BASE = {
    "Spain": 2165, "Argentina": 2113, "France": 2081, "England": 2020,
    "Brazil": 1988, "Portugal": 1984, "Ecuador": 1935, "Germany": 1925,
    "Japan": 1906, "Costa Rica": 1900, "Netherlands": 1960, "Croatia": 1940,
    "Colombia": 1930, "Belgium": 1888, "Mexico": 1900, "Senegal": 1867,
    "Turkey": 1855, "Denmark": 1870, "Uruguay": 1870, "Chile": 1840,
    "Austria": 1820, "Switzerland": 1820, "Morocco": 1824, "Canada": 1793,
    "Australia": 1774, "Iran": 1772, "South Korea": 1760, "Poland": 1770,
    "USA": 1733, "Serbia": 1674, "Jamaica": 1680, "Panama": 1710,
    "Nigeria": 1800, "Ivory Coast": 1780, "Egypt": 1720, "Algeria": 1750,
    "Czech Republic": 1750, "Czechia": 1750, "Ukraine": 1840, "Paraguay": 1720,
    "Honduras": 1580, "Tunisia": 1620, "Wales": 1691, "Saudi Arabia": 1566,
    "Qatar": 1423, "Ghana": 1680, "Cameroon": 1613, "Bolivia": 1530,
    "New Zealand": 1450, "South Africa": 1650, "Haiti": 1420, "Scotland": 1790,
    "DR Congo": 1680, "Uzbekistan": 1620, "Jordan": 1560, "Cape Verde": 1580,
    "Curaçao": 1400, "Bosnia-Herzegovina": 1720,
}

# Moyenne de buts par match en WC (plus conservateur que les clubs)
WC_BASE_GOALS = 1.18

# Titres WC = facteur de pression en KO
WC_PRESTIGE = {
    "Brazil": 1.08, "Germany": 1.07, "Italy": 1.06,
    "Argentina": 1.07, "France": 1.05, "Uruguay": 1.03,
    "England": 1.02, "Spain": 1.04,
}


class MatchPredictorV2:

    # Poids des signaux (somme = 1.0 quand tous disponibles)
    W_ELO   = 0.30   # ELO long terme (ancre principale pour les grands écarts)
    W_DC    = 0.20   # Dixon-Coles (attaque/défense historique)
    W_FORM  = 0.20   # Forme pondérée récente
    W_ODDS  = 0.20   # Marché bookmakers (si disponible)
    W_WC    = 0.05   # Performance historique en WC
    W_XG    = 0.05   # xG rolling (si disponible)

    # Fusion avec cotes : notre modèle (60%) vs marché (40%)
    MODEL_WEIGHT = 0.60
    MARKET_WEIGHT = 0.40

    def __init__(self):
        self.elo = ELO_BASE.copy()

    # ─── Lambda (xG attendu) ───────────────────────────────────────────────

    def _elo_lambda(self, elo_a: float, elo_b: float) -> float:
        factor = 10 ** ((elo_a - elo_b) / 1100)
        return WC_BASE_GOALS * factor

    def _form_multiplier(self, form_score: Optional[float]) -> float:
        """Forme 0-1 → multiplicateur 0.80-1.20"""
        if form_score is None:
            return 1.0
        return 0.80 + form_score * 0.40

    def _wc_multiplier(self, team: str, wc_win_rate: Optional[float]) -> float:
        """Expérience WC → léger avantage en tournoi"""
        prestige = WC_PRESTIGE.get(team, 1.0)
        if wc_win_rate is None:
            return prestige
        return prestige * (0.90 + wc_win_rate * 0.20)

    def compute_lambda(self, team: str, opp: str, data: dict) -> float:
        elo_a = data.get(f"elo_{team}") or self.elo.get(team, 1700)
        elo_b = data.get(f"elo_{opp}")  or self.elo.get(opp, 1700)

        # Signal ELO
        lambda_elo = self._elo_lambda(elo_a, elo_b)

        # Signal Dixon-Coles (attaque/défense appris sur données historiques)
        # On normalise avec WC_BASE_GOALS/DC_MU pour ramener au rythme réel du WC
        # (le DC est entraîné sur tous les matchs internationaux, plus offensifs)
        WC_SCALE = WC_BASE_GOALS / DC_MU  # ≈ 0.844
        lambda_dc = None
        if team in DC_ATTACK and opp in DC_DEFENSE:
            lambda_dc = DC_ATTACK[team] * DC_DEFENSE[opp] * DC_MU * WC_SCALE
            # Petit ajustement ELO : corrige les équipes sans historique récent
            # mais de manière très conservatrice (±10% max)
            elo_ratio = 10 ** ((elo_a - elo_b) / 4000)
            lambda_dc = lambda_dc * elo_ratio
            # Cap WC : même le plus gros mismatch ne dépasse pas 3.0 xG
            lambda_dc = min(lambda_dc, 3.0)

        # Signal xG rolling (fbref / eloratings proxy)
        lambda_xg = data.get(f"xg_rolling_{team}")

        # Signal cotes → xG implicite
        lambda_odds = data.get(f"xg_implied_{team}")

        # Signal forme
        form = data.get(f"form_score_{team}")
        form_mult = self._form_multiplier(form)

        # Signal WC historique
        wc_win_rate = data.get(f"wc_win_rate_{team}")
        wc_mult = self._wc_multiplier(team, wc_win_rate)

        # Ajustement blessures
        injury_mult = 0.82 if data.get(f"star_injured_{team}") else 1.0

        # Fusion pondérée des signaux disponibles
        signals, weights = {"elo": lambda_elo}, {"elo": self.W_ELO}

        if lambda_dc and lambda_dc > 0:
            signals["dc"]   = lambda_dc
            weights["dc"]   = self.W_DC
        if lambda_xg and lambda_xg > 0:
            signals["xg"]  = lambda_xg
            weights["xg"]  = self.W_XG
        if lambda_odds and lambda_odds > 0:
            signals["odds"] = lambda_odds
            weights["odds"] = self.W_ODDS

        # Renormalise les poids
        total_w = sum(weights.values())
        lambda_base = sum(signals[k] * weights[k] for k in signals) / total_w

        # Applique les multiplicateurs
        # Pressing : équipe pressante génère plus de xG
        press_mult = data.get(f"press_attack_mult_{team}", 1.0) or 1.0

        # Fatigue : trop de matchs récents réduit la production offensive
        fatigue = data.get(f"fatigue_score_{team}", 0.0) or 0.0
        fatigue_mult = 1.0 - fatigue * 0.08   # max -8% si épuisé

        # Voyage : long trajet réduit légèrement le rendement
        travel_mult = data.get(f"travel_mult_{team}", 1.0) or 1.0

        # Psychologie : confiance ou tensions internes
        psych = data.get(f"psych_score_{team}", 0.5) or 0.5
        psych_mult = 0.94 + psych * 0.12   # 0.94 (très négatif) → 1.06 (très positif)

        # Arbitre : avantage/désavantage selon style
        if team == opp:   # sécurité, ne devrait pas arriver
            ref_mult = 1.0
        else:
            ref_adv = data.get("ref_advantage_home", 0.0) if team == list(data.keys())[0] else data.get("ref_advantage_away", 0.0)
            ref_mult = 1.0 + (ref_adv or 0.0)

        result = lambda_base * form_mult * wc_mult * injury_mult * press_mult * fatigue_mult * travel_mult * psych_mult

        return max(0.18, min(result, 2.8))

    # ─── Probabilités ─────────────────────────────────────────────────────

    def _skellam_probs(self, la: float, lb: float):
        """Distribution de Skellam (différence de buts)"""
        if HAS_SCIPY:
            p_home = float(sum(_skellam.pmf(k, la, lb) for k in range(1, 9)))
            p_draw = float(_skellam.pmf(0, la, lb))
            p_away = float(sum(_skellam.pmf(-k, la, lb) for k in range(1, 9)))
        else:
            # Fallback : Poisson bivarié
            p_home, p_draw, p_away = 0.0, 0.0, 0.0
            for i in range(8):
                for j in range(8):
                    p = self._poisson_pmf(la, i) * self._poisson_pmf(lb, j)
                    if i > j:   p_home += p
                    elif i == j: p_draw += p
                    else:        p_away += p

        # Normalise (Skellam peut légèrement dépasser 1)
        total = p_home + p_draw + p_away
        return p_home/total, p_draw/total, p_away/total

    def _poisson_pmf(self, lam: float, k: int) -> float:
        return math.exp(-lam) * (lam**k) / math.factorial(k)

    def _score_matrix(self, la: float, lb: float) -> list[dict]:
        """Top scores les plus probables."""
        scores = []
        pmf_a = [self._poisson_pmf(la, k) for k in range(8)]
        pmf_b = [self._poisson_pmf(lb, k) for k in range(8)]
        for i in range(8):
            for j in range(8):
                scores.append({"score": f"{i}-{j}", "prob": round(pmf_a[i]*pmf_b[j]*100, 2)})
        scores.sort(key=lambda x: -x["prob"])
        return scores[:8]

    def _bayesian_blend(self, model_probs: list, market_probs: list) -> list:
        """
        Fusionne notre modèle avec les cotes du marché.
        Marché = meilleur agrégateur d'information disponible.
        """
        blended = [
            self.MODEL_WEIGHT * m + self.MARKET_WEIGHT * k
            for m, k in zip(model_probs, market_probs)
        ]
        total = sum(blended)
        return [b / total for b in blended]

    def _confidence_score(self, data: dict, team_a: str, team_b: str) -> dict:
        """Score de confiance composite 0-100."""
        score = 50  # base neutre
        factors = []

        elo_a = data.get(f"elo_{team_a}") or self.elo.get(team_a, 1700)
        elo_b = data.get(f"elo_{team_b}") or self.elo.get(team_b, 1700)
        gap = abs(elo_a - elo_b)

        # ELO gap → plus le gap est grand, plus c'est prévisible
        if gap > 400:   score += 20; factors.append("très grand écart ELO (+20)")
        elif gap > 250: score += 12; factors.append("grand écart ELO (+12)")
        elif gap > 150: score += 6;  factors.append("écart ELO modéré (+6)")
        elif gap < 50:  score -= 8;  factors.append("match équilibré ELO (-8)")

        # H2H disponible
        h2h_n = data.get("h2h_matches", 0)
        if h2h_n >= 5:   score += 8;  factors.append("H2H riche (+8)")
        elif h2h_n >= 2: score += 4;  factors.append("H2H modéré (+4)")
        elif h2h_n == 0: score -= 6;  factors.append("pas de H2H (-6)")

        # Forme disponible et alignée
        form_a = data.get(f"form_score_{team_a}")
        form_b = data.get(f"form_score_{team_b}")
        if form_a and form_b:
            fav_by_elo   = team_a if elo_a > elo_b else team_b
            form_a_val   = form_a if fav_by_elo == team_a else form_b
            form_b_val   = form_b if fav_by_elo == team_a else form_a
            if form_a_val > form_b_val + 0.2:
                score += 8; factors.append("forme confirme le favori ELO (+8)")
            elif form_a_val < form_b_val - 0.2:
                score -= 5; factors.append("forme contredit le favori ELO (-5)")
        else:
            score -= 4; factors.append("forme non disponible (-4)")

        # Cotes disponibles
        if data.get("odds_available"):
            score += 10; factors.append("cotes bookmakers disponibles (+10)")
            if data.get("has_pinnacle"):
                score += 5; factors.append("Pinnacle (sharp money) disponible (+5)")
        else:
            score -= 5; factors.append("pas de cotes live (-5)")

        # Blessures
        if data.get(f"star_injured_{team_a}") or data.get(f"star_injured_{team_b}"):
            score -= 8; factors.append("blessure majeure signalée (-8)")

        # Dixon-Coles disponible
        if team_a in DC_ATTACK and team_b in DC_ATTACK:
            score += 8; factors.append("Dixon-Coles actif (+8)")

        # Squad value gap (Transfermarkt) — confirme la hiérarchie
        val_a = data.get(f"squad_value_{team_a}")
        val_b = data.get(f"squad_value_{team_b}")
        if val_a and val_b and max(val_a, val_b) > 0:
            ratio = max(val_a, val_b) / max(min(val_a, val_b), 1)
            if ratio > 20:   score += 6;  factors.append(f"écart squad value x{ratio:.0f} (+6)")
            elif ratio > 5:  score += 4;  factors.append(f"écart squad value x{ratio:.0f} (+4)")
            elif ratio < 2:  score -= 3;  factors.append("squads de valeur similaire (-3)")

        # Blessure star confirmée → diminue confiance
        if data.get(f"star_injured_{team_a}") or data.get(f"star_injured_{team_b}"):
            score -= 10; factors.append("star blessée confirmée TM (-10)")

        # Fatigue
        fat_a = data.get(f"fatigue_score_{team_a}", 0)
        fat_b = data.get(f"fatigue_score_{team_b}", 0)
        if fat_a > 0.6 or fat_b > 0.6:
            score -= 5; factors.append("fatigue élevée détectée (-5)")

        # Tensions internes (news)
        if data.get(f"internal_conflict_{team_a}") or data.get(f"internal_conflict_{team_b}"):
            score -= 7; factors.append("tension interne signalée (-7)")

        # Coach sentiment négatif
        if data.get(f"coach_sentiment_{team_a}") == "negative" or data.get(f"coach_sentiment_{team_b}") == "negative":
            score -= 4; factors.append("coach négatif en conf de presse (-4)")

        # Long voyage (> 10 000 km)
        km_a = data.get(f"travel_km_{team_a}", 0) or 0
        km_b = data.get(f"travel_km_{team_b}", 0) or 0
        if max(km_a, km_b) > 10000:
            score -= 3; factors.append(f"voyage intercontinental ({max(km_a,km_b):.0f} km) (-3)")

        # News disponibles et positives
        psych_a = data.get(f"psych_score_{team_a}", 0.5) or 0.5
        psych_b = data.get(f"psych_score_{team_b}", 0.5) or 0.5
        if abs(psych_a - psych_b) > 0.15:
            score += 4; factors.append(f"écart psychologique significatif (+4)")

        level = "high" if score >= 70 else "medium" if score >= 50 else "low"
        return {
            "score":   min(max(score, 5), 95),
            "level":   level,
            "factors": factors,
        }

    # ─── Prédiction principale ────────────────────────────────────────────

    def predict(self, team_a: str, team_b: str, data: dict = None) -> dict:
        if data is None:
            data = {}

        la = self.compute_lambda(team_a, team_b, data)
        lb = self.compute_lambda(team_b, team_a, data)

        p_home, p_draw, p_away = self._skellam_probs(la, lb)

        # Fusion bayésienne avec cotes si disponibles
        blended = False
        if data.get("odds_available") and all(
            data.get(k) for k in ["prob_home", "prob_draw", "prob_away"]
        ):
            p_home, p_draw, p_away = self._bayesian_blend(
                [p_home, p_draw, p_away],
                [data["prob_home"], data["prob_draw"], data["prob_away"]]
            )
            blended = True

        # Over/Under & BTTS
        over25 = sum(
            self._poisson_pmf(la, i) * self._poisson_pmf(lb, j)
            for i in range(8) for j in range(8) if i+j >= 3
        )
        btts = sum(
            self._poisson_pmf(la, i) * self._poisson_pmf(lb, j)
            for i in range(1, 8) for j in range(1, 8)
        )

        # Scores probables
        top_scores = self._score_matrix(la, lb)

        # Confiance
        confidence = self._confidence_score(data, team_a, team_b)

        # Résumé
        probs = {"home": p_home, "draw": p_draw, "away": p_away}
        winner = max(probs, key=probs.get)
        winner_team = team_a if winner == "home" else (team_b if winner == "away" else "Draw")

        return {
            "version":     "v2",
            "team_a":      team_a,
            "team_b":      team_b,
            "elo_a":       data.get(f"elo_{team_a}", self.elo.get(team_a, 1700)),
            "elo_b":       data.get(f"elo_{team_b}", self.elo.get(team_b, 1700)),
            "lambda_a":    round(la, 3),
            "lambda_b":    round(lb, 3),
            "p_home":      round(p_home * 100, 1),
            "p_draw":      round(p_draw * 100, 1),
            "p_away":      round(p_away * 100, 1),
            "winner":      winner_team,
            "winner_prob": round(max(p_home, p_draw, p_away) * 100, 1),
            "top_scores":  top_scores,
            "best_score":  top_scores[0]["score"] if top_scores else "1-1",
            "over25":      round(over25 * 100, 1),
            "btts":        round(btts * 100, 1),
            "avg_goals":   round(la + lb, 2),
            "bayesian_blend": blended,
            "confidence":  confidence,
            "signals_used": {
                "elo":          True,
                "dixon_coles":  team_a in DC_ATTACK and team_b in DC_ATTACK,
                "form_a":       data.get(f"form_score_{team_a}") is not None,
                "form_b":       data.get(f"form_score_{team_b}") is not None,
                "odds":         data.get("odds_available", False),
                "xg_a":         data.get(f"xg_rolling_{team_a}") is not None,
                "xg_b":         data.get(f"xg_rolling_{team_b}") is not None,
                "h2h":          data.get("h2h_matches", 0) > 0,
                "wc_history":   data.get(f"wc_win_rate_{team_a}") is not None,
                "squad_value":  data.get(f"squad_value_{team_a}") is not None,
                "injuries":     data.get(f"n_injured_{team_a}") is not None,
                "news_nlp":     data.get(f"psych_score_{team_a}") is not None,
                "fatigue":      data.get(f"fatigue_score_{team_a}") is not None,
                "travel":       data.get(f"travel_km_{team_a}") is not None,
                "pressing":     data.get(f"pressing_score_{team_a}") is not None,
                "penalties":    data.get(f"penalty_rate_{team_a}") is not None,
                "referee":      data.get("ref_style") is not None,
            },
        }


# Instance globale
predictor = MatchPredictorV2()


if __name__ == "__main__":
    import json
    print("Testing Predictor V2...")

    # Test sans données enrichies
    r = predictor.predict("France", "Argentina")
    print("\n=== France vs Argentina (ELO only) ===")
    print(f"  Proba : {r['p_home']}% / {r['p_draw']}% / {r['p_away']}%")
    print(f"  Score : {r['best_score']}")
    print(f"  xG    : {r['lambda_a']} - {r['lambda_b']}")
    print(f"  Confidence: {r['confidence']['level']} ({r['confidence']['score']})")

    # Test avec données enrichies
    data_enriched = {
        "form_score_France":      0.75,
        "form_score_Argentina":   0.65,
        "xg_rolling_France":      1.8,
        "xg_rolling_Argentina":   1.6,
        "wc_win_rate_France":     0.55,
        "wc_win_rate_Argentina":  0.60,
        "h2h_matches":            4,
        "h2h_dominant":           "Argentina",
        "odds_available":         True,
        "prob_home":              0.38,
        "prob_draw":              0.26,
        "prob_away":              0.36,
        "has_pinnacle":           True,
    }
    r2 = predictor.predict("France", "Argentina", data_enriched)
    print("\n=== France vs Argentina (fully enriched) ===")
    print(f"  Proba : {r2['p_home']}% / {r2['p_draw']}% / {r2['p_away']}%")
    print(f"  Score : {r2['best_score']}")
    print(f"  Bayesian blend: {r2['bayesian_blend']}")
    print(f"  Confidence: {r2['confidence']['level']} ({r2['confidence']['score']})")
    print(f"  Factors: {r2['confidence']['factors']}")
