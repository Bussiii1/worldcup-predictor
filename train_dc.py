"""
Entraîne le modèle Dixon-Coles sur les résultats internationaux historiques
et sauvegarde les paramètres dans data/dc_model.json.

Usage : python3 train_dc.py
Durée : ~30 secondes (téléchargement + optimisation)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dixon_coles.data_loader import load_matches
from dixon_coles.model import DixonColesModel

OUT = Path(__file__).parent / "data" / "dc_model.json"
OUT.parent.mkdir(exist_ok=True)


def train_and_save():
    print("=" * 55)
    print("  ENTRAÎNEMENT DIXON-COLES")
    print("=" * 55)

    # 1. Charger les données (matchs depuis 2018)
    df = load_matches(cutoff_year=2018)

    # 2. Entraîner le modèle
    model = DixonColesModel()
    model.fit(df, verbose=True)

    # 3. Sauvegarder les paramètres
    out = {
        "mu":      round(model.mu, 6),
        "attack":  {t: round(v, 6) for t, v in model.attack.items()},
        "defense": {t: round(v, 6) for t, v in model.defense.items()},
        "teams":   model.teams,
        "n_matches": len(df),
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\n✅ Modèle sauvegardé → {OUT}")

    # 4. Top 15 équipes
    rankings = model.rankings()
    print("\n=== Top 15 équipes par force (attaque / défense) ===")
    for i, r in enumerate(rankings[:15], 1):
        print(f"  {i:2}. {r['team']:<22} att={r['attack']:.3f}  def={r['defense']:.3f}  strength={r['strength']:.3f}")

    # 5. Quelques prédictions de test
    print("\n=== Tests de prédiction ===")
    tests = [
        ("France", "Senegal"),
        ("Brazil", "Argentina"),
        ("Spain", "Germany"),
        ("England", "Croatia"),
    ]
    for home, away in tests:
        if home in model.attack and away in model.attack:
            p = model.match_probabilities(home, away)
            lh, la = model.expected_goals(home, away)
            print(f"  {home:<12} vs {away:<12}  →  {home} {p['home']*100:.0f}%  Nul {p['draw']*100:.0f}%  {away} {p['away']*100:.0f}%  xG {lh:.2f}-{la:.2f}")

    return out


if __name__ == "__main__":
    train_and_save()
