<overview>
此參考文件詳細說明 CASS Freight Index 與通膨的領先關係，包括理論基礎、計算方法、與訊號判斷標準。
</overview>

<theoretical_basis>

<section name="transmission_mechanism">
**傳導機制：CASS Freight Index → 通膨**

```
                    ┌─────────────────────────────────────────────┐
                    │           傳導鏈示意圖                        │
                    ├─────────────────────────────────────────────┤
                    │                                              │
                    │   CASS 出貨量下降                            │
                    │         ↓                                    │
                    │   終端需求減弱                                │
                    │         ↓                                    │
                    │   庫存累積 / 補庫動能下降                     │
                    │         ↓                                    │
                    │   企業定價能力下降                            │
                    │         ↓                                    │
                    │   CPI 增速放緩                                │
                    │                                              │
                    │   領先時間：約 4-6 個月                       │
                    │                                              │
                    └─────────────────────────────────────────────┘
```

**核心邏輯**：

1. **CASS Freight Index = 北美實體經濟活動的「先行者」**
   - 商品從生產端到消費端，必須經過運輸
   - CASS 追蹤北美地區的卡車和鐵路貨運
   - 出貨量反映「即將被消費」的商品量

2. **需求減弱 → 定價能力下降**
   - 當終端需求減弱，企業難以轉嫁成本
   - 價格增速放緩，CPI 隨之下降

3. **領先性來源**
   - 貨運發生在最終銷售之前
   - 庫存調整週期約 3-6 個月
   - CPI 統計有 2-4 週滯後

</section>

<section name="cass_vs_alternatives">
**為何選擇 CASS Freight Index**

| 指標 | 優勢 | 劣勢 |
|------|------|------|
| **CASS Freight Index** | 最權威、涵蓋卡車+鐵路、有 YoY 版本 | 需從 MacroMicro 爬取 |
| TSI | FRED 免費、涵蓋廣 | 平滑波動、更新慢 |
| TRUCKD11 | FRED 免費、敏感度高 | 僅卡車 |

**CASS 四個指標的角色**：

1. **Shipments YoY**（主要分析指標）
   - 直接反映需求端變化
   - 最適合週期轉折偵測
   - YoY 自動消除季節性

2. **Expenditures YoY**
   - 反映運費成本壓力
   - 可交叉驗證 Shipments 訊號
   - 成本傳導可能有額外滯後

3. **Shipments Index / Expenditures Index**
   - 絕對水準參考
   - 用於長期趨勢分析

</section>

<section name="academic_evidence">
**學術與實證依據**

1. **Stock & Watson (1999) "Forecasting Inflation"**
   - 實質經濟活動指標對通膨有預測能力
   - 運輸指標屬於有效的先行指標

2. **Cass Freight Index Reports**
   - 長期追蹤貨運與經濟週期的關係
   - 歷史驗證貨運量領先 GDP 和通膨

3. **Fed 經濟學家研究**
   - 供應鏈壓力與通膨的滯後關係
   - 運輸成本傳導至消費者價格約需 4-6 個月

</section>

</theoretical_basis>

<calculation_methods>

<method name="yoy_calculation">
**年增率 (YoY) 計算**

```python
def calculate_yoy(series: pd.Series) -> pd.Series:
    """
    計算年增率

    公式: YoY_t = (Index_t / Index_{t-12}) - 1

    Parameters
    ----------
    series : pd.Series
        月度指數序列（如 CASS Shipments Index）

    Returns
    -------
    pd.Series
        年增率序列（百分比形式）
    """
    yoy = (series / series.shift(12) - 1) * 100
    return yoy
```

**CASS 已提供 YoY 版本**：
- `shipments_yoy` 和 `expenditures_yoy` 已是 YoY 數據
- 無需自行計算
- 可直接用於週期分析

**為何使用 YoY 而非 MoM**：
- MoM 波動大，容易被噪音干擾
- YoY 自動消除季節性
- 更適合偵測週期性轉折

</method>

<method name="cycle_low_detection">
**週期低點偵測**

```python
def detect_cycle_low(
    yoy: pd.Series,
    window: int = 18,
    min_periods: int = 12
) -> pd.Series:
    """
    偵測是否為 N 個月新低

    定義：當前 YoY 等於過去 N 個月的最小值

    Parameters
    ----------
    yoy : pd.Series
        年增率序列（CASS Shipments YoY）
    window : int
        回看窗口（月），建議 12-18
    min_periods : int
        最小觀察期

    Returns
    -------
    pd.Series
        布林值序列
    """
    rolling_min = yoy.rolling(window=window, min_periods=min_periods).min()
    is_new_low = (yoy == rolling_min)
    return is_new_low
```

**窗口選擇建議**：
- 12 個月：敏感度高，可能有較多誤判
- 18 個月：穩健性高，適合週期分析（推薦）
- 24 個月：保守，可能錯過短週期

</method>

<method name="lead_alignment">
**領先對齊分析**

```python
def lead_alignment_analysis(
    cass_yoy: pd.Series,
    cpi_yoy: pd.Series,
    lead_months: int = 6
) -> dict:
    """
    分析 CASS YoY 對 CPI YoY 的領先性

    方法：
    1. 將 CASS YoY 向前平移 lead_months
    2. 計算與 CPI YoY 的相關係數
    3. 驗證轉折點的領先關係

    Parameters
    ----------
    cass_yoy : pd.Series
        CASS Shipments 年增率
    cpi_yoy : pd.Series
        CPI 年增率
    lead_months : int
        假設的領先月數

    Returns
    -------
    dict
        {
            'correlation': float,
            'optimal_lead': int,
            'alignment_quality': str
        }
    """
    # 建立領先序列
    cass_lead = cass_yoy.shift(lead_months)

    # 對齊並計算相關性
    aligned = pd.DataFrame({
        'cass_lead': cass_lead,
        'cpi': cpi_yoy
    }).dropna()

    correlation = aligned['cass_lead'].corr(aligned['cpi'])

    # 找最佳領先月數
    correlations = {}
    for lead in range(1, 13):
        shifted = cass_yoy.shift(lead)
        corr = shifted.corr(cpi_yoy)
        correlations[lead] = corr

    optimal_lead = max(correlations, key=correlations.get)

    # 對齊品質評估
    if correlation > 0.6:
        quality = 'high'
    elif correlation > 0.4:
        quality = 'medium'
    else:
        quality = 'low'

    return {
        'correlation': correlation,
        'optimal_lead': optimal_lead,
        'alignment_quality': quality,
        'lead_correlations': correlations
    }
```

**領先月數選擇**：
- 預設 6 個月：歷史平均
- 可調整範圍：3-12 個月
- 經濟週期不同階段可能有差異

</method>

</calculation_methods>

<signal_assessment>

<criteria name="inflation_easing">
**通膨緩解訊號（Inflation Easing）**

```python
# 強訊號（High Confidence）
if cass_yoy < 0 and is_new_cycle_low:
    signal = 'inflation_easing'
    confidence = 'high'

# 中等訊號（Medium Confidence）
elif cass_yoy < 0:
    signal = 'inflation_easing'
    confidence = 'medium'
```

**觸發條件**：
1. CASS Shipments YoY 轉負（< 0）
2. 創 18 個月新低（is_new_cycle_low = True）

**訊號強度加權**：
- YoY 跌幅越深，訊號越強
- 負值持續時間越長，訊號越強
- 多指標（Shipments + Expenditures）一致，訊號越強

</criteria>

<criteria name="inflation_rising">
**通膨上行訊號（Inflation Rising）**

```python
# 中等訊號
if cass_yoy > 5 and cycle_status == 'positive':
    signal = 'inflation_rising'
    confidence = 'medium'
```

**觸發條件**：
1. CASS Shipments YoY > 5%
2. 處於上行週期

**注意**：通膨上行的領先性較不穩定，需結合其他指標。

</criteria>

<criteria name="neutral">
**中性訊號（Neutral）**

```python
# 低信心
else:
    signal = 'neutral'
    confidence = 'low'
```

**觸發條件**：
1. CASS YoY 在 0 附近震盪
2. 無明顯週期轉折

**建議行動**：持續監控，等待更明確訊號。

</criteria>

</signal_assessment>

<multi_indicator_validation>

**多指標交叉驗證**

CASS 提供四個指標，可進行交叉驗證：

```python
def cross_validate_signals(all_indicators: dict) -> dict:
    """
    使用多個 CASS 指標交叉驗證

    Parameters
    ----------
    all_indicators : dict
        {
            'shipments_yoy': DataFrame,
            'expenditures_yoy': DataFrame,
            ...
        }

    Returns
    -------
    dict
        驗證結果與一致性評分
    """
    shipments_signal = get_signal(all_indicators['shipments_yoy'])
    expenditures_signal = get_signal(all_indicators['expenditures_yoy'])

    # 一致性檢查
    if shipments_signal == expenditures_signal:
        consistency = 'high'
        adjusted_confidence = 'high'
    else:
        consistency = 'divergent'
        adjusted_confidence = 'medium'

    return {
        'shipments_signal': shipments_signal,
        'expenditures_signal': expenditures_signal,
        'consistency': consistency,
        'adjusted_confidence': adjusted_confidence
    }
```

**驗證規則**：
- Shipments YoY 和 Expenditures YoY 同時轉負 → 高信心
- 僅 Shipments YoY 轉負 → 中信心
- 兩者分歧 → 需進一步分析

</multi_indicator_validation>

<confidence_factors>

**影響信心水準的因素**

| 因素 | 高信心 | 中信心 | 低信心 |
|------|-------|-------|-------|
| 週期狀態 | new_cycle_low | negative | positive |
| YoY 幅度 | < -3% | -3% ~ 0% | > 0% |
| 持續時間 | > 3 個月 | 1-3 個月 | < 1 個月 |
| 指標一致性 | Shipments + Expenditures 同向 | 部分一致 | 分歧 |
| 領先相關性 | > 0.6 | 0.4-0.6 | < 0.4 |

**信心調整規則**：
```python
def adjust_confidence(
    base_confidence: str,
    alignment_quality: str,
    indicator_consistency: bool
) -> str:
    """根據多因素調整信心水準"""

    confidence_map = {'high': 3, 'medium': 2, 'low': 1}
    score = confidence_map[base_confidence]

    # 對齊品質低 → 降級
    if alignment_quality == 'low':
        score -= 1

    # 多指標一致 → 升級
    if indicator_consistency:
        score += 1

    # 轉回文字
    if score >= 3:
        return 'high'
    elif score >= 2:
        return 'medium'
    else:
        return 'low'
```

</confidence_factors>

<limitations>

**方法論限制**

1. **供給側干擾**
   - 貨運量下降可能是供給受限（如港口壅塞）
   - 需區分需求減弱 vs 供給瓶頸

2. **結構性變化**
   - 電商改變貨運結構
   - 疫情後供應鏈重組
   - 服務業占比上升，製造業貨運代表性下降

3. **全球化因素**
   - 進口通膨獨立於北美貨運
   - 匯率變動影響進口價格

4. **政策干預**
   - 大規模財政刺激可能延長通膨週期
   - 貨幣政策影響通膨的路徑可能繞過貨運

**建議**：
- 同時觀察 CASS 四個指標
- 考慮供給側因素
- 關注 Fed 政策聲明
- 不要只依賴單一訊號做決策

</limitations>
