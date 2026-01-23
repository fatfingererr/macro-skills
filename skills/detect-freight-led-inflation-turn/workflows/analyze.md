<required_reading>
**執行此 workflow 前，先閱讀：**
1. references/data-sources.md - CASS Freight Index 資料來源與爬蟲說明
2. references/methodology.md - CASS 與通膨領先性方法論
</required_reading>

<objective>
執行完整的 CASS Freight Index 週期轉折分析，產出三層訊號：Freight Status、Lead Alignment、Signal Assessment。
</objective>

<process>

<step number="1" name="執行分析腳本">

**使用 Python 腳本執行分析**

```bash
# 進入 skill 目錄
cd skills/detect-freight-led-inflation-turn

# 安裝依賴（首次使用）
pip install pandas numpy requests selenium webdriver-manager

# 執行完整分析
python scripts/freight_inflation_detector.py \
  --start {START_DATE} \
  --end {END_DATE} \
  --indicator {INDICATOR} \
  --lead-months {LEAD_MONTHS} \
  --yoy-threshold {YOY_THRESHOLD} \
  --output analysis_result.json
```

**參數說明**：
- `--start`: 起始日期 (YYYY-MM-DD)，建議至少 10 年歷史
- `--end`: 結束日期 (YYYY-MM-DD)
- `--indicator`: CASS 指標選擇
  - `shipments_yoy`（推薦，主要分析指標）
  - `expenditures_yoy`
  - `shipments_index`
  - `expenditures_index`
- `--lead-months`: 領先月數（預設 6）
- `--yoy-threshold`: YoY 警戒門檻（預設 0.0）
- `--cache-dir`: 快取目錄（可選，加速重複分析）

**範例**：
```bash
# 使用 Shipments YoY，分析 2015 年至今
python scripts/freight_inflation_detector.py --start 2015-01-01 --indicator shipments_yoy

# 使用 Expenditures YoY，領先 4 個月
python scripts/freight_inflation_detector.py --start 2015-01-01 --indicator expenditures_yoy --lead-months 4

# 使用快取加速
python scripts/freight_inflation_detector.py --start 2015-01-01 --cache-dir ./cache
```

</step>

<step number="2" name="抓取 CASS 四個指標">

**若需查看所有 CASS 指標**

```bash
python scripts/fetch_cass_freight.py --cache-dir ./cache
```

**輸出**：
```
CASS Freight Index 數據摘要
==================================================

[shipments_index]
  數據點: 300
  範圍: 2000-01-01 ~ 2025-12-01
  最新值: 1.15

[expenditures_index]
  數據點: 300
  範圍: 2000-01-01 ~ 2025-12-01
  最新值: 4.25

[shipments_yoy]
  數據點: 288
  範圍: 2001-01-01 ~ 2025-12-01
  最新值: -2.9

[expenditures_yoy]
  數據點: 288
  範圍: 2001-01-01 ~ 2025-12-01
  最新值: -1.5
```

</step>

<step number="3" name="計算週期狀態">

**核心計算邏輯（已內建於腳本）**

```python
import pandas as pd

# 1. 偵測週期低點
def detect_cycle_low(yoy: pd.Series, window: int = 18) -> pd.Series:
    """
    偵測是否為 N 個月新低

    Parameters
    ----------
    yoy : pd.Series
        CASS YoY 序列
    window : int
        回看窗口（月）

    Returns
    -------
    pd.Series
        布林值，True 表示為週期新低
    """
    rolling_min = yoy.rolling(window=window, min_periods=window).min()
    return yoy == rolling_min

# 2. 判斷週期狀態
def get_cycle_status(latest_yoy: float, is_new_low: bool) -> str:
    """
    判斷週期狀態

    Returns
    -------
    str
        'new_cycle_low' | 'negative' | 'positive'
    """
    if is_new_low and latest_yoy < 0:
        return 'new_cycle_low'
    elif latest_yoy < 0:
        return 'negative'
    else:
        return 'positive'
```

**驗證要點**：
- CASS YoY 數據直接使用（已是年增率）
- 週期低點窗口設定合理（12-18 個月）
- 處理缺失值（使用 ffill 或 interpolate）

</step>

<step number="4" name="進行領先對齊分析">

**將 CASS YoY 與 CPI YoY 對齊**

```python
def lead_alignment_analysis(
    cass_yoy: pd.Series,
    cpi_yoy: pd.Series,
    lead_months: int = 6
) -> dict:
    """
    領先對齊分析

    Parameters
    ----------
    cass_yoy : pd.Series
        CASS Shipments 年增率
    cpi_yoy : pd.Series
        CPI 年增率
    lead_months : int
        領先月數

    Returns
    -------
    dict
        包含領先相關性和對齊驗證
    """
    # 將 CASS YoY 向前平移
    cass_lead = cass_yoy.shift(lead_months)

    # 對齊並計算相關性
    aligned = pd.DataFrame({
        'cass_lead': cass_lead,
        'cpi': cpi_yoy
    }).dropna()

    correlation = aligned['cass_lead'].corr(aligned['cpi'])

    return {
        'correlation': correlation,
        'lead_months': lead_months,
        'alignment_quality': 'high' if correlation > 0.5 else 'medium' if correlation > 0.3 else 'low'
    }
```

</step>

<step number="5" name="產生訊號評估">

**訊號判斷邏輯**

```python
def assess_signal(
    cass_yoy: float,
    cycle_status: str,
    alignment_quality: str,
    yoy_threshold: float = 0.0
) -> dict:
    """
    訊號評估

    Returns
    -------
    dict
        包含 signal, confidence, macro_implication
    """
    # 訊號判斷
    if cycle_status == 'new_cycle_low' and cass_yoy < yoy_threshold:
        signal = 'inflation_easing'
        confidence = 'high'
        implication = '通膨壓力正在放緩，未來 CPI 下行風險上升'
    elif cass_yoy < yoy_threshold:
        signal = 'inflation_easing'
        confidence = 'medium'
        implication = 'CASS 指標轉負，通膨可能開始降溫'
    elif cycle_status == 'positive' and cass_yoy > 5:
        signal = 'inflation_rising'
        confidence = 'medium'
        implication = 'CASS 指標強勁，通膨上行壓力可能延續'
    else:
        signal = 'neutral'
        confidence = 'low'
        implication = 'CASS 指標處於中性區間，通膨方向待觀察'

    # 根據對齊品質調整信心
    if alignment_quality == 'low':
        confidence = 'low'

    return {
        'signal': signal,
        'confidence': confidence,
        'macro_implication': implication
    }
```

</step>

<step number="6" name="解讀分析結果">

**檢查輸出的 JSON 結構**

```python
import json
with open('analysis_result.json', 'r') as f:
    result = json.load(f)

# 1. Freight Status
print(f"CASS Shipments YoY: {result['freight_status']['yoy']}%")
print(f"週期狀態: {result['freight_status']['cycle_status']}")
print(f"是否為新低: {result['freight_status']['is_new_cycle_low']}")

# 2. Lead Alignment
print(f"領先相關性: {result['lead_alignment']['correlation']:.2f}")
print(f"對齊品質: {result['lead_alignment']['alignment_quality']}")

# 3. Signal Assessment
print(f"訊號: {result['signal_assessment']['signal']}")
print(f"信心: {result['signal_assessment']['confidence']}")
print(f"宏觀含義: {result['signal_assessment']['macro_implication']}")

# 4. All Indicators (所有四個 CASS 指標)
for key, data in result.get('all_indicators', {}).items():
    print(f"{key}: {data['latest_value']}")
```

</step>

<step number="7" name="生成報告（可選）">

**使用模板生成 Markdown 報告**

參考 `templates/output-markdown.md` 的模板結構，將 JSON 結果轉換為可讀報告。

```python
result = json.load(open('analysis_result.json'))

report = f"""
# CASS Freight Index 週期轉折分析報告

## 摘要

**訊號**: {result['signal_assessment']['signal']}
**信心水準**: {result['signal_assessment']['confidence']}

## CASS 狀態

- 選用指標: {result['freight_status']['indicator']}
- 最新 YoY: {result['freight_status']['yoy']}%
- 週期狀態: {result['freight_status']['cycle_status']}

## 四個指標概覽

| 指標 | 最新值 | 狀態 |
|------|-------|------|
| Shipments YoY | {result['all_indicators']['shipments_yoy']['latest_value']}% | {result['all_indicators']['shipments_yoy']['status']} |
| Expenditures YoY | {result['all_indicators']['expenditures_yoy']['latest_value']}% | {result['all_indicators']['expenditures_yoy']['status']} |

## 宏觀含義

{result['signal_assessment']['macro_implication']}

## 注意事項

{chr(10).join('- ' + c for c in result.get('caveats', []))}
"""
print(report)
```

</step>

</process>

<alternative_approach>

**若腳本無法執行，可手動分析**

1. **手動抓取 CASS 資料**
   - 訪問 https://en.macromicro.me/charts/46877/cass-freight-index
   - 記錄最新的 Shipments YoY 和 Expenditures YoY

2. **手動下載 CPI 資料**
   ```
   https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL
   ```

3. **在 Excel/Google Sheets 中計算**
   - 18M Rolling Min: `=MIN(OFFSET(cell,-17,0):cell)`
   - 是否新低: `=IF(YoY=Rolling_Min, TRUE, FALSE)`

4. **參考 references/methodology.md 中的判斷標準**

</alternative_approach>

<troubleshooting>

**常見問題**

<issue name="module_not_found">
**錯誤**: `ModuleNotFoundError: No module named 'selenium'`

**解決**:
```bash
pip install pandas numpy requests selenium webdriver-manager
```
</issue>

<issue name="chromedriver_error">
**錯誤**: `WebDriverException: chromedriver not found`

**解決**:
- webdriver-manager 會自動下載 ChromeDriver
- 確保安裝了 Google Chrome 瀏覽器
- 若仍有問題，手動下載 ChromeDriver
</issue>

<issue name="macromicro_blocked">
**錯誤**: 無法抓取 MacroMicro 資料

**解決**:
- 等待一段時間後重試（可能被暫時封鎖）
- 使用 `--cache-dir` 啟用快取
- 手動訪問網站確認是否正常
</issue>

<issue name="insufficient_data">
**錯誤**: 資料點不足

**解決**:
- 確保網路正常，CASS 資料成功抓取
- 檢查快取是否過期
</issue>

<issue name="divergent_indicators">
**情況**: Shipments YoY 和 Expenditures YoY 走勢不一致

**解決**:
- 這是正常情況，可能反映不同的經濟動態
- 報告中標註不一致性
- 以 Shipments YoY 為主要參考
</issue>

</troubleshooting>

<success_criteria>
此 workflow 完成時應確認：

- [ ] 成功抓取 CASS Freight Index 四個指標
- [ ] 成功抓取 CPI 資料（FRED）
- [ ] 計算選定指標的週期狀態（new_cycle_low / negative / positive）
- [ ] 完成與 CPI 的領先對齊分析
- [ ] 產生訊號評估（signal + confidence）
- [ ] 輸出包含可操作的宏觀含義
- [ ] 明確標註資料限制與假設
</success_criteria>
