#!/usr/bin/env python3
"""
forecast-sector-relative-return-from-yield-spread

用美債殖利率曲線利差（如 2Y-10Y）建立「領先關係」，
推估未來一段時間內成長股（Nasdaq 100）相對防禦股（Healthcare/XLV）的相對績效方向與幅度。
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
import requests

try:
    import yfinance as yf
except ImportError:
    print("請安裝 yfinance: pip install yfinance")
    sys.exit(1)


# =============================================================================
# Constants
# =============================================================================

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

TENOR_TO_FRED = {
    "3M": "DGS3MO",
    "1Y": "DGS1",
    "2Y": "DGS2",
    "3Y": "DGS3",
    "5Y": "DGS5",
    "7Y": "DGS7",
    "10Y": "DGS10",
    "30Y": "DGS30",
}

DEFAULT_PARAMS = {
    "risk_ticker": "QQQ",
    "defensive_ticker": "XLV",
    "short_tenor": "2Y",
    "long_tenor": "10Y",
    "lead_months": 24,
    "lookback_years": 12,
    "freq": "weekly",
    "smoothing_window": 13,
    "return_horizon_months": 24,
    "model_type": "lagged_regression",
    "confidence_level": 0.80,
}


# =============================================================================
# Data Fetching
# =============================================================================

def fetch_fred_series(series_id: str, start_date: str, end_date: str) -> pd.Series:
    """從 FRED 抓取時間序列（無需 API key）"""
    params = {"id": series_id, "cosd": start_date, "coed": end_date}

    try:
        response = requests.get(FRED_CSV_URL, params=params, timeout=30)
        response.raise_for_status()

        df = pd.read_csv(StringIO(response.text))
        df.columns = ["DATE", series_id]
        df["DATE"] = pd.to_datetime(df["DATE"])
        df[series_id] = df[series_id].replace(".", pd.NA)
        df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
        df = df.dropna().set_index("DATE")

        return df[series_id]

    except Exception as e:
        print(f"Error fetching {series_id} from FRED: {e}")
        return pd.Series(dtype=float)


def fetch_price_series(ticker: str, start_date: str, end_date: str) -> pd.Series:
    """從 Yahoo Finance 抓取調整後收盤價"""
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if data.empty:
            print(f"No data returned for {ticker}")
            return pd.Series(dtype=float)

        # Handle different yfinance versions (MultiIndex vs single-level)
        if isinstance(data.columns, pd.MultiIndex):
            # New yfinance: ('Close', 'QQQ') format - Close is already adjusted
            if ("Close", ticker) in data.columns:
                return data[("Close", ticker)]
            # Fallback to Adj Close if available
            elif ("Adj Close", ticker) in data.columns:
                return data[("Adj Close", ticker)]
            else:
                # Try first available price column
                close_cols = [c for c in data.columns if c[0] in ["Close", "Adj Close"]]
                if close_cols:
                    return data[close_cols[0]]
        else:
            # Old yfinance: single-level columns
            if "Adj Close" in data.columns:
                return data["Adj Close"]
            elif "Close" in data.columns:
                return data["Close"]

        print(f"No Close column found for {ticker}, columns: {data.columns.tolist()}")
        return pd.Series(dtype=float)
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return pd.Series(dtype=float)


# =============================================================================
# Data Processing
# =============================================================================

def to_weekly(series: pd.Series) -> pd.Series:
    """轉換為週頻（週五收盤）"""
    return series.resample("W-FRI").last().dropna()


def to_monthly(series: pd.Series) -> pd.Series:
    """轉換為月頻（月底）"""
    return series.resample("ME").last().dropna()


def compute_future_rel_return(ratio: pd.Series, horizon_periods: int) -> pd.Series:
    """計算未來 H 期的對數相對報酬"""
    return np.log(ratio.shift(-horizon_periods) / ratio)


def compute_spread_changes(spread: pd.Series) -> dict:
    """計算利差的近期變化"""
    current = spread.iloc[-1]
    changes = {}

    for months, label in [(3, "3m"), (6, "6m"), (12, "12m")]:
        periods = months * 4 if len(spread) > months * 4 else len(spread) - 1
        if periods > 0 and len(spread) > periods:
            past = spread.iloc[-periods - 1]
            changes[f"{label}_change"] = current - past

    return changes


# =============================================================================
# Model Estimation
# =============================================================================

def fit_lagged_regression(x: pd.Series, y: pd.Series) -> dict:
    """簡單 OLS 迴歸"""
    valid = x.notna() & y.notna()
    x_clean = x[valid].values
    y_clean = y[valid].values

    if len(x_clean) < 30:
        return {"error": "Insufficient data points"}

    # Compute statistics
    x_mean = np.mean(x_clean)
    y_mean = np.mean(y_clean)
    cov_xy = np.cov(x_clean, y_clean, ddof=1)[0, 1]
    var_x = np.var(x_clean, ddof=1)

    beta = cov_xy / var_x
    alpha = y_mean - beta * x_mean

    # Correlation
    corr = np.corrcoef(x_clean, y_clean)[0, 1]

    # R-squared
    y_pred = alpha + beta * x_clean
    ss_res = np.sum((y_clean - y_pred) ** 2)
    ss_tot = np.sum((y_clean - y_mean) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    # Residuals for interval estimation
    residuals = y_clean - y_pred

    # Simple t-test for beta
    n = len(x_clean)
    se_beta = np.sqrt(ss_res / (n - 2)) / np.sqrt(np.sum((x_clean - x_mean) ** 2))
    t_stat = beta / se_beta if se_beta > 0 else 0

    # Approximate p-value (two-tailed)
    from scipy import stats
    try:
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
    except:
        p_value = None

    return {
        "alpha": float(alpha),
        "beta": float(beta),
        "corr_x_y": float(corr),
        "r_squared": float(r_squared),
        "p_value": float(p_value) if p_value is not None else None,
        "n_observations": int(n),
        "residuals": residuals.tolist(),
    }


def lead_scan(spread: pd.Series, ratio: pd.Series, leads: list, freq: str) -> dict:
    """掃描多個領先期"""
    results = {}
    periods_per_month = 4 if freq == "weekly" else 1  # 週: 4.345, 近似 4

    for lead in leads:
        horizon_periods = int(lead * periods_per_month)
        y = compute_future_rel_return(ratio, horizon_periods)
        valid = spread.notna() & y.notna()

        if valid.sum() < 30:
            results[lead] = None
            continue

        corr = np.corrcoef(spread[valid], y[valid])[0, 1]
        results[lead] = float(corr)

    return results


def stability_check(spread: pd.Series, y: pd.Series) -> dict:
    """子樣本穩定性檢查"""
    valid = spread.notna() & y.notna()
    spread_clean = spread[valid]
    y_clean = y[valid]

    n = len(spread_clean)
    mid = n // 2

    first_half = spread_clean.iloc[:mid]
    y_first = y_clean.iloc[:mid]
    second_half = spread_clean.iloc[mid:]
    y_second = y_clean.iloc[mid:]

    corr_first = np.corrcoef(first_half, y_first)[0, 1] if len(first_half) > 10 else None
    corr_second = np.corrcoef(second_half, y_second)[0, 1] if len(second_half) > 10 else None

    # Determine consistency
    if corr_first is None or corr_second is None:
        consistency = "insufficient_data"
    elif np.sign(corr_first) != np.sign(corr_second):
        consistency = "low"
    elif abs(corr_first - corr_second) < 0.1:
        consistency = "high"
    elif abs(corr_first - corr_second) < 0.2:
        consistency = "medium-high"
    else:
        consistency = "medium"

    return {
        "first_half_period": f"{spread_clean.index[0].date()} to {spread_clean.index[mid-1].date()}",
        "second_half_period": f"{spread_clean.index[mid].date()} to {spread_clean.index[-1].date()}",
        "first_half_corr": float(corr_first) if corr_first is not None else None,
        "second_half_corr": float(corr_second) if corr_second is not None else None,
        "consistency": consistency,
    }


# =============================================================================
# Forecasting
# =============================================================================

def make_forecast(model_result: dict, x_now: float, confidence_level: float) -> dict:
    """產出預測結果"""
    alpha = model_result["alpha"]
    beta = model_result["beta"]
    residuals = np.array(model_result["residuals"])

    # Point estimate
    y_hat = alpha + beta * x_now

    # Interval estimate
    lo_q = (1 - confidence_level) / 2
    hi_q = 1 - lo_q
    lo_resid, hi_resid = np.quantile(residuals, [lo_q, hi_q])
    y_lo = y_hat + lo_resid
    y_hi = y_hat + hi_resid

    # Convert to percentage
    pct_hat = float(np.exp(y_hat) - 1)
    pct_lo = float(np.exp(y_lo) - 1)
    pct_hi = float(np.exp(y_hi) - 1)

    # Direction probability (based on residuals distribution)
    defensive_outperform_prob = np.mean(residuals < -y_hat) if y_hat > 0 else np.mean(residuals < -y_hat)
    # Simplified: if y_hat < 0, defensive likely wins
    if y_hat < 0:
        defensive_outperform_prob = 0.5 + abs(y_hat) / (2 * np.std(residuals)) if np.std(residuals) > 0 else 0.5
        defensive_outperform_prob = min(0.95, max(0.5, defensive_outperform_prob))
    else:
        defensive_outperform_prob = 0.5 - abs(y_hat) / (2 * np.std(residuals)) if np.std(residuals) > 0 else 0.5
        defensive_outperform_prob = max(0.05, min(0.5, defensive_outperform_prob))

    return {
        "log": float(y_hat),
        "pct": pct_hat,
        "interval_log": [float(y_lo), float(y_hi)],
        "interval_pct": [pct_lo, pct_hi],
        "defensive_outperform_prob": float(defensive_outperform_prob),
    }


# =============================================================================
# Main Analysis
# =============================================================================

def run_analysis(params: dict) -> dict:
    """執行完整分析"""
    # Extract params
    risk_ticker = params.get("risk_ticker", DEFAULT_PARAMS["risk_ticker"])
    defensive_ticker = params.get("defensive_ticker", DEFAULT_PARAMS["defensive_ticker"])
    short_tenor = params.get("short_tenor", DEFAULT_PARAMS["short_tenor"])
    long_tenor = params.get("long_tenor", DEFAULT_PARAMS["long_tenor"])
    lead_months = params.get("lead_months", DEFAULT_PARAMS["lead_months"])
    lookback_years = params.get("lookback_years", DEFAULT_PARAMS["lookback_years"])
    freq = params.get("freq", DEFAULT_PARAMS["freq"])
    smoothing_window = params.get("smoothing_window", DEFAULT_PARAMS["smoothing_window"])
    return_horizon_months = params.get("return_horizon_months", DEFAULT_PARAMS["return_horizon_months"])
    model_type = params.get("model_type", DEFAULT_PARAMS["model_type"])
    confidence_level = params.get("confidence_level", DEFAULT_PARAMS["confidence_level"])
    do_lead_scan = params.get("lead_scan", False)
    scan_range = params.get("scan_range", [6, 12, 18, 24, 30])

    # Date range
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=lookback_years * 365 + 365)).strftime("%Y-%m-%d")

    # Fetch data
    print(f"Fetching yield data from FRED...")
    short_code = TENOR_TO_FRED.get(short_tenor, "DGS2")
    long_code = TENOR_TO_FRED.get(long_tenor, "DGS10")

    short_yield = fetch_fred_series(short_code, start_date, end_date)
    long_yield = fetch_fred_series(long_code, start_date, end_date)

    print(f"Fetching price data from Yahoo Finance...")
    risk_price = fetch_price_series(risk_ticker, start_date, end_date)
    defensive_price = fetch_price_series(defensive_ticker, start_date, end_date)

    # Validate data
    if short_yield.empty or long_yield.empty:
        return {"status": "error", "error": {"code": "DATA_FETCH_FAILED", "message": "Failed to fetch yield data"}}
    if risk_price.empty or defensive_price.empty:
        return {"status": "error", "error": {"code": "DATA_FETCH_FAILED", "message": "Failed to fetch price data"}}

    # Compute spread and ratio
    spread = short_yield - long_yield  # 2Y - 10Y
    ratio = risk_price / defensive_price

    # Align frequency
    if freq == "weekly":
        spread = to_weekly(spread)
        ratio = to_weekly(ratio)
    elif freq == "monthly":
        spread = to_monthly(spread)
        ratio = to_monthly(ratio)

    # Align dates
    aligned = pd.concat({"spread": spread, "ratio": ratio}, axis=1).dropna()
    spread = aligned["spread"]
    ratio = aligned["ratio"]

    if len(spread) < 100:
        return {"status": "error", "error": {"code": "INSUFFICIENT_DATA", "message": f"Only {len(spread)} data points"}}

    # Optional smoothing
    if smoothing_window > 1:
        spread_smoothed = spread.rolling(smoothing_window).mean().dropna()
    else:
        spread_smoothed = spread

    # Compute future relative return
    periods_per_month = 4 if freq == "weekly" else 1
    horizon_periods = int(return_horizon_months * periods_per_month)
    y = compute_future_rel_return(ratio, horizon_periods)

    # Align for modeling
    model_data = pd.concat({"x": spread_smoothed, "y": y}, axis=1).dropna()

    if len(model_data) < 50:
        return {"status": "error", "error": {"code": "INSUFFICIENT_DATA", "message": "Not enough overlapping data"}}

    # Fit model
    print(f"Fitting {model_type} model...")
    model_result = fit_lagged_regression(model_data["x"], model_data["y"])

    if "error" in model_result:
        return {"status": "error", "error": {"code": "MODEL_FIT_FAILED", "message": model_result["error"]}}

    # Current state
    x_now = spread_smoothed.iloc[-1]
    spread_changes = compute_spread_changes(spread_smoothed)
    spread_percentile = (spread_smoothed < x_now).sum() / len(spread_smoothed) * 100

    # Forecast
    forecast = make_forecast(model_result, x_now, confidence_level)

    # Stability check
    stability = stability_check(model_data["x"], model_data["y"])

    # Lead scan (optional)
    lead_scan_result = None
    if do_lead_scan:
        print("Running lead scan...")
        lead_scan_result = lead_scan(spread_smoothed, ratio, scan_range, freq)
        best_lead = max(lead_scan_result, key=lambda k: abs(lead_scan_result[k]) if lead_scan_result[k] else 0)

    # Build output
    output = {
        "skill": "forecast_sector_relative_return_from_yield_spread",
        "version": "0.1.0",
        "generated_at": datetime.now().isoformat(),

        "inputs": {
            "risk_ticker": risk_ticker,
            "defensive_ticker": defensive_ticker,
            "short_tenor": short_tenor,
            "long_tenor": long_tenor,
            "lead_months": lead_months,
            "lookback_years": lookback_years,
            "freq": freq,
            "smoothing_window": smoothing_window,
            "return_horizon_months": return_horizon_months,
            "model_type": model_type,
            "confidence_level": confidence_level,
        },

        "signal_name": f"{short_code}_minus_{long_code}_leads_{risk_ticker}_over_{defensive_ticker}",

        "current_state": {
            "spread": round(float(x_now), 4),
            "spread_percentile": round(float(spread_percentile), 1),
            "spread_3m_change": round(spread_changes.get("3m_change", 0), 4),
            "spread_6m_change": round(spread_changes.get("6m_change", 0), 4),
            "spread_trend": "steepening" if spread_changes.get("3m_change", 0) < 0 else "flattening",
            "as_of_date": spread.index[-1].strftime("%Y-%m-%d"),
        },

        "model": {
            "type": model_type,
            "coefficients": {
                "alpha": round(model_result["alpha"], 4),
                "beta": round(model_result["beta"], 4),
            },
            "fit_quality": {
                "corr_x_y": round(model_result["corr_x_y"], 3),
                "r_squared": round(model_result["r_squared"], 3),
                "p_value": round(model_result["p_value"], 4) if model_result["p_value"] else None,
                "n_observations": model_result["n_observations"],
                "notes": f"{'負' if model_result['beta'] < 0 else '正'} beta 意味 spread {'越高' if model_result['beta'] < 0 else '越低'} → 未來 {risk_ticker} 相對 {defensive_ticker} {'越弱' if model_result['beta'] < 0 else '越強'}",
            },
        },

        "forecast": {
            "horizon_months": return_horizon_months,
            "future_relative_return": {
                "log": round(forecast["log"], 4),
                "pct": round(forecast["pct"], 4),
            },
            "interval": {
                "confidence_level": confidence_level,
                "log": [round(v, 4) for v in forecast["interval_log"]],
                "pct": [round(v, 4) for v in forecast["interval_pct"]],
            },
            "direction": {
                "defensive_outperform_prob": round(forecast["defensive_outperform_prob"], 2),
                "expected_winner": defensive_ticker if forecast["pct"] < 0 else risk_ticker,
            },
            "interpretation": _generate_interpretation(forecast, risk_ticker, defensive_ticker, return_horizon_months),
        },

        "diagnostics": {
            "stability_checks": stability,
            "data_quality": {
                "yield_data_points": len(short_yield),
                "price_data_points": len(ratio),
                "aligned_data_points": len(model_data),
                "date_range": f"{spread.index[0].strftime('%Y-%m-%d')} to {spread.index[-1].strftime('%Y-%m-%d')}",
            },
        },

        "summary": _generate_summary(x_now, forecast, risk_ticker, defensive_ticker, return_horizon_months),

        "notes": [
            "領先關係反映的是『歷史統計規律』，不保證未來成立。",
            f"R² 為 {model_result['r_squared']:.2f}，spread 僅解釋約 {model_result['r_squared']*100:.0f}% 的相對報酬變異。",
            f"當前 spread {'正在變陡（從倒掛回正）' if spread_changes.get('3m_change', 0) < 0 else '正在變平（趨向倒掛）'}，需持續觀察。",
            "建議搭配：景氣指標、估值分位、資金流向做交叉驗證。",
        ],
    }

    # Add lead scan if performed
    if lead_scan_result:
        output["diagnostics"]["lead_scan"] = {
            "performed": True,
            "scan_range": scan_range,
            "best_lead_months": best_lead,
            "correlation_by_lead": {str(k): round(v, 3) if v else None for k, v in lead_scan_result.items()},
        }

    return output


def _generate_interpretation(forecast: dict, risk_ticker: str, defensive_ticker: str, horizon: int) -> str:
    """生成預測解讀"""
    pct = forecast["pct"]
    lo, hi = forecast["interval_pct"]

    if pct < 0:
        return f"若此關係維持，未來 {horizon} 個月 {risk_ticker} 相對 {defensive_ticker} 期望報酬為 {pct*100:.1f}%，{defensive_ticker} 較可能跑贏；但 {hi*100:.0f}% 上界仍為正值，需搭配其他條件確認。"
    else:
        return f"若此關係維持，未來 {horizon} 個月 {risk_ticker} 相對 {defensive_ticker} 期望報酬為 +{pct*100:.1f}%，{risk_ticker} 較可能跑贏；但 {lo*100:.0f}% 下界為負值，仍有不確定性。"


def _generate_summary(spread: float, forecast: dict, risk_ticker: str, defensive_ticker: str, horizon: int) -> str:
    """生成摘要"""
    curve_status = "曲線倒掛" if spread > 0 else "曲線正常" if spread < -0.5 else "曲線輕微倒掛"
    winner = defensive_ticker if forecast["pct"] < 0 else risk_ticker
    return f"美國公債利差（2Y-10Y）對 {risk_ticker}/{defensive_ticker} 相對報酬存在領先關係。當前 spread 為 {spread:.2f}%（{curve_status}），對應未來 {horizon} 個月 {winner} 相對跑贏的預期。"


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="美國公債利差 → 板塊相對報酬預測")

    parser.add_argument("--quick", action="store_true", help="使用預設參數快速執行")
    parser.add_argument("--risk-ticker", default=DEFAULT_PARAMS["risk_ticker"], help="成長股標的")
    parser.add_argument("--defensive-ticker", default=DEFAULT_PARAMS["defensive_ticker"], help="防禦股標的")
    parser.add_argument("--short-tenor", default=DEFAULT_PARAMS["short_tenor"], help="短端期限")
    parser.add_argument("--long-tenor", default=DEFAULT_PARAMS["long_tenor"], help="長端期限")
    parser.add_argument("--lead-months", type=int, default=DEFAULT_PARAMS["lead_months"], help="領先期（月）")
    parser.add_argument("--lookback-years", type=int, default=DEFAULT_PARAMS["lookback_years"], help="回測年數")
    parser.add_argument("--freq", default=DEFAULT_PARAMS["freq"], choices=["daily", "weekly", "monthly"])
    parser.add_argument("--smoothing-window", type=int, default=DEFAULT_PARAMS["smoothing_window"])
    parser.add_argument("--model-type", default=DEFAULT_PARAMS["model_type"])
    parser.add_argument("--confidence-level", type=float, default=DEFAULT_PARAMS["confidence_level"])
    parser.add_argument("--lead-scan", action="store_true", help="執行領先期掃描")
    parser.add_argument("--scan-range", default="6,12,18,24,30", help="掃描範圍（逗號分隔）")
    parser.add_argument("--output", default=None, help="輸出 JSON 檔案路徑")

    args = parser.parse_args()

    # Build params
    params = {
        "risk_ticker": args.risk_ticker,
        "defensive_ticker": args.defensive_ticker,
        "short_tenor": args.short_tenor,
        "long_tenor": args.long_tenor,
        "lead_months": args.lead_months,
        "lookback_years": args.lookback_years,
        "freq": args.freq,
        "smoothing_window": args.smoothing_window,
        "model_type": args.model_type,
        "confidence_level": args.confidence_level,
        "lead_scan": args.lead_scan,
        "scan_range": [int(x) for x in args.scan_range.split(",")],
    }

    # Run analysis
    result = run_analysis(params)

    # Output
    output_json = json.dumps(result, indent=2, ensure_ascii=False, default=str)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Result saved to {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
