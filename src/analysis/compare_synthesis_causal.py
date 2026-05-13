"""
Compare Causal Impact across Synthesis Methods

Runs AIPW estimation on all 5 synthetic datasets to evaluate how
microdata reconstruction assumptions affect the estimated 'Calculus Effect'.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json

# Setup paths
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

from src.analysis.causal_estimators import AIPWEstimator

def compare_ate_across_methods():
    output_dir = project_root / 'outputs' / 'tables'
    methods = ['heuristic', 'ipf', 'copula', 'bayesian', 'sri']

    treatment = 'calculus'
    outcome = 'stem_major'
    confounders = ['sex', 'ses', 'high_expectation', 'math_enjoyment']

    comparison_results = []

    print(f"{'Method':<12} | {'ATE':<10} | {'SE':<10} | {'95% CI':<20}")
    print("-" * 60)

    for method in methods:
        file_path = output_dir / f'synthetic_students_{method}.csv'
        if not file_path.exists():
            continue

        df = pd.read_csv(file_path)

        try:
            aipw = AIPWEstimator(df, treatment, outcome, confounders)
            aipw.fit()
            ate, se = aipw.estimate_ate()

            ci_low = ate - 1.96 * se
            ci_high = ate + 1.96 * se

            comparison_results.append({
                'method': method,
                'ate': ate,
                'se': se,
                'ci_lower': ci_low,
                'ci_upper': ci_high
            })

            print(f"{method:<12} | {ate:>10.4f} | {se:>10.4f} | [{ci_low:>7.4f}, {ci_high:>7.4f}]")

        except Exception as e:
            print(f"{method:<12} | Error: {str(e)}")

    # Save comparison to JSON for presentation/notebooks
    with open(output_dir / 'causal_comparison_metadata.json', 'w') as f:
        json.dump(comparison_results, f, indent=2)

    print("-" * 60)
    print(f"Comparison results saved to {output_dir / 'causal_comparison_metadata.json'}")

if __name__ == "__main__":
    compare_ate_across_methods()
