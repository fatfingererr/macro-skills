<required_reading>
**執行此工作流程前，請先閱讀：**
1. references/input-schema.md - 了解輸入參數
2. references/signal-types.md - 了解訊號分型
</required_reading>

<objective>
驗證社群貼文或圖表中關於 Google Trends 的主張是否屬實。
</objective>

<use_cases>
**適用場景：**

1. 用戶看到推文說「XXX 搜尋創歷史新高」，想確認是否屬實
2. 用戶有 Google Trends 截圖，想驗證數據
3. 用戶想檢查社群討論的訊號是否有季節性解釋
</use_cases>

<process>
**Step 1: 收集主張信息**

詢問用戶：

```yaml
claim_info:
  topic: "貼文提到的搜尋主題是什麼？"
  claim_type: "主張類型是什麼？"
    options:
      - ath: "創歷史新高"
      - spike: "異常飆升"
      - trend_up: "趨勢上升"
  geo: "地區是哪裡？（預設 US）"
  claimed_date: "主張的時間點是什麼時候？"
  chart_image_path: "有圖表截圖嗎？（可選）"
  source_url: "貼文來源 URL（可選）"
```

**Step 2: 獨立抓取數據**

```python
# 用相同參數抓取 Google Trends 數據
ts = fetch_trends(
    topic=claim_info['topic'],
    geo=claim_info['geo'],
    timeframe="2004-01-01 today",  # 盡可能長的歷史
    granularity="weekly"
)
```

**Step 3: 驗證主張**

```python
def verify_claim(ts, claim_type, claimed_date):
    """驗證主張是否屬實"""

    # 找到主張日期的數據點
    if claimed_date:
        claimed_value = ts.loc[ts.index <= claimed_date].iloc[-1]
    else:
        claimed_value = ts.iloc[-1]

    results = {
        "claimed_value": float(claimed_value),
        "verification": {}
    }

    if claim_type == "ath":
        hist_max = ts.max()
        is_verified = claimed_value >= hist_max * 0.98  # 允許 2% 誤差

        results["verification"] = {
            "claim": "創歷史新高",
            "is_verified": is_verified,
            "actual_max": float(hist_max),
            "claimed_value": float(claimed_value),
            "explanation": f"主張值 {claimed_value} vs 歷史最高 {hist_max}"
        }

        # 額外檢查：是否有季節性解釋
        if is_verified:
            seasonal_check = check_seasonality(ts, claimed_date)
            results["verification"]["seasonal_context"] = seasonal_check

    elif claim_type == "spike":
        # 計算 z-score
        mean = ts.mean()
        std = ts.std()
        zscore = (claimed_value - mean) / std

        is_verified = zscore >= 2.0

        results["verification"] = {
            "claim": "異常飆升",
            "is_verified": is_verified,
            "zscore": round(zscore, 2),
            "explanation": f"z-score = {zscore:.2f}，{'確認異常' if is_verified else '屬正常波動'}"
        }

    return results
```

**Step 4: 圖表驗證（若有圖片）**

```python
def verify_chart_image(image_path, expected_ts):
    """
    驗證圖表截圖與實際數據的一致性

    注意：此功能需要 OCR/圖像分析能力
    簡化實作：用視覺比對確認趨勢形狀
    """
    # 讀取圖片
    # 提取曲線特徵（峰值位置、整體形狀）
    # 與 expected_ts 比對

    return {
        "image_analyzed": True,
        "visual_match": "high|medium|low",
        "discrepancies": [],
        "note": "建議用官方 Google Trends 網站交叉驗證"
    }
```

**Step 5: 生成驗證報告**

```python
report = {
    "claim_source": claim_info.get('source_url'),
    "topic": claim_info['topic'],
    "geo": claim_info['geo'],
    "claim_type": claim_info['claim_type'],
    "claimed_date": claim_info['claimed_date'],

    "verification_result": {
        "is_verified": verification['is_verified'],
        "confidence": "high|medium|low",
        "details": verification
    },

    "context": {
        "historical_percentile": percentile_rank(ts, claimed_value),
        "similar_peaks_in_history": find_similar_peaks(ts, claimed_value),
        "seasonal_explanation": seasonal_check if seasonal_check else None
    },

    "caveats": [
        "Google Trends 指數是相對值，不同查詢條件可能得到不同結果",
        "數據可能有 2-3 天延遲",
        "Topic Entity vs 關鍵字可能影響結果"
    ],

    "recommendation": generate_recommendation(verification)
}
```
</process>

<verification_matrix>
**驗證結果解讀：**

| 主張 | 驗證結果 | 建議 |
|------|----------|------|
| ATH | 確認 | 進一步分析是否有季節性/事件性解釋 |
| ATH | 否定 | 檢查時間範圍、地區、Topic Entity 差異 |
| Spike | 確認 | 進入 analyze workflow 了解驅動因素 |
| Spike | 否定 | 可能是正常波動或季節性 |
</verification_matrix>

<success_criteria>
此工作流程成功完成時：
- [ ] 獨立抓取 Google Trends 數據
- [ ] 驗證主張是否屬實
- [ ] 提供歷史百分位數上下文
- [ ] 檢查季節性解釋
- [ ] 生成驗證報告與建議
</success_criteria>

<error_handling>
**常見差異來源：**

1. **時間範圍不同** → 不同時間範圍會影響 0-100 標準化
2. **Topic vs Keyword** → Topic Entity 可能涵蓋更多/更少內容
3. **地區不同** → 確認 geo 參數一致
4. **數據更新延遲** → Google Trends 有 2-3 天延遲
</error_handling>
