<overview>
可檢驗假說模板庫。根據主題類別與驅動詞彙，生成對應的假說與驗證數據清單。
</overview>

<hypothesis_structure>
**假說結構**

每個假說包含：

```yaml
hypothesis:
  id: "H1"                      # 假說編號
  hypothesis: "假說描述"         # 簡潔的假說陳述
  trigger_terms: ["term1"]      # 觸發此假說的 related queries
  evidence_in_trends: []        # 趨勢中支持此假說的證據
  verify_with: []               # 驗證數據來源
  confidence: "high|medium|low" # 信心程度
```
</hypothesis_structure>

<health_insurance_hypotheses>
**Health Insurance 相關假說模板**

```yaml
- id: "H1"
  hypothesis: "保費/自付額壓力上升造成注意力結構性抬升"
  trigger_terms:
    - "premium"
    - "premium increase"
    - "deductible"
    - "cost"
    - "expensive"
    - "rate hike"
  evidence_in_trends:
    - "premium/cost 類詞在 rising queries"
    - "去季節化殘差偏高"
    - "趨勢線上移"
  verify_with:
    - "FRED: CUSR0000SAM (Medical Care CPI)"
    - "FRED: CUSR0000SAM2 (Health Insurance CPI)"
    - "州級保費公告 (rate filings)"
    - "KFF Health Insurance Marketplace Calculator"

- id: "H2"
  hypothesis: "就業/雇主保險變動導致搜尋上升"
  trigger_terms:
    - "COBRA"
    - "lose coverage"
    - "lost job"
    - "layoff"
    - "unemployment"
    - "job loss"
  evidence_in_trends:
    - "就業相關詞在 rising queries"
    - "與 Unemployment 搜尋共振"
  verify_with:
    - "FRED: ICSA (Initial Claims)"
    - "FRED: PAYEMS (Nonfarm Payrolls)"
    - "BLS: Layoffs and Discharges"
    - "FRED: LNU02026620 (Job losers)"

- id: "H3"
  hypothesis: "政策/資格變動（Medicaid/ACA）引發搜尋"
  trigger_terms:
    - "Medicaid"
    - "Medicaid renewal"
    - "eligibility"
    - "ACA"
    - "Obamacare"
    - "marketplace"
    - "subsidy"
  evidence_in_trends:
    - "政策相關詞上升"
    - "與政策公告時間對齊"
  verify_with:
    - "CMS Medicaid enrollment data"
    - "Healthcare.gov 公告"
    - "州級 Medicaid eligibility 變更時間表"

- id: "H4"
  hypothesis: "開放投保期季節性造成週期性尖峰"
  trigger_terms:
    - "open enrollment"
    - "sign up"
    - "deadline"
    - "enroll"
  evidence_in_trends:
    - "每年固定月份上升（11-12月）"
    - "去季節化後殘差不顯著"
  verify_with:
    - "Open Enrollment 官方日期"
    - "比較過去 5 年同週期分位數"
```
</health_insurance_hypotheses>

<economic_anxiety_hypotheses>
**經濟焦慮相關假說模板**

```yaml
- id: "E1"
  hypothesis: "通膨壓力導致生活成本焦慮上升"
  trigger_terms:
    - "inflation"
    - "cost of living"
    - "prices"
    - "expensive"
    - "afford"
  verify_with:
    - "FRED: CPIAUCSL (CPI All Items)"
    - "FRED: PCEPILFE (Core PCE)"
    - "FRED: RSXFS (Retail Sales)"

- id: "E2"
  hypothesis: "就業市場變動引發經濟不安"
  trigger_terms:
    - "layoff"
    - "unemployment"
    - "job search"
    - "hiring freeze"
    - "recession"
  verify_with:
    - "FRED: UNRATE (Unemployment Rate)"
    - "FRED: ICSA (Initial Claims)"
    - "FRED: JTSJOL (Job Openings)"

- id: "E3"
  hypothesis: "利率上升影響財務決策搜尋"
  trigger_terms:
    - "interest rate"
    - "mortgage"
    - "refinance"
    - "loan"
    - "Fed"
  verify_with:
    - "FRED: FEDFUNDS (Federal Funds Rate)"
    - "FRED: MORTGAGE30US (30-Year Mortgage Rate)"
```
</economic_anxiety_hypotheses>

<generic_hypothesis_builder>
**通用假說生成邏輯**

```python
def build_hypotheses_from_drivers(topic, drivers, signal_type):
    """根據驅動詞彙自動生成假說"""

    hypotheses = []

    # 載入主題相關模板
    templates = load_templates_for_topic(topic)

    # 根據驅動詞彙匹配模板
    for template in templates:
        match_score = calculate_match_score(drivers, template['trigger_terms'])

        if match_score > 0.3:  # 30% 以上詞彙匹配
            evidence = []
            for driver in drivers:
                if driver['term'].lower() in [t.lower() for t in template['trigger_terms']]:
                    evidence.append(f"'{driver['term']}' 在 {driver['type']} queries 中出現")

            hypotheses.append({
                "id": template['id'],
                "hypothesis": template['hypothesis'],
                "match_score": round(match_score, 2),
                "evidence_in_trends": evidence,
                "verify_with": template['verify_with']
            })

    # 根據 signal_type 調整排序
    if signal_type == "seasonal_spike":
        # 優先季節性假說
        hypotheses.sort(key=lambda x: 'seasonal' in x['hypothesis'].lower(), reverse=True)
    elif signal_type == "regime_shift":
        # 優先結構性假說
        hypotheses.sort(key=lambda x: 'structural' in x['hypothesis'].lower() or 'pressure' in x['hypothesis'].lower(), reverse=True)

    return hypotheses[:4]
```
</generic_hypothesis_builder>

<verification_data_mapping>
**驗證數據映射表**

| 假說類型 | 主要驗證數據 | 備用數據 |
|----------|--------------|----------|
| 成本壓力 | CPI 分項 | 企業公告、新聞 |
| 就業變動 | Initial Claims, JOLTS | LinkedIn 數據 |
| 政策變動 | 官方公告 | 新聞事件時間線 |
| 季節性 | 歷史同期比較 | 行業日曆 |
| 系統性焦慮 | 多指標共振 | Consumer Sentiment |
</verification_data_mapping>

<confidence_scoring>
**信心程度評分**

```python
def calculate_hypothesis_confidence(hypothesis, drivers, correlations):
    """計算假說信心程度"""

    score = 0

    # 驅動詞彙匹配數量
    matched_terms = len(hypothesis.get('evidence_in_trends', []))
    score += min(matched_terms * 0.15, 0.45)  # 最多 +0.45

    # 是否有強相關對照主題
    if correlations:
        max_corr = max(c['recent'] for c in correlations.values())
        score += max_corr * 0.3  # 最多 +0.3

    # 是否有確切驗證數據
    if hypothesis.get('verify_with'):
        score += 0.25  # +0.25

    if score >= 0.7:
        return "high"
    elif score >= 0.4:
        return "medium"
    else:
        return "low"
```
</confidence_scoring>
