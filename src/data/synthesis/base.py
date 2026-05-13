"""
Base Synthesizer Abstract Class

All synthesis methods must inherit from BaseSynthesizer and implement:
- fit_marginals(): Extract and validate NCES marginal distributions
- synthesize(): Generate synthetic microdata preserving marginals
"""

from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class BaseSynthesizer(ABC):
    """Abstract base class for all synthesis methods."""

    REQUIRED_COLUMNS = {
        'sex': 'object',       # 'Male' or 'Female'
        'ses': 'object',       # 'Lowest', 'Second', 'Third', 'Highest'
        'calculus': 'int64',   # 0 or 1
        'high_expectation': 'int64',  # 0 or 1
        'math_enjoyment': 'int64',    # 0 or 1
        'stem_prob': 'float64',       # probability between 0 and 1
        'stem_major': 'int64'         # 0 or 1
    }

    def __init__(self, n: int = 10000, seed: int = 42):
        """
        Initialize synthesizer.

        Parameters:
        - n: Number of synthetic records to generate
        - seed: Random seed for reproducibility
        """
        self.n = n
        self.seed = seed
        self.metadata: Dict[str, Any] = {
            'method_name': self.__class__.__name__,
            'parameters': {'n': n, 'seed': seed},
            'timestamp': datetime.now().isoformat(),
            'version': '1.0'
        }

    @abstractmethod
    def fit_marginals(self, nces_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract and validate marginal distributions from NCES data.

        Parameters:
        - nces_df: Tidy NCES data with columns:
            table_id, section_label, row_label, column_group,
            column_label, estimate, standard_error

        Returns:
        - marginals: Dictionary of extracted marginal distributions
        """
        pass

    @abstractmethod
    def synthesize(self, marginals: Dict[str, Any]) -> pd.DataFrame:
        """
        Generate synthetic microdata from fitted marginals.

        Parameters:
        - marginals: Marginal distributions from fit_marginals()

        Returns:
        - synthetic_df: DataFrame with 7 required columns
        """
        pass

    def validate_output_schema(self, df: pd.DataFrame) -> bool:
        """
        Ensure output DataFrame has required schema.

        Returns True if all columns exist with correct types.
        Raises ValueError otherwise.
        """
        missing_cols = set(self.REQUIRED_COLUMNS.keys()) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        for col, expected_type in self.REQUIRED_COLUMNS.items():
            actual_dtype = df[col].dtype.name
            # Allow flexible type matching
            if expected_type == 'object':
                if actual_dtype not in ['object', 'str', 'string']:
                    raise ValueError(f"Column '{col}' has type {actual_dtype}, expected {expected_type}")
            elif expected_type == 'int64':
                if actual_dtype not in ['int64', 'int32', 'int']:
                    raise ValueError(f"Column '{col}' has type {actual_dtype}, expected {expected_type}")
            elif expected_type == 'float64':
                if actual_dtype not in ['float64', 'float32', 'float']:
                    raise ValueError(f"Column '{col}' has type {actual_dtype}, expected {expected_type}")

        # Validate value ranges
        if not set(df['sex'].unique()).issubset({'Male', 'Female'}):
            raise ValueError("sex must be 'Male' or 'Female'")

        valid_ses = {'Lowest', 'Second', 'Third', 'Highest'}
        if not set(df['ses'].unique()).issubset(valid_ses):
            raise ValueError(f"ses must be in {valid_ses}")

        for binary_col in ['calculus', 'high_expectation', 'math_enjoyment', 'stem_major']:
            if not set(df[binary_col].unique()).issubset({0, 1}):
                raise ValueError(f"{binary_col} must be 0 or 1")

        if not (0 <= df['stem_prob'].min() and df['stem_prob'].max() <= 1):
            raise ValueError("stem_prob must be between 0 and 1")

        return True

    def save_metadata(self, output_path: Path) -> None:
        """
        Write method-specific metadata to JSON file.
        """
        import json

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def run(self, nces_df: pd.DataFrame) -> pd.DataFrame:
        """
        Full pipeline: fit marginals -> synthesize -> validate.

        Convenience method that combines fit_marginals and synthesize
        with automatic validation.
        """
        marginals = self.fit_marginals(nces_df)
        synthetic_df = self.synthesize(marginals)
        self.validate_output_schema(synthetic_df)

        # Add fidelity metrics to metadata
        self._compute_fidelity_metrics(synthetic_df, marginals)

        return synthetic_df

    def _compute_fidelity_metrics(self, synthetic_df: pd.DataFrame,
                                   marginals: Dict[str, Any]) -> None:
        """
        Compute marginal fidelity metrics (to be implemented by subclasses).

        Adds to self.metadata['fidelity_metrics']:
        - marginal_matching_error: MAE between synthetic and NCES marginals
        - joint_distribution_metrics: KL divergence, correlation preservation
        """
        # Base implementation: placeholder
        # Subclasses can override with specific metrics
        pass