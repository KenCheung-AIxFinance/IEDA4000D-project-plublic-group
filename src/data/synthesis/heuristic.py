"""
Heuristic Synthesizer - Baseline Method

This is the original manual approach from synthesis.py, preserved as a baseline.
Uses hard-coded conditional probabilities to generate synthetic data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any

from .base import BaseSynthesizer


class HeuristicSynthesizer(BaseSynthesizer):
    """
    Heuristic synthesis using manual sequential conditional probability.

    This is the original implementation from synthesis.py, preserved as
    the baseline for comparison with formal methods.
    """

    def fit_marginals(self, nces_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract marginals from NCES data.

        For heuristic method, we don't actually fit marginals from data
        but document the hard-coded probabilities used.
        """
        # Document the hard-coded probabilities in metadata
        self.metadata['marginals'] = {
            'sex': {'Male': 0.49, 'Female': 0.51},
            'ses': {'Lowest': 0.25, 'Second': 0.25, 'Third': 0.25, 'Highest': 0.25},
            'calculus_by_ses': {
                'Lowest': 0.05,
                'Second': 0.10,
                'Third': 0.15,
                'Highest': 0.30
            },
            'high_expectation_by_calculus': {
                1: 0.66,  # Calculus takers
                0: 0.31   # Non-calculus
            },
            'math_enjoyment': {
                'base_calculus': 0.45,
                'base_no_calculus': 0.20,
                'ses_highest_boost': 0.10
            },
            'stem_probability': {
                'sex': {'Male': 0.25, 'Female': 0.08},
                'ses': {'Lowest': 0.10, 'Second': 0.14, 'Third': 0.18, 'Highest': 0.22},
                'calculus': {1: 0.40, 0: 0.14},
                'enjoyment_boost': 0.15,
                'expectation_boost': 0.05
            }
        }

        # Note: This method doesn't actually use NCES data for fitting
        # The probabilities are hard-coded based on NCES Table 1, 4, 10, 15
        self.metadata['data_quality_issues'] = [
            {
                'issue': 'hardcoded_probabilities',
                'description': 'Probabilities manually specified from NCES tables, not fitted from data'
            }
        ]

        return self.metadata['marginals']

    def synthesize(self, marginals: Dict[str, Any]) -> pd.DataFrame:
        """
        Generate synthetic data using hard-coded conditional probabilities.
        """
        np.random.seed(self.seed)

        # Initialize DataFrame
        data = pd.DataFrame(index=range(self.n))

        # A. Assign Sex (50/50 based on NCES norms)
        data['sex'] = np.random.choice(
            ['Male', 'Female'],
            size=self.n,
            p=[marginals['sex']['Male'], marginals['sex']['Female']]
        )

        # B. Assign SES (Uniform quartiles)
        ses_options = ['Lowest', 'Second', 'Third', 'Highest']
        data['ses'] = np.random.choice(ses_options, size=self.n)

        # C. Assign Math Treatment (Calculus) - SES-dependent
        ses_map = marginals['calculus_by_ses']
        data['calculus'] = data['ses'].apply(
            lambda s: 1 if np.random.random() < ses_map[s] else 0
        ).astype(int)

        # D. Assign Expectations (based on Calculus)
        expectation_map = marginals['high_expectation_by_calculus']
        data['high_expectation'] = data['calculus'].apply(
            lambda is_calc: 1 if np.random.random() < expectation_map[is_calc] else 0
        ).astype(int)

        # E. Assign Math Enjoyment (Calculus + SES)
        enjoyment_params = marginals['math_enjoyment']

        def assign_enjoyment(is_calc, ses):
            p = enjoyment_params['base_calculus'] if is_calc else enjoyment_params['base_no_calculus']
            if ses == 'Highest':
                p += enjoyment_params['ses_highest_boost']
            return 1 if np.random.random() < p else 0

        data['math_enjoyment'] = data.apply(
            lambda row: assign_enjoyment(row['calculus'], row['ses']),
            axis=1
        ).astype(int)

        # F. Assign STEM Outcome
        stem_params = marginals['stem_probability']

        def get_stem_prob(row):
            # Base probability from demographics and treatment
            p = (
                stem_params['sex'][row['sex']] +
                stem_params['ses'][row['ses']] +
                stem_params['calculus'][row['calculus']]
            ) / 3

            # Psychosocial boosts
            if row['math_enjoyment']:
                p += stem_params['enjoyment_boost']
            if row['high_expectation']:
                p += stem_params['expectation_boost']

            return np.clip(p, 0, 1)

        data['stem_prob'] = data.apply(get_stem_prob, axis=1)
        data['stem_major'] = (
            np.random.random(self.n) < data['stem_prob']
        ).astype(int)

        # Add metadata
        self.metadata['convergence'] = None
        self.metadata['uncertainty_quantification'] = None

        return data