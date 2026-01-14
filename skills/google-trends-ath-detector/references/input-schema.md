<overview>
完整的 Google Trends ATH Detector 輸入參數定義與預設值。
</overview>

<required_parameters>
**必要參數**

| 參數      | 類型   | 說明                       | 範例                    |
|-----------|--------|----------------------------|-------------------------|
| topic     | string | Google Trends 主題或關鍵字 | "Health Insurance"      |
| geo       | string | 地區代碼                   | "US", "TW", "JP", "GB"  |
| timeframe | string | 時間範圍                   | "2004-01-01 2025-12-31" |
</required_parameters>

<optional_parameters>
**可選參數**

| 參數                | 類型    | 預設值         | 說明                                       |
|---------------------|---------|----------------|--------------------------------------------|
| granularity         | string  | "weekly"       | 數據粒度：daily, weekly, monthly           |
| use_topic_entity    | boolean | true           | 使用 Topic Entity 而非純關鍵字             |
| smoothing_window    | int     | 4              | 平滑視窗（週數）                           |
| seasonality_method  | string  | "stl"          | 季節性分解：none, stl, month_fixed_effects |
| ath_lookback_policy | string  | "full_history" | ATH 定義範圍：full_history, last_n_years   |
| anomaly_method      | string  | "zscore"       | 異常偵測：zscore, mad, changepoint         |
| anomaly_threshold   | number  | 2.5            | 異常門檻                                   |
| compare_terms       | array   | []             | 對照主題                                   |
| related_queries     | boolean | true           | 是否抓取 related queries                   |
| event_calendars     | array   | []             | 事件日曆來源                               |
| chart_image_path    | string  | null           | 圖表截圖路徑（驗證用）                     |
| output_mode         | string  | "json"         | 輸出格式：json, markdown                   |
</optional_parameters>

<parameter_details>
**granularity 詳解**

| 值      | 說明     | 適用場景                          |
|---------|----------|-----------------------------------|
| daily   | 每日數據 | 短期分析（< 90 天），但可能有噪音 |
| weekly  | 每週數據 | 最常用，平衡精度與穩定性          |
| monthly | 每月數據 | 長期趨勢分析，較平滑              |

**注意：** Google Trends 對長時間範圍（> 5 年）只提供週或月數據。

---

**use_topic_entity 詳解**

Google Trends 支援兩種查詢方式：

1. **Topic Entity（推薦）**
   - 使用 Google Knowledge Graph 的實體
   - 範例："Health Insurance" 作為 Topic 會涵蓋所有語言變體
   - 避免同名歧義（如 "Apple" 公司 vs 水果）

2. **Search Term**
   - 純文字關鍵字匹配
   - 更精確但可能錯過變體

```python
# pytrends 中的使用方式
if use_topic_entity:
    # 先搜尋 Topic ID
    suggestions = pytrends.suggestions(keyword='Health Insurance')
    topic_mid = suggestions[0]['mid']  # 如 '/m/01b9s0'
    kw_list = [topic_mid]
else:
    kw_list = ['Health Insurance']
```

---

**seasonality_method 詳解**

| 方法                | 說明         | 適用場景                 |
|---------------------|--------------|--------------------------|
| none                | 不做分解     | 快速分析或季節性不重要時 |
| stl                 | STL 分解     | 標準方法，適合大多數情況 |
| month_fixed_effects | 月份固定效果 | 當季節性規律且穩定時     |

---

**anomaly_method 詳解**

| 方法        | 說明                      | 優點                | 缺點         |
|-------------|---------------------------|---------------------|--------------|
| zscore      | 標準分數                  | 簡單直觀            | 受極端值影響 |
| mad         | Median Absolute Deviation | 抗極端值            | 計算較複雜   |
| changepoint | 變點偵測                  | 能識別 regime shift | 需要更多數據 |

---

**ath_lookback_policy 詳解**

| 值           | 說明          | 適用場景                         |
|--------------|---------------|----------------------------------|
| full_history | 比較全歷史    | 嚴格的「歷史新高」定義           |
| last_n_years | 只比較近 N 年 | 避免久遠數據干擾（結構可能已變） |
</parameter_details>

<timeframe_format>
**timeframe 格式說明**

pytrends 支援多種時間範圍格式：

```python
# 絕對時間範圍
"2004-01-01 2025-12-31"  # YYYY-MM-DD YYYY-MM-DD

# 相對時間範圍
"today 5-y"              # 過去 5 年
"today 12-m"             # 過去 12 個月
"today 3-m"              # 過去 3 個月
"now 7-d"                # 過去 7 天
"now 1-H"                # 過去 1 小時
```

**建議：**
- ATH 分析使用最長歷史（"2004-01-01 today"）
- 近期異常分析使用 "today 5-y"
- 事件分析使用特定時間窗口
</timeframe_format>

<geo_codes>
**常用地區代碼**

| 代碼  | 地區     |
|-------|----------|
| (空)  | 全球     |
| US    | 美國     |
| US-CA | 美國加州 |
| GB    | 英國     |
| DE    | 德國     |
| JP    | 日本     |
| TW    | 台灣     |
| CN    | 中國     |
| HK    | 香港     |
| SG    | 新加坡   |

完整列表見：Google Trends 網站的地區選擇器
</geo_codes>

<validation_rules>
**參數驗證規則**

```python
def validate_params(params):
    errors = []

    # topic 必填且非空
    if not params.get('topic'):
        errors.append("topic 是必要參數")

    # geo 必填
    if not params.get('geo'):
        errors.append("geo 是必要參數")

    # timeframe 格式驗證
    timeframe = params.get('timeframe', '')
    if not is_valid_timeframe(timeframe):
        errors.append(f"無效的 timeframe 格式: {timeframe}")

    # anomaly_threshold 範圍
    threshold = params.get('anomaly_threshold', 2.5)
    if threshold < 1.0 or threshold > 5.0:
        errors.append("anomaly_threshold 建議在 1.0-5.0 之間")

    # smoothing_window 範圍
    window = params.get('smoothing_window', 4)
    if window < 1 or window > 12:
        errors.append("smoothing_window 建議在 1-12 之間")

    return errors
```
</validation_rules>
