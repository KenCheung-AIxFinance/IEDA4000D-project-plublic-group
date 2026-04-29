import pandas as pd
import numpy as np
from pathlib import Path

def synthesize_data(n=10000, seed=42):
    np.random.seed(seed)
    project_root = Path('.').resolve()
    df = pd.read_csv(project_root / 'outputs' / 'tables' / 'nces_postsecondary_tidy.csv')

    # --- 1. Extract Marginals ---
    def get_marginal(table_id, section_label, col_group='STEM major', col_label='Total'):
        mask = (df['table_id'] == str(table_id)) & \
               (df['section_label'] == section_label) & \
               (df['column_group'] == col_group) & \
               (df['column_label'] == col_label)
        return df[mask][['row_label', 'estimate']].copy()

    # Probability of STEM given Characteristic (Table 1)
    # Note: Table 1 column 'STEM major' / 'Total' is the percentage of that group in STEM
    prob_sex = get_marginal(1, 'Sex')
    prob_ses = get_marginal(1, 'Family socio-economic status')
    prob_race = get_marginal(1, 'Race/ethnicity1')

    # Probability of STEM given Course (Table 10)
    # Table 10: Row is course, Col is STEM major
    prob_course = df[(df['table_id'] == '10') &
                     (df['column_group'] == 'STEM major in 2006') &
                     (df['column_label'] == 'Total')][['row_label', 'estimate']]

    # Probability of Expectations given Course (Table 4)
    # This captures the "Ambition" confounder
    prob_exp = df[(df['table_id'] == '4') &
                  (df['column_group'] == 'Educational expectation in 2006')][['section_label', 'row_label', 'column_label', 'estimate']]

    # --- 2. Initialize Synthetic Dataset ---
    data = pd.DataFrame(index=range(n))

    # A. Assign Sex (Roughly 50/50 based on NCES norms)
    data['sex'] = np.random.choice(['Male', 'Female'], size=n, p=[0.49, 0.51])

    # B. Assign SES (Uniform quartiles)
    data['ses'] = np.random.choice(['Lowest', 'Second', 'Third', 'Highest'], size=n)

    # C. Assign Math Treatment (Calculus)
    # Overall Calculus rate is ~14.6% in Table 10 total row
    # We add SES bias: Higher SES -> Higher Calculus probability
    ses_map = {'Lowest': 0.05, 'Second': 0.10, 'Third': 0.15, 'Highest': 0.30}
    data['calculus'] = data['ses'].apply(lambda s: np.random.random() < ses_map[s]).astype(int)

    # D. Assign Expectations (based on Table 4)
    # Simplify to binary: High Expectation (Graduate/Professional)
    # Table 4: Calculus takers -> 66% High Expectation
    # Algebra II takers -> 31% High Expectation
    def assign_expectation(is_calc):
        p = 0.66 if is_calc else 0.31
        return 1 if np.random.random() < p else 0
    data['high_expectation'] = data['calculus'].apply(assign_expectation)

    # NEW: E. Assign Math Enjoyment (based on Table 15)
    # Viewpoint: Calculus takers are more likely to enjoy math (Selection into Treatment)
    # Table 15: ~40% of those who "Strongly Agree" math is fun end up in STEM.
    def assign_enjoyment(is_calc, ses):
        # Base probability of high enjoyment
        p = 0.45 if is_calc else 0.20
        # Add SES boost (cultural capital)
        if ses == 'Highest': p += 0.1
        return 1 if np.random.random() < p else 0
    data['math_enjoyment'] = data.apply(lambda row: assign_enjoyment(row['calculus'], row['ses']), axis=1)

    # F. Assign STEM Outcome
    # Map sex effect (Male: ~25%, Female: ~8% from Table 1)
    sex_p = {'Male': 0.25, 'Female': 0.08}
    ses_p = {'Highest': 0.22, 'Third': 0.18, 'Second': 0.14, 'Lowest': 0.10}
    calc_p = {1: 0.40, 0: 0.14}

    def get_stem_prob(row):
        # 1. Base probability from demographics and treatment
        p = (sex_p[row['sex']] + ses_p[row['ses']] + calc_p[row['calculus']]) / 3

        # 2. Add Psychosocial Boosts
        # Math Enjoyment is a massive predictor (~40% probability in Table 15)
        if row['math_enjoyment']:
            p += 0.15  # The "Passion" premium

        # Educational Ambition
        if row['high_expectation']:
            p += 0.05  # The "Ambition" premium

        return np.clip(p, 0, 1)

    data['stem_prob'] = data.apply(get_stem_prob, axis=1)
    data['stem_major'] = (np.random.random(n) < data['stem_prob']).astype(int)

    # Save output
    output_path = project_root / 'outputs' / 'tables' / 'synthetic_students.csv'
    data.to_csv(output_path, index=False)
    print(f"Generated {n} synthetic student records at {output_path}")

if __name__ == "__main__":
    synthesize_data()
