#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
財政赤字情境視覺化工具

生成三軸圖表，顯示勞動市場與財政赤字的關聯：
- 職缺數 (JOLTS) - 藍色
- 失業人數 (UNEMPLOY) - 紅色
- 財政赤字/GDP - 綠色 (右軸)

並加入情境模擬（高失業 + 高 GDP 情境下的赤字推演）
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use('Agg')  # 使用非互動式後端
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

# 導入數據抓取模組
from fetch_data import fetch_multiple_series

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 顏色配置（FRED 圖表風格）
COLORS = {
    'jolts': '#1f77b4',      # 藍色 - 職缺
    'unemploy': '#d62728',   # 紅色 - 失業
    'deficit': '#2ca02c',    # 綠色 - 赤字/GDP
    'gdp_growth': '#9467bd', # 紫色 - GDP 成長率
    'recession': '#e0e0e0',  # 灰色 - 衰退期
    'scenario': '#ff7f0e',   # 橘色 - 情境模擬
    'annotation': '#333333', # 深灰 - 標註文字
}

# 勞動-財政彈性係數（基於 2000-2025 歷史回歸分析）
# 詳見 references/methodology.md
ELASTICITY = {
    'beta_ur': 0.59,       # 失業率每↑1ppt → 赤字/GDP↑0.59ppt
    'beta_ujo': 0.69,      # UJO每↑1 → 赤字/GDP↑0.69ppt
    'beta_jolts': -0.07,   # 職缺每↑1M → 赤字/GDP↓0.07ppt
    'lag_quarters': 4,     # 勞動指標領先赤字約4季
    'deficit_mean_loose': 5.6,   # UJO > 1 時平均赤字 (%)
    'deficit_mean_tight': 5.2,   # UJO ≤ 1 時平均赤字 (%)
}

# NBER 衰退期（簡化版，主要顯示近 30 年）
RECESSIONS = [
    ('2001-03-01', '2001-11-01'),  # Dot-com
    ('2007-12-01', '2009-06-01'),  # 金融危機
    ('2020-02-01', '2020-04-01'),  # COVID
]


def fetch_visualization_data(years: int = 30) -> pd.DataFrame:
    """抓取視覺化所需數據（含 GDP 成長率）"""
    series = ['UNRATE', 'UNEMPLOY', 'JTSJOL', 'FYFSGDA188S', 'A191RL1Q225SBEA']
    # A191RL1Q225SBEA = Real GDP Growth Rate (Quarterly, SAAR)
    data = fetch_multiple_series(series, years=years)
    return data


def identify_crossover_events(
    unemploy: pd.Series,
    jolts: pd.Series,
    deficit_gdp: pd.Series,
    min_gap_months: int = 6
) -> List[Dict]:
    """
    識別勞動市場由緊轉鬆的關鍵事件（失業急升或 JOLTS 急降）

    關鍵洞察：
    - 2018年以前，失業一直高於職缺是「常態」
    - 2018年後首次出現 JOLTS > Unemployed（勞動市場極緊）
    - 重點關注「由緊轉鬆」的事件，這才是會推動赤字擴張的關鍵

    識別方式：
    1. 尋找 UJO（失業/職缺比）急升的時期
    2. 關注失業急升、職缺急降的「剪刀差」時期
    3. 關聯這些時期的赤字變化

    Parameters
    ----------
    unemploy : pd.Series
        失業人數（千人）
    jolts : pd.Series
        職缺數（千人）
    deficit_gdp : pd.Series
        財政赤字/GDP（%）
    min_gap_months : int
        事件間最小間隔月數

    Returns
    -------
    list
        事件列表，包含日期、指標數值、赤字跳升幅度
    """
    # 對齊數據到月頻
    df = pd.DataFrame({
        'unemploy': unemploy,
        'jolts': jolts,
        'deficit': deficit_gdp
    }).resample('ME').last()

    # 只分析有完整勞動數據的時間段
    df = df.dropna(subset=['unemploy', 'jolts'])

    # 前向填充年度赤字數據
    df['deficit'] = df['deficit'].ffill()
    df = df.dropna()

    # 計算 UJO 比率
    df['ujo'] = df['unemploy'] / df['jolts']

    # 計算 UJO 的 6 個月變化
    df['ujo_change_6m'] = df['ujo'].diff(6)

    # 計算失業的 6 個月變化百分比
    df['unemploy_pct_change_6m'] = df['unemploy'].pct_change(6) * 100

    # 預定義的重大勞動市場惡化事件（基於經濟衰退）
    # 這些是已知的會導致赤字大幅擴張的時期
    known_crisis_periods = [
        {
            'name': '2001 Dot-com Recession',
            'start': '2001-03-01',
            'end': '2003-06-30',
            'description': 'Dot-com bubble burst, unemployment rose from 4% to 6.3%'
        },
        {
            'name': '2008 Financial Crisis',
            'start': '2008-01-01',
            'end': '2010-12-31',
            'description': 'Global financial crisis, unemployment spike from 5% to 10%'
        },
        {
            'name': '2020 COVID Crisis',
            'start': '2020-02-01',
            'end': '2020-12-31',
            'description': 'COVID-19 pandemic, unemployment spike from 3.5% to 14.7%'
        },
    ]

    events = []

    for crisis in known_crisis_periods:
        start_dt = pd.to_datetime(crisis['start'])
        end_dt = pd.to_datetime(crisis['end'])

        # 確保在數據範圍內
        if start_dt < df.index.min() or end_dt > df.index.max():
            continue

        # 取事件期間的數據
        mask = (df.index >= start_dt) & (df.index <= end_dt)
        period_data = df.loc[mask]

        if len(period_data) < 3:
            continue

        # 取事件開始前的赤字（前一年的最後一個值）
        pre_mask = df.index < start_dt
        if pre_mask.any():
            deficit_before = df.loc[pre_mask, 'deficit'].iloc[-1]
        else:
            deficit_before = period_data['deficit'].iloc[0]

        # 找出期間內赤字的峰值（最負 = 最大赤字）
        deficit_peak = period_data['deficit'].min()

        # 計算赤字跳升
        deficit_jump = abs(deficit_peak) - abs(deficit_before)

        # 取事件期間的失業和職缺變化
        unemploy_start = period_data['unemploy'].iloc[0]
        unemploy_peak = period_data['unemploy'].max()
        jolts_start = period_data['jolts'].iloc[0]
        jolts_trough = period_data['jolts'].min()

        events.append({
            'name': crisis['name'],
            'start_date': period_data.index[0],
            'end_date': period_data.index[-1],
            'duration_months': len(period_data),
            'deficit_at_start': abs(deficit_before),
            'deficit_peak': abs(deficit_peak),
            'deficit_jump_bps': int(deficit_jump * 100),
            'unemploy_at_start': unemploy_start,
            'unemploy_peak': unemploy_peak,
            'jolts_at_start': jolts_start,
            'jolts_trough': jolts_trough,
            'description': crisis['description'],
        })

    return events


def generate_scenario_projection(
    current_data: pd.DataFrame,
    scenario_type: str = 'moderate',
    horizon_months: int = 36
) -> Dict[str, pd.Series]:
    """
    生成多階段動態情境模擬

    歷史規律顯示勞動市場惡化與財政赤字擴張存在時間差：
    - Phase 1（0-12M）：勞動市場轉弱，GDP 仍正成長，赤字小幅上升
    - Phase 2（12-24M）：GDP 成長放緩/轉負，赤字加速上升
    - Phase 3（24-36M）：赤字達峰值，勞動市場開始修復

    歷史參數參考：
    - 2001 Dot-com: 失業 +58%，職缺 -35%，赤字 +400 bps
    - 2008 GFC: 失業 +100%，職缺 -55%，赤字 +864 bps
    - 2020 COVID: 失業 +300%（短暫），職缺 -30%，赤字 +1000 bps

    Parameters
    ----------
    current_data : pd.DataFrame
        當前數據
    scenario_type : str
        情境類型：'mild', 'moderate', 'severe'
    horizon_months : int
        投影月數（建議 36 個月以完整模擬週期）

    Returns
    -------
    dict
        包含各序列的投影數據及階段資訊
    """
    # 取各序列最新有效數據點
    unemploy_series = current_data['UNEMPLOY'].dropna()
    jolts_series = current_data['JTSJOL'].dropna()
    deficit_series = current_data['FYFSGDA188S'].dropna()

    unemploy_start = unemploy_series.iloc[-1]
    jolts_start = jolts_series.iloc[-1]
    deficit_start = deficit_series.iloc[-1]

    latest_date = max(unemploy_series.index.max(), jolts_series.index.max())

    # 多階段情境參數（基於歷史數據分析）
    # GDP 成長率參考歷史：
    # - 2001 Dot-com: GDP 從 +4% 降至 -1%, 後回升至 +2%
    # - 2008 GFC: GDP 從 +2% 降至 -8%, 後回升至 +4%
    # - 2020 COVID: GDP 從 +2% 降至 -31%, 後回升至 +33%
    scenarios = {
        'mild': {
            # Phase 1: 勞動轉弱，GDP 仍正但放緩，赤字微升
            'phase1_months': 12,
            'phase1_unemploy_mult': 1.15,     # 失業 +15%
            'phase1_jolts_mult': 0.90,        # 職缺 -10%
            'phase1_deficit_jump': 1.0,       # 赤字 +100 bps
            'phase1_gdp_target': 1.5,         # GDP 從當前降至 +1.5%
            # Phase 2: GDP 接近零或小負，赤字加速
            'phase2_months': 12,
            'phase2_unemploy_mult': 1.30,     # 失業累計 +30%
            'phase2_jolts_mult': 0.80,        # 職缺累計 -20%
            'phase2_deficit_jump': 4.0,       # 赤字累計 +400 bps
            'phase2_gdp_target': -0.5,        # GDP 降至 -0.5%
            # Phase 3: 復甦階段
            'phase3_months': 12,
            'phase3_unemploy_mult': 1.20,     # 失業回落至 +20%
            'phase3_jolts_mult': 0.85,        # 職缺回升至 -15%
            'phase3_deficit_jump': 3.5,       # 赤字回落至 +350 bps
            'phase3_gdp_target': 2.5,         # GDP 回升至 +2.5%
            'description': '軟著陸情境：類似 2001 Dot-com 溫和衰退',
        },
        'moderate': {
            # Phase 1: 勞動轉弱，GDP 仍正但明顯放緩，赤字微升
            'phase1_months': 10,
            'phase1_unemploy_mult': 1.25,     # 失業 +25%
            'phase1_jolts_mult': 0.85,        # 職缺 -15%
            'phase1_deficit_jump': 1.5,       # 赤字 +150 bps
            'phase1_gdp_target': 1.0,         # GDP 從當前降至 +1.0%
            # Phase 2: GDP 轉負，赤字加速
            'phase2_months': 14,
            'phase2_unemploy_mult': 1.60,     # 失業累計 +60%
            'phase2_jolts_mult': 0.65,        # 職缺累計 -35%
            'phase2_deficit_jump': 6.0,       # 赤字累計 +600 bps
            'phase2_gdp_target': -3.0,        # GDP 降至 -3.0%（衰退谷底）
            # Phase 3: 緩慢復甦
            'phase3_months': 12,
            'phase3_unemploy_mult': 1.40,     # 失業回落至 +40%
            'phase3_jolts_mult': 0.75,        # 職缺回升至 -25%
            'phase3_deficit_jump': 5.0,       # 赤字回落至 +500 bps
            'phase3_gdp_target': 3.0,         # GDP 回升至 +3.0%
            'description': '典型衰退情境：類似 2008 GFC 前半段',
        },
        'severe': {
            # Phase 1: 勞動快速惡化，GDP 急降
            'phase1_months': 6,
            'phase1_unemploy_mult': 1.40,     # 失業 +40%
            'phase1_jolts_mult': 0.75,        # 職缺 -25%
            'phase1_deficit_jump': 2.0,       # 赤字 +200 bps
            'phase1_gdp_target': 0.0,         # GDP 急降至 0%
            # Phase 2: 危機深化，GDP 大幅負成長
            'phase2_months': 18,
            'phase2_unemploy_mult': 2.00,     # 失業累計 +100%
            'phase2_jolts_mult': 0.50,        # 職缺累計 -50%
            'phase2_deficit_jump': 10.0,      # 赤字累計 +1000 bps
            'phase2_gdp_target': -6.0,        # GDP 降至 -6.0%（深度衰退）
            # Phase 3: 政策介入後修復
            'phase3_months': 12,
            'phase3_unemploy_mult': 1.60,     # 失業回落至 +60%
            'phase3_jolts_mult': 0.65,        # 職缺回升至 -35%
            'phase3_deficit_jump': 8.0,       # 赤字回落至 +800 bps
            'phase3_gdp_target': 4.0,         # GDP 強勁反彈至 +4.0%
            'description': '深度衰退情境：類似 2008 GFC 完整週期',
        }
    }

    params = scenarios.get(scenario_type, scenarios['moderate'])

    # 計算各階段的月數
    p1_months = params['phase1_months']
    p2_months = params['phase2_months']
    p3_months = params['phase3_months']
    total_months = min(horizon_months, p1_months + p2_months + p3_months)

    # 生成日期序列
    future_dates = pd.date_range(
        start=latest_date + timedelta(days=30),
        periods=total_months,
        freq='ME'
    )

    # 取 GDP 成長率起始值（如果有的話）
    gdp_growth_start = None
    if 'A191RL1Q225SBEA' in current_data.columns:
        gdp_series = current_data['A191RL1Q225SBEA'].dropna()
        if len(gdp_series) > 0:
            gdp_growth_start = gdp_series.iloc[-1]

    # 初始化投影數組
    unemploy_proj = np.zeros(total_months)
    jolts_proj = np.zeros(total_months)
    deficit_proj = np.zeros(total_months)
    gdp_proj = np.zeros(total_months) if gdp_growth_start is not None else None

    # Phase 1: 勞動轉弱，GDP 放緩，赤字微升
    for i in range(min(p1_months, total_months)):
        progress = (i + 1) / p1_months
        # 使用平滑的 S 曲線
        s = 1 / (1 + np.exp(-8 * (progress - 0.5)))

        unemploy_proj[i] = unemploy_start * (1 + (params['phase1_unemploy_mult'] - 1) * s)
        jolts_proj[i] = jolts_start * (1 - (1 - params['phase1_jolts_mult']) * s)
        deficit_proj[i] = deficit_start - params['phase1_deficit_jump'] * s

        # GDP 成長率投影
        if gdp_proj is not None and gdp_growth_start is not None:
            gdp_proj[i] = gdp_growth_start + (params['phase1_gdp_target'] - gdp_growth_start) * s

    # Phase 2: GDP 轉負，赤字加速
    p2_start = p1_months
    p2_end = min(p1_months + p2_months, total_months)

    if p2_start < total_months:
        # 繼承 Phase 1 終點
        unemploy_p1_end = unemploy_start * params['phase1_unemploy_mult']
        jolts_p1_end = jolts_start * params['phase1_jolts_mult']
        deficit_p1_end = deficit_start - params['phase1_deficit_jump']
        gdp_p1_end = params['phase1_gdp_target']

        unemploy_p2_target = unemploy_start * params['phase2_unemploy_mult']
        jolts_p2_target = jolts_start * params['phase2_jolts_mult']
        deficit_p2_target = deficit_start - params['phase2_deficit_jump']
        gdp_p2_target = params['phase2_gdp_target']

        for i in range(p2_start, p2_end):
            progress = (i - p2_start + 1) / p2_months
            # Phase 2 使用更陡的曲線（加速惡化）
            s = 1 / (1 + np.exp(-10 * (progress - 0.4)))

            unemploy_proj[i] = unemploy_p1_end + (unemploy_p2_target - unemploy_p1_end) * s
            jolts_proj[i] = jolts_p1_end + (jolts_p2_target - jolts_p1_end) * s
            deficit_proj[i] = deficit_p1_end + (deficit_p2_target - deficit_p1_end) * s

            # GDP 成長率投影（Phase 2 降至谷底）
            if gdp_proj is not None:
                gdp_proj[i] = gdp_p1_end + (gdp_p2_target - gdp_p1_end) * s

    # Phase 3: 修復階段，GDP 反彈
    p3_start = p1_months + p2_months
    p3_end = min(p3_start + p3_months, total_months)

    if p3_start < total_months:
        # 繼承 Phase 2 終點
        unemploy_p2_end = unemploy_start * params['phase2_unemploy_mult']
        jolts_p2_end = jolts_start * params['phase2_jolts_mult']
        deficit_p2_end = deficit_start - params['phase2_deficit_jump']
        gdp_p2_end = params['phase2_gdp_target']

        unemploy_p3_target = unemploy_start * params['phase3_unemploy_mult']
        jolts_p3_target = jolts_start * params['phase3_jolts_mult']
        deficit_p3_target = deficit_start - params['phase3_deficit_jump']
        gdp_p3_target = params['phase3_gdp_target']

        for i in range(p3_start, p3_end):
            progress = (i - p3_start + 1) / p3_months
            # Phase 3 使用較平緩曲線（緩慢修復）
            s = 1 / (1 + np.exp(-6 * (progress - 0.5)))

            unemploy_proj[i] = unemploy_p2_end + (unemploy_p3_target - unemploy_p2_end) * s
            jolts_proj[i] = jolts_p2_end + (jolts_p3_target - jolts_p2_end) * s
            deficit_proj[i] = deficit_p2_end + (deficit_p3_target - deficit_p2_end) * s

            # GDP 成長率投影（Phase 3 反彈復甦）
            if gdp_proj is not None:
                gdp_proj[i] = gdp_p2_end + (gdp_p3_target - gdp_p2_end) * s

    # 記錄參數供後續使用
    params['unemploy_start'] = float(unemploy_start)
    params['jolts_start'] = float(jolts_start)
    params['deficit_start'] = float(abs(deficit_start))
    params['unemploy_peak'] = float(unemploy_start * params['phase2_unemploy_mult'])
    params['jolts_trough'] = float(jolts_start * params['phase2_jolts_mult'])
    params['deficit_peak'] = float(abs(deficit_start - params['phase2_deficit_jump']))
    params['total_deficit_jump_pct'] = params['phase2_deficit_jump']

    # GDP 相關參數
    if gdp_growth_start is not None:
        params['gdp_start'] = float(gdp_growth_start)
        params['gdp_trough'] = float(params['phase2_gdp_target'])
        params['gdp_recovery'] = float(params['phase3_gdp_target'])

    # 階段標記（用於圖表標註）
    phase_boundaries = {
        'phase1_end_idx': min(p1_months - 1, total_months - 1),
        'phase2_end_idx': min(p1_months + p2_months - 1, total_months - 1),
        'phase1_label': f'Phase 1: Labor weakening\n(Deficit +{params["phase1_deficit_jump"]*100:.0f} bps)',
        'phase2_label': f'Phase 2: GDP slows, Deficit spikes\n(Deficit +{params["phase2_deficit_jump"]*100:.0f} bps)',
        'phase3_label': f'Phase 3: Recovery\n(Deficit +{params["phase3_deficit_jump"]*100:.0f} bps)',
    }

    result = {
        'dates': future_dates,
        'unemploy': pd.Series(unemploy_proj, index=future_dates),
        'jolts': pd.Series(jolts_proj, index=future_dates),
        'deficit': pd.Series(deficit_proj, index=future_dates),
        'scenario_type': scenario_type,
        'params': params,
        'start_date': latest_date,
        'phase_boundaries': phase_boundaries,
        'phases': {
            'phase1': {'months': p1_months, 'description': 'Labor market weakening, GDP slowing'},
            'phase2': {'months': p2_months, 'description': 'GDP negative, deficit accelerates'},
            'phase3': {'months': p3_months, 'description': 'Recovery begins, GDP rebounds'},
        }
    }

    # 加入 GDP 投影（如果有）
    if gdp_proj is not None:
        result['gdp_growth'] = pd.Series(gdp_proj, index=future_dates)

    return result


def project_deficit_with_elasticity(
    current_deficit: float,
    current_ur: float,
    current_ujo: float,
    target_ur: float,
    target_ujo: float,
    lag_adjust: bool = True
) -> Dict[str, float]:
    """
    使用彈性係數推演財政赤字

    基於歷史回歸分析的彈性係數：
    - β_UR = 0.59: 失業率每↑1ppt → 赤字/GDP↑0.59ppt
    - β_UJO = 0.69: UJO每↑1 → 赤字/GDP↑0.69ppt
    - 滯後期約 4 季

    Parameters
    ----------
    current_deficit : float
        當前赤字/GDP (%)
    current_ur : float
        當前失業率 (%)
    current_ujo : float
        當前 UJO 比率
    target_ur : float
        目標失業率 (%)
    target_ujo : float
        目標 UJO 比率
    lag_adjust : bool
        是否考慮滯後效應（預設 True）

    Returns
    -------
    dict
        包含推演結果和彈性分解
    """
    delta_ur = target_ur - current_ur
    delta_ujo = target_ujo - current_ujo

    # 彈性驅動的赤字變化
    deficit_from_ur = ELASTICITY['beta_ur'] * delta_ur
    deficit_from_ujo = ELASTICITY['beta_ujo'] * delta_ujo
    total_delta = deficit_from_ur + deficit_from_ujo

    projected_deficit = current_deficit + total_delta

    return {
        'current_deficit': current_deficit,
        'projected_deficit': projected_deficit,
        'delta_deficit': total_delta,
        'elasticity_decomposition': {
            'from_ur_change': deficit_from_ur,
            'from_ujo_change': deficit_from_ujo,
            'delta_ur': delta_ur,
            'delta_ujo': delta_ujo,
        },
        'elasticity_params': {
            'beta_ur': ELASTICITY['beta_ur'],
            'beta_ujo': ELASTICITY['beta_ujo'],
            'lag_quarters': ELASTICITY['lag_quarters'],
        },
        'notes': f"Based on regression: β_UR={ELASTICITY['beta_ur']}, β_UJO={ELASTICITY['beta_ujo']}, Lag={ELASTICITY['lag_quarters']}Q"
    }


def plot_gromen_style_chart(
    data: pd.DataFrame,
    events: List[Dict],
    scenario: Optional[Dict] = None,
    output_path: Optional[str] = None,
    title: str = None,
    show_annotations: bool = True,
    figsize: Tuple[int, int] = (14, 8)
) -> plt.Figure:
    """
    繪製三軸圖表（職缺/失業/赤字GDP）

    Parameters
    ----------
    data : pd.DataFrame
        歷史數據
    events : list
        crossover 事件列表
    scenario : dict, optional
        情境模擬數據
    output_path : str, optional
        輸出檔案路徑
    title : str, optional
        圖表標題
    show_annotations : bool
        是否顯示標註
    figsize : tuple
        圖表大小

    Returns
    -------
    matplotlib.figure.Figure
        圖表物件
    """
    fig, ax1 = plt.subplots(figsize=figsize, facecolor='white')

    # 準備數據
    unemploy = data['UNEMPLOY'].dropna()
    jolts = data['JTSJOL'].dropna()
    deficit = data['FYFSGDA188S'].dropna()

    # GDP 成長率（如果有）
    gdp_growth = None
    if 'A191RL1Q225SBEA' in data.columns:
        gdp_growth = data['A191RL1Q225SBEA'].dropna()

    # === 第一層：GDP 成長率作為背景（無軸刻度，淡色填充） ===
    if gdp_growth is not None and len(gdp_growth) > 0:
        # 創建隱藏的第三軸用於 GDP 成長率（不顯示刻度）
        ax_gdp = ax1.twinx()
        ax_gdp.spines['right'].set_position(('axes', 1.0))  # 不偏移
        ax_gdp.spines['right'].set_visible(False)  # 隱藏軸線
        ax_gdp.tick_params(right=False, labelright=False)  # 隱藏刻度

        # 繪製 GDP 成長率曲線（作為背景）
        ax_gdp.plot(gdp_growth.index, gdp_growth.values,
                   color=COLORS['gdp_growth'], linewidth=1.5, alpha=0.4,
                   label='Real GDP Growth Rate (background)', zorder=1)

        # 填充 GDP 成長率區域（正負不同顏色）
        ax_gdp.fill_between(gdp_growth.index, 0, gdp_growth.values,
                           where=(gdp_growth.values >= 0),
                           color=COLORS['gdp_growth'], alpha=0.08,
                           interpolate=True, zorder=0)
        ax_gdp.fill_between(gdp_growth.index, 0, gdp_growth.values,
                           where=(gdp_growth.values < 0),
                           color='red', alpha=0.12,
                           interpolate=True, zorder=0)

        # 添加零線
        ax_gdp.axhline(y=0, color=COLORS['gdp_growth'], linestyle='--',
                      linewidth=0.8, alpha=0.5, zorder=1)

        # 設置 GDP 軸範圍（固定範圍避免影響其他線）
        gdp_min = min(gdp_growth.min(), -5)
        gdp_max = max(gdp_growth.max(), 10)
        ax_gdp.set_ylim(gdp_min * 1.2, gdp_max * 1.5)

        # 在圖例區域添加 GDP 標籤（右上角小字）
        ax_gdp.text(0.98, 0.98, f'GDP Growth: {gdp_growth.iloc[-1]:.1f}%',
                   transform=ax_gdp.transAxes,
                   fontsize=9, color=COLORS['gdp_growth'], alpha=0.8,
                   ha='right', va='top',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                            edgecolor=COLORS['gdp_growth'], alpha=0.7))

    # 繪製衰退期陰影
    for start, end in RECESSIONS:
        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end)
        if start_dt >= data.index.min():
            ax1.axvspan(start_dt, end_dt, alpha=0.3, color=COLORS['recession'],
                       label='_nolegend_')

    # 左軸：失業人數和職缺數（千人）
    ax1.set_ylabel('Level in Thousands of Persons', fontsize=11, color='black')
    ax1.set_xlabel('')

    # 繪製職缺數（藍色）
    line_jolts, = ax1.plot(jolts.index, jolts.values,
                           color=COLORS['jolts'], linewidth=2,
                           label='Job Openings: Total Nonfarm (left)')

    # 繪製失業人數（紅色）
    line_unemploy, = ax1.plot(unemploy.index, unemploy.values,
                              color=COLORS['unemploy'], linewidth=2,
                              label='Unemployment Level (left)')

    # 設置左軸範圍（考慮情境投影）
    y1_min = min(jolts.min(), unemploy.min()) * 0.8
    y1_max = max(jolts.max(), unemploy.max()) * 1.1
    if scenario:
        # 擴展範圍以容納投影
        y1_max = max(y1_max, scenario['params']['unemploy_peak'] * 1.15)
        y1_min = min(y1_min, scenario['params']['jolts_trough'] * 0.85)
    ax1.set_ylim(y1_min, y1_max)
    ax1.tick_params(axis='y', labelcolor='black')

    # 右軸：財政赤字/GDP（%）
    ax2 = ax1.twinx()
    ax2.set_ylabel('% of GDP', fontsize=11, color=COLORS['deficit'])

    # 繪製赤字/GDP（綠色，取負值顯示為正赤字）
    deficit_display = -deficit  # 轉為正數顯示赤字
    line_deficit, = ax2.plot(deficit.index, deficit_display.values,
                             color=COLORS['deficit'], linewidth=2,
                             label='-Federal Surplus or Deficit [-] as Percent of GDP (right)')

    # 設置右軸範圍（考慮情境投影，確保底部有足夠空間）
    y2_min = -1  # 確保綠線不被切掉
    y2_max = max(deficit_display.max() * 1.2, 20)
    if scenario:
        y2_max = max(y2_max, scenario['params']['deficit_peak'] * 1.15)
    ax2.set_ylim(y2_min, y2_max)
    ax2.tick_params(axis='y', labelcolor=COLORS['deficit'])

    # 繪製情境模擬（虛線）
    scenario_lines = []
    if scenario:
        proj_dates = scenario['dates']
        start_date = scenario.get('start_date', data.index.max())

        # 創建連接點：從歷史數據最後一個點連接到投影
        connect_dates = pd.DatetimeIndex([start_date, proj_dates[0]])

        # 失業：連接線 + 投影
        unemploy_connect = [scenario['params']['unemploy_start'], scenario['unemploy'].iloc[0]]
        ax1.plot(connect_dates, unemploy_connect,
                color=COLORS['unemploy'], linewidth=2, linestyle='--', alpha=0.7)
        ax1.plot(proj_dates, scenario['unemploy'].values,
                color=COLORS['unemploy'], linewidth=2, linestyle='--', alpha=0.7)

        # 職缺：連接線 + 投影
        jolts_connect = [scenario['params']['jolts_start'], scenario['jolts'].iloc[0]]
        ax1.plot(connect_dates, jolts_connect,
                color=COLORS['jolts'], linewidth=2, linestyle='--', alpha=0.7)
        ax1.plot(proj_dates, scenario['jolts'].values,
                color=COLORS['jolts'], linewidth=2, linestyle='--', alpha=0.7)

        # 赤字投影（連接線 + 投影）
        deficit_proj_display = -scenario['deficit']  # 轉為正數
        deficit_connect = [scenario['params']['deficit_start'], deficit_proj_display.iloc[0]]
        ax2.plot(connect_dates, deficit_connect,
                color=COLORS['deficit'], linewidth=2, linestyle='--', alpha=0.7)
        ax2.plot(proj_dates, deficit_proj_display.values,
                color=COLORS['deficit'], linewidth=2, linestyle='--', alpha=0.7)

        # GDP 成長率投影（如果有）
        if 'gdp_growth' in scenario and 'gdp_start' in scenario['params']:
            gdp_proj_series = scenario['gdp_growth']

            # 連接線
            gdp_connect = [scenario['params']['gdp_start'], gdp_proj_series.iloc[0]]
            ax_gdp.plot(connect_dates, gdp_connect,
                       color=COLORS['gdp_growth'], linewidth=2, linestyle='--', alpha=0.7)
            # 投影線
            ax_gdp.plot(proj_dates, gdp_proj_series.values,
                       color=COLORS['gdp_growth'], linewidth=2, linestyle='--', alpha=0.7)

            # 標註 GDP 投影終點
            ax_gdp.annotate(
                f"GDP: {scenario['params']['gdp_start']:.1f}% → {scenario['params']['gdp_trough']:.1f}% → {scenario['params']['gdp_recovery']:.1f}%",
                xy=(proj_dates[-1], gdp_proj_series.iloc[-1]),
                xytext=(-80, -30),
                textcoords='offset points',
                fontsize=8,
                color=COLORS['gdp_growth'],
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lavender', edgecolor=COLORS['gdp_growth'], alpha=0.8),
                ha='right',
                va='top'
            )

        # 添加階段分隔線和標註
        phase_boundaries = scenario.get('phase_boundaries', {})
        if phase_boundaries:
            # Phase 1/2 分界線
            p1_end_idx = phase_boundaries.get('phase1_end_idx', 0)
            if p1_end_idx < len(proj_dates) - 1:
                p1_end_date = proj_dates[p1_end_idx]
                ax1.axvline(x=p1_end_date, color='purple', linestyle=':', alpha=0.5, linewidth=1.5)
                ax1.annotate(
                    'Phase 1→2\n(GDP slows)',
                    xy=(p1_end_date, y1_max * 0.95),
                    fontsize=7,
                    color='purple',
                    ha='center',
                    va='top',
                    alpha=0.8
                )

            # Phase 2/3 分界線
            p2_end_idx = phase_boundaries.get('phase2_end_idx', 0)
            if p2_end_idx < len(proj_dates) - 1 and p2_end_idx > p1_end_idx:
                p2_end_date = proj_dates[p2_end_idx]
                ax1.axvline(x=p2_end_date, color='green', linestyle=':', alpha=0.5, linewidth=1.5)
                ax1.annotate(
                    'Phase 2→3\n(Recovery)',
                    xy=(p2_end_date, y1_max * 0.95),
                    fontsize=7,
                    color='green',
                    ha='center',
                    va='top',
                    alpha=0.8
                )

        # 標註情境：在投影線峰值位置加標註
        scenario_label = scenario['scenario_type'].upper()
        deficit_jump = scenario['params'].get('total_deficit_jump_pct', scenario['params'].get('deficit_jump_pct', 6.0))

        # 找赤字峰值位置
        peak_idx = deficit_proj_display.idxmax()
        peak_date = peak_idx
        peak_value = deficit_proj_display.loc[peak_idx]

        scenario_text = (
            f"【{scenario_label} Scenario】\n"
            f"Multi-phase dynamics:\n"
            f"Phase 1: Labor weakens, deficit +{scenario['params'].get('phase1_deficit_jump', 1.5)*100:.0f} bps\n"
            f"Phase 2: GDP slows, deficit +{scenario['params'].get('phase2_deficit_jump', 6.0)*100:.0f} bps\n"
            f"→ Peak: {scenario['params']['deficit_start']:.1f}% → {scenario['params']['deficit_peak']:.1f}%"
        )
        ax2.annotate(
            scenario_text,
            xy=(peak_date, peak_value),
            xytext=(20, 30),
            textcoords='offset points',
            fontsize=8,
            color=COLORS['annotation'],
            bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow', edgecolor='orange', alpha=0.9),
            ha='left',
            va='bottom',
            arrowprops=dict(arrowstyle='->', color='orange', alpha=0.7)
        )

        # 在投影終點加標註（勞動市場）
        proj_end = proj_dates[-1]
        ax1.annotate(
            f"JOLTS: {scenario['params']['jolts_start']/1000:.1f}M → {scenario['params']['jolts_trough']/1000:.1f}M",
            xy=(proj_end, scenario['jolts'].iloc[-1]),
            xytext=(15, -15),
            textcoords='offset points',
            fontsize=8,
            color=COLORS['jolts'],
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', edgecolor='blue', alpha=0.8),
            ha='left',
            va='top'
        )

        ax1.annotate(
            f"Unemployed: {scenario['params']['unemploy_start']/1000:.1f}M → {scenario['params']['unemploy_peak']/1000:.1f}M",
            xy=(proj_end, scenario['unemploy'].iloc[-1]),
            xytext=(15, 15),
            textcoords='offset points',
            fontsize=8,
            color=COLORS['unemploy'],
            bbox=dict(boxstyle='round,pad=0.3', facecolor='mistyrose', edgecolor='red', alpha=0.8),
            ha='left',
            va='bottom'
        )

    # 標註歷史事件
    if show_annotations and events:
        for i, event in enumerate(events[-3:]):  # 只標註最近 3 個事件
            event_date = event['start_date']
            deficit_jump = event['deficit_jump_bps']
            event_name = event.get('name', f"{event_date.year} Event")

            # 標註位置（在事件中間）
            mid_date = event_date + (event['end_date'] - event_date) / 2

            # 找對應的 y 值（使用失業峰值）
            y_pos = event.get('unemploy_peak', unemploy.max())

            annotation_text = (
                f"【{event_name}】\n"
                f"Deficit/GDP:\n"
                f"{event['deficit_at_start']:.1f}% → {event['deficit_peak']:.1f}%\n"
                f"(+{deficit_jump} bps)"
            )

            # 交錯標註位置避免重疊
            offset_y = 50 if i % 2 == 0 else -80

            ax1.annotate(
                annotation_text,
                xy=(mid_date, y_pos),
                xytext=(0, offset_y),
                textcoords='offset points',
                fontsize=8,
                color=COLORS['annotation'],
                ha='center',
                va='bottom' if offset_y > 0 else 'top',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=0.9),
                arrowprops=dict(arrowstyle='->', color='gray', alpha=0.5)
            )

    # 設置 x 軸格式
    ax1.xaxis.set_major_locator(mdates.YearLocator(5))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax1.xaxis.set_minor_locator(mdates.YearLocator(1))

    # 設置標題
    if title is None:
        if scenario:
            scenario_label = scenario['scenario_type'].capitalize()
            title = f'Job Openings, Unemployment & Federal Deficit/GDP\n({scenario_label} Scenario Projection)'
        else:
            title = 'Job Openings, Unemployment & Federal Deficit/GDP'
    ax1.set_title(title, fontsize=14, fontweight='bold', pad=20)

    # 圖例
    legend_elements = [
        Line2D([0], [0], color=COLORS['jolts'], linewidth=2, label='Job Openings: Total Nonfarm (left)'),
        Line2D([0], [0], color=COLORS['unemploy'], linewidth=2, label='Unemployment Level (left)'),
        Line2D([0], [0], color=COLORS['deficit'], linewidth=2, label='-Federal Surplus or Deficit as % of GDP (right)'),
        Line2D([0], [0], color=COLORS['gdp_growth'], linewidth=1.5, alpha=0.5, label='Real GDP Growth Rate (background)'),
    ]
    if scenario:
        legend_elements.append(
            Line2D([0], [0], color='gray', linewidth=2, linestyle='--', label='Scenario Projection')
        )

    ax1.legend(handles=legend_elements, loc='upper left', fontsize=8, framealpha=0.9)

    # 添加資料來源
    fig.text(0.12, 0.02,
             'Sources: Federal Reserve Bank of St. Louis; U.S. Bureau of Labor Statistics; U.S. Office of Management and Budget\n'
             'Shaded areas indicate U.S. recessions.',
             fontsize=8, color='gray', ha='left')

    # 添加浮水印
    fig.text(0.88, 0.02, f'Generated: {datetime.now().strftime("%Y-%m-%d")}',
             fontsize=8, color='gray', ha='right')

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.1)

    # 儲存圖表
    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        print(f"圖表已保存至: {output_path}")

    return fig


def generate_summary_stats(
    data: pd.DataFrame,
    events: List[Dict],
    scenario: Optional[Dict] = None
) -> Dict:
    """生成摘要統計（含彈性分析）"""
    # 取各序列最新有效值
    unemploy_series = data['UNEMPLOY'].dropna()
    jolts_series = data['JTSJOL'].dropna()
    deficit_series = data['FYFSGDA188S'].dropna()
    ur_series = data['UNRATE'].dropna() if 'UNRATE' in data else None

    current_unemploy = unemploy_series.iloc[-1]
    current_jolts = jolts_series.iloc[-1]
    current_deficit = abs(deficit_series.iloc[-1])
    current_ur = ur_series.iloc[-1] if ur_series is not None and len(ur_series) > 0 else None
    current_ujo = current_unemploy / current_jolts

    # 是否處於 crossover（勞動市場轉弱信號）
    is_crossover = current_unemploy > current_jolts

    # 歷史事件統計
    if events:
        avg_jump = np.mean([e['deficit_jump_bps'] for e in events])
        max_jump = max(e['deficit_jump_bps'] for e in events)
    else:
        avg_jump = 0
        max_jump = 0

    summary = {
        'as_of': max(unemploy_series.index.max(), jolts_series.index.max()).strftime('%Y-%m-%d'),
        'current_state': {
            'unemployment_level_thousands': float(current_unemploy),
            'job_openings_thousands': float(current_jolts),
            'unemployment_rate_pct': float(current_ur) if current_ur is not None else None,
            'ujo_ratio': float(current_ujo),
            'deficit_gdp_pct': float(current_deficit),
            'is_crossover': bool(is_crossover),
            'labor_market_status': 'Tight (JOLTS > Unemployed)' if not is_crossover else 'Loosening (Unemployed > JOLTS)',
        },
        'elasticity_model': {
            'parameters': {
                'beta_ur': ELASTICITY['beta_ur'],
                'beta_ujo': ELASTICITY['beta_ujo'],
                'beta_jolts': ELASTICITY['beta_jolts'],
                'lag_quarters': ELASTICITY['lag_quarters'],
            },
            'interpretation': {
                'ur_effect': f"每 1ppt 失業率上升 → 赤字/GDP 上升 {ELASTICITY['beta_ur']} ppt",
                'ujo_effect': f"UJO 每上升 1 → 赤字/GDP 上升 {ELASTICITY['beta_ujo']} ppt",
                'lag_effect': f"勞動指標領先赤字約 {ELASTICITY['lag_quarters']} 季",
            },
            'conditional_means': {
                'deficit_when_loose': ELASTICITY['deficit_mean_loose'],
                'deficit_when_tight': ELASTICITY['deficit_mean_tight'],
            },
        },
        'historical_events': {
            'count': len(events),
            'avg_deficit_jump_bps': float(avg_jump),
            'max_deficit_jump_bps': float(max_jump),
            'key_insight': 'Historical crises show deficit/GDP jumps 600-1000+ bps when unemployment spikes',
            'events': [
                {
                    'name': e.get('name', 'Unknown'),
                    'period': f"{e['start_date'].strftime('%Y-%m')} to {e['end_date'].strftime('%Y-%m')}",
                    'deficit_change': f"{e['deficit_at_start']:.1f}% → {e['deficit_peak']:.1f}%",
                    'deficit_jump_bps': e['deficit_jump_bps'],
                    'description': e.get('description', ''),
                }
                for e in events
            ]
        }
    }

    if scenario:
        deficit_jump = scenario['params'].get('total_deficit_jump_pct', scenario['params'].get('phase2_deficit_jump', 6.0))
        summary['scenario_projection'] = {
            'type': scenario['scenario_type'],
            'current_deficit_pct': scenario['params']['deficit_start'],
            'projected_deficit_pct': scenario['params']['deficit_peak'],
            'projected_deficit_jump_pct': deficit_jump,
            'projected_deficit_jump_bps': int(deficit_jump * 100),
            'horizon_months': len(scenario['dates']),
            'unemploy_projection': f"{scenario['params']['unemploy_start']/1000:.1f}M → {scenario['params']['unemploy_peak']/1000:.1f}M",
            'jolts_projection': f"{scenario['params']['jolts_start']/1000:.1f}M → {scenario['params']['jolts_trough']/1000:.1f}M",
            'phases': scenario.get('phases', {}),
        }

    return summary


def main():
    parser = argparse.ArgumentParser(
        description='財政赤字情境視覺化工具（三軸圖表）'
    )
    parser.add_argument(
        '--years',
        type=int,
        default=25,
        help='回看年數 (預設: 25)'
    )
    parser.add_argument(
        '--scenario',
        type=str,
        choices=['mild', 'moderate', 'severe', 'none'],
        default='moderate',
        help='情境類型 (預設: moderate)'
    )
    parser.add_argument(
        '--horizon',
        type=int,
        default=24,
        help='情境投影月數 (預設: 24)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='輸出圖表檔案路徑'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='輸出目錄（自動生成檔名）'
    )
    parser.add_argument(
        '--no-annotations',
        action='store_true',
        help='不顯示標註'
    )
    parser.add_argument(
        '--json',
        type=str,
        default=None,
        help='輸出 JSON 摘要檔案路徑'
    )

    args = parser.parse_args()

    # 抓取數據
    print("正在抓取數據...")
    data = fetch_visualization_data(years=args.years)

    # 識別 crossover 事件
    print("識別歷史事件...")
    events = identify_crossover_events(
        data['UNEMPLOY'],
        data['JTSJOL'],
        data['FYFSGDA188S']
    )
    print(f"  找到 {len(events)} 個 crossover 事件")

    # 生成情境投影
    scenario = None
    if args.scenario != 'none':
        print(f"生成 {args.scenario} 情境投影...")
        scenario = generate_scenario_projection(
            data,
            scenario_type=args.scenario,
            horizon_months=args.horizon
        )

    # 決定輸出路徑
    if args.output:
        output_path = args.output
    elif args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = str(output_dir / f'fiscal_deficit_scenario_{timestamp}.png')
    else:
        output_dir = Path(__file__).parent.parent / 'output'
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = str(output_dir / f'fiscal_deficit_scenario_{timestamp}.png')

    # 繪製圖表
    print("繪製圖表...")
    fig = plot_gromen_style_chart(
        data,
        events,
        scenario=scenario,
        output_path=output_path,
        show_annotations=not args.no_annotations
    )

    # 生成摘要統計
    summary = generate_summary_stats(data, events, scenario)

    # 輸出 JSON
    if args.json:
        json_path = args.json
    else:
        json_path = output_path.replace('.png', '.json')

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"摘要已保存至: {json_path}")

    # 顯示摘要
    print("\n" + "=" * 60)
    print("分析摘要")
    print("=" * 60)
    print(f"數據截至: {summary['as_of']}")
    print(f"\n當前狀態:")
    print(f"  失業人數: {summary['current_state']['unemployment_level_thousands']:,.0f} 千人")
    print(f"  職缺數: {summary['current_state']['job_openings_thousands']:,.0f} 千人")
    print(f"  UJO 比率: {summary['current_state']['ujo_ratio']:.2f}")
    print(f"  赤字/GDP: {summary['current_state']['deficit_gdp_pct']:.1f}%")
    print(f"  失業 > 職缺: {'是' if summary['current_state']['is_crossover'] else '否'}")

    print(f"\n歷史事件 (失業 > 職缺):")
    print(f"  事件數: {summary['historical_events']['count']}")
    print(f"  平均赤字跳升: {summary['historical_events']['avg_deficit_jump_bps']:.0f} bps")
    print(f"  最大赤字跳升: {summary['historical_events']['max_deficit_jump_bps']:.0f} bps")

    if scenario:
        print(f"\n情境投影 ({summary['scenario_projection']['type']}):")
        print(f"  預期赤字跳升: {summary['scenario_projection']['projected_deficit_jump_bps']} bps")

    plt.show()


if __name__ == "__main__":
    main()
