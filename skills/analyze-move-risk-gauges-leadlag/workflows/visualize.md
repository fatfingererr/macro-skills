# Workflow: 視覺化圖表

<required_reading>
**執行前請閱讀：**
1. references/methodology.md - 了解各圖表的含義
</required_reading>

<process>

## Step 1: 準備數據

確保已執行分析並有結果：

```bash
# 若尚未分析，先執行
python scripts/analyze.py --start 2024-01-01 --end 2026-01-01 --output result.json
```

## Step 2: 執行視覺化

使用 `scripts/visualize.py` 生成圖表：

```bash
python scripts/visualize.py \
  -i result.json \
  -o output/leadlag_analysis.png \
  --dpi 150
```

## Step 3: 圖表說明

### 多面板圖表結構

生成的圖表包含 4 個面板：

```
┌─────────────────────────────────────────────┐
│ Panel 1: 原始時間序列 (MOVE, VIX, Credit)   │
│   - 左軸: MOVE Index                        │
│   - 右軸: VIX, Credit Spread                │
│   - 標記: JGB 衝擊事件 (垂直虛線)           │
├─────────────────────────────────────────────┤
│ Panel 2: Z 分數標準化後的序列               │
│   - 三條線在同一尺度                        │
│   - 水平線: Z = 0, ±1, ±2                   │
│   - 標記: 當前 MOVE Z 分數位置              │
├─────────────────────────────────────────────┤
│ Panel 3: 交叉相關函數 (Cross-Correlation)   │
│   - X 軸: Lag (天)                          │
│   - Y 軸: Correlation                        │
│   - 兩條線: MOVE vs VIX, MOVE vs Credit     │
│   - 標記: 最大相關點                        │
├─────────────────────────────────────────────┤
│ Panel 4: 事件窗反應                         │
│   - 每次 JGB 衝擊事件的 MOVE 反應           │
│   - 水平線: 平均反應                        │
│   - 直方圖: 反應分布                        │
└─────────────────────────────────────────────┘
```

### Panel 1: 原始時間序列

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(4, 1, figsize=(12, 16), sharex=True)

# Panel 1: Raw series
ax1 = axes[0]
ax1.plot(df.index, df["MOVE"], label="MOVE", color="blue")
ax1.set_ylabel("MOVE Index", color="blue")

ax1_right = ax1.twinx()
ax1_right.plot(df.index, df["VIX"], label="VIX", color="orange", alpha=0.7)
ax1_right.plot(df.index, df["CREDIT"], label="Credit", color="green", alpha=0.7)
ax1_right.set_ylabel("VIX / Credit Spread")

# Mark shock events
for shock_date in shock_dates:
    ax1.axvline(shock_date, color="red", linestyle="--", alpha=0.3)

ax1.set_title("Raw Time Series (MOVE, VIX, Credit Spread)")
ax1.legend(loc="upper left")
```

### Panel 2: Z 分數

```python
ax2 = axes[1]
ax2.plot(df_z.index, df_z["MOVE"], label="MOVE Z", color="blue")
ax2.plot(df_z.index, df_z["VIX"], label="VIX Z", color="orange", alpha=0.7)
ax2.plot(df_z.index, df_z["CREDIT"], label="Credit Z", color="green", alpha=0.7)

# Reference lines
ax2.axhline(0, color="gray", linestyle="-", alpha=0.5)
ax2.axhline(1, color="gray", linestyle="--", alpha=0.3)
ax2.axhline(-1, color="gray", linestyle="--", alpha=0.3)
ax2.axhline(2, color="red", linestyle="--", alpha=0.3)
ax2.axhline(-2, color="red", linestyle="--", alpha=0.3)

ax2.set_ylabel("Z-Score")
ax2.set_title("Standardized Series (Z-Score)")
ax2.legend()
```

### Panel 3: 交叉相關

```python
ax3 = axes[2]

lags = range(-lead_lag_max_days, lead_lag_max_days + 1)
corr_vix_all = [df_smooth["MOVE"].shift(lag).corr(df_smooth["VIX"]) for lag in lags]
corr_credit_all = [df_smooth["MOVE"].shift(lag).corr(df_smooth["CREDIT"]) for lag in lags]

ax3.plot(lags, corr_vix_all, label="MOVE vs VIX", color="orange")
ax3.plot(lags, corr_credit_all, label="MOVE vs Credit", color="green")
ax3.axvline(0, color="gray", linestyle="--", alpha=0.5)

# Mark best lags
ax3.axvline(best_lag_vix, color="orange", linestyle=":", label=f"Best lag VIX: {best_lag_vix}")
ax3.axvline(best_lag_credit, color="green", linestyle=":", label=f"Best lag Credit: {best_lag_credit}")

ax3.set_xlabel("Lag (days, positive = MOVE leads)")
ax3.set_ylabel("Correlation")
ax3.set_title("Cross-Correlation Function")
ax3.legend()
```

### Panel 4: 事件窗反應

```python
ax4 = axes[3]

# Histogram of reactions
ax4.hist(reactions, bins=10, alpha=0.7, color="blue", edgecolor="black")
ax4.axvline(reactions.mean(), color="red", linestyle="--", label=f"Mean: {reactions.mean():.2f}")
ax4.axvline(0, color="gray", linestyle="-", alpha=0.5)

ax4.set_xlabel("MOVE Reaction to JGB Shock")
ax4.set_ylabel("Frequency")
ax4.set_title(f"MOVE Reaction Distribution ({len(reactions)} shock events)")
ax4.legend()

plt.tight_layout()
plt.savefig(output_path, dpi=dpi)
```

## Step 4: 輸出選項

### 高解析度輸出

```bash
python scripts/visualize.py -i result.json -o output/chart_hires.png --dpi 300
```

### 多格式輸出

```bash
# PNG
python scripts/visualize.py -i result.json -o output/chart.png

# PDF (向量格式)
python scripts/visualize.py -i result.json -o output/chart.pdf

# SVG (網頁用)
python scripts/visualize.py -i result.json -o output/chart.svg
```

### 互動式圖表（Plotly）

```bash
python scripts/visualize.py -i result.json -o output/chart.html --interactive
```

</process>

<success_criteria>
完成此 workflow 時：

- [ ] 生成 4 面板圖表
- [ ] Panel 1 顯示原始序列與衝擊事件
- [ ] Panel 2 顯示 Z 分數與參考線
- [ ] Panel 3 顯示交叉相關與最佳 lag
- [ ] Panel 4 顯示事件窗反應分布
- [ ] 圖表已保存到指定路徑
</success_criteria>
