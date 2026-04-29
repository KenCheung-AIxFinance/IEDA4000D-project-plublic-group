# Identification notes

## Desired causal story
We want to study whether stronger high school math achievement increases the probability that a student chooses a STEM major.

## Baseline design
Start from an observational-study design with adjustment for confounders.

Potential first methods:
- outcome regression
- propensity score weighting / stratification
- AIPW as robustness check

## Assumptions we would need for a causal claim
- conditional ignorability after observed adjustment
- overlap / positivity
- consistent measurement of treatment proxy and STEM outcome
- no severe model misspecification

## Current feasibility concern
The current Excel files appear to be aggregated tables. Aggregated percentages are useful for project setup and descriptive evidence, but may be insufficient for defensible unit-level causal estimation.

## Immediate next check
Map which tables contain:
1. a usable proxy for math achievement or preparedness
2. a usable STEM-major outcome
3. enough conditioning variables to support an observational argument
