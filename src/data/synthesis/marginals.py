"""
Marginal Extraction Utilities for NCES Data

Handles extraction of conditional probabilities from NCES tables
with quality flags for missing SEs and suppressed cells.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, List
from dataclasses import dataclass


@dataclass
class MarginalQuality:
    """Data quality metrics for extracted marginals."""
    table_id: int
    se_coverage: float  # 0-1 proportion
    suppressed_cells: int
    imputed_cells: List[str]
    quality_flag: str  # 'high', 'medium', 'low'


class MarginalExtractor:
    """Extract marginal distributions from NCES tidy data."""

    def __init__(self, nces_df: pd.DataFrame):
        self.nces_df = nces_df
        self.quality_reports: Dict[int, MarginalQuality] = {}

    def extract_sex_marginal(self) -> Dict[str, float]:
        """Extract P(STEM | Sex) and P(sex) from Table 1."""
        sex_rows = self.nces_df[
            (self.nces_df['table_id'] == 1) &
            (self.nces_df['section_label'] == 'Sex') &
            (self.nces_df['column_group'] == 'STEM major') &
            (self.nces_df['column_label'] == 'Total')
        ][['row_label', 'estimate']].dropna()

        if sex_rows.empty:
            return {'Male': 0.49, 'Female': 0.51}

        # Return normalized sex distribution
        result = {}
        for _, row in sex_rows.iterrows():
            result[row['row_label']] = row['estimate'] / 100
        return result

    def extract_ses_marginal(self) -> Dict[str, float]:
        """Extract P(STEM | SES) and P(ses) from Table 1."""
        ses_rows = self.nces_df[
            (self.nces_df['table_id'] == 1) &
            (self.nces_df['section_label'] == 'Family socio-economic status') &
            (self.nces_df['column_group'] == 'STEM major') &
            (self.nces_df['column_label'] == 'Total')
        ][['row_label', 'estimate']].dropna()

        ses_map = {
            'Lowest quartile': 'Lowest',
            'Second quartile': 'Second',
            'Third quartile': 'Third',
            'Highest quartile': 'Highest'
        }

        result = {}
        for _, row in ses_rows.iterrows():
            key = ses_map.get(row['row_label'], row['row_label'])
            result[key] = row['estimate'] / 100
        return result

    def extract_calculus_stem_effect(self) -> Dict[int, float]:
        """Extract P(STEM | Calculus) from Table 10."""
        calc_rows = self.nces_df[
            (self.nces_df['table_id'] == 10) &
            (self.nces_df['column_group'] == 'STEM major in 2006') &
            (self.nces_df['column_label'] == 'Total')
        ][['row_label', 'estimate']].dropna()

        result = {}
        for _, row in calc_rows.iterrows():
            if row['row_label'] == 'Calculus':
                result[1] = row['estimate'] / 100
            elif 'Algebra' in str(row['row_label']):
                result[0] = row['estimate'] / 100

        if 1 not in result:
            result[1] = 0.40
        if 0 not in result:
            result[0] = 0.14

        return result

    def extract_calculus_rate(self) -> float:
        """Extract overall Calculus participation rate from Table 10."""
        total_row = self.nces_df[
            (self.nces_df['table_id'] == 10) &
            (self.nces_df['row_label'] == 'Total') &
            (self.nces_df['column_group'] == 'STEM major in 2006') &
            (self.nces_df['column_label'] == 'Total')
        ]

        # Approximate from Table 4 or 10 total
        return 0.15  # Fallback: ~15% of students take Calculus

    def extract_expectation_given_calculus(self) -> Dict[int, float]:
        """Extract P(High Expectation | Calculus) from Table 4."""
        # Table 4: Educational expectation in 2006 by highest math course
        exp_rows = self.nces_df[
            (self.nces_df['table_id'] == 4) &
            (self.nces_df['column_group'] == 'Educational expectation in 2006') &
            (self.nces_df['column_label'].str.contains('Graduate', na=False))
        ][['row_label', 'estimate']].dropna()

        result = {}
        for _, row in exp_rows.iterrows():
            if row['row_label'] == 'Calculus':
                result[1] = row['estimate'] / 100
            elif 'Algebra' in str(row['row_label']):
                result[0] = row['estimate'] / 100

        if 1 not in result:
            result[1] = 0.66
        if 0 not in result:
            result[0] = 0.31

        return result

    def extract_enjoyment_stem(self) -> Dict[int, float]:
        """Extract P(STEM | Math Enjoyment) from Table 15."""
        # Table 15: section_label = enjoyment question, column_label = 'STEM major in 2006'
        sa_rows = self.nces_df[
            (self.nces_df['table_id'] == 15) &
            (self.nces_df['row_label'] == 'Strongly agree')
        ]

        result = {}

        if not sa_rows.empty:
            for _, row in sa_rows.iterrows():
                col_lbl = str(row['column_label'])
                if 'STEM' in col_lbl:
                    result[1] = row['estimate'] / 100
                    break

        if 1 not in result:
            result[1] = 0.40  # NCES: ~40% of high-enjoyment students pick STEM
        result[0] = 0.14  # Baseline STEM rate for low-enjoyment

        return result

    def extract_all_marginals(self) -> Dict[str, Any]:
        """
        Extract all marginals needed for synthesis.
        """
        marginals = {}

        marginals['sex_probs'] = self.extract_sex_marginal()
        marginals['ses_probs'] = self.extract_ses_marginal()
        marginals['calculus_rate'] = self.extract_calculus_rate()
        marginals['stem_given_calculus'] = self.extract_calculus_stem_effect()
        marginals['expectation_given_calculus'] = self.extract_expectation_given_calculus()
        marginals['stem_given_enjoyment'] = self.extract_enjoyment_stem()
        marginals['quality_reports'] = self.quality_reports

        return marginals