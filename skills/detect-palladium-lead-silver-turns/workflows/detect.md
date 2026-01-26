# Workflow: 單次偵測

<required_reading>
**執行前請閱讀：**
1. references/input-schema.md - 完整參數定義
2. references/data-sources.md - 數據來源與代碼
</required_reading>

<process>

## Step 1: 確認輸入參數

確認以下必要參數：

| 參數              | 預設值 | 說明                   |
|-------------------|--------|------------------------|
| silver_symbol     | SI=F   | 白銀標的代碼           |
| palladium_symbol  | PA=F   | 鈀金標的代碼           |
| timeframe         | 1h     | 分析時間尺度           |
| lookback_bars     | 1000   | 回溯 K 棒數            |

如果用戶提供了特定參數，使用用戶的值。

## Step 2: 執行偵測腳本

```bash
cd skills/detect-palladium-lead-silver-turns
python scripts/palladium_lead_silver.py \
  --silver {silver_symbol} \
  --palladium {palladium_symbol} \
  --timeframe {timeframe} \
  --lookback {lookback_bars}
```

快速模式（使用預設參數）：
```bash
python scripts/palladium_lead_silver.py --quick
```

## Step 3: 解讀輸出結果

輸出 JSON 包含以下關鍵資訊：

### 3.1 領先滯後估計

```json
{
  "estimated_pd_leads_by_bars": 6,
  "lead_lag_corr": 0.42
}
```

- `estimated_pd_leads_by_bars > 0`：鈀金領先白銀
- `lead_lag_corr > 0.3`：有意義的領先關係

### 3.2 確認統計

```json
{
  "confirmation_rate": 0.71,
  "unconfirmed_failure_rate": 0.64
}
```

- `confirmation_rate > 0.6`：多數白銀拐點被確認
- `unconfirmed_failure_rate > 0.5`：未確認事件多數失敗

### 3.3 最新事件

```json
{
  "latest_event": {
    "ts": "2026-01-15T14:00:00Z",
    "turn": "top",
    "confirmed": false,
    "participation_ok": false,
    "failed_move": true
  }
}
```

重點關注 `confirmed` 和 `failed_move` 欄位。

## Step 4: 生成視覺化（可選）

### 4.1 Bloomberg 風格圖表（推薦）

```bash
pip install matplotlib yfinance  # 首次使用
python scripts/plot_bloomberg_style.py \
  --input result.json \
  --output output/palladium_silver_{date}.png
```

特色：
- Bloomberg 專業配色（深色背景）
- 雙軸價格疊加（白銀橙紅、鈀金橙黃）
- 拐點標記（綠色=已確認、紅色=未確認）
- 最新事件醒目標註
- 滾動確認率趨勢圖
- 統計面板與行情解讀

### 4.2 傳統三合一圖表

```bash
python scripts/plot_palladium_silver.py \
  --silver {silver_symbol} \
  --palladium {palladium_symbol} \
  --output output/
```

包含：
- 價格疊加與拐點標記
- 確認/未確認分布
- 滾動相關係數

## Step 5: 輸出報告

根據 `templates/output-markdown.md` 格式化結果，包含：

1. **數據摘要表格**
2. **最新事件判定**
3. **可操作建議**
4. **行情解讀**

</process>

<parameter_tuning>

## 參數調校指南

### 確認窗口 (confirm_window_bars)

| 時間尺度 | 建議值 | 說明               |
|----------|--------|--------------------|
| 1h       | 6-12   | 約半天到一天       |
| 4h       | 3-6    | 約半天到一天       |
| 1d       | 2-5    | 約一週             |

調校方法：
```bash
# 測試不同窗口
python scripts/palladium_lead_silver.py --silver SI=F --palladium PA=F --confirm-window 4
python scripts/palladium_lead_silver.py --silver SI=F --palladium PA=F --confirm-window 8
python scripts/palladium_lead_silver.py --silver SI=F --palladium PA=F --confirm-window 12
```

選擇確認率與失敗率差異最大的窗口。

### 拐點偵測方法 (turn_method)

| 方法          | 適用場景                 | 參數             |
|---------------|--------------------------|------------------|
| pivot         | 結構明確的趨勢           | pivot_left, pivot_right |
| peaks         | 自動化密度控制           | prominence, distance |
| slope_change  | 平滑趨勢追蹤             | slope_window     |

```bash
# 使用 pivot 法
python scripts/palladium_lead_silver.py --turn-method pivot --pivot-left 3 --pivot-right 3

# 使用 peaks 法
python scripts/palladium_lead_silver.py --turn-method peaks --prominence 0.5

# 使用 slope_change 法
python scripts/palladium_lead_silver.py --turn-method slope_change --slope-window 10
```

### 參與度門檻 (participation_threshold)

建議範圍：0.5 - 0.7

- 太低（< 0.5）：假陽性增加
- 太高（> 0.7）：漏掉有效確認

</parameter_tuning>

<success_criteria>
此工作流程完成時應有：

- [ ] 鈀金對白銀的領先滯後估計
- [ ] 白銀拐點的確認率統計
- [ ] 最新事件的判定結果
- [ ] 可操作的交易建議
- [ ] （可選）視覺化圖表
</success_criteria>
