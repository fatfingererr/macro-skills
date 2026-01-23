<required_reading>
**執行此 workflow 前，先閱讀：**
1. references/data-sources.md - CASS Freight Index 資料來源與爬蟲說明（含 Chrome CDP 方法）
2. references/methodology.md - CASS 與通膨領先性方法論
</required_reading>

<objective>
執行完整的 CASS Freight Index 週期轉折分析，產出三層訊號：Freight Status、Lead Alignment、Signal Assessment。
</objective>

<process>

<step number="1" name="抓取 CASS 數據">

**方法一：Chrome CDP（推薦）**

Chrome CDP 可以繞過 Cloudflare 防護，是最可靠的抓取方法。

```bash
# 安裝依賴
pip install requests websocket-client pandas numpy
```

**啟動 Chrome 調試模式**（關閉所有 Chrome 視窗後執行）：

**Windows**:
```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --remote-allow-origins=* ^
  --user-data-dir="%USERPROFILE%\.chrome-debug-profile" ^
  "https://www.macromicro.me/charts/46877/cass-freight-index"
```

**macOS**:
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir="$HOME/.chrome-debug-profile" \
  "https://www.macromicro.me/charts/46877/cass-freight-index"
```

等待頁面完全載入（圖表顯示），然後執行：
```bash
cd scripts
python fetch_cass_freight.py --cdp --cache-dir ./cache
```

**方法二：Selenium（備選）**

若 CDP 不可用：
```bash
pip install selenium webdriver-manager pandas numpy
python scripts/fetch_cass_freight.py --selenium --no-headless --cache-dir ./cache
```

</step>

<step number="2" name="執行分析腳本">

**使用 Python 腳本執行分析**

```bash
# 進入 scripts 目錄
cd scripts

# 執行完整分析
python freight_inflation_detector.py \
  --start {START_DATE} \
  --end {END_DATE} \
  --indicator {INDICATOR} \
  --lead-months {LEAD_MONTHS} \
  --yoy-threshold {YOY_THRESHOLD} \
  --cache-dir ./cache \
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
- `--cache-dir`: 快取目錄（使用步驟 1 抓取的數據）

**範例**：
```bash
# 使用 Shipments YoY，分析 2015 年至今
python freight_inflation_detector.py --start 2015-01-01 --indicator shipments_yoy --cache-dir ./cache

# 使用 Expenditures YoY，領先 4 個月
python freight_inflation_detector.py --start 2015-01-01 --indicator expenditures_yoy --lead-months 4 --cache-dir ./cache

# 快速檢查（使用快取）
python freight_inflation_detector.py --quick --cache-dir ./cache
```

**輸出範例**：
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

<step number="7" name="生成視覺化圖表">

**繪製 CASS vs CPI 領先性對比圖**

核心特徵：
1. CASS Freight Index 向前移動 6 個月（6M fwd）
2. 雙軸對比：CPI YoY（左軸）vs CASS（右軸）
3. NBER 衰退區間標記
4. Bloomberg 深色風格

```bash
python visualize_freight_cpi.py \
  --cache cache/cass_freight_cdp.json \
  --output ../../output/freight_cpi_$(date +%Y-%m-%d).png \
  --start 1995-01-01 \
  --lead-months 6
```

**參數說明**：
- `--cache`: CASS 數據快取路徑
- `--output`: 輸出圖片路徑（包含日期）
- `--start`: 圖表起始日期
- `--lead-months`: CASS 領先月數（預設 6）
- `--no-cpi`: 不抓取 CPI 數據（可選）

**輸出範例**：`output/freight_cpi_2026-01-23.png`

</step>

<step number="8" name="生成報告（可選）">

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

<issue name="cdp_connection_failed">
**錯誤**: 無法連接到 Chrome 調試端口

**解決**:
1. 確保所有 Chrome 視窗都已關閉
2. 確認啟動時使用了 `--remote-allow-origins=*`
3. 確認使用了非預設的 `--user-data-dir`
4. 檢查端口是否可用：`curl -s http://127.0.0.1:9222/json`
</issue>

<issue name="highcharts_not_found">
**錯誤**: `Highcharts not found`

**解決**:
1. 確認頁面已完全載入（圖表已顯示）
2. 在 Chrome Console 執行 `typeof Highcharts` 確認
3. 可能需要登入 MacroMicro 帳號
4. 等待更久讓圖表完全渲染
</issue>

<issue name="module_not_found">
**錯誤**: `ModuleNotFoundError: No module named 'websocket'`

**解決**:
```bash
# CDP 方法依賴
pip install requests websocket-client pandas numpy

# Selenium 方法依賴（備選）
pip install selenium webdriver-manager pandas numpy
```
</issue>

<issue name="macromicro_blocked">
**錯誤**: 被 Cloudflare 擋住

**解決**:
1. 優先使用 CDP 方法（最可靠）
2. 在 Chrome 中手動完成 Cloudflare 驗證
3. 登入 MacroMicro 帳號後再執行
4. 使用 `--cache-dir` 啟用快取減少請求
</issue>

<issue name="insufficient_data">
**錯誤**: 資料點不足

**解決**:
- 確保網路正常，CASS 資料成功抓取
- 檢查快取是否過期（有效期 12 小時）
- 使用 `--force-refresh` 強制重新抓取
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
- [ ] **生成 CASS vs CPI 領先性對比圖**（output/freight_cpi_YYYY-MM-DD.png）
- [ ] 明確標註資料限制與假設
</success_criteria>
