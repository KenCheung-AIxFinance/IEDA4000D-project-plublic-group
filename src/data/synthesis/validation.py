"""
Synthesis Validation Utilities

Functions to compare synthetic data fidelity against NCES marginals.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from itertools import product


def compute_marginal_mae(
    synthetic_df: pd.DataFrame,
    nces_marginals: Dict[str, Any]
) -> Dict[str, float]:
    """
    Compute Mean Absolute Error between synthetic and NCES marginals.

    Returns:
    - Dictionary of MAE for each marginal
    """
    errors = {}

    # 1. Sex distribution
    syn_sex = synthetic_df['sex'].value_counts(normalize=True)
    nces_sex = nces_marginals.get('sex_probs', nces_marginals.get('sex', {}))
    if isinstance(nces_sex, dict):
        for cat, prob in nces_sex.items():
            if cat in syn_sex.index:
                errors[f'sex_{cat}'] = abs(syn_sex[cat] - prob)

    # 2. SES distribution
    syn_ses = synthetic_df['ses'].value_counts(normalize=True)
    nces_ses = nces_marginals.get('ses_probs', nces_marginals.get('ses', {}))
    if isinstance(nces_ses, dict):
        for cat, prob in nces_ses.items():
            if cat in syn_ses.index:
                errors[f'ses_{cat}'] = abs(syn_ses[cat] - prob)

    # 3. Calculus rate
    syn_calc = synthetic_df['calculus'].mean()
    errors['calculus_rate'] = abs(syn_calc - 0.15)  # Approx NCES rate

    # 4. STEM rate
    syn_stem = synthetic_df['stem_major'].mean()
    errors['stem_rate'] = abs(syn_stem - 0.16)  # Approx NCES rate

    return errors


def compute_conditional_probability(
    df: pd.DataFrame,
    target_col: str,
    condition_col: str,
    condition_val: Any
) -> float:
    """
    Compute P(target=1 | condition=condition_val).

    Returns conditional probability.
    """
    subset = df[df[condition_col] == condition_val]
    if len(subset) == 0:
        return 0.0
    return subset[target_col].mean()


def compute_bivariate_marginals(
    synthetic_df: pd.DataFrame,
    nces_extractor
) -> Dict[Tuple[str, str], Dict[str, float]]:
    """
    Compute all bivariate marginals and compare with NCES.

    Returns:
    - Dictionary of (var1, var2) -> {condition: synthetic_prob, nces_prob}
    """
    bivariate = {}

    # P(STEM | Sex)
    for sex in ['Male', 'Female']:
        syn_prob = compute_conditional_probability(
            synthetic_df, 'stem_major', 'sex', sex
        )
        # NCES from Table 1: Male ~25%, Female ~8%
        nces_prob = 0.25 if sex == 'Male' else 0.08
        bivariate[('stem', f'sex={sex}')] = {
            'synthetic': syn_prob,
            'nces': nces_prob,
            'error': abs(syn_prob - nces_prob)
        }

    # P(STEM | SES)
    for ses in ['Lowest', 'Second', 'Third', 'Highest']:
        syn_prob = compute_conditional_probability(
            synthetic_df, 'stem_major', 'ses', ses
        )
        # NCES from Table 1
        nces_prob = {'Lowest': 0.10, 'Second': 0.14, 'Third': 0.18, 'Highest': 0.22}[ses]
        bivariate[('stem', f'ses={ses}')] = {
            'synthetic': syn_prob,
            'nces': nces_prob,
            'error': abs(syn_prob - nces_prob)
        }

    # P(STEM | Calculus)
    for calc in [0, 1]:
        syn_prob = compute_conditional_probability(
            synthetic_df, 'stem_major', 'calculus', calc
        )
        nces_prob = {1: 0.40, 0: 0.14}[calc]
        bivariate[('stem', f'calculus={calc}')] = {
            'synthetic': syn_prob,
            'nces': nces_prob,
            'error': abs(syn_prob - nces_prob)
        }

    return bivariate


def compute_correlation_matrix(
    df: pd.DataFrame,
    numeric_cols: List[str] = None
) -> pd.DataFrame:
    """
    Compute correlation matrix for synthetic data.

    Returns:
    - Correlation matrix DataFrame
    """
    if numeric_cols is None:
        # Default: encode categorical variables
        df_encoded = df.copy()
        df_encoded['sex_code'] = (df_encoded['sex'] == 'Male').astype(int)
        df_encoded['ses_code'] = df_encoded['ses'].map(
            {'Lowest': 0, 'Second': 1, 'Third': 2, 'Highest': 3}
        )
        numeric_cols = ['sex_code', 'ses_code', 'calculus', 'high_expectation',
                        'math_enjoyment', 'stem_major']
        return df_encoded[numeric_cols].corr()

    return df[numeric_cols].corr()


def compute_kl_divergence(
    p: np.ndarray,
    q: np.ndarray,
    epsilon: float = 1e-10
) -> float:
    """
    Compute KL divergence between two distributions.

    D(p || q) = sum(p * log(p / q))
    """
    p = np.clip(p, epsilon, 1)
    q = np.clip(q, epsilon, 1)
    return np.sum(p * np.log(p / q))


def summarize_fidelity(
    synthetic_df: pd.DataFrame,
    nces_marginals: Dict[str, Any],
    nces_extractor
) -> Dict[str, Any]:
    """
    Generate comprehensive fidelity summary.

    Returns:
    - Dictionary with all fidelity metrics
    """
    summary = {}

    # Univariate MAE
    summary['univariate_mae'] = compute_marginal_mae(synthetic_df, nces_marginals)

    # Bivariate comparison
    summary['bivariate'] = compute_bivariate_marginals(synthetic_df, nces_extractor)

    # Overall MAE
    all_errors = [v for v in summary['univariate_mae'].values()] + \
                 [v['error'] for v in summary['bivariate'].values()]
    summary['overall_mae'] = np.mean(all_errors)
    summary['overall_rmse'] = np.sqrt(np.mean([e**2 for e in all_errors]))

    # Correlation structure
    summary['correlation'] = compute_correlation_matrix(synthetic_df)

    return summary


def create_fidelity_heatmap_data(
    methods_results: Dict[str, Dict[str, float]]
) -> pd.DataFrame:
    """
    Create matrix data for fidelity heatmap visualization.

    Parameters:
    - methods_results: Dict of method_name -> {marginal_name: error}

    Returns:
    - DataFrame suitable for heatmap plotting
    """
    # Get all marginals
    all_marginals = set()
    for errors in methods_results.values():
        all_marginals.update(errors.keys())

    # Build matrix
    matrix = []
    for method, errors in methods_results.items():
        row = {'method': method}
        for marginal in sorted(all_marginals):
            row[marginal] = errors.get(marginal, np.nan)
        matrix.append(row)

    return pd.DataFrame(matrix).set_index('method')
