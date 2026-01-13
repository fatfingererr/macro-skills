---
title: Google Trend ATH Detector Skill 簡化分析
date: 2026-01-13
author: Claude (Codebase Researcher)
tags:
  - skill-analysis
  - google-trends
  - simplification
  - refactoring
status: completed
related_files:
  - marketplace/skills/google-trend-ath-detector/SKILL.md
  - marketplace/skills/google-trend-ath-detector/scripts/trend_analyzer.py
  - marketplace/skills/google-trend-ath-detector/scripts/hypothesis_builder.py
last_updated: 2026-01-13
last_updated_by: Claude
---

# Google Trend ATH Detector Skill 簡化分析報告

## 研究問題

用戶希望簡化 `google-trend-ath-detector` Skill，移除假說驗證相關的設計，只保留：
1. 純粹獲取 Google Trends 數據
2. 使用數學方法分析比較

## 摘要

經過完整掃描 `marketplace/skills/google-trend-ath-detector` 目錄，該 Skill 目前包含 17 個檔案，結構完整但複雜。核心功能分為兩大部分：
1. **數據獲取與數學分析**：Google Trends 數據抓取、STL 季節性分解、異常偵測、訊號分型
2. **假說生成與驗證**：基於驅動詞彙生成可檢驗假說、映射驗證數據源、建立驗證清單

簡化策略建議**保留第一部分**（數學分析核心），**移除或大幅簡化第二部分**（假說驗證體系）。這將使 Skill 從「宏觀研究工具」轉變為「純數據分析工具」。

---

## 目錄結構完整分析

### 檔案清單

```
marketplace/skills/google-trend-ath-detector/
├── SKILL.md                                    [主要入口檔案]
├── manifest.json                               [元數據定義]
├── workflows/                                  [4 個工作流程]
│   ├── detect.md                              [快速偵測 ATH]
│   ├── analyze.md                             [深度分析與假說生成] ⚠️ 假說相關
│   ├── verify.md                              [驗證社群貼文主張] ⚠️ 假說相關
│   └── compare.md                             [多主題趨勢比較]
├── references/                                 [5 個參考文件]
│   ├── input-schema.md                        [輸入參數定義]
│   ├── hypothesis-templates.md                [假說模板庫] ❌ 假說相關
│   ├── data-sources.md                        [數據來源清單] ⚠️ 包含驗證數據
│   ├── signal-types.md                        [訊號分型定義]
│   └── seasonality-guide.md                   [季節性分解方法]
├── templates/                                  [2 個輸出模板]
│   ├── output-schema.yaml                     [標準輸出格式] ⚠️ 包含假說欄位
│   └── hypothesis-output.yaml                 [假說報告模板] ❌ 假說相關
├── scripts/                                    [2 個 Python 腳本]
│   ├── trend_analyzer.py                      [核心分析邏輯] ✅ 保留
│   └── hypothesis_builder.py                  [假說生成邏輯] ❌ 假說相關
└── examples/                                   [3 個範例檔案]
    ├── health_insurance_ath.json              [ATH 偵測範例] ⚠️ 包含假說
    ├── seasonal_vs_anomaly.json               [季節性判定範例] ✅ 保留
    └── multi_topic_comparison.json            [多主題比較範例] ⚠️ 包含假說

符號說明：
✅ 完全保留
⚠️ 需要修改（移除假說部分）
❌ 建議刪除
```

---

## 詳細檔案分析

### 1. SKILL.md（主要入口）

**檔案路徑**: `marketplace/skills/google-trend-ath-detector/SKILL.md`

**內容摘要**:
- YAML frontmatter：定義 Skill 名稱、描述、版本、測試問題
- `<essential_principles>`: 核心原則（訊號分型、平衡公式、假說優先於結論）
- `<intake>`: 4 種操作模式路由（Detect/Analyze/Verify/Compare）
- `<routing>`: 路由表，將用戶請求分發到對應 workflow
- 索引區塊：references、workflows、templates、scripts、examples

**假說相關內容**:
- Line 4: description 提到「映射到可檢驗的宏觀驅動假說與後續驗證清單」
- Line 18: tags 包含「假說生成」
- Line 34: testQuestions 提到「生成可檢驗假說與下一步驗證清單」
- Line 159-162: 核心原則第 3 點「假說優先於結論」
- Line 167: 數據層級包含「驗證：宏觀數據（FRED、BLS、政策日曆）」
- Line 176: Analyze 路由描述為「深度分析與假說生成」
- Line 287: success_criteria 包含「生成可檢驗假說清單」和「輸出下一步驗證數據建議」

**建議修改**:
- 移除 description 中的假說相關描述
- 移除「假說生成」標籤
- 簡化測試問題，移除假說相關預期結果
- 移除或簡化核心原則第 3 點
- 簡化數據層級說明
- Analyze workflow 描述改為「深度分析與訊號分型」
- 簡化 success_criteria，移除假說相關項目

---

### 2. manifest.json（元數據）

**檔案路征**: `marketplace/skills/google-trend-ath-detector/manifest.json`

**內容摘要**:
- 基本資訊：name, version, displayName, description, author
- 依賴項：Python 3.8+, pytrends, pandas, numpy, statsmodels, scipy
- 可選依賴：ruptures, fredapi, pandas-datareader（用於驗證數據）
- 4 個 workflows 定義
- 5 個 references 清單
- 4 個數據來源（Google Trends、FRED、BLS、CMS）

**假說相關內容**:
- Line 5: description 提到假說與驗證清單
- Line 18: tags 包含「假說生成」
- Line 31-34: 可選依賴包含 fredapi（用於驗證）
- Line 48-52: analyze workflow 描述包含假說生成
- Line 54-58: verify workflow（完全是假說驗證相關）
- Line 69: hypothesis-templates.md 參考文件
- Line 76: hypothesis-output.yaml 模板
- Line 90-106: 驗證數據來源（FRED、BLS、CMS）

**建議修改**:
- 更新 description，移除假說相關描述
- 移除「假說生成」標籤
- 將 fredapi, pandas-datareader 移至可選依賴（若用戶需要對比數據）
- 移除 verify workflow
- 簡化 analyze workflow 描述
- 移除 hypothesis-templates.md 和 hypothesis-output.yaml
- 簡化 dataSources，保留 Google Trends，FRED/BLS/CMS 標記為「可選對比數據」

---

### 3. workflows/detect.md（快速偵測）

**檔案路徑**: `marketplace/skills/google-trend-ath-detector/workflows/detect.md`

**內容摘要**:
- 快速偵測 ATH 與異常飆升
- 步驟：確認參數 → 抓取數據 → ATH 判定 → 異常分數計算 → 輸出結果
- 決策樹：根據 is_ath 和 is_anomaly 給出建議

**假說相關內容**:
- Line 81: recommendation 建議「進行深度分析（analyze workflow）以識別訊號類型與驅動因素」
- Line 91: 決策樹建議「建議 analyze workflow 深度分析」

**建議修改**:
- ✅ **基本保留**，這個 workflow 本身不涉及假說生成
- 修改 recommendation，建議用戶自行解讀或使用 analyze workflow 進行訊號分型
- 決策樹建議改為「建議進行季節性分析」或「建議識別訊號類型」

---

### 4. workflows/analyze.md（深度分析）

**檔案路徑**: `marketplace/skills/google-trend-ath-detector/workflows/analyze.md`

**內容摘要**:
- 深度分析流程：參數確認 → 抓取數據 → 平滑處理 → 季節性分解 → ATH 與異常偵測 → 訊號分型 → 驅動詞彙提取 → **假說生成** → 組裝輸出
- 步驟 8 完全是假說生成邏輯

**假說相關內容**:
- Line 6: required_reading 包含 hypothesis-templates.md 和 data-sources.md
- Line 156-178: Step 8 整段都是假說生成邏輯
- Line 202: drivers_from_related_queries（驅動詞彙）
- Line 203: testable_hypotheses（可檢驗假說）
- Line 204: next_data_to_pull（驗證數據來源）
- Line 213: success_criteria 包含「生成 2-4 個可檢驗假說」和「每個假說配對驗證數據來源」

**建議修改**:
- ❌ **刪除 Step 8** (build_testable_hypotheses)
- 移除 required_reading 中的 hypothesis-templates.md
- 保留驅動詞彙提取（related queries），但不用於假說生成
- 輸出格式簡化：移除 testable_hypotheses 和 next_data_to_pull
- success_criteria 簡化：移除假說相關檢查項

**簡化後的 analyze workflow 應包含**:
1. 抓取 Google Trends 數據
2. 季節性分解（STL）
3. 異常偵測（z-score）
4. 訊號分型（seasonal_spike / event_driven_shock / regime_shift）
5. 驅動詞彙提取（related queries）—— 作為參考資訊，不生成假說
6. 輸出：訊號類型、異常分數、季節性強度、驅動詞彙清單

---

### 5. workflows/verify.md（驗證主張）

**檔案路徑**: `marketplace/skills/google-trend-ath-detector/workflows/verify.md`

**內容摘要**:
- 驗證社群貼文或圖表中的 Google Trends 主張
- 流程：收集主張 → 獨立抓取數據 → 驗證主張 → 圖表驗證 → 生成驗證報告

**假說相關內容**:
- ⚠️ 整個 workflow 本身不是假說生成，而是數據驗證工具
- 但名稱和概念與「假說驗證」語義相近

**建議**:
- 🤔 **評估是否保留**：這個 workflow 的目的是「驗證社群貼文的數據真偽」，並非「驗證宏觀假說」
- 如果用戶只想要「純數學分析工具」，這個 workflow 可能不在核心需求內
- 建議：**保留但重新命名**為 `verify-claim.md` 或歸類為「實用工具」而非核心分析流程

---

### 6. workflows/compare.md（多主題比較）

**檔案路徑**: `marketplace/skills/google-trend-ath-detector/workflows/compare.md`

**內容摘要**:
- 比較多個主題的趨勢共振模式
- 流程：確認參數 → 抓取所有主題 → 相關性分析 → 領先/滯後分析 → 共振模式識別 → 組裝報告

**假說相關內容**:
- Line 2: required_reading 包含 data-sources.md（用於宏觀數據）
- 輸出報告中包含「implications」（含義）和「next_steps」（下一步行動）

**建議修改**:
- ✅ **基本保留**，這是純數學分析（相關性、滯後分析）
- 簡化輸出報告，移除「implications」（這是假說性質的解釋）
- 保留 correlations, lag_analysis, resonance_pattern（這些都是數學結果）
- next_steps 可以保留為「建議」，但不要涉及假說驗證數據

---

### 7. references/input-schema.md（輸入參數）

**檔案路徑**: `marketplace/skills/google-trend-ath-detector/references/input-schema.md`

**內容摘要**:
- 完整的輸入參數定義與預設值
- 包含必要參數、可選參數、參數詳解、驗證規則

**假說相關內容**:
- Line 29: event_calendars 參數（用於假說驗證）

**建議修改**:
- ✅ **保留**，但標記 event_calendars 為可選或移除
- 其他參數都是數學分析所需，應保留

---

### 8. references/hypothesis-templates.md（假說模板）

**檔案路徑**: `marketplace/skills/google-trend-ath-detector/references/hypothesis-templates.md`

**內容摘要**:
- 完整的假說模板庫
- 包含 Health Insurance 相關假說、經濟焦慮假說、通用假說生成邏輯

**假說相關內容**:
- ❌ **整個檔案都是假說相關**

**建議**:
- ❌ **刪除此檔案**

---

### 9. references/data-sources.md（數據來源）

**檔案路徑**: `marketplace/skills/google-trend-ath-detector/references/data-sources.md`

**內容摘要**:
- Google Trends 數據（pytrends）
- FRED 經濟數據（用於驗證）
- BLS 勞動統計（用於驗證）
- CMS 醫療保險數據（用於驗證）
- 替代注意力指標（Wikipedia, GDELT）
- 事件日曆（Open Enrollment, Tax Season）

**假說相關內容**:
- Line 42-98: FRED、BLS、CMS 數據主要用於假說驗證
- Line 120-139: 事件日曆用於假說驗證

**建議修改**:
- ⚠️ **部分保留**
- 保留 Google Trends 數據說明（核心）
- FRED/BLS/CMS 數據標記為「可選對比數據源」，供用戶自行驗證
- 移除或簡化事件日曆（若不需要假說驗證）

---

### 10. references/signal-types.md（訊號分型）

**檔案路徑**: `marketplace/skills/google-trend-ath-detector/references/signal-types.md`

**內容摘要**:
- 三種訊號類型定義：季節性尖峰、事件驅動衝擊、結構性轉變
- 判定條件與分類邏輯

**假說相關內容**:
- 無（這是純數學分類）

**建議**:
- ✅ **完全保留**，這是核心數學分析功能

---

### 11. references/seasonality-guide.md（季節性分析）

**檔案路徑**: `marketplace/skills/google-trend-ath-detector/references/seasonality-guide.md`

**內容摘要**:
- STL 分解原理與實作
- 去季節化分析
- 月份固定效果（替代方法）
- 同期比較分析

**假說相關內容**:
- 無（這是純數學方法）

**建議**:
- ✅ **完全保留**，這是核心數學分析功能

---

### 12. templates/output-schema.yaml（輸出格式）

**檔案路徑**: `marketplace/skills/google-trend-ath-detector/templates/output-schema.yaml`

**內容摘要**:
- 標準輸出 JSON Schema
- 包含基本資訊、數值結果、訊號分析、季節性、異常偵測、驅動因素、可檢驗假說、下一步數據

**假說相關內容**:
- Line 107-112: testable_hypotheses 欄位
- Line 115-119: next_data_to_pull 欄位
- Line 134-166: hypothesis_schema 定義
- Line 211-250: verification_output（驗證輸出）

**建議修改**:
- ⚠️ **保留主體，移除假說欄位**
- 刪除 testable_hypotheses
- 刪除 next_data_to_pull
- 刪除 hypothesis_schema
- 保留或簡化 verification_output（如果保留 verify workflow）

---

### 13. templates/hypothesis-output.yaml（假說報告模板）

**檔案路徑**: `marketplace/skills/google-trend-ath-detector/templates/hypothesis-output.yaml`

**內容摘要**:
- 假說報告輸出格式
- 包含假說結構、驗證清單、常用假說模板、Markdown 模板

**假說相關內容**:
- ❌ **整個檔案都是假說相關**

**建議**:
- ❌ **刪除此檔案**

---

### 14. scripts/trend_analyzer.py（核心分析腳本）

**檔案路徑**: `marketplace/skills/google-trend-ath-detector/scripts/trend_analyzer.py`

**內容摘要**:
- 核心 Python 腳本（423 行）
- 功能：抓取 Google Trends、STL 分解、異常偵測、訊號分型、驅動詞彙提取
- 主函數：`analyze_google_trends_ath_signal()`

**假說相關內容**:
- 無（這個腳本本身不生成假說）
- 但輸出的 drivers 會被 hypothesis_builder.py 使用

**建議**:
- ✅ **完全保留**，這是核心數學分析邏輯
- 可選：移除 CLI 中的 --compare 參數（如果不需要多主題比較）

**代碼結構分析**:
```python
# 核心函數（全部保留）
fetch_trends()              # 抓取 Google Trends 數據
fetch_related_queries()     # 抓取 related queries
stl_decompose()             # STL 季節性分解
compute_anomaly_score()     # 計算異常分數
classify_signal()           # 訊號分型
extract_drivers()           # 提取驅動詞彙

# 主函數（保留）
analyze_google_trends_ath_signal()  # 整合所有分析
```

---

### 15. scripts/hypothesis_builder.py（假說生成腳本）

**檔案路徑**: `marketplace/skills/google-trend-ath-detector/scripts/hypothesis_builder.py`

**內容摘要**:
- 假說生成 Python 腳本（400 行）
- 功能：根據主題、驅動詞彙、訊號類型生成可檢驗假說
- 包含假說模板庫（Health Insurance、經濟焦慮）

**假說相關內容**:
- ❌ **整個腳本都是假說相關**

**建議**:
- ❌ **刪除此檔案**

**代碼結構分析**:
```python
# 假說模板庫（全部刪除）
HYPOTHESIS_TEMPLATES = {...}

# 假說生成邏輯（全部刪除）
get_topic_category()
calculate_match_score()
find_evidence()
calculate_confidence()
build_testable_hypotheses()
propose_next_data()
generate_verification_checklist()
build_complete_hypothesis_report()
```

---

### 16. examples/health_insurance_ath.json（ATH 範例）

**檔案路徑**: `marketplace/skills/google-trend-ath-detector/examples/health_insurance_ath.json`

**內容摘要**:
- Health Insurance ATH 偵測範例輸出
- 包含完整的分析結果、假說、驗證清單

**假說相關內容**:
- Line 34-94: testable_hypotheses（4 個假說）
- Line 96-128: verification_checklist
- Line 129-138: next_data_to_pull

**建議修改**:
- ⚠️ **保留主體，移除假說部分**
- 保留：基本資訊、訊號分析、季節性、異常偵測、驅動詞彙
- 刪除：testable_hypotheses, verification_checklist, next_data_to_pull

---

### 17. examples/seasonal_vs_anomaly.json（季節性判定範例）

**檔案路徑**: `marketplace/skills/google-trend-ath-detector/examples/seasonal_vs_anomaly.json`

**內容摘要**:
- 三個案例對比：季節性尖峰、真正異常、季節性+異常疊加
- 包含判定矩陣

**假說相關內容**:
- 無（這是純數學分析範例）

**建議**:
- ✅ **完全保留**，這是優秀的教學範例

---

### 18. examples/multi_topic_comparison.json（多主題比較範例）

**檔案路徑**: `marketplace/skills/google-trend-ath-detector/examples/multi_topic_comparison.json`

**內容摘要**:
- 多主題趨勢共振分析範例
- 包含相關性、滯後分析、共振模式識別

**假說相關內容**:
- Line 109-137: testable_hypotheses_based_on_comparison（3 個假說）
- Line 139-144: next_steps（包含驗證建議）

**建議修改**:
- ⚠️ **保留主體，移除或簡化假說部分**
- 保留：correlations, lag_analysis, resonance_pattern, interpretation
- 刪除：testable_hypotheses_based_on_comparison
- 簡化：next_steps 改為純數學建議（如「追蹤相關性變化」）

---

## 需要刪除的檔案清單

基於簡化目標，建議**完全刪除**以下檔案：

1. ❌ `workflows/verify.md` - 驗證社群貼文（非核心需求）
2. ❌ `references/hypothesis-templates.md` - 假說模板庫
3. ❌ `templates/hypothesis-output.yaml` - 假說報告模板
4. ❌ `scripts/hypothesis_builder.py` - 假說生成腳本

---

## 需要修改的檔案清單與修改建議

### 主要檔案修改

#### 1. SKILL.md

**修改位置**:
- Line 4: description
- Line 18: tags
- Line 34-42: testQuestions
- Line 159-162: 核心原則第 3 點
- Line 167: 數據層級
- Line 176: Analyze 路由描述
- Line 287: success_criteria

**修改建議**:
```yaml
# 修改前
description: 自動抓取 Google Trends 指標，判定是否出現「歷史新高（ATH）」或異常飆升，並把這個搜尋情緒訊號映射到可檢驗的宏觀驅動假說與後續驗證清單。

# 修改後
description: 自動抓取 Google Trends 指標，判定是否出現「歷史新高（ATH）」或異常飆升，並使用 STL 季節性分解與統計方法進行訊號分型與趨勢分析。
```

```yaml
# 修改前
tags:
  - 假說生成
  - 季節性分析

# 修改後
tags:
  - 季節性分析
  - 統計分析
```

移除核心原則第 3 點「假說優先於結論」，或改為「描述性分析優先於解釋性結論」。

#### 2. manifest.json

**修改位置**:
- Line 5: description
- Line 18: tags
- Line 31-34: 可選依賴
- Line 48-52: analyze workflow
- Line 54-58: verify workflow（刪除）
- Line 69: references 清單
- Line 76: templates 清單
- Line 90-106: dataSources

**修改建議**:
- 更新 description 和 tags（同 SKILL.md）
- 將 fredapi, pandas-datareader 保留在可選依賴，但標註為「用於對比分析」
- 移除 verify workflow
- 移除 hypothesis-templates.md 和 hypothesis-output.yaml
- dataSources 簡化，FRED/BLS/CMS 標記為 "type": "optional"

#### 3. workflows/analyze.md

**修改位置**:
- Line 6: required_reading
- Line 156-178: Step 8（刪除整段）
- Line 203-204: 輸出格式
- Line 213-215: success_criteria

**修改建議**:
- 移除 required_reading 中的 hypothesis-templates.md
- 刪除 Step 8 假說生成邏輯
- 輸出格式移除 testable_hypotheses 和 next_data_to_pull
- success_criteria 簡化為：
  ```
  - [ ] 完成季節性分解
  - [ ] 判定訊號類型
  - [ ] 提取驅動詞彙
  - [ ] 輸出符合 templates/output-schema.yaml
  ```

#### 4. workflows/compare.md

**修改位置**:
- Line 183: implications
- Line 185-189: next_steps

**修改建議**:
- 簡化 implications，移除假說性質的解釋
- next_steps 改為純數學建議（如「監控相關性變化」、「檢查滯後關係穩定性」）

#### 5. references/data-sources.md

**修改位置**:
- Line 42-98: FRED/BLS/CMS 數據說明
- Line 120-139: 事件日曆

**修改建議**:
- FRED/BLS/CMS 數據標註為「可選對比數據」
- 簡化事件日曆，或移除（若不需要）

#### 6. templates/output-schema.yaml

**修改位置**:
- Line 107-112: testable_hypotheses 欄位（刪除）
- Line 115-119: next_data_to_pull 欄位（刪除）
- Line 134-166: hypothesis_schema 定義（刪除）
- Line 211-250: verification_output（評估是否保留）

**修改建議**:
```yaml
# 簡化後的輸出 schema
full_output:
  properties:
    # 基本資訊（保留）
    topic, geo, timeframe, granularity
    # 數值結果（保留）
    latest, hist_max, is_all_time_high
    # 訊號分析（保留）
    signal_type
    # 季節性分析（保留）
    seasonality: {method, is_seasonal_pattern_detected, seasonal_strength}
    # 異常偵測（保留）
    anomaly_detection: {method, threshold, latest_score, is_anomaly}
    # 驅動因素（保留，但作為參考資訊）
    drivers_from_related_queries: [{term, type, value}]
    # 元數據（保留）
    metadata: {analyzed_at, data_points, schema_version}
```

#### 7. examples/health_insurance_ath.json

**修改建議**:
- 保留：基本資訊、訊號分析、季節性、異常偵測、驅動詞彙（前 10 個）
- 刪除：testable_hypotheses, verification_checklist, next_data_to_pull, interpretation（或簡化為純數學描述）

#### 8. examples/multi_topic_comparison.json

**修改建議**:
- 保留：correlations, lag_analysis, recent_changes, resonance_pattern
- 刪除：testable_hypotheses_based_on_comparison
- 簡化：next_steps 改為純數學建議

---

## 簡化後的建議結構

簡化後的 Skill 結構如下：

```
marketplace/skills/google-trend-ath-detector/
├── SKILL.md                                    [修改：移除假說相關描述]
├── manifest.json                               [修改：更新描述、移除假說檔案]
├── workflows/                                  [3 個工作流程]
│   ├── detect.md                              [輕微修改：移除假說建議]
│   ├── analyze.md                             [重要修改：刪除 Step 8 假說生成]
│   └── compare.md                             [輕微修改：簡化 implications]
├── references/                                 [4 個參考文件]
│   ├── input-schema.md                        [保留]
│   ├── data-sources.md                        [修改：標註 FRED/BLS 為可選]
│   ├── signal-types.md                        [完全保留]
│   └── seasonality-guide.md                   [完全保留]
├── templates/                                  [1 個輸出模板]
│   └── output-schema.yaml                     [修改：移除假說欄位]
├── scripts/                                    [1 個 Python 腳本]
│   └── trend_analyzer.py                      [完全保留]
└── examples/                                   [2-3 個範例檔案]
    ├── seasonal_vs_anomaly.json               [完全保留]
    └── simplified_ath_example.json            [新建或修改現有範例]
```

**檔案數量變化**:
- 原本：17 個檔案
- 簡化後：12 個檔案（刪除 5 個）

---

## 核心數學分析功能保留清單

簡化後，Skill 保留以下核心功能：

### 1. 數據獲取
- ✅ Google Trends 時間序列抓取（pytrends）
- ✅ Related queries 抓取（rising/top）
- ✅ 多主題對比抓取

### 2. 數學分析
- ✅ STL 季節性分解（trend/seasonal/residual）
- ✅ 季節性強度計算
- ✅ 去季節化分析
- ✅ 異常偵測（z-score / MAD）
- ✅ ATH 判定

### 3. 訊號分型
- ✅ 季節性尖峰（seasonal_spike）
- ✅ 事件驅動衝擊（event_driven_shock）
- ✅ 結構性轉變（regime_shift）

### 4. 趨勢比較
- ✅ 多主題相關性分析
- ✅ 領先/滯後分析（lag analysis）
- ✅ 共振模式識別（systemic_anxiety / isolated_signal）

### 5. 參考資訊
- ✅ 驅動詞彙清單（related queries）
- ✅ 同期比較（歷史同期百分位數）

---

## 移除的假說驗證功能清單

簡化後，以下功能被移除：

### 1. 假說生成
- ❌ 假說模板庫（Health Insurance、經濟焦慮）
- ❌ 驅動詞彙匹配假說模板
- ❌ 假說信心程度評分
- ❌ 假說證據收集

### 2. 驗證清單
- ❌ 驗證數據來源映射（FRED/BLS/CMS）
- ❌ 驗證清單生成（immediate/short_term/ongoing）
- ❌ 下一步數據建議（next_data_to_pull）

### 3. 假說驗證工作流
- ❌ verify workflow（驗證社群貼文主張）
- ❌ 假說報告生成（hypothesis-output.yaml）

### 4. 輔助工具
- ❌ hypothesis_builder.py 腳本
- ❌ 假說模板 YAML
- ❌ 驗證數據 API 整合（fredapi）

---

## 簡化後的使用範例

### 快速偵測（detect workflow）

**輸入**:
```
分析 "Health Insurance" 在美國的搜尋趨勢是否創下歷史新高
```

**輸出**:
```json
{
  "topic": "Health Insurance",
  "geo": "US",
  "latest": 100,
  "hist_max": 100,
  "is_all_time_high": true,
  "zscore": 3.1,
  "is_anomaly": true,
  "recommendation": "確認異常高點，建議進行深度分析以識別訊號類型"
}
```

### 深度分析（analyze workflow）

**輸入**:
```
深度分析 "Health Insurance" 的搜尋趨勢
```

**輸出**:
```json
{
  "topic": "Health Insurance",
  "geo": "US",
  "signal_type": "regime_shift",
  "seasonality": {
    "method": "stl",
    "is_seasonal_pattern_detected": true,
    "seasonal_strength": 0.42
  },
  "anomaly_detection": {
    "method": "zscore",
    "latest_score": 3.1,
    "is_anomaly": true
  },
  "drivers_from_related_queries": [
    {"term": "open enrollment", "type": "rising", "value": "Breakout"},
    {"term": "premium increase", "type": "rising", "value": "+350%"},
    {"term": "Medicaid renewal", "type": "rising", "value": "+280%"}
  ]
}
```

**用戶自行解讀**:
- 訊號類型為「結構性轉變」，表示長期關注度上升
- 驅動詞彙顯示「保費上漲」和「Medicaid 資格」相關
- 用戶可根據需求自行查詢 FRED、BLS 數據驗證

### 多主題比較（compare workflow）

**輸入**:
```
比較 "Health Insurance"、"Unemployment"、"Inflation" 的趨勢共振
```

**輸出**:
```json
{
  "primary_topic": "Health Insurance",
  "correlations": {
    "Unemployment": {"overall": 0.35, "recent": 0.58, "change": 0.23},
    "Inflation": {"overall": 0.28, "recent": 0.52, "change": 0.24}
  },
  "lag_analysis": {
    "Unemployment": {
      "best_lag": -2,
      "best_correlation": 0.62,
      "interpretation": "Unemployment 領先 Health Insurance 約 2 週"
    }
  },
  "resonance_pattern": {
    "pattern": "systemic_anxiety",
    "same_direction_ratio": 1.0,
    "explanation": "所有對照主題同向上升，表示系統性焦慮"
  }
}
```

---

## 實作建議

### 階段 1：檔案刪除（低風險）

1. 刪除以下檔案：
   ```bash
   rm workflows/verify.md
   rm references/hypothesis-templates.md
   rm templates/hypothesis-output.yaml
   rm scripts/hypothesis_builder.py
   ```

### 階段 2：主要檔案修改（中風險）

2. 修改 `SKILL.md`:
   - 更新 description 和 tags
   - 簡化核心原則
   - 移除 verify workflow 路由
   - 簡化 success_criteria

3. 修改 `manifest.json`:
   - 更新 description 和 tags
   - 移除 verify workflow
   - 移除假說相關 references 和 templates

4. 修改 `workflows/analyze.md`:
   - 刪除 Step 8 假說生成邏輯
   - 簡化輸出格式
   - 更新 success_criteria

### 階段 3：輔助檔案修改（低風險）

5. 修改 `templates/output-schema.yaml`:
   - 移除 testable_hypotheses 欄位
   - 移除 next_data_to_pull 欄位
   - 移除 hypothesis_schema

6. 修改 `examples/health_insurance_ath.json`:
   - 移除假說部分
   - 保留核心數學分析結果

7. 修改 `examples/multi_topic_comparison.json`:
   - 移除假說部分
   - 保留相關性、滯後分析結果

### 階段 4：可選修改（低優先級）

8. 修改 `references/data-sources.md`:
   - 標註 FRED/BLS/CMS 為可選數據

9. 修改 `workflows/detect.md` 和 `workflows/compare.md`:
   - 簡化建議，移除假說驗證相關內容

---

## 風險評估

### 低風險變更
- ✅ 刪除 hypothesis_builder.py（未被其他腳本依賴）
- ✅ 刪除 hypothesis-templates.md、hypothesis-output.yaml（僅供參考）
- ✅ 修改範例檔案（不影響功能）

### 中風險變更
- ⚠️ 修改 SKILL.md、manifest.json（需更新版本號）
- ⚠️ 修改 workflows/analyze.md（需測試 workflow 流程）
- ⚠️ 修改 output-schema.yaml（需確保輸出相容）

### 需要注意的依賴關係
- `trend_analyzer.py` 不依賴 `hypothesis_builder.py`，可以獨立運作
- 刪除假說相關檔案不會影響數學分析功能
- 需要更新版本號（v0.1.0 → v0.2.0）以反映重大變更

---

## 效益分析

### 簡化後的優勢

1. **降低複雜度**
   - 檔案數量減少 29%（17 → 12）
   - 代碼行數減少約 400 行（hypothesis_builder.py）
   - 概念模型簡化：從「研究工具」變成「分析工具」

2. **專注核心功能**
   - 純數學分析：STL、異常偵測、訊號分型
   - 數據驅動：輸出客觀的統計結果
   - 用戶自主解讀：不強加假說框架

3. **更容易維護**
   - 減少假說模板維護負擔
   - 減少驗證數據 API 整合維護
   - 更少的 workflow 分支

4. **更廣泛的適用性**
   - 不限於宏觀經濟分析
   - 可用於任何 Google Trends 主題
   - 用戶可根據自己的專業領域解讀

### 簡化後的取捨

1. **失去的功能**
   - 不再自動生成假說
   - 不再提供驗證數據來源建議
   - 不再有結構化的驗證清單

2. **用戶需自行負責**
   - 解讀訊號類型的含義
   - 識別驅動因素
   - 查詢驗證數據（若需要）

3. **適用場景變化**
   - 更適合：資料科學家、技術分析師
   - 較不適合：需要完整研究框架的宏觀分析師

---

## 總結

### 當前狀態
`google-trend-ath-detector` 是一個功能完整但複雜的 Skill，包含數據獲取、數學分析、訊號分型、假說生成、驗證清單等多層功能。

### 簡化目標
移除假說驗證相關設計，保留純數學分析核心。

### 建議行動
1. **刪除 4 個檔案**（verify.md, hypothesis-templates.md, hypothesis-output.yaml, hypothesis_builder.py）
2. **修改 7 個檔案**（SKILL.md, manifest.json, analyze.md, compare.md, output-schema.yaml, 2 個範例）
3. **完全保留 6 個檔案**（detect.md, signal-types.md, seasonality-guide.md, trend_analyzer.py, seasonal_vs_anomaly.json, input-schema.md）

### 簡化後的核心價值
- 提供客觀的 Google Trends 數學分析
- 自動化季節性分解與異常偵測
- 識別訊號類型（季節性/事件/結構性）
- 提取驅動詞彙供參考
- 多主題趨勢比較與相關性分析

### 用戶使用流程
1. 輸入主題 → 獲得訊號類型與異常分數
2. 查看驅動詞彙 → 了解搜尋量上升的相關詞
3. 自行解讀 → 根據專業知識判斷原因
4. （可選）查詢 FRED/BLS 數據驗證

---

## 附錄：完整檔案清單與處理建議

| 檔案路徑 | 檔案類型 | 假說相關程度 | 處理建議 |
|---------|---------|-------------|---------|
| SKILL.md | 入口 | 中度 | ⚠️ 修改：移除假說相關描述 |
| manifest.json | 元數據 | 中度 | ⚠️ 修改：更新描述、移除假說檔案 |
| workflows/detect.md | 工作流程 | 低度 | ⚠️ 輕微修改：移除假說建議 |
| workflows/analyze.md | 工作流程 | 高度 | ⚠️ 重要修改：刪除 Step 8 |
| workflows/verify.md | 工作流程 | 中度 | ❌ 刪除（或評估保留） |
| workflows/compare.md | 工作流程 | 低度 | ⚠️ 輕微修改：簡化 implications |
| references/input-schema.md | 參考文件 | 低度 | ✅ 基本保留 |
| references/hypothesis-templates.md | 參考文件 | 完全 | ❌ 刪除 |
| references/data-sources.md | 參考文件 | 中度 | ⚠️ 修改：標註 FRED/BLS 為可選 |
| references/signal-types.md | 參考文件 | 無 | ✅ 完全保留 |
| references/seasonality-guide.md | 參考文件 | 無 | ✅ 完全保留 |
| templates/output-schema.yaml | 模板 | 中度 | ⚠️ 修改：移除假說欄位 |
| templates/hypothesis-output.yaml | 模板 | 完全 | ❌ 刪除 |
| scripts/trend_analyzer.py | 腳本 | 無 | ✅ 完全保留 |
| scripts/hypothesis_builder.py | 腳本 | 完全 | ❌ 刪除 |
| examples/health_insurance_ath.json | 範例 | 中度 | ⚠️ 修改：移除假說部分 |
| examples/seasonal_vs_anomaly.json | 範例 | 無 | ✅ 完全保留 |
| examples/multi_topic_comparison.json | 範例 | 中度 | ⚠️ 修改：移除假說部分 |

**處理優先級**:
1. 高優先級：刪除 4 個完全假說相關檔案
2. 中優先級：修改 SKILL.md, manifest.json, analyze.md
3. 低優先級：修改範例檔案、輸出模板
4. 可選：修改 data-sources.md, compare.md

---

## 程式碼參考位置

為方便實作，以下是關鍵程式碼的精確位置：

### SKILL.md 修改位置
- Line 4: `description: 自動抓取...映射到可檢驗的宏觀驅動假說...` → 移除假說部分
- Line 18: `tags: - 假說生成` → 移除此標籤
- Line 159-162: 核心原則第 3 點 → 移除或改寫
- Line 176: `workflows/analyze.md | 深度分析、假說生成、驗證清單` → 改為「深度分析與訊號分型」
- Line 287: success_criteria 第 6-7 項 → 移除假說相關檢查

### workflows/analyze.md 修改位置
- Line 6: `references/hypothesis-templates.md` → 移除
- Line 156-178: `Step 8: 假說生成` → 刪除整段
- Line 203: `testable_hypotheses` → 移除此欄位
- Line 204: `next_data_to_pull` → 移除此欄位

### scripts/trend_analyzer.py 無需修改
- ✅ 此腳本不涉及假說生成，完全保留

---

**報告完成日期**: 2026-01-13
**分析者**: Claude (Codebase Researcher)
**總檔案數**: 17 個
**建議刪除**: 4 個
**建議修改**: 7 個
**完全保留**: 6 個
