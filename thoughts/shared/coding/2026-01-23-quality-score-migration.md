# qualityScore 六維度遷移開發總結

**日期**：2026-01-23
**任務**：將 23 個 skill.yaml 從舊版六維度遷移到新版六維度

---

## 遷移概覽

### 維度對照

| 舊維度          | 新維度          | 評估重點                                          |
|-----------------|-----------------|---------------------------------------------------|
| architecture    | problemFit      | SKILL.md 目標 + workflows/ 覆蓋 + input-schema.md |
| content         | correctness     | methodology.md + scripts 吻合 + examples          |
| security        | dataGovernance  | data-sources.md + fetch scripts + cross-validate  |
| compliance      | robustness      | failure-modes.md + 降級策略 + 錯誤處理            |
| maintainability | maintainability | 版本管理 + 模板穩定 + 無文件漂移                  |
| community       | usability       | TL;DR + 依據 + 風險 + 歷史對照                    |

### Badge 對照

| Badge | 分數範圍 |
|-------|----------|
| 白金  | 90-100   |
| 黃金  | 80-89    |
| 白銀  | 60-79    |
| 青銅  | 40-59    |
| 入門  | 0-39     |

---

## 遷移結果總覽

### 全部 23 個 Skills 更新結果

| Skill                                                              | Overall | Badge | 批次 |
|--------------------------------------------------------------------|---------|-------|------|
| compute-precious-miner-gross-margin                                | 82      | 黃金  | 1    |
| detect-shanghai-silver-stock-drain                                 | 80      | 黃金  | 1    |
| analyze-japan-debt-service-tax-burden                              | 78      | 白銀  | 2    |
| analyze-copper-stock-resilience-dependency                         | 78      | 白銀  | 2    |
| zeberg-salomon-rotator                                             | 76      | 白銀  | 2    |
| analyze-high-unemployment-high-gdp-growth-fiscal-deficit-scenarios | 75      | 白銀  | 2    |
| monitor-etf-holdings-drawdown-risk                                 | 73      | 白銀  | 2    |
| nickel-concentration-risk-analyzer                                 | 73      | 白銀  | 2    |
| analyze-investment-clock-rotation                                  | 71      | 白銀  | 3    |
| detect-atr-squeeze-regime                                          | 69      | 白銀  | 3    |
| analyze-silver-miner-metal-ratio                                   | 69      | 白銀  | 3    |
| lithium-supply-demand-gap-radar                                    | 68      | 白銀  | 3    |
| detect-us-equity-valuation-percentile-extreme                      | 67      | 白銀  | 3    |
| backsolve-miner-vs-metal-ratio-with-fundamentals                   | 66      | 白銀  | 3    |
| demographic-fiscal-trap-analyzer                                   | 65      | 白銀  | 4    |
| evaluate-exponential-trend-deviation-regimes                       | 63      | 白銀  | 4    |
| usd-reserve-loss-gold-revaluation                                  | 62      | 白銀  | 4    |
| detect-palladium-lead-silver-turns                                 | 60      | 白銀  | 4    |
| us-cpi-pce-comparator                                              | 57      | 青銅  | 5    |
| google-trends-ath-detector                                         | 49      | 青銅  | 5    |
| wasde-ingestor                                                     | 44      | 青銅  | 5    |
| list-china-today-macro-news                                        | 42      | 青銅  | 5    |
| cost-density-net-rr-calculator                                     | 37      | 入門  | 5    |

### Badge 分佈統計

| Badge    | 數量   | 佔比     |
|----------|--------|----------|
| 黃金     | 2      | 8.7%     |
| 白銀     | 16     | 69.6%    |
| 青銅     | 4      | 17.4%    |
| 入門     | 1      | 4.3%     |
| **總計** | **23** | **100%** |

---

## 批次處理詳情

### 批次 1：黃金候選（2 個）

| Skill                               | Overall | problemFit | correctness | dataGovernance | robustness | maintainability | usability |
|-------------------------------------|---------|------------|-------------|----------------|------------|-----------------|-----------|
| compute-precious-miner-gross-margin | 82      | 88         | 85          | 80             | 78         | 82              | 79        |
| detect-shanghai-silver-stock-drain  | 80      | 85         | 82          | 78             | 75         | 80              | 80        |

### 批次 2：高白銀（6 個）

| Skill                                                              | Overall | problemFit | correctness | dataGovernance | robustness | maintainability | usability |
|--------------------------------------------------------------------|---------|------------|-------------|----------------|------------|-----------------|-----------|
| analyze-japan-debt-service-tax-burden                              | 78      | 82         | 80          | 78             | 72         | 78              | 78        |
| analyze-copper-stock-resilience-dependency                         | 78      | 80         | 78          | 78             | 75         | 78              | 79        |
| zeberg-salomon-rotator                                             | 76      | 80         | 78          | 72             | 72         | 76              | 78        |
| analyze-high-unemployment-high-gdp-growth-fiscal-deficit-scenarios | 75      | 78         | 76          | 75             | 72         | 75              | 74        |
| monitor-etf-holdings-drawdown-risk                                 | 73      | 78         | 75          | 72             | 68         | 72              | 73        |
| nickel-concentration-risk-analyzer                                 | 73      | 75         | 75          | 72             | 70         | 72              | 74        |

### 批次 3：中白銀（6 個）

| Skill                                            | Overall | problemFit | correctness | dataGovernance | robustness | maintainability | usability |
|--------------------------------------------------|---------|------------|-------------|----------------|------------|-----------------|-----------|
| analyze-investment-clock-rotation                | 71      | 75         | 72          | 70             | 68         | 70              | 71        |
| detect-atr-squeeze-regime                        | 69      | 72         | 70          | 68             | 65         | 70              | 69        |
| analyze-silver-miner-metal-ratio                 | 69      | 72         | 70          | 68             | 66         | 70              | 68        |
| lithium-supply-demand-gap-radar                  | 68      | 72         | 68          | 68             | 65         | 68              | 67        |
| detect-us-equity-valuation-percentile-extreme    | 67      | 70         | 68          | 68             | 62         | 68              | 66        |
| backsolve-miner-vs-metal-ratio-with-fundamentals | 66      | 70         | 68          | 65             | 62         | 66              | 65        |

### 批次 4：低白銀（4 個）

| Skill                                        | Overall | problemFit | correctness | dataGovernance | robustness | maintainability | usability |
|----------------------------------------------|---------|------------|-------------|----------------|------------|-----------------|-----------|
| demographic-fiscal-trap-analyzer             | 65      | 70         | 68          | 62             | 60         | 65              | 65        |
| evaluate-exponential-trend-deviation-regimes | 63      | 68         | 65          | 62             | 58         | 65              | 60        |
| usd-reserve-loss-gold-revaluation            | 62      | 68         | 65          | 60             | 58         | 62              | 59        |
| detect-palladium-lead-silver-turns           | 60      | 65         | 62          | 60             | 55         | 62              | 56        |

### 批次 5：青銅/入門（5 個）

| Skill                          | Overall | problemFit | correctness | dataGovernance | robustness | maintainability | usability |
|--------------------------------|---------|------------|-------------|----------------|------------|-----------------|-----------|
| us-cpi-pce-comparator          | 57      | 65         | 60          | 55             | 50         | 55              | 57        |
| google-trends-ath-detector     | 49      | 60         | 50          | 40             | 42         | 50              | 52        |
| wasde-ingestor                 | 44      | 55         | 45          | 42             | 38         | 45              | 39        |
| list-china-today-macro-news    | 42      | 50         | 45          | 38             | 35         | 45              | 39        |
| cost-density-net-rr-calculator | 37      | 50         | 40          | 30             | 32         | 38              | 32        |

---

## 新 qualityScore 結構

每個 skill.yaml 已更新為以下結構：

```yaml
qualityScore:
  overall: 75                    # 六維度平均
  badge: 白銀                    # 白金/黃金/白銀/青銅/入門
  evaluatedAt: "2026-01-23"

  metrics:
    problemFit: 80               # 任務適配度
    correctness: 78              # 正確性
    dataGovernance: 72           # 資料治理
    robustness: 68               # 穩健性
    maintainability: 75          # 可維護性
    usability: 77                # 輸出可用性

  metricDetails:
    problemFit:
      score: 80
      strengths:
        - [優點列表]
      improvements:
        - [改進建議列表]
    # ... 其他五個維度

  details: |
    **任務適配度（80/100）**
    - 優點與待改進說明
    # ... 其他維度說明

  upgradeNotes:
    targetBadge: 黃金
    requirements:
      - metric: dataGovernance
        currentScore: 72
        targetScore: 75
        suggestion: 改進建議
```

---

## 常見改進建議

### 高分 Skills（黃金/高白銀）常見優點

1. **problemFit**：SKILL.md 目標清晰、workflows 覆蓋完整
2. **correctness**：methodology.md 有完整公式、examples 有實際輸出
3. **dataGovernance**：data-sources.md 完整、有 fallback 來源
4. **robustness**：failure-modes.md 完整、有降級機制
5. **maintainability**：manifest.json 有版本控制、參數集中管理
6. **usability**：output-markdown.md 有 TL;DR、有歷史對照

### 低分 Skills（青銅/入門）常見問題

1. **problemFit**：Alpha 階段功能未完善
2. **correctness**：testQuestions 的 expectedResult 過於簡略
3. **dataGovernance**：缺少 data-sources.md、數據來源不穩定
4. **robustness**：缺少 failure-modes.md、錯誤處理不完整
5. **maintainability**：缺少版本控制、腳本實作不完整
6. **usability**：缺少實際使用範例、執行環境需求高

---

## 升級路徑統計

### 青銅 → 白銀 升級要求（4 個 Skills）

| Skill                       | 主要升級要求                       |
|-----------------------------|------------------------------------|
| us-cpi-pce-comparator       | correctness +10, robustness +15    |
| google-trends-ath-detector  | dataGovernance +20, robustness +18 |
| wasde-ingestor              | robustness +22, correctness +20    |
| list-china-today-macro-news | robustness +25, dataGovernance +22 |

### 入門 → 青銅 升級要求（1 個 Skill）

| Skill                          | 主要升級要求                                   |
|--------------------------------|------------------------------------------------|
| cost-density-net-rr-calculator | correctness +15, robustness +18, usability +18 |

---

## 驗證結果

### 結構驗證 ✓
- 所有 23 個 skill.yaml 已包含新維度
- 舊維度（architecture, content, security, compliance, community）已移除

### 計算驗證 ✓
- overall = 六維度平均（允許 ±1 四捨五入）
- 所有 Skills 計算正確

### Badge 驗證 ✓
- 所有 Badge 與 overall 分數範圍一致
- 黃金：80-89 分（2 個）
- 白銀：60-79 分（16 個）
- 青銅：40-59 分（4 個）
- 入門：0-39 分（1 個）

---

## 相關檔案

| 檔案                                           | 用途                |
|------------------------------------------------|---------------------|
| `thoughts/shared/guide/skill-quality-guide.md` | 評估標準指南        |
| `frontend/src/types/skill.ts`                  | TypeScript 型別定義 |
| `skills/*/skill.yaml`                          | 23 個已更新檔案     |

---

## 後續建議

1. **前端驗證**：啟動 frontend 確認 QualityScoreCard 正確顯示新維度
2. **TypeScript 同步**：確保 `frontend/src/types/skill.ts` 支援新 qualityScore 結構
3. **持續評估**：定期重新評估 Skills 分數，特別是 Alpha 階段的 Skills
4. **升級追蹤**：按照 upgradeNotes 逐步改善低分 Skills
