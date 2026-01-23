<overview>
此參考文件列出貨運領先通膨分析所需的資料來源，包括 CASS Freight Index 的 MacroMicro 爬蟲說明。

**資料來源**：
- **CASS Freight Index**：MacroMicro Highcharts 圖表（主要）
- **CPI**：FRED（輔助驗證用）

**推薦方法**：Chrome CDP（繞過 Cloudflare）
</overview>

<data_access_methods>

<method name="chrome_cdp" recommended="true">
**Chrome CDP 方法（推薦）**

透過 Chrome DevTools Protocol 連接到已開啟的 Chrome 瀏覽器，完全繞過 Cloudflare 和反爬蟲偵測。

**原理**：
```
┌─────────────────┐     WebSocket      ┌─────────────────┐
│  Python Script  │ ◄────────────────► │  Chrome Browser │
│  (CDP Client)   │    Port 9222       │  (你的 Profile) │
└─────────────────┘                    └─────────────────┘
        │                                      │
        │ Runtime.evaluate()                   │
        ▼                                      ▼
   執行 JavaScript ──────────────────► 提取 Highcharts 數據
```

**前置準備**：
```bash
# 安裝依賴
pip install requests websocket-client pandas
```

**操作流程**：

**Step 1：關閉所有 Chrome 視窗**

**Step 2：啟動 Chrome（帶調試端口）**

```bash
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --remote-allow-origins=* ^
  --user-data-dir="%USERPROFILE%\.chrome-debug-profile" ^
  "https://www.macromicro.me/charts/46877/cass-freight-index"
```

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir="$HOME/.chrome-debug-profile" \
  "https://www.macromicro.me/charts/46877/cass-freight-index"
```

**Step 3：等待頁面完全載入**（圖表顯示）

**Step 4：執行爬蟲腳本**
```bash
cd scripts
python fetch_cass_freight.py --cdp
```

**關鍵參數說明**：

| 參數 | 說明 |
|------|------|
| `--remote-debugging-port=9222` | 開啟 CDP 調試端口 |
| `--remote-allow-origins=*` | 允許所有來源連線（**必要**） |
| `--user-data-dir=<path>` | 指定 profile 目錄（**必須非預設**） |

**腳本位置**: `scripts/fetch_cass_freight.py`
</method>

<method name="selenium" recommended="false">
**Selenium 方法（備選）**

當 CDP 方法不可用時的備選方案。注意：**Cloudflare 經常會擋住 Selenium**。

```bash
# 安裝依賴
pip install selenium webdriver-manager pandas

# 執行（顯示瀏覽器視窗以便手動通過驗證）
python scripts/fetch_cass_freight.py --selenium --no-headless
```

**配置**：
```python
CASS_FREIGHT_URL = "https://www.macromicro.me/charts/46877/cass-freight-index"
CHART_WAIT_SECONDS = 35  # 等待圖表渲染
MAX_RETRIES = 3
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

MacroMicro 使用 Highcharts 渲染圖表，數據存儲在全域 `Highcharts.charts` 陣列中：

```javascript
// 瀏覽器控制台中執行
Highcharts.charts                    // 所有圖表實例
Highcharts.charts[0].series          // 第一個圖表的所有 series
Highcharts.charts[0].series[0].data  // 第一個 series 的數據點
```

**數據提取 JavaScript**：
```javascript
(function() {
    if (typeof Highcharts === 'undefined' || !Highcharts.charts) {
        return JSON.stringify({error: 'Highcharts not found'});
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
            var seriesData = [];

            // 優先使用 xData/yData
            if (s.xData && s.xData.length > 0) {
                for (var k = 0; k < s.xData.length; k++) {
                    seriesData.push({
                        x: s.xData[k],
                        y: s.yData[k],
                        date: new Date(s.xData[k]).toISOString().split('T')[0]
                    });
                }
            } else if (s.data && s.data.length > 0) {
                seriesData = s.data.map(function(point) {
                    return {
                        x: point.x,
                        y: point.y,
                        date: point.x ? new Date(point.x).toISOString().split('T')[0] : null
                    };
                });
            }

            chartInfo.series.push({
                name: s.name,
                dataLength: seriesData.length,
                data: seriesData
            });
        }
        result.push(chartInfo);
    }
    return JSON.stringify(result);
})()
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
python scripts/fetch_cass_freight.py --cdp --cache-dir ./cache
```

**強制更新**：
```bash
python scripts/fetch_cass_freight.py --cdp --cache-dir ./cache --force-refresh
```

</cache_strategy>

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

<troubleshooting>

**常見問題排解**

**Q1: WebSocket 連線被拒絕 (403 Forbidden)**

確認啟動 Chrome 時有加上 `--remote-allow-origins=*` 參數。

**Q2: 無法連接到 Chrome 調試端口**

1. 確保所有 Chrome 視窗都已關閉
2. 確認使用了非預設的 `--user-data-dir`
3. 檢查端口 9222 是否被佔用：`curl -s http://127.0.0.1:9222/json`

**Q3: Highcharts not found**

1. 確認頁面已完全載入（圖表已顯示）
2. 在瀏覽器 Console 中執行 `typeof Highcharts` 確認
3. 可能需要登入 MacroMicro 帳號

**Q4: 被 Cloudflare 擋住**

1. 使用 CDP 方法而非 Selenium
2. 在 Chrome 中手動完成 Cloudflare 驗證
3. 登入 MacroMicro 帳號後再執行

</troubleshooting>

<scripts_reference>

**資料抓取腳本**

| 腳本 | 功能 | 資料來源 |
|------|------|---------|
| `scripts/fetch_cass_freight.py` | 抓取 CASS 四個指標 | MacroMicro |
| `scripts/freight_inflation_detector.py` | 完整分析（含 CPI） | MacroMicro + FRED |

**使用範例**：

```bash
# 方法一：Chrome CDP（推薦）
# 先啟動 Chrome 調試模式，載入目標頁面，然後：
python scripts/fetch_cass_freight.py --cdp

# 方法二：Selenium（備選）
python scripts/fetch_cass_freight.py --selenium --no-headless

# 快速檢查
python scripts/freight_inflation_detector.py --quick

# 完整分析（使用 shipments_yoy）
python scripts/freight_inflation_detector.py --start 2015-01-01 --indicator shipments_yoy
```

</scripts_reference>

<related_guides>

**相關指南**

- [Chrome CDP 數據爬取 SOP](../../../thoughts/shared/guide/chrome-cdp-scraping-sop.md)
- [MacroMicro Highcharts 爬蟲指南](../../../thoughts/shared/guide/macromicro-highcharts-crawler.md)

</related_guides>
