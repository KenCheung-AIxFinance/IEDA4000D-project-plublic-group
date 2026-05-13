"""
Copula Synthesizer - Gaussian Copula Method

Uses Gaussian copula to model dependencies while generating data
from marginal distributions derived from NCES tables.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from scipy.stats import norm

from .base import BaseSynthesizer
from .marginals import MarginalExtractor


class CopulaSynthesizer(BaseSynthesizer):
    """
    Gaussian Copula synthesizer.

    Preserves correlation structure between variables while generating
    data from marginal distributions:
    1. Estimate marginals from NCES
    2. Estimate correlation matrix from conditional probabilities
    3. Sample from multivariate Gaussian and transform back
    """

    def fit_marginals(self, nces_df: pd.DataFrame) -> Dict[str, Any]:
        """Extract marginal distributions and estimate correlations."""
        extractor = MarginalExtractor(nces_df)
        marginals = extractor.extract_all_marginals()

        # Estimate correlation matrix (6 variables)
        marginals['correlation_matrix'] = self._build_correlation_matrix(marginals)

        self.metadata['parameters']['correlation_method'] = 'odds_ratio_approximation'

        return marginals

    def _build_correlation_matrix(self, marginals: Dict[str, Any]) -> np.ndarray:
        """Build 6x6 correlation matrix from NCES conditional probabilities."""
        # Variables: sex, ses, calculus, expectation, enjoyment, stem
        corr = np.eye(6)

        # Sex-STEM: male=25%, female=8% → OR≈3.1, corr≈0.35
        corr[0, 5] = corr[5, 0] = 0.35

        # SES-STEM
        corr[1, 5] = corr[5, 1] = 0.30

        # Calculus-STEM: 40% vs 14% → OR≈4, corr≈0.42
        corr[2, 5] = corr[5, 2] = 0.42

        # Expectation-STEM
        corr[3, 5] = corr[5, 3] = 0.28

        # Enjoyment-STEM
        corr[4, 5] = corr[5, 4] = 0.38

        # Calculus-SES correlation
        corr[1, 2] = corr[2, 1] = 0.30

        # Expectation-Calculus
        corr[2, 3] = corr[3, 2] = 0.35

        # Enjoyment-Calculus
        corr[2, 4] = corr[4, 2] = 0.30

        # Ensure positive semi-definite
        eigvals = np.linalg.eigvals(corr)
        if np.any(eigvals < 0):
            # Apply nearest positive semi-definite correction
            eigvecs = np.linalg.eig(corr)[1]
            eigvals = np.maximum(eigvals, 1e-6)
            corr = eigvecs @ np.diag(eigvals) @ eigvecs.T
            # Re-normalize diagonal to 1
            d = np.sqrt(np.diag(corr))
            corr = corr / np.outer(d, d)
            corr = (corr + corr.T) / 2
            np.fill_diagonal(corr, 1.0)

        return corr

    def synthesize(self, marginals: Dict[str, Any]) -> pd.DataFrame:
        """Generate synthetic data using Gaussian Copula."""
        np.random.seed(self.seed)
        n = self.n

        corr = marginals['correlation_matrix']
        sex_prob = marginals['sex_probs'].get('Male', 0.49)
        ses_probs = marginals['ses_probs']
        stem_calc = marginals['stem_given_calculus']
        exp_calc = marginals['expectation_given_calculus']

        # 1. Sample from multivariate Gaussian
        z = np.random.multivariate_normal(mean=np.zeros(6), cov=corr, size=n)

        # 2. Transform to uniform via standard normal CDF
        u = norm.cdf(z)

        # 3. Transform uniform to each marginal
        data = pd.DataFrame(index=range(n))

        # Sex: binary via threshold
        data['sex'] = np.where(u[:, 0] < sex_prob, 'Male', 'Female')

        # SES: categorical via cumulative probabilities
        ses_cats = list(ses_probs.keys())
        ses_p = np.array([ses_probs[c] for c in ses_cats])
        ses_p = ses_p / ses_p.sum()
        ses_cum = np.cumsum(ses_p)
        ses_cum[-1] = 1.0  # Force last to 1.0 for robustness
        ses_idx = np.zeros(n, dtype=int)
        for i, threshold in enumerate(ses_cum):
            # We want to find the first index where u <= threshold
            # Since we iterate in order, the last one to be True wins if we use >
            # But the logic here is: set index if u <= threshold.
            # So we should iterate backwards or use a more direct method.
            pass

        # Better approach for categorical mapping from uniform
        ses_idx = np.digitize(u[:, 1], np.insert(ses_cum[:-1], 0, 0)) - 1
        data['ses'] = [ses_cats[i] for i in ses_idx]

        # Calculus: ~15% rate
        data['calculus'] = (u[:, 2] < 0.15).astype(int)

        # High Expectation
        exp_p = data['calculus'].map(exp_calc)
        data['high_expectation'] = (u[:, 3] < exp_p).astype(int)

        # Math Enjoyment
        enjoy_p = np.where(data['calculus'] == 1, 0.45, 0.20)
        data['math_enjoyment'] = (u[:, 4] < enjoy_p).astype(int)

        # STEM outcome
        stem_p = []
        for idx, row in data.iterrows():
            p = stem_calc.get(row['calculus'], 0.14)
            if row['math_enjoyment']:
                p += 0.15
            if row['high_expectation']:
                p += 0.05
            stem_p.append(min(p, 1.0))

        data['stem_prob'] = stem_p
        data['stem_major'] = (u[:, 5] < data['stem_prob']).astype(int)

        self.metadata['uncertainty_quantification'] = {
            'correlation_matrix': corr.tolist()
        }

        return data