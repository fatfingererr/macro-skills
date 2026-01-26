#!/usr/bin/env python3
"""
聯準會未攤銷折價走勢模式偵測器

主分析腳本：形狀比對 + 交叉驗證
"""

import argparse
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, skew
from scipy.signal import find_peaks

# 嘗試導入 DTW（可選）
try:
    from scipy.spatial.distance import euclidean
    from fastdtw import fastdtw
    HAS_DTW = True
except ImportError:
    HAS_DTW = False
    print("[Warning] fastdtw 未安裝，將使用簡化的 DTW 計算")

from fetch_data import fetch_fred_series, fetch_yield_curve, fetch_all_indicators

# ============================================================================
# 資料結構
# ============================================================================

@dataclass
class BaselineWindow:
    """歷史基準窗口"""
    name: str
    start: str
    end: str
    context: str = ""


@dataclass
class ConfirmatoryIndicator:
    """交叉驗證指標"""
    name: str
    source: str
    series: str
    weight: float = 1.0
    stress_threshold: float = 1.5


@dataclass
class Config:
    """分析配置"""
    target_series: str = "WUDSHO"
    baseline_windows: List[BaselineWindow] = field(default_factory=list)
    recent_window_days: int = 120
    resample_freq: str = "W"
    normalize_method: str = "zscore"
    similarity_metrics: List[str] = field(default_factory=lambda: ["corr", "dtw", "shape_features"])
    similarity_weights: Dict[str, float] = field(default_factory=lambda: {"corr": 0.4, "dtw": 0.3, "shape_features": 0.3})
    confirmatory_indicators: List[ConfirmatoryIndicator] = field(default_factory=list)
    lookahead_days: int = 60
    history_start: str = "2015-01-01"


# 預設配置
DEFAULT_BASELINE_WINDOWS = [
    BaselineWindow("COVID_2020", "2020-01-01", "2020-06-30", "COVID-19 疫情初期市場恐慌"),
    BaselineWindow("GFC_2008", "2008-09-01", "2009-03-31", "全球金融危機"),
    BaselineWindow("TAPER_2013", "2013-05-01", "2013-09-30", "縮減恐慌"),
    BaselineWindow("RATE_HIKE_2022", "2022-01-01", "2022-12-31", "激進升息週期"),
]

DEFAULT_CONFIRMATORY_INDICATORS = [
    ConfirmatoryIndicator("credit_spread", "FRED", "BAMLC0A0CM", 0.25, 1.5),
    ConfirmatoryIndicator("hy_spread", "FRED", "BAMLH0A0HYM2", 0.20, 1.5),
    ConfirmatoryIndicator("equity_vol", "FRED", "VIXCLS", 0.20, 1.5),
    ConfirmatoryIndicator("yield_curve", "FRED", "yield_curve", 0.15, -1.0),
    ConfirmatoryIndicator("fed_balance", "FRED", "WALCL", 0.20, 1.0),
]


# ============================================================================
# 正規化函數
# ============================================================================

def zscore_normalize(series: pd.Series) -> pd.Series:
    """Z-Score 正規化"""
    std = series.std()
    if std == 0 or np.isnan(std):
        return series - series.mean()
    return (series - series.mean()) / std


def minmax_normalize(series: pd.Series) -> pd.Series:
    """Min-Max 正規化"""
    range_val = series.max() - series.min()
    if range_val == 0:
        return pd.Series(0.5, index=series.index)
    return (series - series.min()) / range_val


def pct_change_normalize(series: pd.Series) -> pd.Series:
    """百分比變化正規化"""
    return series.pct_change().fillna(0)


def normalize(series: pd.Series, method: str = "zscore") -> pd.Series:
    """統一正規化介面"""
    if method == "zscore":
        return zscore_normalize(series)
    elif method == "minmax":
        return minmax_normalize(series)
    elif method == "pct_change":
        return pct_change_normalize(series)
    else:
        return zscore_normalize(series)


# ============================================================================
# 相似度計算
# ============================================================================

def pearson_correlation(a: np.ndarray, b: np.ndarray) -> float:
    """計算皮爾遜相關係數"""
    if len(a) != len(b) or len(a) < 3:
        return 0.0
    try:
        corr, _ = pearsonr(a, b)
        return float(corr) if not np.isnan(corr) else 0.0
    except Exception:
        return 0.0


def dtw_distance(a: np.ndarray, b: np.ndarray) -> float:
    """計算 DTW 距離（正規化）"""
    if HAS_DTW:
        try:
            distance, _ = fastdtw(a, b, dist=euclidean)
            return distance / max(len(a), len(b))
        except Exception:
            pass

    # 簡化版本：使用歐氏距離
    if len(a) != len(b):
        # 線性插值對齊
        from scipy.interpolate import interp1d
        x_a = np.linspace(0, 1, len(a))
        x_b = np.linspace(0, 1, len(b))
        f = interp1d(x_b, b, kind='linear')
        b = f(x_a)

    return float(np.sqrt(np.mean((a - b) ** 2)))


def extract_shape_features(series: np.ndarray) -> Dict[str, float]:
    """提取形狀特徵"""
    n = len(series)
    if n < 5:
        return {"slope": 0, "volatility": 0, "skewness": 0, "n_peaks": 0, "n_troughs": 0, "start_to_end": 0}

    x = np.arange(n)

    # 趨勢斜率
    try:
        slope, _ = np.polyfit(x, series, 1)
    except Exception:
        slope = 0

    # 波動度
    volatility = float(np.std(series))

    # 偏度
    try:
        skewness = float(skew(series))
    except Exception:
        skewness = 0

    # 峰谷數量
    try:
        peaks, _ = find_peaks(series)
        troughs, _ = find_peaks(-series)
        n_peaks = len(peaks)
        n_troughs = len(troughs)
    except Exception:
        n_peaks = 0
        n_troughs = 0

    # 首尾變化率
    start_to_end = (series[-1] - series[0]) / (abs(series[0]) + 1e-8)

    return {
        "slope": float(slope),
        "volatility": volatility,
        "skewness": skewness,
        "n_peaks": n_peaks,
        "n_troughs": n_troughs,
        "start_to_end": float(start_to_end)
    }


def feature_similarity(feat_a: Dict, feat_b: Dict) -> float:
    """計算特徵向量的餘弦相似度"""
    keys = list(feat_a.keys())
    vec_a = np.array([feat_a[k] for k in keys], dtype=float)
    vec_b = np.array([feat_b[k] for k in keys], dtype=float)

    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)

    if norm_a < 1e-8 or norm_b < 1e-8:
        return 0.0

    vec_a = vec_a / norm_a
    vec_b = vec_b / norm_b

    return float(np.clip(np.dot(vec_a, vec_b), 0, 1))


def combine_similarity(
    corr: float,
    dtw_dist: float,
    feature_sim: float,
    weights: Dict[str, float]
) -> float:
    """合成綜合相似度分數"""
    # 轉換至 [0, 1] 範圍
    corr_score = (corr + 1) / 2  # [-1, 1] -> [0, 1]
    dtw_score = max(0, 1 - dtw_dist / 2)  # 假設 dtw > 2 為不相似
    feat_score = max(0, feature_sim)

    w_corr = weights.get("corr", 0.4)
    w_dtw = weights.get("dtw", 0.3)
    w_feat = weights.get("shape_features", 0.3)

    total_weight = w_corr + w_dtw + w_feat
    if total_weight == 0:
        return 0.0

    return (w_corr * corr_score + w_dtw * dtw_score + w_feat * feat_score) / total_weight


# ============================================================================
# 窗口比對
# ============================================================================

def rolling_segments(series: pd.Series, length: int, step: int = 1):
    """產生滾動片段"""
    for i in range(0, len(series) - length + 1, step):
        yield series.iloc[i:i+length]


def find_best_match(
    recent: pd.Series,
    baseline_series: pd.Series,
    normalize_method: str,
    similarity_weights: Dict[str, float]
) -> Dict:
    """在基準窗口中找出最佳匹配片段"""
    recent_n = normalize(recent, normalize_method)
    recent_vals = recent_n.values

    best_score = -1
    best_result = None

    for segment in rolling_segments(baseline_series, len(recent)):
        segment_n = normalize(segment, normalize_method)
        segment_vals = segment_n.values

        # 計算相似度
        corr = pearson_correlation(recent_vals, segment_vals)
        dtw_dist = dtw_distance(recent_vals, segment_vals)

        feat_recent = extract_shape_features(recent_vals)
        feat_segment = extract_shape_features(segment_vals)
        feat_sim = feature_similarity(feat_recent, feat_segment)

        score = combine_similarity(corr, dtw_dist, feat_sim, similarity_weights)

        if score > best_score:
            best_score = score
            best_result = {
                "segment_start": segment.index[0].strftime("%Y-%m-%d"),
                "segment_end": segment.index[-1].strftime("%Y-%m-%d"),
                "corr": round(corr, 4),
                "dtw": round(dtw_dist, 4),
                "feature_sim": round(feat_sim, 4),
                "pattern_similarity_score": round(score, 4)
            }

    return best_result


# ============================================================================
# 壓力驗證
# ============================================================================

def calculate_stress_signal(
    indicator_data: pd.Series,
    config: ConfirmatoryIndicator,
    lookback_days: int = 252
) -> Dict:
    """計算單一指標的壓力訊號"""
    if indicator_data.empty or len(indicator_data) < 20:
        return {
            "name": config.name,
            "series": config.series,
            "current_value": None,
            "z": 0,
            "signal": "no_data",
            "weight": config.weight
        }

    recent = indicator_data.iloc[-1]
    historical = indicator_data.iloc[-lookback_days:-1] if len(indicator_data) > lookback_days else indicator_data.iloc[:-1]

    mean = historical.mean()
    std = historical.std()

    if std == 0 or np.isnan(std):
        z = 0
    else:
        z = (recent - mean) / std

    # 判斷訊號
    threshold = config.stress_threshold

    if config.name == "yield_curve":
        # 殖利率曲線：倒掛（負值）為壓力
        if z < -abs(threshold) * 1.5:
            signal = "extreme_stress"
        elif z < -abs(threshold):
            signal = "stress"
        elif z < -abs(threshold) * 0.5:
            signal = "mild_stress"
        else:
            signal = "neutral"
    else:
        # 其他指標：上升為壓力
        if z > threshold * 1.5:
            signal = "extreme_stress"
        elif z > threshold:
            signal = "stress"
        elif z > threshold * 0.5:
            signal = "mild_stress"
        elif z < -threshold * 0.5:
            signal = "mild_risk_on"
        else:
            signal = "neutral"

    return {
        "name": config.name,
        "series": config.series,
        "current_value": round(float(recent), 4),
        "historical_mean": round(float(mean), 4),
        "historical_std": round(float(std), 4),
        "z": round(float(z), 4),
        "signal": signal,
        "weight": config.weight
    }


def aggregate_stress_scores(details: List[Dict]) -> float:
    """合成壓力分數"""
    total_weight = 0
    weighted_score = 0

    for d in details:
        if d["signal"] == "no_data":
            continue

        weight = d.get("weight", 1.0)
        total_weight += weight

        # 根據訊號計算分數
        signal_scores = {
            "extreme_stress": 1.0,
            "stress": 0.8,
            "mild_stress": 0.4,
            "neutral": 0.0,
            "mild_risk_on": -0.2
        }
        score = signal_scores.get(d["signal"], 0)
        weighted_score += weight * max(0, score)

    if total_weight == 0:
        return 0.0

    return weighted_score / total_weight


# ============================================================================
# 解讀生成
# ============================================================================

def generate_interpretation(
    best_match: Dict,
    stress_details: List[Dict],
    stress_score: float,
    composite_score: float
) -> Dict:
    """生成解讀框架"""
    pattern_score = best_match.get("pattern_similarity_score", 0)

    # 風險等級
    if composite_score > 0.7:
        risk_level = "high"
    elif composite_score > 0.5:
        risk_level = "medium_high"
    elif composite_score > 0.3:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Summary
    if pattern_score > 0.7 and stress_score < 0.3:
        summary = f"走勢形狀與 {best_match.get('baseline', '歷史事件')} 相似度高（{pattern_score:.2f}），但壓力驗證指標偏中性（{stress_score:.2f}），綜合風險分數 {composite_score:.2f}（中等）。這更像是「利率/會計結構造成的圖形相似」，不足以支持「系統性壓力升高」的假說。"
    elif pattern_score > 0.7 and stress_score > 0.5:
        summary = f"走勢形狀與 {best_match.get('baseline', '歷史事件')} 高度相似（{pattern_score:.2f}），且壓力驗證指標同步惡化（{stress_score:.2f}），綜合風險分數 {composite_score:.2f}（較高）。需要提高警覺，持續觀察是否為真正的金融壓力。"
    elif pattern_score < 0.5:
        summary = f"走勢形狀與歷史基準窗口相似度較低（{pattern_score:.2f}），圖形類比論述不成立。"
    else:
        summary = f"走勢形狀相似度中等（{pattern_score:.2f}），壓力驗證分數 {stress_score:.2f}，綜合風險 {composite_score:.2f}。建議持續觀察。"

    # 壓力分析
    stress_signals = [d for d in stress_details if d["signal"] in ["stress", "extreme_stress"]]
    neutral_signals = [d for d in stress_details if d["signal"] == "neutral"]

    if len(stress_signals) == 0:
        stress_finding = "壓力驗證指標大多處於中性區間"
    else:
        stress_finding = f"{len(stress_signals)} 個指標顯示壓力訊號"

    key_observations = []
    for d in stress_details:
        if d["signal"] == "no_data":
            continue
        obs = f"{d['name']}: z={d['z']:.2f}, {d['signal']}"
        key_observations.append(obs)

    return {
        "summary": summary,
        "pattern_analysis": {
            "finding": f"近期 WUDSHO 走勢與 {best_match.get('baseline', '歷史事件')} 的形狀相關係數為 {best_match.get('corr', 0):.2f}",
            "possible_causes": [
                "利率環境變化驅動（最可能）",
                "持有債券久期結構調整",
                "會計攤銷時程效果"
            ],
            "unlikely_cause": "系統性金融壓力（缺乏壓力指標共振）" if stress_score < 0.4 else "需要進一步觀察"
        },
        "stress_analysis": {
            "finding": stress_finding,
            "key_observations": key_observations
        },
        "what_to_watch_next_60d": [
            "若形狀相似度維持高檔，同時信用利差明顯走寬（z > 1.5），才應升級風險警報",
            "若 VIX 持續上升並突破 25，顯示市場開始定價風險",
            "觀察 Fed 是否啟用緊急流動性工具"
        ],
        "rebuttal_to_claim": [
            f"「像」可以量化（相關係數 {best_match.get('corr', 0):.2f}），但「像歷史事件」不等於「會發生同樣事件」",
            "WUDSHO 變動最常見的原因是利率效果，不是金融壓力",
            "把「黑天鵝」定義成「精心策劃」屬於不可驗證敘事"
        ]
    }, risk_level


# ============================================================================
# 主分析函數
# ============================================================================

def run_analysis(config: Config) -> Dict:
    """執行完整分析"""
    print(f"\n{'='*60}")
    print(f"聯準會未攤銷折價走勢模式偵測")
    print(f"{'='*60}")

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = config.history_start

    # 1. 抓取資料
    print("\n[Step 1] 抓取資料...")
    all_data = fetch_all_indicators(start_date, end_date)

    target_data = all_data.get(config.target_series, pd.Series())
    if target_data.empty:
        return {"error": f"無法取得 {config.target_series} 資料"}

    # 重採樣至週頻
    if config.resample_freq == "W":
        target_data = target_data.resample("W-FRI").last().dropna()

    # 2. 切出近期窗口
    print("\n[Step 2] 切出近期窗口...")
    recent_start = datetime.now() - timedelta(days=config.recent_window_days)
    recent = target_data[target_data.index >= recent_start]
    print(f"  近期窗口: {recent.index[0].strftime('%Y-%m-%d')} ~ {recent.index[-1].strftime('%Y-%m-%d')} ({len(recent)} 點)")

    # 3. 形狀比對
    print("\n[Step 3] 形狀比對...")
    all_matches = []

    for baseline in config.baseline_windows:
        baseline_data = target_data[(target_data.index >= baseline.start) & (target_data.index <= baseline.end)]
        if len(baseline_data) < len(recent):
            print(f"  {baseline.name}: 資料不足，跳過")
            continue

        match = find_best_match(recent, baseline_data, config.normalize_method, config.similarity_weights)
        if match:
            match["baseline"] = baseline.name
            all_matches.append(match)
            print(f"  {baseline.name}: corr={match['corr']:.2f}, score={match['pattern_similarity_score']:.2f}")

    if not all_matches:
        return {"error": "無法找到匹配的歷史片段"}

    # 最佳匹配
    best_match = max(all_matches, key=lambda x: x["pattern_similarity_score"])

    # 4. 壓力驗證
    print("\n[Step 4] 壓力驗證...")
    stress_details = []

    for indicator in config.confirmatory_indicators:
        if indicator.series == "yield_curve":
            ind_data = all_data.get("yield_curve", pd.Series())
        else:
            ind_data = all_data.get(indicator.series, pd.Series())

        result = calculate_stress_signal(ind_data, indicator)
        stress_details.append(result)
        print(f"  {indicator.name}: z={result['z']:.2f}, {result['signal']}")

    stress_score = aggregate_stress_scores(stress_details)

    # 5. 合成風險分數
    pattern_score = best_match["pattern_similarity_score"]
    composite_score = 0.6 * pattern_score + 0.4 * stress_score

    print(f"\n[Step 5] 合成風險分數")
    print(f"  形狀相似度: {pattern_score:.2f}")
    print(f"  壓力驗證: {stress_score:.2f}")
    print(f"  合成風險: {composite_score:.2f}")

    # 6. 生成解讀
    interpretation, risk_level = generate_interpretation(
        best_match, stress_details, stress_score, composite_score
    )

    # 7. 組裝結果
    result = {
        "skill": "detect-fed-unamortized-discount-pattern",
        "version": "0.1.0",
        "as_of_date": end_date,
        "target_series": config.target_series,
        "parameters": {
            "recent_window_days": config.recent_window_days,
            "resample_freq": config.resample_freq,
            "normalize_method": config.normalize_method,
            "similarity_metrics": config.similarity_metrics
        },
        "best_match": best_match,
        "all_matches": all_matches,
        "stress_confirmation": {
            "score": round(stress_score, 4),
            "details": stress_details
        },
        "composite_risk_score": round(composite_score, 4),
        "risk_level": risk_level,
        "interpretation": interpretation,
        "data_quality": {
            "target_series": {
                "series_id": config.target_series,
                "data_start": target_data.index[0].strftime("%Y-%m-%d"),
                "data_end": target_data.index[-1].strftime("%Y-%m-%d"),
                "frequency": config.resample_freq,
                "missing_values": 0
            }
        },
        "caveats": [
            "形狀相似不代表因果相同；該序列可能強烈受利率、持有期限結構與會計攤銷影響。",
            "若缺乏壓力指標同步惡化，不應把圖形類比直接升級成『黑天鵝預言』。",
            "本工具提供的是『樣態比對 + 交叉驗證』，不是預測器。",
            "任何單一序列都不應被用來做高確信度的危機斷言。"
        ],
        "metadata": {
            "executed_at": datetime.now().isoformat(),
            "skill_version": "0.1.0"
        }
    }

    return result


# ============================================================================
# 命令列介面
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="聯準會未攤銷折價走勢模式偵測器"
    )
    parser.add_argument("--target_series", type=str, default="WUDSHO",
                        help="目標 FRED 系列代碼")
    parser.add_argument("--baseline_windows", type=str, default=None,
                        help="基準窗口 (格式: name:start:end,name:start:end)")
    parser.add_argument("--recent_window_days", type=int, default=120,
                        help="近期窗口天數")
    parser.add_argument("--normalize_method", type=str, default="zscore",
                        choices=["zscore", "minmax", "pct_change"])
    parser.add_argument("--output", type=str, default=None,
                        help="輸出檔案路徑")
    parser.add_argument("--quick", action="store_true",
                        help="快速模式（使用預設參數）")
    parser.add_argument("--config", type=str, default=None,
                        help="配置檔路徑")

    args = parser.parse_args()

    # 建立配置
    config = Config()
    config.target_series = args.target_series
    config.recent_window_days = args.recent_window_days
    config.normalize_method = args.normalize_method
    config.baseline_windows = DEFAULT_BASELINE_WINDOWS
    config.confirmatory_indicators = DEFAULT_CONFIRMATORY_INDICATORS

    # 解析自訂基準窗口
    if args.baseline_windows:
        config.baseline_windows = []
        for win in args.baseline_windows.split(","):
            parts = win.split(":")
            if len(parts) == 3:
                config.baseline_windows.append(BaselineWindow(parts[0], parts[1], parts[2]))

    # 執行分析
    result = run_analysis(config)

    # 輸出結果
    if "error" in result:
        print(f"\n[Error] {result['error']}")
        return

    print(f"\n{'='*60}")
    print("分析結果摘要")
    print(f"{'='*60}")
    print(f"\n{result['interpretation']['summary']}")

    # 儲存結果
    output_path = args.output
    if output_path is None:
        output_dir = Path(__file__).parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"pattern_analysis_{datetime.now().strftime('%Y-%m-%d')}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n結果已儲存至: {output_path}")


if __name__ == "__main__":
    main()
