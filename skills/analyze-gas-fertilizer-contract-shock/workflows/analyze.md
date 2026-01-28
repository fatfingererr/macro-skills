# Workflow: 完整三段式因果分析

<required_reading>
**執行前請閱讀：**
1. references/data-sources.md - Chrome CDP 爬蟲說明
2. references/methodology.md - Shock 偵測與領先落後方法論
3. references/input-schema.md - 完整參數定義
</required_reading>

<process>

## Step 1: 數據準備

### 1.1 確認參數

收集用戶輸入或使用預設值：

```python
params = {
    "start_date": "2025-08-01",        # 分析起始日
    "end_date": "2026-02-01",          # 分析結束日
    "freq": "1D",                       # 日頻
    "te_symbols": {
        "natural_gas": "natural-gas",   # TradingEconomics slug
        "fertilizer": "urea"            # urea / dap / fertilizers
    },
    "spike_detection": {
        "return_window": 1,
        "z_window": 60,
        "parabolic_threshold": {"z": 3.0, "slope_pct_per_day": 1.5}
    },
    "lead_lag": {
        "max_lag_days": 60,
        "method": "corr_returns"
    }
}
```

### 1.2 啟動 Chrome CDP 並抓取數據

**Step 1：關閉所有 Chrome 視窗**

確保沒有其他 Chrome 實例在執行，否則調試端口會無法啟動。

**Step 2：啟動 Chrome 調試模式**

```bash
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --remote-allow-origins=* ^
  --user-data-dir="%USERPROFILE%\.chrome-debug-profile" ^
  "https://tradingeconomics.com/commodity/natural-gas"

# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir="$HOME/.chrome-debug-profile" \
  "https://tradingeconomics.com/commodity/natural-gas"
```

**Step 3：等待頁面載入，驗證連線**

```bash
curl -s http://127.0.0.1:9222/json
```

成功的回應應包含 `webSocketDebuggerUrl`。

**Step 4：執行爬蟲**

```bash
cd skills/analyze-gas-fertilizer-contract-shock/scripts

# 抓取天然氣
python fetch_te_data.py --symbol natural-gas --output ../data/natural_gas.csv

# 切換到化肥頁面（在 Chrome 中切換或開新分頁），抓取化肥
python fetch_te_data.py --symbol urea --output ../data/urea.csv
```

### 1.3 備援方案（若 TradingEconomics 不可用）

```bash
# 使用 FRED 抓取 Henry Hub 天然氣
python fetch_fred_series.py --series DHHNGSP --start 2025-08-01 --end 2026-02-01

# 使用 World Bank Pink Sheet（月頻，需手動下載）
# https://www.worldbank.org/en/research/commodity-markets
```

---

## Step 2: 數據處理與 Shock 偵測

### 2.1 執行主分析腳本

```bash
python gas_fertilizer_analyzer.py \
  --gas-file ../data/natural_gas.csv \
  --fert-file ../data/urea.csv \
  --start 2025-08-01 \
  --end 2026-02-01 \
  --z-window 60 \
  --z-threshold 3.0 \
  --slope-threshold 1.5 \
  --output ../data/analysis_result.json
```

### 2.2 分析邏輯說明

腳本執行以下步驟：

**A. 資料對齊**
```python
# 合併兩個時間序列到共同交易日
merged = gas_df.merge(fert_df, on="date", how="outer").sort_values("date")
merged = merged.ffill()  # forward-fill 缺值
```

**B. 計算報酬率**
```python
merged["gas_ret"] = merged["gas"].pct_change(return_window)
merged["fert_ret"] = merged["fert"].pct_change(return_window)
```

**C. Rolling z-score**
```python
merged["gas_z"] = (merged["gas_ret"] - merged["gas_ret"].rolling(z_window).mean()) \
                / merged["gas_ret"].rolling(z_window).std()
```

**D. 斜率代理**
```python
k = 20
merged["gas_slope"] = (merged["gas"] / merged["gas"].shift(k) - 1) / k
```

**E. Shock 偵測**
```python
merged["gas_shock"] = (merged["gas_z"] >= z_threshold) | (merged["gas_slope"] >= slope_threshold)
merged["fert_spike"] = (merged["fert_z"] >= z_threshold) | (merged["fert_slope"] >= slope_threshold)
```

**F. Regime 合併**
```python
gas_regimes = compress_boolean_to_regimes(merged, "gas_shock", value_col="gas")
fert_regimes = compress_boolean_to_regimes(merged, "fert_spike", value_col="fert")
```

---

## Step 3: 領先落後分析

### 3.1 Cross-Correlation

```python
from scipy import signal

# 計算報酬率的交叉相關
corr = signal.correlate(gas_ret.dropna(), fert_ret.dropna(), mode='full')
lags = signal.correlation_lags(len(gas_ret.dropna()), len(fert_ret.dropna()), mode='full')

# 找最大相關的 lag
best_idx = np.argmax(np.abs(corr))
best_lag = lags[best_idx]
best_corr = corr[best_idx]
```

### 3.2 解讀 lag 值

| best_lag | 意義 |
|----------|------|
| > 0 | 天然氣領先化肥（符合敘事） |
| ≈ 0 | 同時變動（共同驅動） |
| < 0 | 化肥領先天然氣（敘事較弱） |

---

## Step 4: 三段式因果檢驗

### 4.1 A 段檢驗：Gas Shock 存在？

```python
A_pass = len(gas_regimes) > 0
if A_pass:
    A_info = {
        "regime_count": len(gas_regimes),
        "max_return_pct": max(r["regime_return_pct"] for r in gas_regimes),
        "total_days": sum(r["duration_days"] for r in gas_regimes)
    }
```

### 4.2 B 段檢驗：Fert Spike 在 A 段之後？

```python
B_pass = False
for fert_r in fert_regimes:
    for gas_r in gas_regimes:
        # 化肥 spike 起點晚於天然氣 shock 起點
        if fert_r["start"] > gas_r["start"]:
            B_pass = True
            break
```

### 4.3 C 段檢驗：Lead-Lag 支持因果？

```python
# 合理領先期：1-8 週
C_pass = (best_lag > 0) and (7 <= best_lag <= 56)
C_info = {
    "best_lag_days": best_lag,
    "best_corr": best_corr,
    "in_reasonable_range": C_pass
}
```

### 4.4 綜合判斷

```python
if A_pass and B_pass and C_pass:
    signal = "narrative_supported"
    confidence = "high" if best_corr > 0.5 else "medium"
elif A_pass and B_pass:
    signal = "narrative_supported"
    confidence = "low"  # lead-lag 不完全支持
elif A_pass:
    signal = "narrative_weak"
    confidence = "low"
else:
    signal = "inconclusive"
    confidence = "low"
```

---

## Step 5: 生成報告

### 5.1 JSON 輸出

```bash
# 結果已在 Step 2 輸出到 analysis_result.json
cat ../data/analysis_result.json
```

### 5.2 視覺化

```bash
python visualize_shock_regimes.py \
  --data ../data/analysis_result.json \
  --output ../../output/gas_fert_shock_$(date +%Y-%m-%d).png
```

### 5.3 Markdown 報告

根據 `templates/output-markdown.md` 模板生成人類可讀報告。

---

## Step 6: 替代解釋提示

根據分析結果，提供替代解釋：

| 情況 | 替代解釋 |
|------|----------|
| Gas 大漲但 Fert 不動 | 肥價由其他因素主導（運費、需求、政策） |
| Fert 先動 | 供需/政策先改變，Gas 只是後續共振 |
| 兩者同時動 | 共同驅動（能源成本、地緣政治） |

</process>

<success_criteria>
Workflow 完成時應有：

- [ ] Chrome CDP 連線成功驗證
- [ ] 天然氣與化肥數據已抓取並對齊
- [ ] Gas shock regimes 已偵測並記錄
- [ ] Fert spike regimes 已偵測並記錄
- [ ] 領先落後相關分析完成
- [ ] 三段式因果檢驗結論明確
- [ ] JSON 結果已輸出
- [ ] 視覺化圖表已生成
- [ ] 替代解釋已提供（若敘事不成立）
</success_criteria>

<troubleshooting>

### 常見問題

**Q1: 無法連接到 Chrome 調試端口**
1. 確保所有 Chrome 視窗都已關閉
2. 確認使用了非預設的 `--user-data-dir`
3. 檢查端口 9222：`curl -s http://127.0.0.1:9222/json`

**Q2: WebSocket 連線被拒絕 (403 Forbidden)**
確認啟動 Chrome 時有加上 `--remote-allow-origins=*` 參數。

**Q3: Highcharts not found**
1. 確認頁面已完全載入（圖表已顯示）
2. 在瀏覽器 Console 中執行 `typeof Highcharts` 確認
3. 頁面可能仍在載入，等待幾秒後再試

**Q4: 被 Cloudflare 擋住**
1. 在 Chrome 中手動完成 Cloudflare 驗證
2. 登入 TradingEconomics 帳號後再執行

</troubleshooting>
