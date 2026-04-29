# Final Research Outline: The "Calculus Dividend" Causal Project

This outline reflects the final implemented analytical pipeline used to estimate the impact of high school math achievement on STEM major choice.

## 1. Introduction and Motivation
*   **The STEM Gap**: Why major choice is a critical driver of economic mobility.
*   **The Calculus Hypothesis**: Is advanced math a gatekeeper or a ladder?
*   **Research Question**: Does completing Calculus causally increase STEM probability after adjusting for ambition, interest, and socio-economic status?

## 2. Data & Methodology: The Synthesis Bridge
*   **Source**: NCES ELS:2002 Postsecondary Longitudinal Tables.
*   **Weighted Microdata Synthesis**: Technical approach to reconstructing $N=10,000$ unit-level records from aggregated marginal distributions and standard errors.
*   **Variable Buckets**: Demographic (Sex, Race), Background (SES), Psychosocial (Enjoyment, Efficacy), and Ambition (Expectations).

## 3. Causal Identification Strategy
*   **Estimator**: **Augmented Inverse Probability Weighting (AIPW)** for double-robust estimation.
*   **Assumptions**: Unconfoundedness (CIA) and Common Support (Overlap).
*   **Diagnostic Verification**: Overlap plots and Standardized Mean Difference (SMD) balance tests (Love Plot).

## 4. Advanced Heterogeneity & Meta-Learners
*   **Beyond ATE**: Estimating Conditional Average Treatment Effects (CATE).
*   **Machine Learning Integration**: Using **X-Learner** and **DR-Learner** (EconML) to handle unbalanced treatment groups and identify high-impact sub-segments.

## 5. Mechanism Analysis & Decomposition
*   **Oaxaca-Blinder Decomposition**: Separating the STEM gender gap into "Academic Endowments" vs. "Structural Coefficients."
*   **Causal Mediation Analysis**: Quantifying the indirect effect of Calculus through the enhancement of Math Enjoyment.

## 6. Robustness & Policy Simulation
*   **Sensitivity Analysis**: Quantitative bounding of unobserved confounding using **Robustness Values (RV)**.
*   **Counterfactual Policy Simulation**: Predicting the real-world STEM lift from targeted Calculus initiatives for Low-SES students.

## 7. Conclusions & Policy Implications
*   **The Equalizer Effect**: Evidence that Calculus is most impactful for disadvantaged students.
*   **The Structural Barrier**: Findings from the gender gap decomposition.
*   **Summary Claim**: A robust, double-checked causal estimate of the 6.3% "Calculus Dividend."
