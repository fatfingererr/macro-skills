# Workflow: 合約對沖假說分析

<required_reading>
**執行前請閱讀：**
1. references/methodology.md - 了解 hedge_pnl_proxy 的定義
</required_reading>

<overview>
當新聞提到「公司以低價合約鎖定天然氣，現在市價暴漲賺翻」時，
本 workflow 計算一個**價差壓力指標**，量化這個敘事的可信度。

**重要提醒**：這不是公司真實 PnL，只是把敘事轉成可量化的 proxy。
</overview>

<process>

## Step 1: 收集合約假說參數

詢問用戶或從新聞中提取：

```python
hedge_hypothesis = {
    "gas_contract_price": 0.80,     # 新聞宣稱的合約價格
    "gas_contract_unit": "USD/MMBtu",
    "profit_proxy_mode": "spot_minus_contract"
}
```

---

## Step 2: 計算 Hedge PnL Proxy

### 2.1 基本計算

```python
# 取得天然氣現貨/近月價格
gas_spot = merged["gas"]  # 從 TradingEconomics 抓取

# 計算每日的「價差收益代理」
contract_price = hedge_hypothesis["gas_contract_price"]
merged["hedge_pnl_proxy"] = (gas_spot - contract_price).clip(lower=0)
```

### 2.2 解讀

- `hedge_pnl_proxy > 0`：現貨高於合約，理論上「賺錢」
- `hedge_pnl_proxy = 0`：現貨低於合約，無套利空間

---

## Step 3: 生成 Hedge Regime

### 3.1 識別高價差區間

```python
# 當 hedge_pnl_proxy 超過某閾值，標記為 hedge_active
threshold = contract_price * 0.5  # 價差超過合約價 50%
merged["hedge_active"] = merged["hedge_pnl_proxy"] > threshold

# 合併為 regime
hedge_regimes = compress_boolean_to_regimes(merged, "hedge_active", value_col="hedge_pnl_proxy")
```

### 3.2 與 Fert Spike 對比

```python
# 檢查 hedge regime 是否與 fert spike 在時間上重疊或接續
for hedge_r in hedge_regimes:
    for fert_r in fert_regimes:
        if overlaps_or_follows(hedge_r, fert_r):
            # 敘事支持：天然氣價差壓力期間，化肥也在漲
            narrative_support = True
```

---

## Step 4: 輸出報告

```json
{
  "hedge_hypothesis": {
    "contract_price": 0.80,
    "unit": "USD/MMBtu",
    "interpretation": "價格層面的價差壓力指標（非真實公司PnL）"
  },
  "hedge_pnl_proxy_stats": {
    "peak_value": 6.15,
    "peak_date": "2026-01-29",
    "mean_during_shock": 4.2,
    "days_above_threshold": 18
  },
  "hedge_fert_alignment": {
    "overlap_days": 12,
    "interpretation": "hedge regime 與 fert spike 有明顯重疊，敘事有數據支撐"
  },
  "caveats": [
    "這是價格層面的 proxy，不代表任何特定公司的真實損益",
    "實際對沖還涉及合約量、到期日、counterparty 等因素",
    "不能用此結論斷言任何公司的 force majeure 行為"
  ]
}
```

---

## Step 5: 視覺化

```bash
python visualize_hedge_proxy.py \
  --data ../data/analysis_result.json \
  --contract-price 0.80 \
  --output ../../output/hedge_proxy_$(date +%Y-%m-%d).png
```

圖表包含：
- 天然氣現貨價格（實線）
- 合約價格（水平虛線）
- Hedge PnL Proxy（填充區域）
- Fert 價格（次軸）

</process>

<success_criteria>
Workflow 完成時應有：

- [ ] 合約假說參數已確認
- [ ] Hedge PnL Proxy 時間序列已計算
- [ ] Peak proxy 值與日期
- [ ] 與 Fert Spike 的時序對比
- [ ] 明確的 caveats（這不是真實 PnL）
- [ ] 視覺化圖表
</success_criteria>

<important_disclaimer>
**重要聲明**

Hedge PnL Proxy 只是一個「把新聞敘事轉成可量化指標」的工具。

**它不代表**：
- 任何特定公司的真實損益
- Force majeure 是否發生
- 合約是否被毀約

**它只能說明**：
- 如果某公司真的以 X 價格鎖定天然氣
- 且現貨價格如數據所示
- 那麼「價差壓力」的量級是多少

請在報告中明確標註這些限制。
</important_disclaimer>
