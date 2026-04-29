from __future__ import annotations

import pandas as pd


def get_math_achievement_major_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts rows specifically mapping math achievement (quartiles/courses) to major choice.
    """
    # Table 1: Achievement Quartiles
    # Table 2, 10: Highest Math Course
    target_tables = ["1", "2", "10"]
    mask = df["table_id"].isin(target_tables)

    # Filter for total major percentages (avoiding detailed subgroups for primary analysis)
    major_total_mask = df["column_label"] == "Total"

    return df[mask & major_total_mask].copy()


def get_confounders(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts potential confounders (SES, Sex, Race) from relevant tables.
    """
    confounder_sections = [
        "Sex",
        "Race/ethnicity1",
        "Family socio-economic status",
        "Native language2"
    ]
    return df[df["section_label"].isin(confounder_sections)].copy()


def calculate_stem_prob(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates STEM vs Non-STEM probabilities.
    """
    stem_groups = ["STEM major", "STEM major in 2006"]
    df = df.copy()
    df["is_stem"] = df["column_group"].isin(stem_groups)
    return df
