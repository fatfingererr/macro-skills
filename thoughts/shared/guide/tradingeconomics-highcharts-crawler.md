# TradingEconomics Highcharts 圖表爬蟲指南

從 TradingEconomics 網站的 Highcharts 互動圖表中提取完整時間序列數據的實戰經驗整理。

> **推薦方法**：使用 Chrome CDP 全自動模式（自動啟動/關閉 Chrome），詳見 [Chrome CDP 數據爬取 SOP](./chrome-cdp-scraping-sop.md)

---

## 目錄

1. [網站特點](#網站特點)
2. [URL 模式與商品對應](#url-模式與商品對應)
3. [Highcharts 數據結構](#highcharts-數據結構)
4. [時間範圍按鈕操作](#時間範圍按鈕操作)
5. [1Y+5Y 雙重抓取策略](#1y5y-雙重抓取策略)
6. [完整實作流程](#完整實作流程)
7. [數據後處理](#數據後處理)
8. [快取策略](#快取策略)
9. [常見問題與解決方案](#常見問題與解決方案)
10. [可用商品清單](#可用商品清單)
11. [本專案實作參考](#本專案實作參考)

---

## 網站特點

### 架構概覽

```
┌─────────────────────────────────────────────────────────────┐
│              TradingEconomics 圖表頁面結構                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  技術棧：                                                    │
│  ├─ 圖表庫：Highcharts（全站商品圖表統一）                  │
│  ├─ 防護：Cloudflare（偵測 Selenium/自動化瀏覽器）          │
│  ├─ 數據載入：AJAX 動態載入                                 │
│  └─ 渲染時間：需 20-25 秒完全渲染                           │
│                                                              │
│  數據特點：                                                  │
│  ├─ 時間序列：從 Highcharts 對象直接提取                    │
│  ├─ 格式：Unix 時間戳 (毫秒) + 數值                         │
│  ├─ 時間範圍按鈕：1D / 5D / 1M / 3M / 6M / 1Y / 5Y / MAX  │
│  ├─ 預設顯示範圍：約 1Y（日頻數據）                         │
│  ├─ 5Y 範圍：約 5 年（週頻數據）                            │
│  └─ 單一 Series：通常每個商品圖表只有一個主要 series        │
│                                                              │
│  關鍵差異（與 MacroMicro 比較）：                            │
│  ├─ 頁面載入速度較快（~25 秒 vs MacroMicro ~35 秒）         │
│  ├─ 有明確的時間範圍按鈕可切換                              │
│  ├─ 不同時間範圍 = 不同數據頻率（1Y=日頻, 5Y=週頻）        │
│  └─ 部分指標 URL 不在 /commodity/ 路徑下                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 為何不用 API？

| 方案                  | 可行性               | 說明                           |
|-----------------------|----------------------|--------------------------------|
| 官方 API              | ⚠️ 需付費             | 免費方案有嚴格限制             |
| 直接 HTTP 請求        | ❌ 無法取得數據       | 數據由 JavaScript 動態渲染     |
| Selenium 自動化       | ❌ 被 Cloudflare 封鎖 | 自動化瀏覽器立即被偵測         |
| **Chrome CDP 全自動** | ✅ 推薦               | 自動啟動/關閉 Chrome，繞過防護 |

---

## URL 模式與商品對應

### URL 結構

TradingEconomics 有兩種 URL 模式：

```
# 模式一：商品（大多數）
https://tradingeconomics.com/commodity/{slug}

# 模式二：經濟指標（特殊 URL）
https://tradingeconomics.com/{country}/{indicator}
```

### SYMBOL_MAP 設計

使用字典映射商品代碼到網站資訊，支援自訂 URL：

```python
SYMBOL_MAP = {
    # 標準商品（使用 /commodity/{slug}）
    "natural-gas": {
        "slug": "natural-gas",
        "unit": "USD/MMBtu",
        "name": "Natural Gas"
    },
    "urea": {
        "slug": "urea",
        "unit": "USD/ton",
        "name": "Urea"
    },

    # 特殊 URL（不在 /commodity/ 路徑下）
    "dollar-index": {
        "slug": "dollar-index",
        "unit": "Index",
        "name": "US Dollar Index (DXY)",
        "url": "https://tradingeconomics.com/united-states/currency"
        # ↑ 自訂 URL，覆蓋預設的 /commodity/{slug}
    },
}
```

### URL 解析邏輯

```python
TE_BASE_URL = "https://tradingeconomics.com/commodity"

symbol_info = SYMBOL_MAP.get(symbol, {"slug": symbol})
# 優先使用自訂 url，否則走預設路徑
target_url = symbol_info.get('url', f"{TE_BASE_URL}/{symbol_info['slug']}")
```

> **注意**：部分指標（如 DXY）在 `/commodity/dollar-index` 頁面上沒有 1Y/5Y 按鈕，必須使用 `/united-states/currency` 這類頁面才能正確抓取。

---

## Highcharts 數據結構

### 全域對象

TradingEconomics 使用 Highcharts 渲染圖表，數據存儲在全域 `Highcharts.charts` 陣列中：

```javascript
Highcharts.charts                    // 所有圖表實例
Highcharts.charts[0].series          // 第一個圖表的所有 series
Highcharts.charts[0].series[0].xData // 時間戳陣列（毫秒）
Highcharts.charts[0].series[0].yData // 數值陣列
```

### 數據提取 JavaScript

```javascript
(function() {
    if (typeof Highcharts === 'undefined' || !Highcharts.charts) {
        return JSON.stringify({error: 'Highcharts not found'});
    }

    var charts = Highcharts.charts.filter(c => c !== undefined && c !== null);
    if (charts.length === 0) {
        return JSON.stringify({error: 'No charts found'});
    }

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

            // 優先使用 xData/yData（更可靠）
            if (s.xData && s.xData.length > 0) {
                for (var k = 0; k < s.xData.length; k++) {
                    if (s.yData[k] !== null && s.yData[k] !== undefined) {
                        seriesData.push({
                            x: s.xData[k],
                            y: s.yData[k],
                            date: new Date(s.xData[k]).toISOString().split('T')[0]
                        });
                    }
                }
            } else if (s.data && s.data.length > 0) {
                seriesData = s.data.filter(p => p && p.y !== null).map(function(point) {
                    return {
                        x: point.x,
                        y: point.y,
                        date: point.x ? new Date(point.x).toISOString().split('T')[0] : null
                    };
                });
            }

            if (seriesData.length > 0) {
                chartInfo.series.push({
                    name: s.name || 'Series ' + j,
                    type: s.type,
                    dataLength: seriesData.length,
                    data: seriesData
                });
            }
        }

        if (chartInfo.series.length > 0) {
            result.push(chartInfo);
        }
    }

    return JSON.stringify(result);
})()
```

### 關鍵洞察

1. **優先使用 `xData`/`yData`**：比 `s.data` 更可靠，尤其在按鈕切換後 `s.data` 可能未完全更新
2. **過濾 null 值**：TradingEconomics 的數據中可能包含 `null` 的 y 值，必須濾除
3. **選擇最大 series**：通常每個商品頁有多個圖表（主圖 + 迷你圖），選數據點最多的那個
4. **返回值為字串**：CDP `Runtime.evaluate` 中，IIFE 必須 `return JSON.stringify(result)`

---

## 時間範圍按鈕操作

### 按鈕結構

TradingEconomics 的時間範圍按鈕是 `<a>`, `<button>`, 或 `<span>` 元素，文字為 `1D`, `5D`, `1M`, `3M`, `6M`, `1Y`, `5Y`, `MAX`。

### 點擊按鈕 JavaScript

```javascript
(function() {
    var target = '5Y';  // 或 '1Y'
    // 第一輪：遍歷所有 a/button/span
    var buttons = document.querySelectorAll('a, button, span');
    for (var i = 0; i < buttons.length; i++) {
        var text = buttons[i].textContent.trim();
        if (text === target || text.toLowerCase() === target.toLowerCase()) {
            buttons[i].click();
            return JSON.stringify({success: true, clicked: target});
        }
    }
    // 第二輪：嘗試 data-range 屬性選擇器
    var rangeButtons = document.querySelectorAll(
        '[data-range], .chart-range-btn, .range-selector button'
    );
    for (var i = 0; i < rangeButtons.length; i++) {
        var text = rangeButtons[i].textContent.trim();
        if (text === target || text.toLowerCase() === target.toLowerCase()) {
            rangeButtons[i].click();
            return JSON.stringify({success: true, clicked: target + ' (alt)'});
        }
    }
    return JSON.stringify({success: false, error: target + ' button not found'});
})()
```

### 產生器函數

```python
def make_click_button_js(label: str) -> str:
    """生成點擊指定時間範圍按鈕的 JavaScript"""
    return f'''(function() {{
        var target = '{label}';
        var buttons = document.querySelectorAll('a, button, span');
        for (var i = 0; i < buttons.length; i++) {{
            var text = buttons[i].textContent.trim();
            if (text === target || text.toLowerCase() === target.toLowerCase()) {{
                buttons[i].click();
                return JSON.stringify({{success: true, clicked: target}});
            }}
        }}
        return JSON.stringify({{success: false, error: target + ' button not found'}});
    }})()'''

CLICK_1Y_BUTTON_JS = make_click_button_js('1Y')
CLICK_5Y_BUTTON_JS = make_click_button_js('5Y')
```

### 點擊後等待

按鈕點擊後，Highcharts 會重新載入數據。**必須等待 6 秒**讓圖表重新渲染完成：

```python
click_result = cdp_execute_js(ws_url, CLICK_1Y_BUTTON_JS)
time.sleep(6)  # 等待圖表重新渲染
data = cdp_execute_js(ws_url, EXTRACT_HIGHCHARTS_JS)
```

---

## 1Y+5Y 雙重抓取策略

### 問題背景

TradingEconomics 預設顯示約 1 年的日頻數據。如果需要更長歷史，切到 5Y 會得到週頻數據，但會丟失日頻精度。

### 解決方案：雙重抓取 + 合併

```
┌─────────────────────────────────────────────────────────────┐
│                 1Y+5Y 雙重抓取策略                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Step 1: 點擊 1Y → 提取日頻數據                            │
│          ├─ 範圍：約 today - 1Y ~ today                     │
│          ├─ 頻率：日頻（每個交易日一筆）                    │
│          └─ 約 250-300 筆數據                               │
│                                                              │
│  Step 2: 點擊 5Y → 提取週頻數據                            │
│          ├─ 範圍：約 today - 5Y ~ today                     │
│          ├─ 頻率：週頻（每週一筆）                          │
│          └─ 約 250-260 筆數據                               │
│                                                              │
│  Step 3: 合併                                                │
│          ├─ 找出 1Y 日頻的最早日期 = cutoff_date            │
│          ├─ 5Y 只保留 cutoff_date 之前的部分                │
│          ├─ concat([5Y_old, 1Y])                            │
│          └─ 去重 + 排序                                     │
│                                                              │
│  結果：                                                      │
│          ├─ 近 1 年：日頻（高精度）                          │
│          ├─ 1~5 年前：週頻（完整歷史覆蓋）                  │
│          └─ 無縫接合，約 450-500 筆數據                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 抓取流程（單一商品）

```python
# Step 1: 1Y 日頻
click_result = cdp_execute_js(ws_url, CLICK_1Y_BUTTON_JS)
time.sleep(6)
data_1y = cdp_execute_js(ws_url, EXTRACT_HIGHCHARTS_JS)

# Step 2: 5Y 週頻
click_result = cdp_execute_js(ws_url, CLICK_5Y_BUTTON_JS)
time.sleep(6)
data_5y = cdp_execute_js(ws_url, EXTRACT_HIGHCHARTS_JS)

# 儲存兩份
result = {
    "charts_1y": data_1y,
    "charts_5y": data_5y,
}
```

### 合併邏輯

```python
def extract_price_series(chart_data):
    """合併 1Y 日頻 + 5Y 週頻數據"""
    df_1y = _extract_series_from_charts(chart_data.get('charts_1y'))
    df_5y = _extract_series_from_charts(chart_data.get('charts_5y'))

    if df_1y is not None and df_5y is not None:
        # 1Y 數據的最早日期作為切割點
        cutoff_date = df_1y['date'].min()

        # 5Y 只保留 cutoff 之前的部分（避免重複）
        df_5y_old = df_5y[df_5y['date'] < cutoff_date].copy()

        # 合併：舊的週頻 + 新的日頻
        df = pd.concat([df_5y_old, df_1y], ignore_index=True)
        df = df.drop_duplicates(subset=['date']).sort_values('date').reset_index(drop=True)
        return df

    # Fallback: 只有其中一份
    return df_1y if df_1y is not None else df_5y
```

### 輔助函數：從 charts 列表提取最佳 series

```python
def _extract_series_from_charts(charts):
    """從 charts 列表中提取數據點最多的 series"""
    if not charts:
        return None

    best_series = None
    max_points = 0

    for chart in charts:
        for series in chart.get('series', []):
            data_length = series.get('dataLength', 0)
            if data_length > max_points:
                max_points = data_length
                best_series = series

    if not best_series or max_points == 0:
        return None

    df = pd.DataFrame(best_series['data'])
    df['date'] = pd.to_datetime(df['date'])
    df = df.rename(columns={'y': 'value'})
    return df[['date', 'value']].dropna().sort_values('date').reset_index(drop=True)
```

---

## 完整實作流程

### 流程圖

```
┌─────────────────────────────────────────────────────────────┐
│             TradingEconomics 全自動爬蟲流程                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 檢查快取                                                 │
│     ├─ 快取存在且未過期 → 直接使用，跳到 Step 7             │
│     └─ 快取不存在或已過期 → 繼續                            │
│                                                              │
│  2. 啟動 Chrome                                              │
│     ├─ 檢測 CDP 端口是否已開啟                               │
│     ├─ 未開啟 → 自動啟動 Chrome (--remote-debugging-port)    │
│     └─ 已開啟 → 重用現有 Chrome                             │
│     詳見：chrome-cdp-scraping-sop.md                         │
│                                                              │
│  3. 導航到商品頁面                                           │
│     ├─ 使用 Page.navigate CDP 命令                           │
│     └─ 等待 25 秒（頁面 + Highcharts 渲染）                 │
│                                                              │
│  4. 抓取 1Y 日頻數據                                        │
│     ├─ 點擊 1Y 按鈕（等待 6 秒）                            │
│     └─ 提取 Highcharts 數據                                 │
│                                                              │
│  5. 抓取 5Y 週頻數據                                        │
│     ├─ 點擊 5Y 按鈕（等待 6 秒）                            │
│     └─ 提取 Highcharts 數據                                 │
│                                                              │
│  6. 關閉 Chrome                                              │
│     └─ 如果是本次啟動的，自動關閉                           │
│                                                              │
│  7. 數據後處理                                               │
│     ├─ 合併 1Y + 5Y（日頻優先）                             │
│     ├─ 存入快取（JSON 原始 + CSV 整理）                     │
│     └─ 返回 DataFrame                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 等待時間建議

| 階段         | 建議等待時間 | 說明                       |
|--------------|--------------|----------------------------|
| Chrome 啟動  | 最多 30 秒   | 輪詢 CDP 端口直到可用      |
| 初始頁面載入 | 25 秒        | 頁面框架 + Highcharts 渲染 |
| 按鈕點擊後   | 6 秒         | 圖表重新渲染               |
| 多商品間導航 | 25 秒        | 新頁面載入                 |

**單一商品總計**：約 67 秒（啟動 + 載入 + 1Y + 5Y + 關閉）

### 多商品批量抓取

多個商品共享同一個 Chrome 實例，第二個商品開始只需導航 + 等待：

```
商品 1: 啟動 Chrome → 載入頁面(25s) → 1Y(6s) → 5Y(6s) = ~67s
商品 2: 導航(25s) → 1Y(6s) → 5Y(6s) = ~37s
商品 3: 導航(25s) → 1Y(6s) → 5Y(6s) = ~37s
                                       關閉 Chrome
```

---

## 數據後處理

### 週頻/日頻分界點偵測

合併後的數據在時間軸上有一個分界點：之前是週頻，之後是日頻。這個分界點在可視化時可能需要標記。

```python
def find_daily_start(df: pd.DataFrame) -> pd.Timestamp:
    """偵測數據從週頻切換到日頻的時間點"""
    gaps = df["date"].diff().dt.days
    daily_mask = gaps <= 2  # 日頻的間隔 <= 2 天
    if daily_mask.any():
        return df.loc[daily_mask.idxmax(), "date"]
    return df["date"].iloc[-1]
```

### DXY 調整（可選）

將商品價格除以美元指數，消除美元強弱對價格的影響：

```python
def dxy_adjust(price_df, dxy_df):
    """DXY 調整：price / DXY * 100"""
    merged = pd.merge(price_df, dxy_df.rename(columns={"value": "dxy"}),
                      on="date", how="left")
    merged["dxy"] = merged["dxy"].ffill().bfill()
    merged["value"] = merged["value"] / merged["dxy"] * 100
    return merged[["date", "value"]].dropna()
```

---

## 快取策略

### 雙層快取

```python
class TECache:
    def __init__(self, cache_dir='data/cache', max_age_hours=12):
        self.cache_dir = Path(cache_dir)
        self.max_age = timedelta(hours=max_age_hours)

    def _raw_cache_path(self, symbol):
        return self.cache_dir / f"{symbol}_raw.json"  # 原始 JSON

    def _csv_path(self, symbol):
        return self.cache_dir / f"{symbol}.csv"        # 整理後 CSV
```

| 層級     | 格式 | 用途                                 |
|----------|------|--------------------------------------|
| 原始快取 | JSON | 保留完整的 `charts_1y` + `charts_5y` |
| 整理快取 | CSV  | `date,value` 兩欄，可直接載入分析    |

### 快取檔案命名

```
data/cache/
├── natural-gas_raw.json      # 原始 Highcharts 數據
├── natural-gas.csv           # 整理後 CSV
├── urea_raw.json
├── urea.csv
├── dollar-index_raw.json
└── dollar-index.csv
```

### 快取有效期

- **預設 12 小時**：商品價格日頻足夠
- **強制更新**：`--force-refresh` 旗標

---

## 常見問題與解決方案

### 問題 1：1Y/5Y 按鈕未找到

**症狀**：`{success: false, error: '1Y button not found'}`

**原因**：
- 部分頁面（如 `/commodity/dollar-index`）不含時間範圍按鈕
- 按鈕文字不匹配（大小寫或空格）

**解決方案**：
```python
# 1. 使用正確的 URL（有些指標需要特殊路徑）
"dollar-index": {
    "url": "https://tradingeconomics.com/united-states/currency"
}

# 2. 點擊失敗時 fallback 到預設數據
if not click_data.get('success'):
    print("[Warning] 按鈕未找到，使用預設數據")
```

### 問題 2：Highcharts 未載入

**症狀**：`{error: 'Highcharts not found'}`

**解決方案**：
- 增加等待時間（25 → 35 秒）
- 確認頁面 URL 正確（Cloudflare 可能重定向到驗證頁）

### 問題 3：數據點為空

**症狀**：所有 series 的 `dataLength` 為 0

**解決方案**：
- 優先使用 `xData`/`yData`（而非 `s.data`）
- 按鈕點擊後等待更久（6 → 10 秒）

### 問題 4：被 Cloudflare 封鎖

**症狀**：頁面顯示 Cloudflare 驗證

**解決方案**：
- 使用 Chrome CDP（非 Selenium）— 對網站來說是真人瀏覽器
- 使用帶有真實瀏覽歷史的 Chrome profile
- 參考 [Chrome CDP 數據爬取 SOP](./chrome-cdp-scraping-sop.md)

### 問題 5：多商品抓取時第二個商品失敗

**症狀**：第一個商品正常，後續導航失敗

**解決方案**：
```python
# 確保導航後重新取得 WebSocket URL
navigate_to_url(port, target_url)
time.sleep(wait_seconds)
ws_url = get_cdp_ws_url(port)  # 重新取得！
```

---

## 可用商品清單

### 能源

| 商品代碼         | 名稱           | URL Slug       | 單位      |
|------------------|----------------|----------------|-----------|
| `natural-gas`    | Natural Gas    | natural-gas    | USD/MMBtu |
| `eu-natural-gas` | EU Natural Gas | eu-natural-gas | EUR/MWh   |
| `uk-natural-gas` | UK Natural Gas | uk-natural-gas | GBP/therm |

### 化肥

| 商品代碼      | 名稱              | URL Slug    | 單位    |
|---------------|-------------------|-------------|---------|
| `urea`        | Urea              | urea        | USD/ton |
| `dap`         | DAP               | dap         | USD/ton |
| `fertilizers` | Fertilizers Index | fertilizers | Index   |

### 指數

| 商品代碼       | 名稱                  | URL                                                   | 單位  |
|----------------|-----------------------|-------------------------------------------------------|-------|
| `dollar-index` | US Dollar Index (DXY) | `https://tradingeconomics.com/united-states/currency` | Index |

### 探索更多商品

```
https://tradingeconomics.com/commodities
```

1. 在 TradingEconomics 網站瀏覽商品列表
2. 點進商品頁面，複製 URL 中的 slug
3. 加入 `SYMBOL_MAP` 即可使用

---

## 本專案實作參考

| 檔案                                                                                      | 說明                           |
|-------------------------------------------------------------------------------------------|--------------------------------|
| `.claude/skills/analyze-gas-fertilizer-contract-shock/scripts/fetch_te_data.py`           | 完整 TradingEconomics 爬蟲實作 |
| `.claude/skills/analyze-gas-fertilizer-contract-shock/scripts/visualize_shock_regimes.py` | DXY 調整可視化實作             |
| `.claude/skills/analyze-gas-fertilizer-contract-shock/data/cache/`                        | 快取數據範例                   |

### 相關指南

| 指南                                                                 | 說明                                           |
|----------------------------------------------------------------------|------------------------------------------------|
| [Chrome CDP 數據爬取 SOP](./chrome-cdp-scraping-sop.md)              | CDP 連接原理、Chrome 啟動/關閉、WebSocket 操作 |
| [MacroMicro Highcharts 爬蟲指南](./macromicro-highcharts-crawler.md) | 類似架構的另一個網站爬蟲                       |

---

## 總結

| 要點     | 說明                                                   |
|----------|--------------------------------------------------------|
| 核心技術 | Chrome CDP 全自動 + Highcharts `xData`/`yData` 提取    |
| 數據策略 | 1Y 日頻 + 5Y 週頻雙重抓取，合併為完整時間序列          |
| 按鈕等待 | 點擊時間範圍按鈕後等待 6 秒                            |
| 頁面載入 | 首次 25 秒，後續導航 25 秒                             |
| 數據結構 | `{x: 時間戳, y: 數值, date: "YYYY-MM-DD"}`             |
| 快取建議 | 12 小時內使用本地快取（JSON 原始 + CSV 整理雙層快取）  |
| URL 注意 | 部分指標不在 `/commodity/` 路徑下，需用 `url` 欄位自訂 |
