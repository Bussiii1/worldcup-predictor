"""
Étape 2 — Modèle Dixon-Coles (1997).
Trouve attack_i et defense_i pour chaque équipe par MLE pondéré.
Loi de Poisson pour simuler les scores.
"""
import math
import numpy as np
from scipy.optimize import minimize
from scipy.stats import poisson


def _poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def _score_prob(home_goals: int, away_goals: int, lam_h: float, lam_a: float) -> float:
    """P(score = h:a | λ_h, λ_a) selon loi de Poisson."""
    return _poisson_pmf(home_goals, lam_h) * _poisson_pmf(away_goals, lam_a)


class DixonColesModel:
    """
    Paramètres par équipe : attack_i, defense_i
    λ_home = attack_home × defense_away × mu
    λ_away = attack_away × defense_home
    mu = taux de base moyen (buts/match)
    """

    def __init__(self):
        self.teams: list[str] = []
        self.attack: dict[str, float] = {}
        self.defense: dict[str, float] = {}
        self.mu: float = 1.18  # base WC goals/match

    def fit(self, df, verbose: bool = True) -> "DixonColesModel":
        """
        Optimise attack/defense par MLE pondéré sur le DataFrame de matchs.
        df doit avoir : home_team, away_team, home_goals, away_goals, weight
        """
        teams = sorted(set(df["home_team"]) | set(df["away_team"]))
        self.teams = teams
        n = len(teams)
        idx = {t: i for i, t in enumerate(teams)}

        if verbose:
            print(f"Optimisation Dixon-Coles sur {len(df)} matchs, {n} équipes...")

        # Paramètres initiaux : attack=1.0, defense=1.0, log-space pour garantir > 0
        # On fixe mu = moyenne des buts totaux pondérée
        total_goals = (df["home_goals"] + df["away_goals"]) * df["weight"]
        self.mu = float(total_goals.sum() / (2 * df["weight"].sum()))

        # x = [log_attack_0, ..., log_attack_n-1, log_defense_0, ..., log_defense_n-1]
        x0 = np.zeros(2 * n)

        # Pré-calculer les indices et valeurs numpy pour éviter les boucles Python
        home_idx = np.array([idx[t] for t in df["home_team"]], dtype=np.int32)
        away_idx = np.array([idx[t] for t in df["away_team"]], dtype=np.int32)
        home_goals = df["home_goals"].values
        away_goals = df["away_goals"].values
        weights    = df["weight"].values

        # Factorielles pré-calculées pour les buts (0..max_g)
        max_g = int(max(home_goals.max(), away_goals.max())) + 1
        log_fact = np.array([math.lgamma(k + 1) for k in range(max_g + 1)])

        def neg_log_likelihood(x: np.ndarray) -> float:
            attack  = np.exp(x[:n])
            defense = np.exp(x[n:])
            lam_h = attack[home_idx] * defense[away_idx] * self.mu
            lam_a = attack[away_idx] * defense[home_idx]
            # log P(k | λ) = k*log(λ) - λ - log(k!)
            log_p_h = home_goals * np.log(np.maximum(lam_h, 1e-10)) - lam_h - log_fact[home_goals]
            log_p_a = away_goals * np.log(np.maximum(lam_a, 1e-10)) - lam_a - log_fact[away_goals]
            ll = np.sum(weights * (log_p_h + log_p_a))
            return -ll

        if verbose:
            print("  Lancement de l'optimisation L-BFGS-B...")

        result = minimize(
            neg_log_likelihood,
            x0,
            method="L-BFGS-B",
            options={"maxiter": 500, "ftol": 1e-8, "disp": verbose},
        )

        attack_vals  = np.exp(result.x[:n])
        defense_vals = np.exp(result.x[n:])

        # Normalisation : moyenne d'attaque = 1.0
        norm = attack_vals.mean()
        attack_vals  /= norm
        defense_vals /= norm

        self.attack  = {t: float(attack_vals[i])  for i, t in enumerate(teams)}
        self.defense = {t: float(defense_vals[i]) for i, t in enumerate(teams)}

        if verbose:
            print(f"  Optimisation terminée. Log-likelihood = {-result.fun:.2f}")
            print(f"  mu = {self.mu:.4f} buts/match de base")

        return self

    def expected_goals(self, home: str, away: str) -> tuple[float, float]:
        """Retourne (λ_home, λ_away)."""
        lam_h = self.attack.get(home, 1.0) * self.defense.get(away, 1.0) * self.mu
        lam_a = self.attack.get(away, 1.0) * self.defense.get(home, 1.0)
        return lam_h, lam_a

    def score_probability(self, home: str, away: str, gh: int, ga: int) -> float:
        lam_h, lam_a = self.expected_goals(home, away)
        return _score_prob(gh, ga, lam_h, lam_a)

    def match_probabilities(self, home: str, away: str, max_goals: int = 8) -> dict:
        """Retourne P(home win), P(draw), P(away win)."""
        lam_h, lam_a = self.expected_goals(home, away)
        p_home = p_draw = p_away = 0.0
        for gh in range(max_goals + 1):
            ph = _poisson_pmf(gh, lam_h)
            for ga in range(max_goals + 1):
                pa = _poisson_pmf(ga, lam_a)
                p = ph * pa
                if gh > ga:   p_home += p
                elif gh == ga: p_draw += p
                else:          p_away += p
        return {"home": p_home, "draw": p_draw, "away": p_away}

    def simulate_match(self, home: str, away: str, knockout: bool = False) -> tuple[int, int]:
        """
        Tire un score selon les distributions de Poisson.
        En phase KO : si nul → prolongations → tirs au but (50/50).
        """
        lam_h, lam_a = self.expected_goals(home, away)
        gh = int(np.random.poisson(lam_h))
        ga = int(np.random.poisson(lam_a))

        if knockout and gh == ga:
            # Prolongations : petite chance de but supplémentaire
            extra_h = int(np.random.poisson(0.25))
            extra_a = int(np.random.poisson(0.25))
            gh += extra_h
            ga += extra_a
            if gh == ga:
                # Tirs au but
                if np.random.random() < 0.5:
                    gh += 1
                else:
                    ga += 1
        return gh, ga

    def top_scores(self, home: str, away: str, max_goals: int = 6, top_n: int = 8) -> list[dict]:
        lam_h, lam_a = self.expected_goals(home, away)
        scores = []
        for gh in range(max_goals + 1):
            for ga in range(max_goals + 1):
                p = _poisson_pmf(gh, lam_h) * _poisson_pmf(ga, lam_a)
                scores.append({"score": f"{gh}-{ga}", "prob_pct": round(p * 100, 2)})
        scores.sort(key=lambda x: -x["prob_pct"])
        return scores[:top_n]

    def rankings(self) -> list[dict]:
        """Classement par force relative (attaque - défense log)."""
        rows = []
        for t in self.teams:
            rows.append({
                "team":    t,
                "attack":  round(self.attack[t], 4),
                "defense": round(self.defense[t], 4),
                "strength": round(self.attack[t] / self.defense[t], 4),
            })
        rows.sort(key=lambda x: -x["strength"])
        return rows


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from dixon_coles.data_loader import load_matches

    df = load_matches()
    model = DixonColesModel()
    model.fit(df)

    print("\n=== Top 10 équipes par force ===")
    for i, r in enumerate(model.rankings()[:10], 1):
        print(f"  {i:2}. {r['team']:<20} att={r['attack']:.3f} def={r['defense']:.3f} strength={r['strength']:.3f}")

    print("\n=== France vs Espagne ===")
    p = model.match_probabilities("France", "Spain")
    print(f"  France win: {p['home']*100:.1f}%  Draw: {p['draw']*100:.1f}%  Spain win: {p['away']*100:.1f}%")
    print(f"  Scores les plus probables: {model.top_scores('France', 'Spain')[:4]}")
