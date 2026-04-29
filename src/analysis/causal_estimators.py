import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import LogisticRegression

class AIPWEstimator:
    """
    Augmented Inverse Probability Weighting (AIPW) Estimator.
    Provides double robustness: unbiased if either the propensity model
    or the outcome model is correctly specified.
    """

    def __init__(self, df, treatment, outcome, confounders):
        self.df = df.copy()
        self.treatment = treatment
        self.outcome = outcome
        self.confounders = confounders
        self.ps_model = None
        self.mu0_model = None
        self.mu1_model = None

    def fit(self):
        # 1. Estimate Propensity Score e(X)
        X = pd.get_dummies(self.df[self.confounders], drop_first=True)
        X = sm.add_constant(X.astype(float))

        self.ps_model = sm.Logit(self.df[self.treatment], X).fit(disp=0)
        self.df['ps'] = self.ps_model.predict(X)

        # 2. Estimate Outcome Models mu1(X) and mu0(X)
        # mu1: E(Y | T=1, X)
        df1 = self.df[self.df[self.treatment] == 1]
        X1 = pd.get_dummies(df1[self.confounders], drop_first=True)
        X1 = sm.add_constant(X1.astype(float))
        self.mu1_model = sm.OLS(df1[self.outcome], X1).fit()

        # mu0: E(Y | T=0, X)
        df0 = self.df[self.df[self.treatment] == 0]
        X0 = pd.get_dummies(df0[self.confounders], drop_first=True)
        X0 = sm.add_constant(X0.astype(float))
        self.mu0_model = sm.OLS(df0[self.outcome], X0).fit()

        # Predict counterfactuals for all rows
        X_all = pd.get_dummies(self.df[self.confounders], drop_first=True)
        X_all = sm.add_constant(X_all.astype(float))
        self.df['mu1'] = self.mu1_model.predict(X_all)
        self.df['mu0'] = self.mu0_model.predict(X_all)

        return self

    def estimate_ate(self):
        """
        Calculates the AIPW ATE using the formula:
        ATE = 1/n * sum( mu1(Xi) - mu0(Xi) + Ti(Yi - mu1(Xi))/e(Xi) - (1-Ti)(Yi - mu0(Xi))/(1-e(Xi)) )
        """
        if 'ps' not in self.df.columns:
            self.fit()

        y = self.df[self.outcome]
        t = self.df[self.treatment]
        ps = self.df['ps']
        mu1 = self.df['mu1']
        mu0 = self.df['mu0']

        # Trim PS to avoid division by zero (Overlap assumption)
        ps = np.clip(ps, 0.01, 0.99)

        term1 = mu1 - mu0
        term2 = t * (y - mu1) / ps
        term3 = (1 - t) * (y - mu0) / (1 - ps)

        individual_effects = term1 + term2 - term3
        ate = np.mean(individual_effects)
        se = np.std(individual_effects) / np.sqrt(len(self.df))

        return ate, se

    def compute_sensitivity(self, ate):
        """
        Calculates the Sensitivity of the ATE to unobserved confounders.
        """
        y_std = self.df[self.outcome].std()
        t_std = self.df[self.treatment].std()
        rv = ate / (y_std * t_std)
        return np.clip(rv, 0, 1)

    def get_balance_stats(self):
        """
        Calculates Standardized Mean Differences (SMD) before and after weighting.
        Weight for AIPW is 1/ps for T=1 and 1/(1-ps) for T=0.
        """
        if 'ps' not in self.df.columns:
            self.fit()

        X = pd.get_dummies(self.df[self.confounders], drop_first=True).astype(float)
        T = self.df[self.treatment]
        weights = np.where(T == 1, 1/self.df['ps'], 1/(1-self.df['ps']))

        balance_results = []
        for col in X.columns:
            # Unweighted SMD
            m1 = X.loc[T == 1, col].mean()
            m0 = X.loc[T == 0, col].mean()
            v1 = X.loc[T == 1, col].var()
            v0 = X.loc[T == 0, col].var()
            smd_unweighted = (m1 - m0) / np.sqrt((v1 + v0) / 2)

            # Weighted SMD (Simple implementation)
            def weighted_mean(x, w):
                return np.average(x, weights=w)
            def weighted_var(x, w):
                return np.average((x - weighted_mean(x, w))**2, weights=w)

            wm1 = weighted_mean(X.loc[T == 1, col], weights[T == 1])
            wm0 = weighted_mean(X.loc[T == 0, col], weights[T == 0])
            wv1 = weighted_var(X.loc[T == 1, col], weights[T == 1])
            wv0 = weighted_var(X.loc[T == 0, col], weights[T == 0])
            smd_weighted = (wm1 - wm0) / np.sqrt((wv1 + wv0) / 2)

            balance_results.append({
                'Variable': col,
                'Unweighted': smd_unweighted,
                'Weighted': smd_weighted
            })

        return pd.DataFrame(balance_results)

    def get_diagnostics(self):
        """Returns the internal dataframe with PS and counterfactuals for plotting."""
        return self.df

def run_oaxaca_decomposition(df, group_col, group_values, treatment, outcome, confounders):
    """
    Performs a simplified Oaxaca-Blinder decomposition.
    Decomposes the gap in STEM choice between two groups into:
    1. Explained (Endowments): Gap due to differences in math achievement/SES.
    2. Unexplained (Coefficients): Gap due to differences in how those factors translate to STEM.
    """
    g1_df = df[df[group_col] == group_values[0]]
    g2_df = df[df[group_col] == group_values[1]]

    cols = [treatment] + confounders
    def get_model(sub_df):
        X = pd.get_dummies(sub_df[cols], drop_first=True)
        X = sm.add_constant(X.astype(float))
        return sm.OLS(sub_df[outcome], X).fit()

    m1 = get_model(g1_df)
    m2 = get_model(g2_df)

    # Means of features
    x1_mean = sm.add_constant(pd.get_dummies(g1_df[cols], drop_first=True).astype(float)).mean()
    x2_mean = sm.add_constant(pd.get_dummies(g2_df[cols], drop_first=True).astype(float)).mean()

    # Gap = Y1_mean - Y2_mean
    y1_mean = g1_df[outcome].mean()
    y2_mean = g2_df[outcome].mean()
    total_gap = y1_mean - y2_mean

    # Decomposition (using Group 2 as the reference/counterfactual baseline)
    # Explained = (X1 - X2) * Beta2
    explained = np.dot((x1_mean - x2_mean), m2.params)
    # Unexplained = X1 * (Beta1 - Beta2)
    unexplained = np.dot(x1_mean, (m1.params - m2.params))

    return {
        'total_gap': total_gap,
        'explained_endowments': explained,
        'unexplained_coefficients': unexplained
    }

def run_mediation_analysis(df, treatment, mediator, outcome, confounders):
    """
    Simplified Causal Mediation Analysis.
    Decomposes ATE into:
    1. ACME (Average Causal Mediation Effect): Indirect effect through the mediator.
    2. ADE (Average Direct Effect): Effect of treatment not through the mediator.
    """
    # 1. Mediator Model: M ~ T + X
    X_m = pd.get_dummies(df[[treatment] + confounders], drop_first=True)
    X_m = sm.add_constant(X_m.astype(float))
    m_model = sm.OLS(df[mediator], X_m).fit()

    # 2. Outcome Model: Y ~ T + M + X
    X_y = pd.get_dummies(df[[treatment, mediator] + confounders], drop_first=True)
    X_y = sm.add_constant(X_y.astype(float))
    y_model = sm.OLS(df[outcome], X_y).fit()

    # Simple Product of Coefficients (for linear models)
    # ACME = beta_T_in_M_model * beta_M_in_Y_model
    beta_T_m = m_model.params[treatment]
    beta_M_y = y_model.params[mediator]
    acme = beta_T_m * beta_M_y

    # ADE = beta_T_in_Y_model
    ade = y_model.params[treatment]

    return {
        'acme': acme,
        'ade': ade,
        'total_effect': acme + ade,
        'proportion_mediated': acme / (acme + ade) if (acme+ade) != 0 else 0
    }

def simulate_policy_impact(learner, X_df, target_segment_mask, treatment_cost=0.05):
    """
    Simulates the impact of a targeted policy using an EconML learner.
    Calculates the Total Gain in STEM major probability for the target group.
    """
    # Estimate CATE for the whole population
    X_numeric = pd.get_dummies(X_df, drop_first=True).astype(float)
    cate = learner.effect(X_numeric)

    # Apply to target segment
    target_cate = cate[target_segment_mask]

    # Policy: Give treatment to those in target segment where CATE > cost
    treated_mask = target_cate > treatment_cost
    net_gain = np.sum(target_cate[treated_mask] - treatment_cost)
    gross_gain = np.sum(target_cate[treated_mask])

    return {
        'gross_stem_gain': gross_gain,
        'net_gain_after_cost': net_gain,
        'n_treated': np.sum(treated_mask),
        'avg_lift_in_treated': np.mean(target_cate[treated_mask]) if np.sum(treated_mask) > 0 else 0
    }

def run_baseline_ols(df, treatment, outcome, confounders):
    """Runs a simple OLS for comparison."""
    X = pd.get_dummies(df[[treatment] + confounders], drop_first=True)
    X = sm.add_constant(X.astype(float))
    model = sm.OLS(df[outcome], X).fit()
    print(model.summary())
    return model.params[treatment], model.bse[treatment]
