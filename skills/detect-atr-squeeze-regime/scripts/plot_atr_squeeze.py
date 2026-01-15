#!/usr/bin/env python3
"""
ATR Squeeze Regime Visualization

Generates comprehensive dashboard charts for ATR squeeze regime analysis.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    yf = None

# Set matplotlib style (use built-in style)
try:
    plt.style.use('seaborn-v0_8-whitegrid')
except OSError:
    plt.style.use('ggplot')
plt.rcParams['font.family'] = ['DejaVu Sans', 'Microsoft JhengHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.facecolor'] = '#1a1a2e'
plt.rcParams['axes.facecolor'] = '#16213e'
plt.rcParams['axes.edgecolor'] = '#e94560'
plt.rcParams['axes.labelcolor'] = '#edf6f9'
plt.rcParams['text.color'] = '#edf6f9'
plt.rcParams['xtick.color'] = '#edf6f9'
plt.rcParams['ytick.color'] = '#edf6f9'
plt.rcParams['grid.color'] = '#0f3460'
plt.rcParams['grid.alpha'] = 0.3


# Color scheme
COLORS = {
    'squeeze': '#e94560',      # Red - squeeze regime
    'elevated': '#f39c12',     # Orange - elevated volatility
    'orderly': '#27ae60',      # Green - orderly market
    'price': '#3498db',        # Blue - price line
    'atr': '#9b59b6',          # Purple - ATR line
    'baseline': '#95a5a6',     # Gray - baseline
    'background': '#1a1a2e',
    'panel': '#16213e',
    'text': '#edf6f9',
    'accent': '#e94560',
}


def calculate_true_range(df: pd.DataFrame) -> pd.Series:
    """Calculate True Range from OHLC data."""
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate ATR with EMA smoothing."""
    tr = calculate_true_range(df)
    return tr.ewm(span=period, adjust=False).mean()


def fetch_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch OHLCV data."""
    if yf is None:
        raise ImportError("yfinance is required")
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date, interval="1d")
    if df.empty:
        raise ValueError(f"No data found for {symbol}")
    return df


def classify_regime(atr_pct: float, ratio: float) -> str:
    """Classify market regime."""
    if atr_pct >= 6.0 and ratio >= 2.0:
        return "volatility_dominated_squeeze"
    elif ratio >= 1.2:
        return "elevated_volatility_trend"
    else:
        return "orderly_market"


def get_regime_color(regime: str) -> str:
    """Get color for regime."""
    if regime == "volatility_dominated_squeeze":
        return COLORS['squeeze']
    elif regime == "elevated_volatility_trend":
        return COLORS['elevated']
    else:
        return COLORS['orderly']


def create_gauge(ax, value: float, max_value: float = 4.0, label: str = "ATR Ratio"):
    """Create a semi-circular gauge chart."""
    ax.set_aspect('equal')
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-0.2, 1.2)
    ax.axis('off')

    # Define gauge segments
    segments = [
        (0, 1.2, COLORS['orderly'], 'Orderly'),
        (1.2, 2.0, COLORS['elevated'], 'Elevated'),
        (2.0, max_value, COLORS['squeeze'], 'Squeeze'),
    ]

    # Draw gauge background arc
    for start, end, color, _ in segments:
        start_angle = 180 - (start / max_value) * 180
        end_angle = 180 - (end / max_value) * 180
        wedge = mpatches.Wedge(
            (0, 0), 1.0, end_angle, start_angle,
            width=0.3, facecolor=color, alpha=0.7
        )
        ax.add_patch(wedge)

    # Draw needle
    angle = np.radians(180 - (min(value, max_value) / max_value) * 180)
    needle_x = 0.85 * np.cos(angle)
    needle_y = 0.85 * np.sin(angle)
    ax.annotate('', xy=(needle_x, needle_y), xytext=(0, 0),
                arrowprops=dict(arrowstyle='->', color=COLORS['text'], lw=3))

    # Center circle
    circle = plt.Circle((0, 0), 0.15, color=COLORS['panel'], zorder=5)
    ax.add_patch(circle)

    # Value text
    ax.text(0, -0.05, f'{value:.2f}x', ha='center', va='center',
            fontsize=14, fontweight='bold', color=COLORS['text'])
    ax.text(0, 0.5, label, ha='center', va='center',
            fontsize=12, color=COLORS['text'])

    # Scale labels
    ax.text(-1.1, -0.1, '0', ha='center', fontsize=9, color=COLORS['text'])
    ax.text(0, 1.05, f'{max_value/2:.1f}', ha='center', fontsize=9, color=COLORS['text'])
    ax.text(1.1, -0.1, f'{max_value:.1f}', ha='center', fontsize=9, color=COLORS['text'])


def create_status_panel(ax, result: dict):
    """Create status summary panel."""
    ax.axis('off')

    regime = result['regime']
    regime_color = get_regime_color(regime)

    # Regime display names
    regime_names = {
        'volatility_dominated_squeeze': '擠壓行情',
        'elevated_volatility_trend': '波動偏高',
        'orderly_market': '秩序市場',
    }

    # Title
    ax.text(0.5, 0.95, '當前狀態', ha='center', va='top',
            fontsize=16, fontweight='bold', color=COLORS['text'])

    # Regime badge
    badge = mpatches.FancyBboxPatch(
        (0.1, 0.7), 0.8, 0.18,
        boxstyle="round,pad=0.02",
        facecolor=regime_color, alpha=0.8
    )
    ax.add_patch(badge)
    ax.text(0.5, 0.79, regime_names.get(regime, regime),
            ha='center', va='center', fontsize=14, fontweight='bold', color='white')

    # Stats
    stats = [
        ('ATR%', f"{result['atr_pct']:.2f}%"),
        ('倍率', f"{result['atr_ratio_to_baseline']:.2f}x"),
        ('可靠度', f"{result['tech_level_reliability_score']}/100"),
        ('RSI', f"{result['auxiliary_indicators']['rsi_14']:.1f}"),
    ]

    y_pos = 0.55
    for label, value in stats:
        ax.text(0.15, y_pos, label + ':', ha='left', va='center',
                fontsize=11, color=COLORS['baseline'])
        ax.text(0.85, y_pos, value, ha='right', va='center',
                fontsize=11, fontweight='bold', color=COLORS['text'])
        y_pos -= 0.12

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)


def create_recommendations_panel(ax, result: dict):
    """Create recommendations panel."""
    ax.axis('off')

    ax.text(0.5, 0.95, '風控建議', ha='center', va='top',
            fontsize=16, fontweight='bold', color=COLORS['text'])

    adjustments = result['risk_adjustments']

    recs = [
        ('停損倍數', f"{adjustments['suggested_stop_atr_mult']:.1f} ATR"),
        ('倉位規模', f"{adjustments['position_scale']:.0%}"),
        ('時間框架', adjustments['recommended_timeframe'].upper()),
        ('工具建議', '期權/價差' if 'options' in adjustments['instrument_suggestion'] else '裸倉位'),
    ]

    y_pos = 0.75
    for label, value in recs:
        ax.text(0.15, y_pos, label + ':', ha='left', va='center',
                fontsize=11, color=COLORS['baseline'])
        ax.text(0.85, y_pos, value, ha='right', va='center',
                fontsize=11, fontweight='bold', color=COLORS['accent'])
        y_pos -= 0.15

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)


def plot_atr_squeeze_dashboard(
    symbol: str,
    start_date: str = None,
    end_date: str = None,
    output_dir: str = "output",
    baseline_window: int = 756,
) -> str:
    """
    Generate comprehensive ATR squeeze dashboard.

    Returns:
        Path to saved figure
    """
    # Default dates
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if start_date is None:
        start_dt = datetime.now() - timedelta(days=365 * 5)
        start_date = start_dt.strftime("%Y-%m-%d")

    # Fetch data
    df = fetch_data(symbol, start_date, end_date)

    # Calculate indicators
    atr = calculate_atr(df, 14)
    atr_pct = 100.0 * atr / df["Close"]
    baseline = atr_pct.rolling(baseline_window).mean()
    ratio = atr_pct / baseline

    # Get latest values
    latest_atr_pct = float(atr_pct.iloc[-1])
    latest_baseline = float(baseline.iloc[-1]) if not pd.isna(baseline.iloc[-1]) else latest_atr_pct
    latest_ratio = float(ratio.iloc[-1]) if not pd.isna(ratio.iloc[-1]) else 1.0
    latest_close = float(df["Close"].iloc[-1])

    # RSI
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    latest_rsi = float(rsi.iloc[-1])

    # Classify regime
    regime = classify_regime(latest_atr_pct, latest_ratio)
    regime_color = get_regime_color(regime)

    # Build result dict for panels
    result = {
        'symbol': symbol,
        'regime': regime,
        'atr_pct': latest_atr_pct,
        'atr_ratio_to_baseline': latest_ratio,
        'baseline_atr_pct': latest_baseline,
        'tech_level_reliability_score': max(0, min(100, int(50 - (latest_ratio - 2.0) * 20))) if regime == 'volatility_dominated_squeeze' else 70,
        'auxiliary_indicators': {'rsi_14': latest_rsi},
        'risk_adjustments': {
            'suggested_stop_atr_mult': round(2.0 + min(1.0, (latest_atr_pct - 6.0) / 4.0), 1) if regime == 'volatility_dominated_squeeze' else 1.5,
            'position_scale': round(min(1.0, 3.0 / max(latest_atr_pct, 0.01)), 2) if regime == 'volatility_dominated_squeeze' else 0.8,
            'recommended_timeframe': 'weekly' if regime == 'volatility_dominated_squeeze' else 'daily',
            'instrument_suggestion': 'options_or_spreads' if regime == 'volatility_dominated_squeeze' else 'naked_position',
        },
    }

    # Create figure with grid layout
    fig = plt.figure(figsize=(16, 12), facecolor=COLORS['background'])

    # GridSpec layout
    gs = gridspec.GridSpec(3, 3, figure=fig, height_ratios=[2, 2, 1.2],
                           hspace=0.3, wspace=0.25)

    # Title
    fig.suptitle(f'{symbol} ATR 擠壓行情分析儀表盤',
                 fontsize=20, fontweight='bold', color=COLORS['text'], y=0.98)
    fig.text(0.5, 0.94, f"截至 {df.index[-1].strftime('%Y-%m-%d')} | 收盤價 ${latest_close:.2f}",
             ha='center', fontsize=12, color=COLORS['baseline'])

    # Panel 1: Price chart (top left, spans 2 columns)
    ax_price = fig.add_subplot(gs[0, :2])
    ax_price.plot(df.index, df['Close'], color=COLORS['price'], linewidth=1.5, label='Price')
    ax_price.fill_between(df.index, df['Close'], alpha=0.2, color=COLORS['price'])
    ax_price.set_title('價格走勢', fontsize=14, fontweight='bold', color=COLORS['text'], pad=10)
    ax_price.set_ylabel('價格 ($)', color=COLORS['text'])
    ax_price.legend(loc='upper left', facecolor=COLORS['panel'], labelcolor=COLORS['text'])
    ax_price.tick_params(axis='x', rotation=30)

    # Panel 2: ATR% chart (middle left, spans 2 columns)
    ax_atr = fig.add_subplot(gs[1, :2])
    ax_atr.plot(df.index, atr_pct, color=COLORS['atr'], linewidth=1.5, label='ATR%')
    ax_atr.plot(df.index, baseline, color=COLORS['baseline'], linewidth=1.5,
                linestyle='--', label=f'{baseline_window}日均值', alpha=0.8)

    # Fill regime zones
    ax_atr.axhspan(0, 6, alpha=0.1, color=COLORS['orderly'], label='秩序區')
    ax_atr.axhspan(6, 15, alpha=0.1, color=COLORS['squeeze'], label='擠壓區')
    ax_atr.axhline(y=6, color=COLORS['squeeze'], linestyle=':', alpha=0.5)

    ax_atr.set_title('ATR% 波動率', fontsize=14, fontweight='bold', color=COLORS['text'], pad=10)
    ax_atr.set_ylabel('ATR%', color=COLORS['text'])
    ax_atr.legend(loc='upper left', facecolor=COLORS['panel'], labelcolor=COLORS['text'], ncol=2)
    ax_atr.tick_params(axis='x', rotation=30)
    max_atr = atr_pct.dropna().max() if not atr_pct.dropna().empty else 8
    ax_atr.set_ylim(0, max(max_atr * 1.1, 8))

    # Panel 3: Gauge (top right)
    ax_gauge = fig.add_subplot(gs[0, 2])
    create_gauge(ax_gauge, latest_ratio, max_value=4.0, label='ATR 倍率')

    # Panel 4: Status panel (middle right)
    ax_status = fig.add_subplot(gs[1, 2])
    create_status_panel(ax_status, result)

    # Panel 5: Ratio time series (bottom, spans 2 columns)
    ax_ratio = fig.add_subplot(gs[2, :2])
    ratio_recent = ratio.iloc[-252:].copy()
    ratio_recent_clean = ratio_recent.fillna(1.0)  # Fill NaN with baseline
    ax_ratio.plot(df.index[-252:], ratio_recent_clean, color=COLORS['accent'], linewidth=1.5)
    ax_ratio.axhline(y=1.0, color=COLORS['baseline'], linestyle='--', alpha=0.5, label='基準線 (1.0x)')
    ax_ratio.axhline(y=1.2, color=COLORS['elevated'], linestyle=':', alpha=0.7, label='警戒線 (1.2x)')
    ax_ratio.axhline(y=2.0, color=COLORS['squeeze'], linestyle=':', alpha=0.7, label='擠壓線 (2.0x)')
    ax_ratio.fill_between(df.index[-252:], ratio_recent_clean, 1.0,
                          where=ratio_recent_clean >= 2.0, alpha=0.3, color=COLORS['squeeze'])
    ax_ratio.set_title('ATR 倍率 (近一年)', fontsize=14, fontweight='bold', color=COLORS['text'], pad=10)
    ax_ratio.set_ylabel('倍率', color=COLORS['text'])
    ax_ratio.legend(loc='upper left', facecolor=COLORS['panel'], labelcolor=COLORS['text'], ncol=3)
    ax_ratio.tick_params(axis='x', rotation=30)
    max_ratio = ratio_recent_clean.max() if not ratio_recent_clean.empty else 2.5
    ax_ratio.set_ylim(0.5, max(max_ratio * 1.1, 2.5))

    # Panel 6: Recommendations (bottom right)
    ax_rec = fig.add_subplot(gs[2, 2])
    create_recommendations_panel(ax_rec, result)

    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate filename with date
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"atr_squeeze_{symbol.replace('=', '')}_{date_str}.png"
    filepath = output_path / filename

    # Save figure
    plt.savefig(filepath, dpi=150, bbox_inches='tight',
                facecolor=COLORS['background'], edgecolor='none')
    plt.close()

    return str(filepath)


def main():
    parser = argparse.ArgumentParser(description="Plot ATR Squeeze Dashboard")
    parser.add_argument("--symbol", type=str, default="SI=F", help="Asset symbol")
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", type=str, default="output", help="Output directory")
    parser.add_argument("--baseline-window", type=int, default=756, help="Baseline window days")

    args = parser.parse_args()

    try:
        filepath = plot_atr_squeeze_dashboard(
            symbol=args.symbol,
            start_date=args.start,
            end_date=args.end,
            output_dir=args.output,
            baseline_window=args.baseline_window,
        )
        print(f"Dashboard saved to: {filepath}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
