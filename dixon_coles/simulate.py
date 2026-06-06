"""
Main — Pipeline complet.
1. Charge les données
2. Calibre Dixon-Coles
3. Lance 100 000 simulations Monte Carlo
4. Affiche les résultats
"""
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dixon_coles.data_loader import load_matches
from dixon_coles.model import DixonColesModel
from dixon_coles.tournament import simulate_n, format_results

N_SIMULATIONS = 100_000


def main(n: int = N_SIMULATIONS, cutoff_year: int = 2018, save: bool = True):
    print("=" * 60)
    print(f"SIMULATEUR COUPE DU MONDE 2026 — {n:,} simulations")
    print("=" * 60)

    # Étape 1 : données
    df = load_matches(cutoff_year=cutoff_year)

    # Étape 2 : Dixon-Coles
    model = DixonColesModel()
    model.fit(df)

    print("\n=== Classement des équipes par force ===")
    rankings = model.rankings()
    for i, r in enumerate(rankings[:15], 1):
        print(f"  {i:2}. {r['team']:<22} att={r['attack']:.3f}  def={r['defense']:.3f}  strength={r['strength']:.3f}")

    # Étape 3 : Monte Carlo
    print(f"\n=== Lancement de {n:,} simulations ===")
    counts = simulate_n(model, n=n, verbose=True)

    # Résultats
    results = format_results(counts, n)

    print(f"\n{'='*60}")
    print(f"RÉSULTATS — {n:,} Coupes du Monde simulées")
    print(f"{'='*60}")
    print(f"{'Rang':<5} {'Équipe':<22} {'Gagne':>7} {'Finale':>8} {'Demi':>7} {'Quart':>7}")
    print("-" * 60)
    for i, r in enumerate(results[:16], 1):
        print(
            f"  {i:2}. {r['team']:<22} "
            f"{r['win_%']:>6.1f}%  "
            f"{r['final_%']:>6.1f}%  "
            f"{r['semi_%']:>6.1f}%  "
            f"{r['quarter_%']:>6.1f}%"
        )

    if save:
        out_dir = Path(__file__).parent.parent / "output"
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / "wc2026_simulation.json"
        payload = {
            "n_simulations": n,
            "cutoff_year": cutoff_year,
            "rankings": rankings,
            "results": results,
        }
        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        print(f"\nRésultats sauvegardés : {out_path}")

    return results, model


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=N_SIMULATIONS)
    parser.add_argument("--cutoff", type=int, default=2018)
    args = parser.parse_args()
    main(n=args.n, cutoff_year=args.cutoff)
