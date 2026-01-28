# Workflow: 快速檢查

<required_reading>
無需額外閱讀，直接執行。
</required_reading>

<process>

## Step 1: 快速確認最近狀態

使用預設參數，檢查最近 6 個月的 shock 狀態。

### 1.1 如果有快取數據

```bash
cd skills/analyze-gas-fertilizer-contract-shock/scripts

# 檢查快取是否有效（12 小時內）
python gas_fertilizer_analyzer.py --quick --use-cache
```

### 1.2 如果需要更新數據

**Step 1：啟動 Chrome CDP（若尚未啟動）**

```bash
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --remote-allow-origins=* ^
  --user-data-dir="%USERPROFILE%\.chrome-debug-profile" ^
  "https://tradingeconomics.com/commodity/natural-gas"
```

**Step 2：等待頁面載入後執行快速分析**

```bash
python gas_fertilizer_analyzer.py --quick --refresh
```

---

## Step 2: 解讀快速輸出

快速模式輸出精簡結果：

```json
{
  "check_date": "2026-01-28",
  "lookback_days": 180,
  "gas_status": {
    "current_z": 2.1,
    "is_shock": false,
    "recent_shock": {
      "exists": true,
      "last_date": "2026-01-29",
      "days_ago": 0
    }
  },
  "fert_status": {
    "current_z": 1.5,
    "is_spike": false,
    "recent_spike": {
      "exists": true,
      "last_date": "2026-01-31",
      "days_ago": 0
    }
  },
  "quick_assessment": "gas_shock_recent_fert_following",
  "recommendation": "建議執行完整分析以驗證因果關係"
}
```

---

## Step 3: Quick Assessment 解讀

| quick_assessment | 意義 | 建議行動 |
|------------------|------|----------|
| `no_shock` | 近期無天然氣 shock | 無需關注 |
| `gas_shock_only` | 有 gas shock，但化肥未跟隨 | 觀察中 |
| `gas_shock_recent_fert_following` | Gas shock 後化肥開始反應 | 執行完整分析 |
| `both_shocked` | 兩者同時處於 shock | 執行完整分析 |
| `fert_leads` | 化肥先動（異常） | 調查其他因素 |

---

## Step 4: 決定下一步

根據 quick_assessment 決定：

- **無需關注**：`no_shock` → 結束
- **持續觀察**：`gas_shock_only` → 設定提醒，幾天後再查
- **深入分析**：其他 → 執行 `workflows/analyze.md`

</process>

<success_criteria>
快速檢查完成時應有：

- [ ] 天然氣當前 z-score 狀態
- [ ] 化肥當前 z-score 狀態
- [ ] 最近 shock/spike 日期（若有）
- [ ] quick_assessment 判斷
- [ ] 下一步建議
</success_criteria>

<troubleshooting>

### Chrome CDP 連線問題

如果無法連接到 Chrome，請確認：

1. Chrome 已以調試模式啟動
2. 端口 9222 可用：`curl -s http://127.0.0.1:9222/json`
3. 沒有其他 Chrome 實例佔用該端口

### 快取過期

如果快取數據已過期（超過 12 小時），腳本會提示需要重新抓取。
請確保 Chrome CDP 已啟動，然後使用 `--refresh` 參數。

</troubleshooting>
