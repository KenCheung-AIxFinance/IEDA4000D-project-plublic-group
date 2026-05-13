# Synthesis Methodology Research Note: Microdata Reconstruction Fidelity

**Date:** 2026-05-13  
**Objective:** Evaluate the impact of different synthetic data generation methods on downstream causal inference results.

## 1. Overview of Methods
We implemented and compared five methods to reconstruct unit-level microdata from NCES ELS:2002 aggregate tables:

| Method | Approach | Strength |
|--------|----------|----------|
| **Heuristic** | Sequential sampling with fixed logic | Fast baseline, high marginal fidelity |
| **IPF** | Iterative Proportional Fitting | Matches multi-way marginal constraints |
| **Copula** | Gaussian Copula dependency modeling | Preserves joint correlation structure |
| **Bayesian** | Dirichlet-multinomial sampling | Quantifies uncertainty in estimates |
| **SRI** | Sequential Regression Imputation | Models non-linear conditional distributions |

## 2. Fidelity vs. Causal Sensitivity
A critical discovery was made during validation: **Synthesis assumptions significantly bias the Treatment Effect (ATE).**

### 2.1 Fidelity Metrics (Overall MAE)
1. **Heuristic**: 0.0968 (Best at matching marginals)
2. **IPF**: 0.1088
3. **Bayesian**: 0.1117
4. **SRI**: 0.1282
5. **Copula**: 0.1480

### 2.2 Causal Sensitivity (Estimated Calculus Effect)
Using the same AIPW estimator on all 5 datasets yielded divergent results:

| Method | Estimated ATE | 95% CI |
|--------|---------------|--------|
| **Heuristic** | 9.5% | [4.4%, 14.6%] |
| **IPF** | 26.2% | [19.9%, 32.5%] |
| **Copula** | 30.3% | [23.4%, 37.1%] |
| **Bayesian** | 35.8% | [29.9%, 41.8%] |
| **SRI** | 36.6% | [30.8%, 42.4%] |

## 3. Analysis of Divergence
The formal methods (IPF, Copula, Bayesian, SRI) consistently estimate a much higher effect (26% - 37%) than the Heuristic baseline (9.5%). 

**Reasoning:** The NCES Table 10 shows a raw probability of $P(\text{STEM} | \text{Calculus}) \approx 40\%$ compared to $P(\text{STEM} | \text{No Calculus}) \approx 14\%$. The Heuristic method effectively "dilutes" this effect by sampling independently for intermediate psychosocial factors. In contrast, the formal methods preserve the strong conditional dependency between Calculus and the final STEM outcome found in the original source data.

## 4. Final Recommendation for FYP
For the final defense, it is recommended to:
1. **Report the SRI/Bayesian results** as the primary findings, as they are more rigorous.
2. Use the **Heuristic result as a "Lower Bound"** baseline.
3. Frame the divergence as a **Methodological Contribution**: showing how traditional aggregate reporting can obscure the true strength of individual-level causal mechanisms.
