"""
Synthesis Package for Multi-Method Microdata Generation

This package implements 5 formal methods for reconstructing individual-level data
from NCES aggregate tables:
- heuristic: Manual sequential conditional probability (baseline)
- ipf: Iterative Proportional Fitting
- copula: Gaussian Copula via scipy
- bayesian_bootstrap: Bayesian Bootstrap with Dirichlet sampling
- sri: Sequential Regression Imputation with lightgbm
"""

from .base import BaseSynthesizer
from .heuristic import HeuristicSynthesizer
from .ipf import IPFSynthesizer
from .bayesian_bootstrap import BayesianBootstrapSynthesizer
from .copula import CopulaSynthesizer
from .sri import SRISynthesizer
from .marginals import MarginalExtractor

__all__ = [
    'BaseSynthesizer',
    'HeuristicSynthesizer',
    'IPFSynthesizer',
    'BayesianBootstrapSynthesizer',
    'CopulaSynthesizer',
    'SRISynthesizer',
    'MarginalExtractor'
]

METHOD_MAP = {
    'heuristic': HeuristicSynthesizer,
    'ipf': IPFSynthesizer,
    'copula': CopulaSynthesizer,
    'bayesian': BayesianBootstrapSynthesizer,
    'sri': SRISynthesizer
}