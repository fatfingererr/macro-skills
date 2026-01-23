<overview>
此參考文件列出貨運領先通膨分析所需的資料來源，包括 CASS Freight Index 的 MacroMicro 爬蟲說明。

**資料來源**：
- **CASS Freight Index**：MacroMicro Highcharts 圖表（主要）
- **CPI**：FRED（輔助驗證用）
</overview>

<data_access_methods>

<method name="macromicro_highcharts" recommended="true">
**MacroMicro Highcharts 爬蟲（推薦）**

```
URL: https://en.macromicro.me/charts/46877/cass-freight-index
```

**技術說明**：
- 使用 Selenium + ChromeDriver
- 等待 Highcharts 圖表完全渲染
- 透過 JavaScript 提取 `Highcharts.charts` 物件中的數據
- 帶防偵測配置（隨機 User-Agent、disable automation）

**爬蟲配置**：
```python
CASS_FREIGHT_URL = "https://en.macromicro.me/charts/46877/cass-freight-index"
CHART_WAIT_SECONDS = 35  # 等待圖表渲染
MAX_RETRIES = 3
CACHE_MAX_AGE_HOURS = 12
```

**腳本位置**: `scripts/fetch_cass_freight.py`
</method>

<method name="fred_csv">
**FRED CSV Endpoint（CPI 資料）**

```
https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL
```

**用途**：取得 CPI 數據進行領先性驗證

**腳本位置**: `scripts/freight_inflation_detector.py` (內建)
</method>

</data_access_methods>

<cass_freight_index>

**CASS Freight Index 四個指標**

| 指標 Key | 系列名稱 | 說明 | 用途 |
|----------|----------|------|------|
| `shipments_index` | Shipments Index | 出貨量指數 | 衡量實體經濟需求強度 |
| `expenditures_index` | Expenditures Index | 運費支出指數 | 衡量物流成本壓力 |
| `shipments_yoy` | Shipments YoY | 出貨量年增率 | **主要分析指標**（週期轉折偵測） |
| `expenditures_yoy` | Expenditures YoY | 支出年增率 | 驗證成本傳導 |

**資料特性**：
- 由 Cass Information Systems 編制
- 追蹤北美地區的貨運出貨量與支出
- 月度更新，約滯後 1 個月
- 涵蓋卡車和鐵路運輸

**推薦指標優先順序**：
1. `shipments_yoy` - 最適合週期轉折偵測
2. `expenditures_yoy` - 交叉驗證用
3. `shipments_index` / `expenditures_index` - 絕對水準參考

</cass_freight_index>

<cpi_series>

**CPI 指標（FRED）**

| 別名 | Series ID | 描述 | 頻率 | 更新延遲 |
|------|-----------|------|------|----------|
| `cpi_headline` | CPIAUCSL | CPI All Urban Consumers | 月 | ~15 天 |

**CPIAUCSL**：
- 來源：Bureau of Labor Statistics (BLS)
- 涵蓋：所有城市消費者
- 季節調整：是
- 用途：計算通膨年增率，驗證貨運的領先性

</cpi_series>

<highcharts_extraction>

**Highcharts 數據提取邏輯**

```javascript
// 提取 Highcharts 圖表數據的 JavaScript
if (typeof Highcharts === 'undefined') {
    return {error: 'Highcharts not loaded', retry: true};
}

var charts = Highcharts.charts.filter(c => c !== undefined && c !== null);
var result = [];

for (var i = 0; i < charts.length; i++) {
    var chart = charts[i];
    var chartInfo = {
        title: chart.title ? chart.title.textStr : 'Chart ' + i,
        series: []
    };

    for (var j = 0; j < chart.series.length; j++) {
        var s = chart.series[j];
        var seriesData = s.data.map(function(point) {
            return {
                x: point.x,
                y: point.y,
                date: point.x ? new Date(point.x).toISOString().split('T')[0] : null
            };
        });
        chartInfo.series.push({
            name: s.name,
            data: seriesData
        });
    }
    result.push(chartInfo);
}
return result;
```

**Series 匹配關鍵字**：
```python
CASS_SERIES_KEYWORDS = {
    "shipments_index": ["Shipments Index", "shipments index", "Shipments"],
    "expenditures_index": ["Expenditures Index", "expenditures index", "Expenditures"],
    "shipments_yoy": ["Shipments YoY", "shipments yoy", "Shipments Year"],
    "expenditures_yoy": ["Expenditures YoY", "expenditures yoy", "Expenditures Year"]
}
```

</highcharts_extraction>

<cache_strategy>

**快取策略**

| 參數 | 值 | 說明 |
|------|-----|------|
| 快取目錄 | `./cache` | 預設 |
| 最大有效期 | 12 小時 | CASS 為月度數據，無需頻繁更新 |
| 快取檔案 | `cass_freight_cache.json` | 原始 Highcharts 數據 |
| CSV 檔案 | `cass_{indicator}.csv` | 各指標獨立儲存 |

**使用快取**：
```bash
python scripts/fetch_cass_freight.py --cache-dir ./cache
```

**強制更新**：
```bash
python scripts/fetch_cass_freight.py --cache-dir ./cache --force-refresh
```

</cache_strategy>

<anti_detection>

**防偵測配置**

MacroMicro 可能會偵測自動化爬蟲，以下是防偵測設定：

```python
# Chrome Options
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
chrome_options.add_experimental_option('useAutomationExtension', False)

# 隨機 User-Agent
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...',
    ...
]

# 隨機延遲
delay = random.uniform(1.0, 2.0)
time.sleep(delay)
```

**注意事項**：
- 不要頻繁爬取（建議間隔 12 小時以上）
- 使用快取減少請求次數
- 若遭封鎖，等待一段時間後重試

</anti_detection>

<update_schedule>

**資料更新時程**

| 資料 | 來源 | 更新頻率 | 延遲 | 建議抓取時機 |
|------|------|---------|------|-------------|
| CASS Freight Index | MacroMicro | 月 | ~30 天 | 每月月底 |
| CPI | FRED | 月 | ~15 天 | 每月中旬 |

**監控建議**：
- 每月月底檢查 CASS 更新
- 設定快取有效期為 12 小時
- 重大經濟事件後可手動更新

</update_schedule>

<fallback_sources>

**備用數據源**

若 MacroMicro 無法存取：

1. **Cass Information Systems 官網**
   - https://www.cassinfo.com/freight-audit-payment/cass-transportation-indexes
   - 需手動下載 PDF/Excel

2. **其他替代指標（FRED 免費）**
   - TSI (Transportation Services Index): 涵蓋多種運輸方式
   - TRUCKD11 (Truck Tonnage Index): 卡車運量

**CASS vs 替代指標**：
| 指標 | 優點 | 缺點 |
|------|------|------|
| CASS | 最權威、細分完整 | 需爬蟲取得 |
| TSI | FRED 免費、涵蓋廣 | 平滑波動 |
| TRUCKD11 | FRED 免費、敏感度高 | 僅卡車 |

</fallback_sources>

<scripts_reference>

**資料抓取腳本**

| 腳本 | 功能 | 資料來源 |
|------|------|---------|
| `scripts/fetch_cass_freight.py` | 抓取 CASS 四個指標 | MacroMicro |
| `scripts/freight_inflation_detector.py` | 完整分析（含 CPI） | MacroMicro + FRED |

**使用範例**：

```bash
# 抓取 CASS 四個指標
python scripts/fetch_cass_freight.py --cache-dir ./cache

# 快速檢查
python scripts/freight_inflation_detector.py --quick

# 完整分析（使用 shipments_yoy）
python scripts/freight_inflation_detector.py --start 2015-01-01 --indicator shipments_yoy
```

</scripts_reference>
