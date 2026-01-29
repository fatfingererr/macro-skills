# Workflow: 快速檢查（全自動）

<required_reading>
無需額外閱讀，直接執行。
</required_reading>

<process>

## Step 1: 全自動抓取數據

腳本會自動啟動 Chrome、抓取數據、關閉 Chrome，無需手動操作。

### 1.1 如果有快取數據（12 小時內）

```bash
cd scripts
# 直接執行分析（會使用快取）
python gas_fertilizer_analyzer.py \
  --gas-file ../data/cache/natural-gas.csv \
  --fert-file ../data/cache/urea.csv \
  --output ../data/analysis_result.json
```

### 1.2 如果需要更新數據

```bash
cd scripts

# 全自動抓取（自動啟動/關閉 Chrome，約 60 秒）
python fetch_te_data.py --symbol natural-gas --symbol urea

# 執行分析
python gas_fertilizer_analyzer.py \
  --gas-file ../data/cache/natural-gas.csv \
  --fert-file ../data/cache/urea.csv \
  --output ../data/analysis_result.json
```

### 1.3 強制更新（忽略快取）

```bash
python fetch_te_data.py --symbol natural-gas --symbol urea --force-refresh
```

---

## Step 2: 解讀分析結果

分析完成後會顯示：

```
分析完成！結果已儲存至: ../data/analysis_result.json
Signal: narrative_supported (Confidence: medium)
```

### Signal 解讀

| Signal | Confidence | 含義 |
|--------|------------|------|
| `narrative_supported` | `high` | 強力支持「天然氣暴漲→化肥飆價」敘事 |
| `narrative_supported` | `medium` | 數據支持敘事，但相關性偏低 |
| `narrative_weak` | `low` | 敘事較弱，化肥未明顯跟隨 |
| `inconclusive` | `low` | 數據不足以判斷 |

---

## Step 3: 生成視覺化圖表（Bloomberg 風格）

```bash
python visualize_shock_regimes.py
```

**輸出**：`output/gas_fert_shock_YYYY-MM-DD.png`

圖表包含：
- 上圖：天然氣價格 + shock regimes（紅色標記）
- 下圖：化肥價格 + spike regimes（黃色標記）
- 標題顯示 signal、confidence、lead-lag 天數

---

## Step 4: 快速判斷

```
如果 signal == narrative_supported 且 best_lag > 0：
  → 天然氣暴漲可能傳導至化肥，預期滯後 best_lag 天

如果 signal == narrative_weak：
  → 化肥價格可能受其他因素主導（庫存、需求、政策）

如果 signal == inconclusive：
  → 數據範圍不足，建議擴大時間範圍重新分析
```

---

## Step 5: 決定下一步

**若 signal 為 `narrative_supported`**：
1. 查看詳細的 JSON 報告（`../data/analysis_result.json`）
2. 關注 lead_lag 天數，預判化肥價格反應時間點
3. 考慮對農業/肥料相關資產的配置調整

**若 signal 為 `narrative_weak`**：
1. 調查其他可能的化肥驅動因素
2. 設定監控頻率（每週檢查）
3. 關注其他商品傳導路徑

</process>

<success_criteria>
快速檢查完成時應有：

- [ ] 天然氣與化肥數據已抓取（或使用快取）
- [ ] Signal 與 Confidence 判斷
- [ ] Lead-lag 天數
- [ ] Bloomberg 風格視覺化圖表
- [ ] 下一步建議
</success_criteria>

<troubleshooting>

### Chrome 啟動失敗

**問題**：腳本報錯「找不到 Chrome」

**解決**：
1. 確認已安裝 Google Chrome
2. 檢查 Chrome 路徑是否正確（預設路徑在 `fetch_te_data.py` 的 `CHROME_PATHS` 列表中）

### WebSocket 連線失敗

**問題**：`websocket._exceptions.WebSocketBadStatusException`

**解決**：
1. 關閉所有 Chrome 視窗後重試
2. 如果已有 Chrome 調試實例，腳本會自動重用

### Highcharts not found

**問題**：提取數據時報錯 `Highcharts not found`

**解決**：
1. 頁面可能仍在載入，增加等待時間
2. 如遇 Cloudflare 驗證，需要手動完成驗證後重試

### 數據範圍太短

**問題**：TradingEconomics 只返回 1 年數據

**解決**：
1. 這是 TradingEconomics 免費版的限制
2. 對於長期分析，考慮使用 FRED 備援數據源

</troubleshooting>
