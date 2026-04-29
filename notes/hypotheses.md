# Hypotheses to Verify (待印證觀點)

Based on the comprehensive EDA of NCES ELS:2002 tables, the following viewpoints are identified as critical for formal causal verification:

## 1. The Interest-Achievement Duality (興趣與成就的雙重性)
- **Viewpoint:** High school math achievement (Calculus completion) and Math Enjoyment show nearly identical predictive power (~40% STEM probability).
- **Hypothesis to Verify:** Is the "Calculus effect" independent, or is it entirely mediated by student interest? 
- **Verification Method:** Control for Math Enjoyment (`table_15`) when estimating the effect of Calculus (`table_10`).

## 2. Specificity of Math Self-Efficacy (數學自我效能的特異性)
- **Viewpoint:** The "Self-efficacy ladder" (linear increase in STEM probability with confidence) exists only for STEM majors, not for Non-STEM.
- **Hypothesis to Verify:** High math self-efficacy is a specific driver of STEM choice, not just a general marker of high-performing students.
- **Verification Method:** Compare the coefficient of math confidence across different major outcomes (STEM vs Business vs Humanities).

## 3. The "Ambition" Confounder (學術野心的混雜效應)
- **Viewpoint:** Calculus takers are disproportionately likely to expect graduate-level degrees (66% vs 31% for Algebra II).
- **Hypothesis to Verify:** A significant portion of the "Calculus Premium" is actually an "Ambition Premium."
- **Verification Method:** Use Educational Expectations (`table_4`) as a key control variable or perform stratified analysis by expectation level.

## 4. Residual Gender Gap (性別差距的殘差)
- **Viewpoint:** Even in the highest math achievement quartiles and among those who enjoy math, a significant gender gap remains.
- **Hypothesis to Verify:** Increasing math achievement alone will not close the STEM gender gap if cultural/structural factors are not addressed.
- **Verification Method:** Estimate the "Gender effect" while holding Math Achievement and Math Enjoyment constant (Oaxaca-Blinder decomposition or simple regression).

## 5. Early Path Fixation (早期路徑固定)
- **Viewpoint:** Intended major in 12th grade (`table_1`) is a very strong predictor of declared major in college (`table_10`).
- **Hypothesis to Verify:** The "treatment window" for math achievement to influence STEM choice largely closes by the end of high school.
- **Verification Method:** Analyze the transition probability from "Intended STEM" to "Declared STEM" versus "Intended Non-STEM" to "Declared STEM" under different achievement levels.
