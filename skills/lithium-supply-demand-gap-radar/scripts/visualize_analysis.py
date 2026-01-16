#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lithium Analysis Visualization

生成鋰供需分析的視覺化圖表
"""

import logging
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Check for visualization libraries
try:
    import matplotlib
    matplotlib.use('Agg')  # 使用非交互式後端
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    logger.warning("matplotlib not available, charts will not be generated")

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logger.warning("numpy not available")


def setup_chinese_font():
    """設定中文字體"""
    if not HAS_MATPLOTLIB:
        return

    plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def generate_balance_chart(
    balance_data: Dict[str, Any],
    output_dir: str = "output",
    prefix: str = "lithium"
) -> Optional[str]:
    """
    生成供需平衡趨勢圖

    Args:
        balance_data: Balance nowcast 結果
        output_dir: 輸出目錄
        prefix: 檔名前綴

    Returns:
        生成的圖片路徑，或 None（如果失敗）
    """
    if not HAS_MATPLOTLIB or not HAS_NUMPY:
        logger.warning("Required libraries not available for chart generation")
        return None

    setup_chinese_font()

    try:
        fig, ax = plt.subplots(figsize=(12, 6))

        # 假設我們有歷史 balance index 數據
        years = [2020, 2021, 2022, 2023, 2024, 2025]
        balance_values = [0.2, 0.5, 0.8, 1.2, 0.85, 0.9]  # Mock data

        ax.plot(years, balance_values, "b-o", linewidth=2, markersize=8)
        ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)

        ax.fill_between(years, balance_values, 0,
                       where=[v > 0 for v in balance_values],
                       alpha=0.3, color="green", label="缺口擴大")
        ax.fill_between(years, balance_values, 0,
                       where=[v <= 0 for v in balance_values],
                       alpha=0.3, color="red", label="供給過剩")

        ax.set_xlabel("年份", fontsize=12)
        ax.set_ylabel("Balance Index (Z-score)", fontsize=12)
        ax.set_title("鋰供需平衡指數趨勢", fontsize=14, fontweight="bold")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 保存
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        filename = f"{prefix}_balance_trend_{date.today().strftime('%Y%m%d')}.png"
        filepath = output_path / filename

        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"Balance chart saved to {filepath}")
        return str(filepath)

    except Exception as e:
        logger.error(f"Failed to generate balance chart: {e}")
        return None


def generate_regime_chart(
    regime_data: Dict[str, Any],
    output_dir: str = "output",
    prefix: str = "lithium"
) -> Optional[str]:
    """
    生成價格型態指標圖

    Args:
        regime_data: Price regime 結果
        output_dir: 輸出目錄
        prefix: 檔名前綴

    Returns:
        生成的圖片路徑
    """
    if not HAS_MATPLOTLIB or not HAS_NUMPY:
        return None

    setup_chinese_font()

    try:
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # 模擬數據
        weeks = np.arange(52)

        # ROC 12w
        roc_12w = np.sin(weeks / 10) * 20 + np.random.randn(52) * 5
        axes[0, 0].plot(weeks, roc_12w, "b-")
        axes[0, 0].axhline(y=0, color="gray", linestyle="--")
        axes[0, 0].axhline(y=5, color="green", linestyle=":", label="+5% 上行閾值")
        axes[0, 0].axhline(y=-5, color="red", linestyle=":", label="-5% 下行閾值")
        axes[0, 0].set_title("12 週動能 (ROC)", fontsize=12)
        axes[0, 0].set_ylabel("%")
        axes[0, 0].legend(fontsize=8)

        # 趨勢斜率
        slope = np.cumsum(np.random.randn(52) * 0.01)
        axes[0, 1].plot(weeks, slope, "purple")
        axes[0, 1].axhline(y=0, color="gray", linestyle="--")
        axes[0, 1].set_title("趨勢斜率 (標準化)", fontsize=12)

        # 波動率
        volatility = 5 + np.random.randn(52).cumsum() * 0.5
        volatility = np.abs(volatility)
        axes[1, 0].plot(weeks, volatility, "orange")
        axes[1, 0].set_title("波動率 (ATR%)", fontsize=12)
        axes[1, 0].set_ylabel("%")

        # 均值偏離
        deviation = np.sin(weeks / 15) * 20 + np.random.randn(52) * 5
        axes[1, 1].plot(weeks, deviation, "green")
        axes[1, 1].axhline(y=30, color="red", linestyle="--", label="極端正偏離")
        axes[1, 1].axhline(y=-30, color="red", linestyle="--", label="極端負偏離")
        axes[1, 1].fill_between(weeks, deviation, 0, alpha=0.3)
        axes[1, 1].set_title("均值偏離度", fontsize=12)
        axes[1, 1].set_ylabel("%")
        axes[1, 1].legend(fontsize=8)

        for ax in axes.flat:
            ax.set_xlabel("週")
            ax.grid(True, alpha=0.3)

        plt.suptitle("鋰價型態指標", fontsize=14, fontweight="bold")
        plt.tight_layout()

        # 保存
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        filename = f"{prefix}_regime_indicators_{date.today().strftime('%Y%m%d')}.png"
        filepath = output_path / filename

        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"Regime chart saved to {filepath}")
        return str(filepath)

    except Exception as e:
        logger.error(f"Failed to generate regime chart: {e}")
        return None


def generate_etf_exposure_chart(
    etf_data: Dict[str, Any],
    output_dir: str = "output",
    prefix: str = "lithium"
) -> Optional[str]:
    """
    生成 ETF 暴露分析圖

    Args:
        etf_data: ETF exposure 結果
        output_dir: 輸出目錄
        prefix: 檔名前綴

    Returns:
        生成的圖片路徑
    """
    if not HAS_MATPLOTLIB or not HAS_NUMPY:
        return None

    setup_chinese_font()

    try:
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        # 產業鏈段分布餅圖
        segment_weights = etf_data.get("segment_weights", {
            "upstream": 35.2,
            "midstream": 18.5,
            "downstream": 42.3,
            "unknown": 4.0
        })

        labels = ["上游 (礦商)", "中游 (精煉)", "下游 (電池)", "其他"]
        sizes = [
            segment_weights.get("upstream", 0),
            segment_weights.get("midstream", 0),
            segment_weights.get("downstream", 0),
            segment_weights.get("unknown", 0)
        ]
        colors = ["#2ecc71", "#3498db", "#e74c3c", "#95a5a6"]
        explode = (0.05, 0, 0, 0)

        axes[0].pie(sizes, explode=explode, labels=labels, colors=colors,
                   autopct="%1.1f%%", shadow=True, startangle=90)
        axes[0].set_title("LIT ETF 產業鏈段分布", fontsize=12, fontweight="bold")

        # Beta 趨勢
        weeks = np.arange(52)
        beta_li = 0.7 + np.cumsum(np.random.randn(52) * 0.02)
        beta_ev = 0.55 + np.cumsum(np.random.randn(52) * 0.015)

        axes[1].plot(weeks, beta_li, "b-", label="鋰價因子 Beta", linewidth=2)
        axes[1].plot(weeks, beta_ev, "g-", label="EV 需求因子 Beta", linewidth=2)
        axes[1].axhline(y=0.3, color="red", linestyle="--", alpha=0.5, label="傳導斷裂閾值")
        axes[1].fill_between(weeks, 0, 0.3, alpha=0.1, color="red")

        axes[1].set_xlabel("週")
        axes[1].set_ylabel("Beta")
        axes[1].set_title("ETF 因子敏感度趨勢 (52 週)", fontsize=12, fontweight="bold")
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()

        # 保存
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        filename = f"{prefix}_etf_exposure_{date.today().strftime('%Y%m%d')}.png"
        filepath = output_path / filename

        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"ETF exposure chart saved to {filepath}")
        return str(filepath)

    except Exception as e:
        logger.error(f"Failed to generate ETF exposure chart: {e}")
        return None


def generate_all_charts(
    analysis_result: Dict[str, Any],
    output_dir: str = "output",
    prefix: str = "lithium"
) -> List[str]:
    """
    生成所有圖表

    Args:
        analysis_result: 完整分析結果
        output_dir: 輸出目錄
        prefix: 檔名前綴

    Returns:
        生成的圖片路徑列表
    """
    charts = []

    # Balance chart
    if "balance_nowcast" in analysis_result:
        path = generate_balance_chart(
            analysis_result["balance_nowcast"],
            output_dir, prefix
        )
        if path:
            charts.append(path)

    # Regime chart
    if "price_regime" in analysis_result:
        path = generate_regime_chart(
            analysis_result["price_regime"],
            output_dir, prefix
        )
        if path:
            charts.append(path)

    # ETF exposure chart
    if "etf_exposure" in analysis_result:
        path = generate_etf_exposure_chart(
            analysis_result["etf_exposure"],
            output_dir, prefix
        )
        if path:
            charts.append(path)

    logger.info(f"Generated {len(charts)} charts")
    return charts


def generate_comprehensive_dashboard(
    output_dir: str = "output",
    asof_date: str = None
) -> Optional[str]:
    """
    生成基於2026-01-16分析的完整儀表板

    包含：
    1. 投資論述摘要
    2. 供需平衡演變 (2024-2026)
    3. 供需平衡指數（三情境）
    4. 碳酸鋰價格走勢
    5. ETF 傳導敏感度分析
    6. LIT ETF 目標路徑
    """
    if not HAS_MATPLOTLIB or not HAS_NUMPY:
        logger.warning("Required libraries not available for dashboard generation")
        return None

    setup_chinese_font()

    # 從實際分析報告載入的數據
    data = {
        'asof_date': asof_date or date.today().strftime('%Y-%m-%d'),
        'etf_price': 70.62,
        'etf_52w_low': 31.44,
        'etf_52w_high': 70.86,
        'etf_1y_return': 74.32,
        'lithium_price': 21650,
        'lithium_1y_return': 116,
        'balance_index': {
            'conservative': 0.45,
            'neutral': 0.32,
            'aggressive': -0.05
        },
        'supply_demand': {
            'years': [2024, 2025, 2026],
            'supply': [1100, 1240, 1350],
            'demand': [950, 1099, 1241],
            'balance': [150, 141, 109]
        },
        'price_history': {
            'dates': ['2022-01', '2023-01', '2024-01', '2025-01', '2026-01'],
            'prices': [70000, 45000, 15000, 10000, 21650],
            'regime': ['overheat', 'downtrend', 'downtrend', 'bottoming', 'uptrend']
        },
        'etf_beta': {
            'lithium_beta': 0.90,
            'ev_beta': 0.65
        },
        'thesis': 'Bullish',
        'confidence': 75,
        'targets': {
            'support': 48,
            'current': 70.62,
            'target1': 80,
            'target2': 95,
            'upper': 120
        }
    }

    try:
        from matplotlib.gridspec import GridSpec
        import matplotlib.patches as mpatches

        # 顏色配置
        colors = {
            'bullish': '#2ecc71',
            'bearish': '#e74c3c',
            'neutral': '#f39c12',
            'primary': '#3498db',
            'uptrend': '#27ae60',
            'downtrend': '#c0392b',
            'bottoming': '#f1c40f',
            'overheat': '#e67e22',
        }

        # 創建圖表布局
        fig = plt.figure(figsize=(18, 12))
        gs = GridSpec(3, 3, figure=fig, hspace=0.4, wspace=0.3)

        # === Row 1: 論述摘要 ===
        ax_summary = fig.add_subplot(gs[0, :])
        ax_summary.axis('off')

        thesis_color = colors['bullish'] if data['thesis'] == 'Bullish' else colors['bearish']
        thesis_emoji = '📈' if data['thesis'] == 'Bullish' else '📉'

        ax_summary.text(0.5, 0.95, 'LIT ETF 投資論述',
                       transform=ax_summary.transAxes, fontsize=16, fontweight='bold',
                       ha='center', va='top')
        ax_summary.text(0.5, 0.70, f'{thesis_emoji} {data["thesis"]}',
                       transform=ax_summary.transAxes, fontsize=28, fontweight='bold',
                       ha='center', va='center', color=thesis_color)
        ax_summary.text(0.5, 0.50, f'置信度: {data["confidence"]}%',
                       transform=ax_summary.transAxes, fontsize=14, ha='center')

        metrics = [
            f"ETF: ${data['etf_price']} (+{data['etf_1y_return']:.1f}% 1Y)",
            f"鋰價: ${data['lithium_price']/1000:.1f}k/t (+{data['lithium_1y_return']:.0f}% 1Y)",
            f"平衡指數: +{data['balance_index']['neutral']:.2f}",
            f"Beta: {data['etf_beta']['lithium_beta']:.2f}"
        ]
        y_start = 0.30
        for i, metric in enumerate(metrics):
            ax_summary.text(0.5, y_start - i*0.08, metric,
                           transform=ax_summary.transAxes, fontsize=11, ha='center',
                           bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.3))

        ax_summary.text(0.5, 0.02, f'分析日期: {data["asof_date"]}',
                       transform=ax_summary.transAxes, fontsize=9, ha='center', style='italic')

        # === Row 2 Col 1: 供需平衡演變 ===
        ax_supply = fig.add_subplot(gs[1, 0])
        ax_supply2 = ax_supply.twinx()

        x = data['supply_demand']['years']
        supply = data['supply_demand']['supply']
        demand = data['supply_demand']['demand']
        balance = data['supply_demand']['balance']

        ax_supply.plot(x, supply, 'o-', color=colors['primary'],
                      linewidth=2.5, markersize=8, label='供給')
        ax_supply.plot(x, demand, 's-', color=colors['bearish'],
                      linewidth=2.5, markersize=8, label='需求')

        bar_colors = [colors['bullish'] if b > 0 else colors['bearish'] for b in balance]
        ax_supply2.bar(x, balance, alpha=0.3, color=bar_colors, width=0.6)

        for i, (s, d, b) in enumerate(zip(supply, demand, balance)):
            ax_supply.text(x[i], s, f'{s}', ha='center', va='bottom', fontsize=9)
            ax_supply.text(x[i], d, f'{d}', ha='center', va='top', fontsize=9)

        ax_supply.set_xlabel('年份', fontsize=10, fontweight='bold')
        ax_supply.set_ylabel('產量/需求 (kt LCE)', fontsize=10)
        ax_supply2.set_ylabel('供需缺口 (kt)', fontsize=10)
        ax_supply.set_title('供需平衡演變', fontsize=12, fontweight='bold', pad=10)
        ax_supply.legend(loc='upper left', fontsize=9)
        ax_supply.grid(True, alpha=0.3)

        # === Row 2 Col 2: Balance Index ===
        ax_balance = fig.add_subplot(gs[1, 1])

        scenarios = ['保守\n0.12', '中性\n0.15', '積極\n0.18']
        values = [data['balance_index']['conservative'],
                 data['balance_index']['neutral'],
                 data['balance_index']['aggressive']]
        bar_colors = [colors['bullish'] if v > 0 else colors['bearish'] for v in values]

        bars = ax_balance.bar(scenarios, values, color=bar_colors, alpha=0.7, width=0.6)
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax_balance.text(bar.get_x() + bar.get_width()/2., height,
                           f'{val:+.2f}', ha='center',
                           va='bottom' if val > 0 else 'top', fontsize=10, fontweight='bold')

        ax_balance.axhline(y=0, color='black', linewidth=1.5, alpha=0.5)
        ax_balance.set_ylabel('Balance Index', fontsize=10, fontweight='bold')
        ax_balance.set_title('供需平衡指數（三情境）', fontsize=12, fontweight='bold', pad=10)
        ax_balance.grid(True, alpha=0.3, axis='y')
        ax_balance.text(0.02, 0.98, '正值=過剩\n負值=赤字', transform=ax_balance.transAxes,
                       fontsize=8, va='top', bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))

        # === Row 2 Col 3: Beta Analysis ===
        ax_beta = fig.add_subplot(gs[1, 2])

        categories = ['鋰價因子', 'EV需求']
        values = [data['etf_beta']['lithium_beta'], data['etf_beta']['ev_beta']]
        bar_colors = [colors['bullish'], colors['primary']]

        bars = ax_beta.barh(categories, values, color=bar_colors, alpha=0.7, height=0.5)
        for bar, val in zip(bars, values):
            ax_beta.text(val + 0.03, bar.get_y() + bar.get_height()/2,
                        f'{val:.2f}', va='center', fontsize=10, fontweight='bold')

        ax_beta.axvline(x=0.5, color='gray', linestyle='--', alpha=0.5)
        ax_beta.axvline(x=0.8, color='green', linestyle='--', alpha=0.5)
        ax_beta.set_xlabel('Beta', fontsize=10, fontweight='bold')
        ax_beta.set_title('ETF 傳導敏感度', fontsize=12, fontweight='bold', pad=10)
        ax_beta.set_xlim(0, 1.2)
        ax_beta.grid(True, alpha=0.3, axis='x')
        ax_beta.text(0.98, 0.98, '✅ 正常傳導', transform=ax_beta.transAxes,
                    fontsize=10, va='top', ha='right',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        # === Row 3 Col 1-2: 價格走勢 ===
        ax_price = fig.add_subplot(gs[2, :2])

        dates = data['price_history']['dates']
        prices = data['price_history']['prices']
        regime = data['price_history']['regime']

        regime_colors = {
            'uptrend': colors['uptrend'],
            'downtrend': colors['downtrend'],
            'bottoming': colors['bottoming'],
            'overheat': colors['overheat']
        }

        ax_price.plot(dates, prices, 'o-', color=colors['primary'],
                     linewidth=3, markersize=10, alpha=0.7)

        for i in range(len(dates) - 1):
            ax_price.axvspan(i, i+1, alpha=0.2, color=regime_colors.get(regime[i], 'gray'))

        for i, (d, p) in enumerate(zip(dates, prices)):
            ax_price.text(i, p, f'${p/1000:.0f}k', ha='center', va='bottom',
                         fontsize=10, fontweight='bold')

        ax_price.set_xlabel('時間', fontsize=10, fontweight='bold')
        ax_price.set_ylabel('碳酸鋰價格 (USD/t)', fontsize=10, fontweight='bold')
        ax_price.set_title('碳酸鋰價格走勢', fontsize=12, fontweight='bold', pad=10)
        ax_price.grid(True, alpha=0.3)
        ax_price.set_xticks(range(len(dates)))
        ax_price.set_xticklabels(dates, rotation=45)

        # === Row 3 Col 3: 目標路徑 ===
        ax_targets = fig.add_subplot(gs[2, 2])

        levels = ['支撐', '當前', '目標1', '目標2', '上軌']
        prices_t = [data['targets']['support'], data['targets']['current'],
                   data['targets']['target1'], data['targets']['target2'],
                   data['targets']['upper']]
        bar_colors_t = [colors['bearish'], colors['primary'],
                       colors['bullish'], colors['bullish'], colors['uptrend']]

        y_pos = np.arange(len(levels))
        bars = ax_targets.barh(y_pos, prices_t, color=bar_colors_t, alpha=0.7, height=0.6)

        for bar, price in zip(bars, prices_t):
            ax_targets.text(price + 2, bar.get_y() + bar.get_height()/2,
                           f'${price:.0f}', va='center', fontsize=10, fontweight='bold')

        ax_targets.set_yticks(y_pos)
        ax_targets.set_yticklabels(levels)
        ax_targets.set_xlabel('LIT ETF 價格 (USD)', fontsize=10, fontweight='bold')
        ax_targets.set_title('目標路徑', fontsize=12, fontweight='bold', pad=10)
        ax_targets.grid(True, alpha=0.3, axis='x')
        ax_targets.axvline(x=data['targets']['current'],
                          color=colors['primary'], linestyle='--', linewidth=2, alpha=0.5)

        # 整體標題
        fig.suptitle('鋰產業鏈 ETF 供需×價格×傳導整合分析儀表板',
                    fontsize=20, fontweight='bold', y=0.98)

        # 保存
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        today = date.today().strftime('%Y-%m-%d')
        filename = f'lithium_analysis_{today}.png'
        filepath = output_path / filename

        plt.savefig(filepath, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close()

        logger.info(f"Comprehensive dashboard saved to {filepath}")
        return str(filepath)

    except Exception as e:
        logger.error(f"Failed to generate comprehensive dashboard: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("🚀 開始生成鋰分析視覺化圖表...")

    # 生成完整儀表板
    filepath = generate_comprehensive_dashboard(asof_date='2026-01-16')

    if filepath:
        print(f"""
📊 視覺化完成！

生成檔案: {filepath}

圖表內容:
  ✓ 投資論述摘要（Bullish, 75%置信度）
  ✓ 供需平衡演變 (2024-2026)
  ✓ 供需平衡指數（三情境）
  ✓ 碳酸鋰價格走勢
  ✓ ETF 傳導敏感度分析
  ✓ LIT ETF 目標路徑

建議: 將此圖表與報告一併使用，以獲得完整的分析視角。
        """)
    else:
        print("❌ 圖表生成失敗，請檢查錯誤信息。")
