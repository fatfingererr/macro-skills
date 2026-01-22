# Workflow: 完整庫存分析

<required_reading>
**執行前請先閱讀：**
1. references/methodology.md - 三維度量化方法論
2. references/data-sources.md - SGE/SHFE 資料來源
3. references/input-schema.md - 完整輸入參數定義
</required_reading>

<process>

## Step 1: 確認分析參數

確認用戶提供的參數，或使用預設值：

| 參數 | 預設值 | 說明 |
|------|--------|------|
| start_date | 3 年前 | 分析起始日 |
| end_date | 今天 | 分析結束日 |
| frequency | weekly | 數據頻率 |
| include_sources | ["SGE", "SHFE"] | 庫存來源 |
| unit | tonnes | 輸出單位 |
| smoothing_window_weeks | 4 | 平滑視窗 |
| drain_threshold_z | -1.5 | 耗盡速度 Z 門檻 |
| accel_threshold_z | +1.0 | 加速度 Z 門檻 |

## Step 2: 數據採集

執行數據抓取腳本：

```bash
cd skills/detect-shanghai-silver-stock-drain

# 抓取 SGE 庫存（PDF 解析）
python scripts/fetch_sge_stock.py \
  --start {start_date} \
  --end {end_date} \
  --output data/sge_stock.csv

# 抓取 SHFE 庫存
python scripts/fetch_shfe_stock.py \
  --start {start_date} \
  --end {end_date} \
  --output data/shfe_stock.csv
```

如果數據已存在且在快取有效期內（12 小時），可跳過此步驟。

## Step 3: 數據處理與合併

執行主分析腳本的數據處理階段：

```python
# drain_detector.py 內部邏輯
def build_combined_stock(df_sge, df_shfe, unit="tonnes"):
    """合併 SGE + SHFE 庫存"""
    df = merge_weekly(df_sge, df_shfe)  # 按週對齊
    df["combined_kg"] = df["sge_kg"].fillna(0) + df["shfe_kg"].fillna(0)

    if unit == "tonnes":
        df["combined"] = df["combined_kg"] / 1000.0
    elif unit == "troy_oz":
        df["combined"] = (df["combined_kg"] / 1000.0) * 32150.7466

    return df.sort_values("date")
```

## Step 4: 三維度量化計算

計算方向、速度、加速度：

```python
def compute_drain_metrics(df, smooth=4, z_window=156):
    """計算耗盡三維度指標"""
    # 方向（每週變化）
    df["delta1"] = df["combined"].diff(1)

    # 速度（流出量，正值 = 流出）
    df["drain_rate"] = -df["delta1"]

    # 加速度（速度變化）
    df["accel"] = df["drain_rate"].diff(1)

    # 平滑處理
    for c in ["combined", "drain_rate", "accel"]:
        df[f"{c}_sm"] = df[c].rolling(smooth, min_periods=1).mean()

    # Z 分數標準化
    for c in ["drain_rate_sm", "accel_sm"]:
        m = df[c].rolling(z_window, min_periods=20).mean()
        s = df[c].rolling(z_window, min_periods=20).std()
        df[f"z_{c}"] = (df[c] - m) / s

    # 水位百分位
    df["level_pct_rank"] = df["combined_sm"].rolling(z_window, min_periods=20)\
        .apply(lambda x: x.rank(pct=True).iloc[-1], raw=False)

    return df
```

## Step 5: 訊號分級判定

執行三段式訊號判定：

```python
def classify_signal(df, drain_z=-1.5, accel_z=1.0, level_pctl=0.2):
    """判定供給訊號等級"""
    latest = df.iloc[-1]

    A = latest["level_pct_rank"] <= level_pctl      # 庫存水位偏低
    B = latest["z_drain_rate_sm"] <= drain_z        # 耗盡速度異常
    C = latest["z_accel_sm"] >= accel_z             # 耗盡加速

    if A and B and C:
        return "HIGH_LATE_STAGE_SUPPLY_SIGNAL"
    if (B and C) or (A and B):
        return "MEDIUM_SUPPLY_TIGHTENING"
    if B or A or C:
        return "WATCH"
    return "NO_SIGNAL"
```

## Step 6: 生成敘事解讀

根據分析結果生成中文敘事：

```python
def generate_narrative(result):
    """生成敘事解讀"""
    narrative = []

    # 水位描述
    pct = result["level_percentile"]
    narrative.append(f"上海合併庫存處於歷史低分位（約 {pct*100:.0f}% 分位）。")

    # 速度描述
    z_drain = result["z_scores"]["z_drain_rate"]
    if z_drain <= -1.5:
        narrative.append(f"近 4 週平均庫存流出顯著高於常態（耗盡速度 Z={z_drain:.1f}）。")

    # 加速度描述
    z_accel = result["z_scores"]["z_acceleration"]
    if z_accel >= 1.0:
        narrative.append(f"流出在加速（加速度 Z=+{z_accel:.1f}），符合「方向 + 速度」核心判準。")

    # 建議
    narrative.append("若同時觀察到其他市場庫存/溢價惡化，可進一步提高信心。")

    return narrative
```

## Step 7: 輸出結果

執行完整分析並輸出：

```bash
python scripts/drain_detector.py \
  --start {start_date} \
  --end {end_date} \
  --sources SGE SHFE \
  --unit tonnes \
  --output result.json
```

結果將包含：
- JSON 分析結果（符合 `templates/output-json.md` 格式）
- 數據快取（供後續分析使用）

## Step 8: 視覺化報告（選配）

如需視覺化報告：

```bash
python scripts/visualize_drain.py \
  --result result.json \
  --output ../../../output/
```

輸出：
- PNG 圖表：`output/shanghai_silver_drain_report_{date}.png`
- PDF 報告：`output/shanghai_silver_drain_report_{date}.pdf`

</process>

<success_criteria>
此工作流程完成時應產出：

- [ ] SGE + SHFE 合併庫存時間序列
- [ ] 三維度量化結果（方向、速度、加速度）
- [ ] Z 分數標準化數值
- [ ] 庫存水位歷史分位數
- [ ] 訊號分級（HIGH/MEDIUM/WATCH/NO_SIGNAL）
- [ ] 中文敘事解讀
- [ ] JSON 格式結果檔案
- [ ] （選配）視覺化報告
</success_criteria>
