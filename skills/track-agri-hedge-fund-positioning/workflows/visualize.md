# Workflow: 視覺化圖表

<required_reading>
**執行前請先閱讀：**
1. references/methodology.md
2. templates/annotations.md
</required_reading>

<process>

## Step 1: 確認輸入資料

需要以下資料作為輸入：
- 分析結果 JSON（來自 `workflows/analyze.md` 輸出）
- 或直接重新執行分析

```bash
# 使用既有分析結果
python scripts/visualize_flows.py -i output/result.json -o output/chart.png

# 或重新分析並視覺化
python scripts/analyze_positioning.py --full --visualize
```

## Step 2: 生成分組柱狀圖

重建新聞風格的週流量柱狀圖：

```python
import matplotlib.pyplot as plt
import numpy as np

def plot_weekly_flows(flows_df, output_path):
    """生成分組柱狀圖"""
    fig, ax = plt.subplots(figsize=(14, 7))

    dates = flows_df.index
    width = 0.15
    x = np.arange(len(dates))

    # 分組柱狀
    colors = {
        'grains': '#F4A460',     # 橙色
        'oilseeds': '#32CD32',   # 綠色
        'meats': '#DC143C',      # 紅色
        'softs': '#8B4513'       # 棕色
    }

    for i, (group, color) in enumerate(colors.items()):
        ax.bar(x + i*width, flows_df[group], width,
               label=group.capitalize(), color=color)

    # 總和線
    ax.plot(x + 2*width, flows_df['total'], 'k-o',
            label='Total', linewidth=2)

    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax.set_xlabel('Week')
    ax.set_ylabel('Net Flow (# contracts)')
    ax.set_title('Hedge Fund Positioning: Weekly Flows by Group')
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
```

## Step 3: 生成火力時序圖

```python
def plot_firepower_timeseries(firepower_df, output_path):
    """生成火力時序圖"""
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))

    # 上圖：各群組火力
    for group in ['grains', 'oilseeds', 'meats', 'softs']:
        axes[0].plot(firepower_df.index, firepower_df[group],
                    label=group.capitalize())

    axes[0].axhline(y=0.6, color='green', linestyle='--',
                   alpha=0.5, label='High Firepower Zone')
    axes[0].axhline(y=0.3, color='red', linestyle='--',
                   alpha=0.5, label='Low Firepower Zone')
    axes[0].fill_between(firepower_df.index, 0.6, 1.0,
                        alpha=0.1, color='green')
    axes[0].fill_between(firepower_df.index, 0.0, 0.3,
                        alpha=0.1, color='red')

    axes[0].set_ylabel('Buying Firepower')
    axes[0].set_title('Buying Firepower by Group')
    axes[0].legend()
    axes[0].set_ylim(0, 1)

    # 下圖：總火力與宏觀評分
    axes[1].plot(firepower_df.index, firepower_df['total'],
                'b-', label='Total Firepower', linewidth=2)
    axes[1].set_ylabel('Total Firepower', color='blue')

    ax2 = axes[1].twinx()
    ax2.plot(firepower_df.index, firepower_df['macro_score'],
            'orange', label='Macro Tailwind', linewidth=2)
    ax2.set_ylabel('Macro Tailwind Score', color='orange')

    axes[1].set_title('Total Firepower vs Macro Tailwind')
    axes[1].legend(loc='upper left')
    ax2.legend(loc='upper right')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
```

## Step 4: 添加標註

依據 `templates/annotations.md` 的規則，在圖表上添加事件標註：

```python
def add_annotations(ax, annotations_list, flows_df):
    """在圖表上添加事件標註"""
    label_styles = {
        'strong_corn_demand': {'color': 'green', 'marker': '^'},
        'bearish_usda_stats': {'color': 'red', 'marker': 'v'},
        'macro_mood_bullish': {'color': 'blue', 'marker': 'o'},
        'small_holiday_flows': {'color': 'gray', 'marker': 's'}
    }

    for ann in annotations_list:
        if ann['rule_hit']:
            date = ann.get('date')
            idx = flows_df.index.get_loc(date)
            style = label_styles.get(ann['label'], {})

            ax.annotate(
                ann['label'].replace('_', ' ').title(),
                xy=(idx, flows_df.loc[date, 'total']),
                xytext=(10, 10),
                textcoords='offset points',
                fontsize=8,
                arrowprops=dict(arrowstyle='->', color=style.get('color', 'black'))
            )
```

## Step 5: 生成綜合儀表板

```python
def create_dashboard(result_json, output_path):
    """生成綜合儀表板"""
    fig = plt.figure(figsize=(16, 12))

    # 布局：2x2 格子
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

    # 左上：週流量柱狀圖
    ax1 = fig.add_subplot(gs[0, 0])
    plot_weekly_flows_subplot(ax1, result_json['weekly_flows'])

    # 右上：火力儀表
    ax2 = fig.add_subplot(gs[0, 1])
    plot_firepower_gauge(ax2, result_json['latest_metrics']['buying_firepower'])

    # 左下：宏觀順風指標
    ax3 = fig.add_subplot(gs[1, 0])
    plot_macro_indicators(ax3, result_json)

    # 右下：摘要卡片
    ax4 = fig.add_subplot(gs[1, 1])
    plot_summary_card(ax4, result_json['summary'])

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
```

## Step 6: 輸出檔案

```bash
# 輸出目錄結構
output/
├── flows_chart.png          # 週流量柱狀圖
├── firepower_chart.png      # 火力時序圖
├── dashboard.png            # 綜合儀表板
└── charts/                  # 單獨群組圖表
    ├── grains.png
    ├── oilseeds.png
    ├── meats.png
    └── softs.png
```

</process>

<success_criteria>
此工作流程完成時應確認：

- [ ] 週流量柱狀圖成功生成（重建新聞風格）
- [ ] 各群組顏色區分清楚
- [ ] 火力分數圖包含區間標示（綠/紅區）
- [ ] 事件標註正確顯示
- [ ] 圖表解析度足夠（>= 150 dpi）
- [ ] 輸出至指定路徑
</success_criteria>
