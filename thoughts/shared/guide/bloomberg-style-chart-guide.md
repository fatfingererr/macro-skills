# Bloomberg 風格圖表設計規範

本指南定義了模仿 Bloomberg Intelligence 風格的視覺化圖表設計規範，供所有 skill 的視覺化模組參考使用。

---

## 1. 配色方案 (Color Scheme)

### 1.1 核心配色定義

```python
BLOOMBERG_COLORS = {
    # 背景與網格
    "background": "#1a1a2e",      # 深藍黑色背景
    "grid": "#2d2d44",            # 暗灰紫網格線

    # 文字
    "text": "#ffffff",            # 主要文字（白色）
    "text_dim": "#888888",        # 次要文字（灰色）

    # 主要數據線
    "primary": "#ff6b35",         # 橙紅色（主要指標）
    "secondary": "#ffaa00",       # 橙黃色（次要指標/均線）
    "tertiary": "#ffff00",        # 黃色（第三指標）

    # 蠟燭圖配色
    "candle_up": "#00ff88",       # 綠色（上漲）
    "candle_down": "#ff4444",     # 紅色（下跌）

    # 面積圖
    "area_fill": "#ff8c00",       # 橙色面積填充
    "area_alpha": 0.4,            # 面積透明度

    # 輔助元素
    "level_line": "#666666",      # 關卡/水平線
    "annotation": "#ffffff",      # 標註文字
}
```

### 1.2 配色使用原則

| 元素類型       | 建議配色              | 說明                   |
|----------------|-----------------------|------------------------|
| 價格線（主要） | `#ff6b35` 橙紅        | 最重要的數據序列       |
| 均線/趨勢線    | `#ffaa00` 橙黃        | 技術指標、輔助線       |
| 面積圖         | `#ff8c00` + alpha 0.4 | 背景填充、總量指標     |
| 輔助線（黃）   | `#ffff00` 黃色        | 債券、殖利率、次要指標 |
| 關卡線         | `#666666` 灰色        | 整數關卡、支撐/阻力    |

---

## 2. 字體設定 (Font Configuration)

### 2.1 中文字體配置

```python
import matplotlib
matplotlib.use('Agg')  # 非交互式後端，必須在 import pyplot 前設定

import matplotlib.pyplot as plt

# 中文字體設定（按優先順序）
plt.rcParams['font.sans-serif'] = [
    'Microsoft JhengHei',  # Windows 正黑體
    'SimHei',              # Windows 黑體
    'Microsoft YaHei',     # Windows 微軟雅黑
    'PingFang TC',         # macOS 蘋方
    'Noto Sans CJK TC',    # Linux/通用
    'DejaVu Sans'          # 備用
]

# 修復負號顯示
plt.rcParams['axes.unicode_minus'] = False
```

### 2.2 字體大小規範

| 元素      | 字體大小 | 粗細        |
|-----------|----------|-------------|
| 標題      | 14pt     | bold        |
| 軸標籤    | 10pt     | normal      |
| 圖例      | 8pt      | normal      |
| 數值標註  | 9-11pt   | normal/bold |
| 來源/日期 | 8pt      | normal      |

---

## 3. 多軸疊加佈局 (Multi-Axis Layout)

### 3.1 軸位置命名規範

Bloomberg 圖表常用的軸位置標記：

| 標記 | 位置         | 用途                 |
|------|--------------|----------------------|
| R1   | 右軸（內側） | 主要價格指標         |
| R2   | 右軸（外側） | 次要價格指標         |
| L1   | 左軸（外側） | 輔助指標（如殖利率） |
| L2   | 左軸（內側） | 面積圖基底軸         |
| P1   | 疊加層       | 技術指標（如 SMA）   |

### 3.2 多軸建立模式

```python
fig, ax1 = plt.subplots(figsize=(14, 8), facecolor=COLORS["background"])
ax1.set_facecolor(COLORS["background"])

# L2 左軸（主軸，面積圖基底）
ax_l2 = ax1
ax_l2.fill_between(...)
ax_l2.set_ylabel("標籤 (L2)", color=COLORS["text_dim"])

# L1 左軸（外側，使用 twinx + 手動調整位置）
ax_l1 = ax1.twinx()
ax_l1.spines['left'].set_position(('outward', 60))  # 向外偏移 60pt
ax_l1.yaxis.set_label_position('left')
ax_l1.yaxis.set_ticks_position('left')
ax_l1.plot(...)
ax_l1.set_ylabel("標籤 (L1)", color=COLORS["tertiary"])

# R1 右軸（主要價格）
ax_r1 = ax1.twinx()
ax_r1.plot(...)
ax_r1.set_ylabel("標籤 (R1)", color=COLORS["primary"])
```

### 3.3 Z-Order（圖層順序）

| 圖層 | zorder | 元素           |
|------|--------|----------------|
| 底層 | 1      | 面積圖填充     |
| 輔助 | 2      | 關卡線、網格   |
| 次要 | 3      | 輔助指標線     |
| 疊加 | 4      | 均線、技術指標 |
| 頂層 | 5      | 主要價格線     |

---

## 4. 數值標註 (Annotations)

### 4.1 最新值標註模式

```python
latest_date = series.index[-1]
latest_value = series.iloc[-1]

ax.annotate(
    f'{latest_value:,.0f}',        # 格式化數值
    xy=(latest_date, latest_value), # 數據點位置
    xytext=(10, 0),                 # 文字偏移（向右 10pt）
    textcoords='offset points',
    color=COLORS["primary"],
    fontsize=11,
    fontweight='bold',
    va='center'
)
```

### 4.2 數值格式化函數

```python
from matplotlib.ticker import FuncFormatter

def format_price(x, pos):
    """價格格式化（K 表示千）"""
    if x >= 1000:
        return f'{x/1000:.1f}K'
    return f'{x:.0f}'

def format_trillion(x, pos):
    """兆美元格式化"""
    return f'{x:.0f}'

def format_percent(x, pos):
    """百分比格式化"""
    return f'{x:.1f}%'

def format_bond_price(x, pos):
    """債券價格格式化"""
    return f'{x:.2f}'

# 應用到軸
ax.yaxis.set_major_formatter(FuncFormatter(format_price))
```

---

## 5. 圖例設計 (Legend)

### 5.1 圖例元素建立

```python
legend_elements = [
    # 線圖
    plt.Line2D([0], [0],
        color=COLORS["primary"],
        linewidth=2,
        label='主要指標 (R1)'
    ),

    # 虛線
    plt.Line2D([0], [0],
        color=COLORS["secondary"],
        linewidth=1.5,
        linestyle='--',
        label='均線 (P1)'
    ),

    # 面積圖
    plt.Rectangle((0, 0), 1, 1,
        fc=COLORS["area_fill"],
        alpha=COLORS["area_alpha"],
        label='面積指標 (L2)'
    ),
]
```

### 5.2 圖例配置

```python
ax1.legend(
    handles=legend_elements,
    loc='upper left',
    fontsize=8,
    facecolor=COLORS["background"],
    edgecolor=COLORS["grid"],
    labelcolor=COLORS["text"]
)
```

---

## 6. 網格與背景 (Grid & Background)

```python
# 深色背景
plt.style.use('dark_background')
fig.set_facecolor(COLORS["background"])
ax.set_facecolor(COLORS["background"])

# 網格設定
ax.grid(
    True,
    color=COLORS["grid"],
    alpha=0.3,
    linestyle='-',
    linewidth=0.5
)
ax.set_axisbelow(True)  # 網格在數據下方
```

---

## 7. X 軸時間格式 (Time Axis)

```python
import matplotlib.dates as mdates

# 年份標記
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.xaxis.set_major_locator(mdates.YearLocator())

# 月份標記（較短時間範圍）
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))

# 顏色
ax.tick_params(axis='x', colors=COLORS["text_dim"])
```

---

## 8. 標題與頁尾 (Title & Footer)

### 8.1 標題

```python
fig.suptitle(
    "圖表標題",
    color=COLORS["text"],
    fontsize=14,
    fontweight='bold',
    y=0.98
)
```

### 8.2 來源與日期標註

```python
# 左下角：資料來源
fig.text(
    0.02, 0.02,
    "資料來源: Yahoo Finance, MacroMicro",
    color=COLORS["text_dim"],
    fontsize=8,
    ha='left'
)

# 右下角：截止日期
fig.text(
    0.98, 0.02,
    f'截至: {latest_date.strftime("%Y-%m-%d")}',
    color=COLORS["text_dim"],
    fontsize=8,
    ha='right'
)
```

---

## 9. 佈局微調 (Layout Adjustment)

```python
plt.tight_layout()
plt.subplots_adjust(
    top=0.93,    # 標題空間
    bottom=0.08  # 頁尾空間
)
```

---

## 10. 檔案輸出 (Export)

```python
from pathlib import Path

output_path = Path(output_path)
output_path.parent.mkdir(parents=True, exist_ok=True)

plt.savefig(
    output_path,
    dpi=150,                           # 解析度
    bbox_inches='tight',               # 緊密邊界
    facecolor=COLORS["background"]     # 保持背景色
)
plt.close()
```

### 10.1 建議輸出規格

| 參數    | 建議值  | 說明          |
|---------|---------|---------------|
| figsize | (14, 8) | 寬螢幕比例    |
| dpi     | 150     | 網頁/文檔用途 |
| dpi     | 300     | 印刷用途      |
| format  | PNG     | 透明度支援    |

---

## 11. 完整範例模板

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bloomberg 風格圖表模板
"""

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import pandas as pd
from pathlib import Path
from datetime import datetime

# 中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# Bloomberg 配色
COLORS = {
    "background": "#1a1a2e",
    "grid": "#2d2d44",
    "text": "#ffffff",
    "text_dim": "#888888",
    "primary": "#ff6b35",
    "secondary": "#ffaa00",
    "tertiary": "#ffff00",
    "area_fill": "#ff8c00",
    "area_alpha": 0.4,
    "level_line": "#666666",
}


def plot_bloomberg_chart(
    data: pd.DataFrame,
    output_path: str,
    title: str = "圖表標題",
    source: str = "資料來源: Yahoo Finance"
):
    """
    繪製 Bloomberg 風格圖表

    Parameters
    ----------
    data : pd.DataFrame
        包含 DatetimeIndex 的數據框
    output_path : str
        輸出路徑
    title : str
        圖表標題
    source : str
        資料來源
    """
    plt.style.use('dark_background')

    fig, ax1 = plt.subplots(figsize=(14, 8), facecolor=COLORS["background"])
    ax1.set_facecolor(COLORS["background"])

    # === 繪製數據 ===
    # TODO: 根據需求繪製數據

    # === 網格 ===
    ax1.grid(True, color=COLORS["grid"], alpha=0.3, linestyle='-', linewidth=0.5)
    ax1.set_axisbelow(True)

    # === X 軸 ===
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.tick_params(axis='x', colors=COLORS["text_dim"])

    # === 標題 ===
    fig.suptitle(title, color=COLORS["text"], fontsize=14, fontweight='bold', y=0.98)

    # === 頁尾 ===
    fig.text(0.02, 0.02, source, color=COLORS["text_dim"], fontsize=8, ha='left')
    fig.text(0.98, 0.02, f'截至: {datetime.now().strftime("%Y-%m-%d")}',
             color=COLORS["text_dim"], fontsize=8, ha='right')

    # === 輸出 ===
    plt.tight_layout()
    plt.subplots_adjust(top=0.93, bottom=0.08)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=COLORS["background"])
    plt.close()

    print(f"圖表已儲存: {output_path}")


if __name__ == "__main__":
    # 測試用
    import numpy as np

    dates = pd.date_range('2020-01-01', periods=60, freq='ME')
    data = pd.DataFrame({
        'value': np.random.randn(60).cumsum() + 100
    }, index=dates)

    plot_bloomberg_chart(data, 'output/test_chart.png', '測試圖表')
```

---

## 12. 常見問題 (Troubleshooting)

### 12.1 中文亂碼

**問題**：圖表中文顯示為方框或亂碼

**解決**：
```python
# 確保在 import pyplot 前設定
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
```

### 12.2 Segmentation Fault

**問題**：在無 GUI 環境執行時崩潰

**解決**：
```python
import matplotlib
matplotlib.use('Agg')  # 必須在 import pyplot 前
```

### 12.3 圖表比例失真

**問題**：輸出圖表被裁切或比例不對

**解決**：
```python
plt.savefig(output_path, bbox_inches='tight')
```

### 12.4 多軸標籤重疊

**問題**：左側多軸標籤互相重疊

**解決**：
```python
ax_outer.spines['left'].set_position(('outward', 60))  # 調整偏移量
```

---

## 13. 參考資源

- [Matplotlib 官方文檔](https://matplotlib.org/stable/)
- [Bloomberg Intelligence 圖表範例](https://www.bloomberg.com/professional/solution/bloomberg-intelligence/)
- 本專案範例：`skills/analyze-copper-stock-resilience-dependency/scripts/visualize.py`
