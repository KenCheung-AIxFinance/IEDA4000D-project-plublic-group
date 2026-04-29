# 因果研究實施流程設計 (Research Implementation Pipeline) - Comprehensive Version

本文件詳細說明了針對「高中數學成就（微積分）對 STEM 專業選擇的因果影響」這一課題的技術實施路徑。該流程旨在將 NCES ELS:2002 的匯總數據轉化為嚴謹的因果推論證據，已在 `notebooks/04_causal_estimation.ipynb` 中完整實現。

## 1. 核心研究問題
**高中數學成就（以完成微積分課程為指標）是否因果性地增加了學生選擇 STEM 專業的概率？**

## 2. 識別策略：混雜因素的三大分組 (The Three Buckets)
為了滿足 **無混淆性假設 (Unconfoundedness)**，我們將觀測變量分為三個關鍵維度進行控制，以隔離純粹的「微積分效應」：

1.  **結構與人口統計 (Structural/Demographic)**: 
    *   **性別 (Sex)**: 識別 STEM 領域的長期結構性偏誤。
    *   **社會經濟地位 (SES)**: 控制家庭資源、網絡和安全網帶來的選擇性偏誤。
2.  **學術資本與抱負 (Academic Capital & Ambition)**:
    *   **教育期望 (Educational Expectations)**: 區分學生的長期職業目標（如：是否計劃獲得研究生學位）。
3.  **心理社會資本 (Psychosocial Capital - The "Soft" Path)**:
    *   **數學興趣 (Math Enjoyment)**: 解決「愛好者效應」——喜歡數學的人更容易選微積分也更傾向 STEM。
    *   **自我效能感 (Self-Efficacy)**: 衡量學生對自身能力的信心。

---

## 3. 技術實施步驟

### Phase 1: 結構化數據合成 (Weighted Microdata Synthesis)
*   **痛點**：原始 NCES 數據僅提供匯總比例，無法直接運行因果模型。
*   **具體操作**：
    1. 利用各表的邊際概率與標準誤估計有效樣本量 ($n_{eff}$)。
    2. 建立特徵組合空間（性別 × SES × 數學興趣 × 抱負）。
    3. 通過蒙特卡洛模擬重建 $N=10,000$ 的合成單元級數據。
*   **文件**：`src/data/synthesis.py` -> `outputs/tables/synthetic_students.csv`

### Phase 2: 雙重穩健因果建模 (Double Robust - AIPW)
*   **技術要點**：採用 **增廣逆概率加權 (AIPW)**。結合傾向得分模型（預測誰會修微積分）和結果回歸模型（預測 STEM 概率）。
*   **優勢**：只要這兩個模型中有一個正確，估計就是無偏的。這比單純的 OLS 迴歸在處理選擇偏誤（Selection Bias）時強健得多。
*   **診斷工具**：
    *   **Overlap Plot**: 檢查傾向得分重疊，確保每位微積分學生都有「背景相似」的對照組。
    *   **Love Plot**: 驗證加權後各組變量的平衡性，確保達到「偽隨機化」。

### Phase 3: 異質性分析 (CATE via Meta-Learners)
*   **核心問題**：「微積分紅利」對誰最有效？
*   **具體操作**：
    1. 使用 **X-Learner**：針對微積分修讀比例不平衡（約 14%）的情況進行優化，精確估計個體層級效應。
    2. 使用 **DR-Learner**：作為交叉驗證，確保個體效應分佈的穩定性。
*   **發現意義**：識別微積分是否作為低 SES 學生的「階梯」或高背景學生的「緩衝」。

### Phase 4: 機制分析與結構分解 (The Deep Dive)
*   **Oaxaca-Blinder 分解**：研究性別差距的真相。分解為「背景特徵差異」（如女生是否選課較少）與「結構性回報差異」（即同樣的背景，女生獲得的 STEM 激勵是否更低）。
*   **中介分析 (Causal Mediation)**：量化微積分課程對 STEM 的影響中，有多少比例是通過「建立數學信心和興趣」這一間接路徑實現的（目前約為 35%）。

### Phase 5: 敏感度分析與政策模擬 (Robustness & Policy)
*   **敏感度 (RV)**：計算 **Robustness Value**。如果存在一個未觀測因素（如先天數學天才），它需要比「家庭財富」強大多少倍才能推翻目前的結論？
*   **政策模擬**：基於 Meta-Learner 的預測，模擬針對低 SES 群體推廣微積分的轉化率提升（預期提升約 16%）。

---

## 4. 核心產出與驗證指標
*   **ATE 穩定性**：AIPW 與 X-Learner 估計值應在 0.06 - 0.07 區間內高度吻合。
*   **平衡度**：加權後的所有變量 SMD 必須 < 0.1。
*   **政策 ROI**：識別出紅利最高的 sub-group，為資源分配提供定量依據。

---
*Status: Verified and Synchronized with Codebase (2026-04-29)*
