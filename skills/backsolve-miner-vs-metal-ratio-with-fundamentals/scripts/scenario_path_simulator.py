#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
共同上漲情境路徑模擬器

分析銀價與礦業股在不同比率假設下的漲幅關係，並生成路徑表與視覺化圖表。

核心公式：
  礦業股漲幅 = (1 + 銀價漲幅) × (R1/R0) - 1

Usage:
    python scenario_path_simulator.py --quick
    python scenario_path_simulator.py --silver-monthly 5 --ratio-start 1.10 --ratio-end 1.20 --months 6
    python scenario_path_simulator.py --miner-target 15 --ratio-range 1.00,1.20
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Tuple

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 配色
COLORS = {
    'silver': '#C0C0C0',
    'miner': '#2E86AB',
    'ratio': '#F18F01',
    'grid': '#E9ECEF',
    'background': '#F8F9FA',
    'text': '#212529',
    'gain': '#28A745',
    'loss': '#C73E1D',
}


def compute_miner_return(
    silver_return: float,
    ratio_start: float,
    ratio_end: float
) -> float:
    """
    計算礦業股漲幅

    公式：礦業股漲幅 = (1 + 銀價漲幅) × (R1/R0) - 1

    Parameters
    ----------
    silver_return : float
        銀價漲幅（如 0.05 = 5%）
    ratio_start : float
        起始比率 R0
    ratio_end : float
        結束比率 R1

    Returns
    -------
    float
        礦業股漲幅
    """
    return (1 + silver_return) * (ratio_end / ratio_start) - 1


def compute_silver_return(
    miner_return: float,
    ratio_start: float,
    ratio_end: float
) -> float:
    """
    反推銀價漲幅

    公式：銀價漲幅 = (1 + 礦業股漲幅) × (R0/R1) - 1
    """
    return (1 + miner_return) * (ratio_start / ratio_end) - 1


def generate_return_grid(
    ratio_start: float = 1.103,
    silver_returns: list = None,
    ratio_ends: list = None
) -> pd.DataFrame:
    """
    生成銀價漲幅 × 比率變動的礦業股漲幅網格
    """
    if silver_returns is None:
        silver_returns = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
    if ratio_ends is None:
        ratio_ends = [1.00, 1.05, 1.10, 1.15, 1.20]

    data = []
    for sr in silver_returns:
        row = {'silver_return': sr}
        for re in ratio_ends:
            mr = compute_miner_return(sr, ratio_start, re)
            row[f'R={re:.2f}'] = mr
        data.append(row)

    return pd.DataFrame(data)


def generate_path_table(
    S0: float = 30.17,
    P0: float = 33.28,
    R0: float = 1.103,
    silver_monthly_return: float = 0.05,
    ratio_start: float = 1.10,
    ratio_end: float = 1.20,
    months: int = 6
) -> pd.DataFrame:
    """
    生成共同上漲路徑表

    Parameters
    ----------
    S0 : float
        起始銀價
    P0 : float
        起始礦業股價格
    R0 : float
        起始比率
    silver_monthly_return : float
        銀價每月漲幅
    ratio_start : float
        比率起點（M1 起）
    ratio_end : float
        比率終點
    months : int
        模擬月數

    Returns
    -------
    pd.DataFrame
        路徑表
    """
    # 比率線性插值
    ratios = [R0] + list(np.linspace(ratio_start, ratio_end, months))

    data = []
    S_prev, P_prev = S0, P0
    S_cum, P_cum = 0, 0

    for t in range(months + 1):
        if t == 0:
            S, R = S0, R0
            P = P0
            S_mom, P_mom = 0, 0
        else:
            S = S_prev * (1 + silver_monthly_return)
            R = ratios[t]
            P = R * S
            S_mom = S / S_prev - 1
            P_mom = P / P_prev - 1

        S_cum = S / S0 - 1
        P_cum = P / P0 - 1

        data.append({
            'month': f'M{t}',
            'silver': round(S, 2),
            'ratio': round(R, 3),
            'miner': round(P, 2),
            'silver_mom': round(S_mom * 100, 1),
            'miner_mom': round(P_mom * 100, 1),
            'silver_cum': round(S_cum * 100, 1),
            'miner_cum': round(P_cum * 100, 1),
        })

        S_prev, P_prev = S, P

    return pd.DataFrame(data)


def plot_scenario_path(
    df: pd.DataFrame,
    output_path: str,
    title: str = None
):
    """
    繪製共同上漲路徑圖（雙軸：價格 + 比率）
    """
    fig, ax1 = plt.subplots(figsize=(12, 7), facecolor=COLORS['background'])

    months = df['month'].tolist()
    x = range(len(months))

    # 左軸：價格
    ax1.set_facecolor(COLORS['background'])

    # 銀價線
    line1, = ax1.plot(x, df['silver'], marker='o', markersize=8,
                      color=COLORS['silver'], linewidth=2.5,
                      label='白銀價格 ($/oz)', zorder=3)
    ax1.fill_between(x, df['silver'].min() * 0.95, df['silver'],
                     color=COLORS['silver'], alpha=0.15)

    # 礦業股線
    line2, = ax1.plot(x, df['miner'], marker='s', markersize=8,
                      color=COLORS['miner'], linewidth=2.5,
                      label='礦業股價格 (SIL $)', zorder=3)
    ax1.fill_between(x, df['miner'].min() * 0.95, df['miner'],
                     color=COLORS['miner'], alpha=0.15)

    ax1.set_xlabel('月份', fontsize=11)
    ax1.set_ylabel('價格', fontsize=11, color=COLORS['text'])
    ax1.set_xticks(x)
    ax1.set_xticklabels(months)
    ax1.tick_params(axis='y', labelcolor=COLORS['text'])
    ax1.grid(True, alpha=0.3, linestyle='--')

    # 標註價格
    for i, (s, p) in enumerate(zip(df['silver'], df['miner'])):
        ax1.annotate(f'${s:.1f}', (i, s), textcoords='offset points',
                     xytext=(0, 8), ha='center', fontsize=8, color='gray')
        ax1.annotate(f'${p:.1f}', (i, p), textcoords='offset points',
                     xytext=(0, -15), ha='center', fontsize=8, color=COLORS['miner'])

    # 右軸：比率
    ax2 = ax1.twinx()
    line3, = ax2.plot(x, df['ratio'], marker='D', markersize=7,
                      color=COLORS['ratio'], linewidth=2, linestyle='--',
                      label='比率 (SIL/白銀)', zorder=2)
    ax2.set_ylabel('比率', fontsize=11, color=COLORS['ratio'])
    ax2.tick_params(axis='y', labelcolor=COLORS['ratio'])

    # 標註比率
    for i, r in enumerate(df['ratio']):
        ax2.annotate(f'{r:.2f}', (i, r), textcoords='offset points',
                     xytext=(0, 8), ha='center', fontsize=9,
                     color=COLORS['ratio'], fontweight='bold')

    # 合併圖例
    lines = [line1, line2, line3]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left', fontsize=10,
               framealpha=0.9, edgecolor='none')

    # 標題
    if title:
        fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
    else:
        # 自動生成標題
        silver_total = df['silver_cum'].iloc[-1]
        miner_total = df['miner_cum'].iloc[-1]
        ratio_change = df['ratio'].iloc[-1] - df['ratio'].iloc[0]
        fig.suptitle(
            f"共同上漲情境：白銀 +{silver_total:.0f}% → 礦業股 +{miner_total:.0f}% "
            f"(比率 {ratio_change:+.2f})",
            fontsize=13, fontweight='bold', y=0.98
        )

    # 添加累積收益摘要
    summary = (
        f"累積收益｜白銀: +{df['silver_cum'].iloc[-1]:.1f}%  "
        f"礦業股: +{df['miner_cum'].iloc[-1]:.1f}%  "
        f"超額: +{df['miner_cum'].iloc[-1] - df['silver_cum'].iloc[-1]:.1f}%"
    )
    fig.text(0.5, 0.02, summary, ha='center', fontsize=10,
             style='italic', color=COLORS['text'])

    plt.tight_layout(rect=[0, 0.04, 1, 0.96])
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=COLORS['background'])
    plt.close()

    print(f"圖表已保存至: {output_path}")


def plot_return_heatmap(
    grid_df: pd.DataFrame,
    ratio_start: float,
    output_path: str
):
    """
    繪製收益率網格熱力圖
    """
    fig, ax = plt.subplots(figsize=(10, 7), facecolor=COLORS['background'])

    # 準備數據
    silver_returns = grid_df['silver_return'].values
    ratio_cols = [c for c in grid_df.columns if c.startswith('R=')]
    ratios = [float(c.split('=')[1]) for c in ratio_cols]

    matrix = grid_df[ratio_cols].values * 100  # 轉為百分比

    # 繪製熱力圖
    cmap = plt.cm.RdYlGn
    im = ax.imshow(matrix, cmap=cmap, aspect='auto',
                   vmin=-10, vmax=50)

    # 標註數值
    for i in range(len(silver_returns)):
        for j in range(len(ratios)):
            val = matrix[i, j]
            color = 'white' if abs(val) > 25 else 'black'
            ax.text(j, i, f'{val:+.0f}%', ha='center', va='center',
                    fontsize=10, color=color, fontweight='bold')

    # 軸標籤
    ax.set_xticks(range(len(ratios)))
    ax.set_yticks(range(len(silver_returns)))
    ax.set_xticklabels([f'{r:.2f}' for r in ratios], fontsize=10)
    ax.set_yticklabels([f'+{int(sr*100)}%' for sr in silver_returns], fontsize=10)

    ax.set_xlabel(f'目標比率 R₁ (起始 R₀={ratio_start:.3f})', fontsize=11)
    ax.set_ylabel('銀價漲幅', fontsize=11)
    ax.set_title('礦業股漲幅對照表\n(銀價漲幅 × 比率變動)', fontsize=13, fontweight='bold')

    # 色條
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('礦業股漲幅 (%)', fontsize=10)

    # 標記比率不變線
    r0_idx = None
    for i, r in enumerate(ratios):
        if abs(r - ratio_start) < 0.01:
            r0_idx = i
            break
    if r0_idx is not None:
        ax.axvline(r0_idx, color='red', linewidth=2, linestyle='--', alpha=0.7)
        ax.text(r0_idx, -0.7, '比率不變', ha='center', fontsize=9, color='red')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=COLORS['background'])
    plt.close()

    print(f"熱力圖已保存至: {output_path}")


def print_quick_reference(ratio_start: float = 1.103):
    """
    打印快速對照表
    """
    print("\n" + "="*60)
    print(f"快速對照表：銀價漲幅 → 礦業股漲幅 (R₀={ratio_start:.3f})")
    print("="*60)

    silver_returns = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
    ratio_ends = [1.00, 1.10, 1.20]

    print(f"\n{'銀價漲幅':^10} | {'R₁=1.00':^12} | {'R₁=1.10':^12} | {'R₁=1.20':^12}")
    print("-" * 55)

    for sr in silver_returns:
        row = f"{'+' + str(int(sr*100)) + '%':^10} |"
        for re in ratio_ends:
            mr = compute_miner_return(sr, ratio_start, re)
            row += f" {mr*100:+6.1f}%     |"
        print(row)

    print("\n直覺讀法：")
    print("  - 比率維持不變 → 礦業股漲幅 ≈ 銀價漲幅")
    print("  - 比率上修（→1.20）→ 礦業股明顯跑贏銀價")
    print("  - 比率下修（→1.00）→ 礦業股落後，甚至可能銀漲但礦不漲")
    print("\n近似公式：礦業股漲幅 ≈ 銀價漲幅 + 比率變動幅度")


def main():
    parser = argparse.ArgumentParser(description="共同上漲情境路徑模擬器")

    parser.add_argument("--quick", action="store_true",
                        help="快速模式：銀價月漲5%，比率1.10→1.20，6個月")
    parser.add_argument("--silver-monthly", type=float, default=5,
                        help="銀價每月漲幅 (%%)")
    parser.add_argument("--ratio-start", type=float, default=1.10,
                        help="比率起點 (M1起)")
    parser.add_argument("--ratio-end", type=float, default=1.20,
                        help="比率終點")
    parser.add_argument("--months", type=int, default=6,
                        help="模擬月數")
    parser.add_argument("--s0", type=float, default=30.17,
                        help="起始銀價")
    parser.add_argument("--p0", type=float, default=33.28,
                        help="起始礦業股價格")
    parser.add_argument("--r0", type=float, default=1.103,
                        help="當前比率")
    parser.add_argument("--output", type=str, default="output/",
                        help="輸出目錄")
    parser.add_argument("--heatmap", action="store_true",
                        help="同時生成收益率熱力圖")

    args = parser.parse_args()

    # 確保輸出目錄存在
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")

    # 打印快速對照表
    print_quick_reference(args.r0)

    # 生成路徑表
    print("\n" + "="*60)
    print("生成路徑表...")
    print("="*60)

    df = generate_path_table(
        S0=args.s0,
        P0=args.p0,
        R0=args.r0,
        silver_monthly_return=args.silver_monthly / 100,
        ratio_start=args.ratio_start,
        ratio_end=args.ratio_end,
        months=args.months
    )

    # 打印路徑表
    print(f"\n假設：銀價每月 +{args.silver_monthly}%，比率 {args.ratio_start} → {args.ratio_end}")
    print(df.to_string(index=False))

    # 生成路徑圖
    path_output = output_dir / f"scenario_path_{today}.png"
    plot_scenario_path(df, str(path_output))

    # 生成熱力圖
    if args.heatmap or args.quick:
        grid_df = generate_return_grid(args.r0)
        heatmap_output = output_dir / f"return_heatmap_{today}.png"
        plot_return_heatmap(grid_df, args.r0, str(heatmap_output))

    # 輸出 JSON
    result = {
        "skill": "scenario_path_simulator",
        "generated_at": datetime.now().isoformat(),
        "inputs": {
            "S0": args.s0,
            "P0": args.p0,
            "R0": args.r0,
            "silver_monthly_return": args.silver_monthly / 100,
            "ratio_start": args.ratio_start,
            "ratio_end": args.ratio_end,
            "months": args.months,
        },
        "path_table": df.to_dict(orient='records'),
        "summary": {
            "silver_cumulative": df['silver_cum'].iloc[-1],
            "miner_cumulative": df['miner_cum'].iloc[-1],
            "excess_return": df['miner_cum'].iloc[-1] - df['silver_cum'].iloc[-1],
        },
        "formula": {
            "miner_return": "(1 + silver_return) * (R1/R0) - 1",
            "approx": "miner_return ≈ silver_return + ratio_change",
        }
    }

    json_output = output_dir / f"scenario_result_{today}.json"
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nJSON 結果已保存至: {json_output}")


if __name__ == "__main__":
    main()
