# Workflow: 完整回測

<required_reading>
**執行前請先閱讀：**
1. references/input-schema.md - 完整參數定義
2. references/methodology.md - 方法論與切換邏輯
3. references/data-sources.md - 數據來源與系列代碼
</required_reading>

<process>

## Step 1: 確認參數

檢查用戶提供的參數，補充預設值：

```python
params = {
    "start_date": "2000-01-01",      # 回測起始
    "end_date": "today",              # 回測結束
    "freq": "M",                      # 月頻
    "equity_proxy": "SPY",            # 風險資產
    "bond_proxy": "TLT",              # 長債資產
    "iceberg_threshold": -0.3,        # 冰山門檻
    "sinking_threshold": -0.5,        # 下沉門檻
    "confirm_periods": 2,             # 確認期數
    "hysteresis": 0.15,               # 進出場間距
    "rebalance_on": "next_month_open",
    "transaction_cost_bps": 5,
    "slippage_bps": 0
}
```

若用戶有指定參數，覆蓋上述預設值。

## Step 2: 抓取數據

執行 `scripts/fetch_data.py` 抓取所需數據：

```bash
python scripts/fetch_data.py \
  --leading T10Y3M,T10Y2Y,PERMIT,ACDGNO,UMCSENT \
  --coincident PAYEMS,INDPRO,W875RX1,CMRMTSPL \
  --prices SPY,TLT \
  --start {start_date} \
  --end {end_date} \
  --output data.json
```

或使用 Python API：

```python
from scripts.fetch_data import fetch_all_data

data = fetch_all_data(
    leading_series=["T10Y3M", "T10Y2Y", "PERMIT", "ACDGNO", "UMCSENT"],
    coincident_series=["PAYEMS", "INDPRO", "W875RX1", "CMRMTSPL"],
    price_tickers=["SPY", "TLT"],
    start_date=params["start_date"],
    end_date=params["end_date"]
)
```

## Step 3: 建構指標

計算 LeadingIndex 和 CoincidentIndex：

```python
from scripts.rotator import build_index

leading_config = [
    {"id": "T10Y3M", "transform": "level", "direction": 1, "weight": 0.25},
    {"id": "T10Y2Y", "transform": "level", "direction": 1, "weight": 0.15},
    {"id": "PERMIT", "transform": "yoy", "direction": 1, "weight": 0.20},
    {"id": "ACDGNO", "transform": "yoy", "direction": 1, "weight": 0.20},
    {"id": "UMCSENT", "transform": "level", "direction": 1, "weight": 0.20}
]

coincident_config = [
    {"id": "PAYEMS", "transform": "yoy", "direction": 1, "weight": 0.30},
    {"id": "INDPRO", "transform": "yoy", "direction": 1, "weight": 0.30},
    {"id": "W875RX1", "transform": "yoy", "direction": 1, "weight": 0.20},
    {"id": "CMRMTSPL", "transform": "yoy", "direction": 1, "weight": 0.20}
]

L = build_index(leading_config, data["macro"], z_win=120, smooth_win=3)
C = build_index(coincident_config, data["macro"], z_win=120, smooth_win=3)
```

## Step 4: 執行切換邏輯

使用 `protocol_signals` 產生切換訊號：

```python
from scripts.rotator import protocol_signals

result = protocol_signals(
    params=params,
    price_eq=data["prices"]["SPY"],
    price_bd=data["prices"]["TLT"],
    leading_index=L,
    coincident_index=C
)
```

## Step 5: 回測績效

計算累積報酬與績效指標：

```python
# result 包含：
# - signals: 切換事件清單
# - backtest: 回測績效
#   - cumulative_return
#   - cagr
#   - max_drawdown
#   - sharpe_ratio
#   - turnovers
#   - periods_in_equity
#   - periods_in_bonds
```

## Step 6: 比較 Benchmark

與買入持有、60/40 組合比較：

```python
benchmarks = {
    "equity_buy_hold": calculate_buy_hold(data["prices"]["SPY"]),
    "bond_buy_hold": calculate_buy_hold(data["prices"]["TLT"]),
    "60_40": calculate_60_40(data["prices"]["SPY"], data["prices"]["TLT"])
}
```

## Step 7: 輸出結果

依據 `output_format` 參數產出結果：

- JSON 格式：參考 `templates/output-json.md`
- Markdown 格式：參考 `templates/output-markdown.md`

```bash
python scripts/rotator.py \
  --start {start_date} \
  --end {end_date} \
  --output result.json
```

</process>

<success_criteria>
回測完成時應產出：

- [ ] LeadingIndex 與 CoincidentIndex 時間序列
- [ ] 所有切換事件清單（含日期、動作、原因）
- [ ] 回測期間的累積報酬曲線
- [ ] CAGR、MaxDD、Sharpe、換手次數
- [ ] 與 benchmark 比較
- [ ] 診斷資訊（各指標貢獻）
- [ ] 結果輸出為指定格式
</success_criteria>
