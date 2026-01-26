#!/usr/bin/env python3
"""
JSDA 保險公司超長期 JGB 淨買賣流量分析器

從 JSDA 公開統計數據（Trading Volume of OTC Bonds）分析日本保險公司
對超長期（10年以上）JGB 的淨買賣流量。

數據來源：
- https://www.jsda.or.jp/shiryoshitsu/toukei/tentoubaibai/koushasai.xlsx（當前財年）
- https://www.jsda.or.jp/shiryoshitsu/toukei/tentoubaibai/koushasai{YYYY}.xlsx（歷史財年）

注意：JSDA 在 2018/05 改版，將「投資人別交易」整併進「Trading Volume of OTC Bonds」。
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import urllib.request
import ssl

import numpy as np
import pandas as pd

# 專案路徑設定
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
OUTPUT_DIR = SKILL_DIR.parent.parent.parent / "output"

# 確保目錄存在
CACHE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# 配置
# ============================================================

JSDA_BASE_URL = "https://www.jsda.or.jp/shiryoshitsu/toukei/tentoubaibai"
JSDA_CURRENT_FILE = "koushasai.xlsx"
JSDA_HISTORICAL_PATTERN = "koushasai{year}.xlsx"

# Excel 欄位映射（基於實際 JSDA 結構）
SHEET_NET_PURCHASE = "(Ｊ)合計差引"  # 淨買賣額 sheet
COL_DATE = 0           # 年/月 欄位
COL_INVESTOR = 1       # 投資人類型欄位
COL_SUPER_LONG = 4     # 超長期國債欄位（Interest-bearing Long-term over 10-year）

# 投資人識別關鍵字
INSURANCE_KEYWORDS = ["生保・損保", "生保", "Life & Non-Life Insurance"]


# ============================================================
# 數據抓取
# ============================================================

def download_jsda_file(url: str, local_path: Path, force: bool = False) -> bool:
    """
    下載 JSDA Excel 檔案

    Args:
        url: 下載 URL
        local_path: 本地儲存路徑
        force: 是否強制重新下載

    Returns:
        是否成功
    """
    if local_path.exists() and not force:
        # 檢查檔案是否有效（大於 50KB）
        if local_path.stat().st_size > 50000:
            return True

    try:
        # 建立 SSL context（部分環境需要）
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        print(f"下載中: {url}", file=sys.stderr)

        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )

        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            data = response.read()

        if len(data) < 50000:
            print(f"警告: 檔案太小，可能下載失敗: {len(data)} bytes", file=sys.stderr)
            return False

        with open(local_path, 'wb') as f:
            f.write(data)

        print(f"下載完成: {local_path} ({len(data)} bytes)", file=sys.stderr)
        return True

    except Exception as e:
        print(f"下載失敗: {url} - {e}", file=sys.stderr)
        return False


def fetch_jsda_data(
    start_year: int = 2018,
    end_year: int = None,
    refresh: bool = False
) -> pd.DataFrame:
    """
    抓取 JSDA 數據

    Args:
        start_year: 起始財年（日本財年 4 月開始）
        end_year: 結束財年
        refresh: 是否強制刷新

    Returns:
        pd.DataFrame: 合併後的淨買賣數據
    """
    if end_year is None:
        end_year = datetime.now().year

    all_records = []

    # 下載當前財年
    current_url = f"{JSDA_BASE_URL}/{JSDA_CURRENT_FILE}"
    current_path = CACHE_DIR / JSDA_CURRENT_FILE
    if download_jsda_file(current_url, current_path, force=refresh):
        records = extract_insurance_superlong(current_path)
        all_records.extend(records)

    # 下載歷史財年
    for year in range(end_year - 1, start_year - 1, -1):
        filename = JSDA_HISTORICAL_PATTERN.format(year=year)
        url = f"{JSDA_BASE_URL}/{filename}"
        local_path = CACHE_DIR / filename

        if download_jsda_file(url, local_path, force=refresh):
            records = extract_insurance_superlong(local_path)
            all_records.extend(records)

    # 去重並排序
    seen = set()
    unique_records = []
    for r in all_records:
        if r['year_month'] not in seen:
            seen.add(r['year_month'])
            unique_records.append(r)

    # 轉換為 DataFrame
    df = pd.DataFrame(unique_records)
    if df.empty:
        return df

    df['date'] = pd.to_datetime(df['year_month'].str.replace('/', '-') + '-01')
    df = df.sort_values('date').set_index('date')

    return df


def extract_insurance_superlong(xlsx_path: Path) -> List[Dict]:
    """
    從 JSDA Excel 提取保險公司超長期國債淨買賣數據

    Args:
        xlsx_path: Excel 檔案路徑

    Returns:
        List[Dict]: 每月數據記錄
    """
    try:
        df = pd.read_excel(xlsx_path, sheet_name=SHEET_NET_PURCHASE, header=None)
    except Exception as e:
        print(f"讀取失敗 {xlsx_path}: {e}", file=sys.stderr)
        return []

    records = []
    for idx, row in df.iterrows():
        investor = str(row[COL_INVESTOR]) if pd.notna(row[COL_INVESTOR]) else ""

        # 檢查是否為保險公司行
        is_insurance = any(kw in investor for kw in INSURANCE_KEYWORDS)
        if not is_insurance:
            continue

        year_month = row[COL_DATE]
        super_long = row[COL_SUPER_LONG]

        if pd.isna(year_month) or pd.isna(super_long):
            continue

        try:
            records.append({
                'year_month': str(year_month).strip(),
                'net_sale_100m_yen': float(super_long)  # 正值=淨賣出，負值=淨買入
            })
        except (ValueError, TypeError):
            continue

    return records


# ============================================================
# 核心分析函數
# ============================================================

def calc_streak(series: pd.Series, sign: str = "positive") -> Tuple[int, str]:
    """
    計算連續淨賣出（或淨買入）月數

    注意：JSDA 數據中正值=淨賣出，負值=淨買入

    Args:
        series: 淨賣出時間序列（正值=賣出）
        sign: "positive"（連續淨賣出）或 "negative"（連續淨買入）

    Returns:
        (連續月數, 起始月份)
    """
    s = series.dropna()
    if s.empty:
        return 0, None

    streak = 0
    for v in reversed(s.values):
        if sign == "positive" and v > 0:
            streak += 1
        elif sign == "negative" and v < 0:
            streak += 1
        else:
            break

    if streak > 0:
        streak_start = s.index[-streak].strftime("%Y-%m")
    else:
        streak_start = None

    return streak, streak_start


def calc_cumulative(series: pd.Series, streak_len: int) -> float:
    """計算本輪累積淨賣出"""
    if streak_len == 0:
        return 0.0
    streak_window = series.tail(streak_len)
    return float(streak_window.sum())


def is_record_sale(
    series: pd.Series,
    lookback_months: int = None
) -> Dict:
    """
    判斷是否創下歷史最大淨賣出

    Args:
        series: 淨賣出時間序列（正值=賣出）
        lookback_months: 回溯月數（None = 全樣本）

    Returns:
        dict: 包含 is_record, record_high, record_date 等
    """
    if lookback_months:
        sample = series.tail(lookback_months)
    else:
        sample = series

    latest = series.iloc[-1]
    record_high = sample.max()  # 最大淨賣出（正值）
    record_low = sample.min()   # 最大淨買入（負值）

    return {
        "is_record_sale": bool((latest == record_high) and (latest > 0)),
        "is_record_purchase": bool((latest == record_low) and (latest < 0)),
        "record_sale_100m_yen": float(record_high),
        "record_sale_date": str(sample.idxmax().strftime("%Y-%m")),
        "record_purchase_100m_yen": float(record_low),
        "record_purchase_date": str(sample.idxmin().strftime("%Y-%m")),
        "lookback_period": f"近 {lookback_months} 個月" if lookback_months else f"全樣本 ({len(sample)} 個月)"
    }


def calc_historical_stats(series: pd.Series) -> Dict:
    """計算歷史統計"""
    return {
        "count": int(len(series)),
        "mean_100m_yen": float(series.mean()),
        "std_100m_yen": float(series.std()),
        "min_100m_yen": float(series.min()),
        "max_100m_yen": float(series.max()),
        "median_100m_yen": float(series.median()),
        "percentile_25_100m_yen": float(series.quantile(0.25)),
        "percentile_75_100m_yen": float(series.quantile(0.75))
    }


def calc_zscore(value: float, mean: float, std: float) -> float:
    """計算 Z-score"""
    if std == 0:
        return 0.0
    return (value - mean) / std


def calc_percentile(series: pd.Series, value: float) -> float:
    """計算數值在歷史中的分位數"""
    return float((series < value).mean())


def analyze(df: pd.DataFrame, lookback_months: int = None) -> Dict:
    """
    執行完整分析

    Args:
        df: 淨賣出 DataFrame（含 net_sale_100m_yen 欄位）
        lookback_months: 回溯月數

    Returns:
        dict: 完整分析結果
    """
    series = df['net_sale_100m_yen']
    latest_date = series.index[-1]
    latest_value = series.iloc[-1]

    streak_len, streak_start = calc_streak(series, sign="positive")
    cumulative = calc_cumulative(series, streak_len)
    record_info = is_record_sale(series, lookback_months)
    stats = calc_historical_stats(series)

    zscore = calc_zscore(latest_value, stats["mean_100m_yen"], stats["std_100m_yen"])
    percentile = calc_percentile(series, latest_value)

    return {
        "skill": "analyze_jgb_insurer_superlong_flow",
        "version": "1.0.0",
        "as_of": datetime.now().strftime("%Y-%m-%d"),
        "status": "success",
        "data_source": {
            "name": "JSDA Trading Volume of OTC Bonds (公社債店頭売買高)",
            "url": "https://www.jsda.or.jp/shiryoshitsu/toukei/tentoubaibai/",
            "sheet": SHEET_NET_PURCHASE,
            "fetch_timestamp": datetime.now().isoformat(),
            "data_version": latest_date.strftime("%Y-%m")
        },
        "parameters": {
            "investor_group": "life_and_nonlife_insurance",
            "investor_label": "生保・損保 (Life & Non-Life Insurance Companies)",
            "maturity_bucket": "super_long",
            "maturity_label": "超長期 (Interest-bearing Long-term over 10-year)",
            "measure": "net_sale",
            "unit": "100 million yen (億円)",
            "sign_convention": "正值=淨賣出 (Sell-Purchase), 負值=淨買入",
            "frequency": "monthly"
        },
        "analysis_period": {
            "start": series.index[0].strftime("%Y-%m"),
            "end": latest_date.strftime("%Y-%m"),
            "months": len(series)
        },
        "latest_month": {
            "date": latest_date.strftime("%Y-%m"),
            "net_sale_100m_yen": round(latest_value, 0),
            "net_sale_trillion_yen": round(latest_value / 10000, 4),
            "interpretation": "淨賣出" if latest_value > 0 else "淨買入",
            "abs_value_100m_yen": abs(round(latest_value, 0))
        },
        "record_analysis": record_info,
        "streak_analysis": {
            "consecutive_net_sale_months": streak_len,
            "streak_start": streak_start,
            "streak_end": latest_date.strftime("%Y-%m") if streak_len > 0 else None,
            "cumulative_net_sale_100m_yen": round(cumulative, 0),
            "cumulative_net_sale_trillion_yen": round(cumulative / 10000, 4)
        },
        "historical_stats": {
            "sample_period": {
                "start": series.index[0].strftime("%Y-%m"),
                "end": latest_date.strftime("%Y-%m")
            },
            **{k: round(v, 2) if isinstance(v, float) else v for k, v in stats.items()},
            "latest_zscore": round(zscore, 2),
            "latest_percentile": round(percentile, 4)
        },
        "headline_takeaways": generate_takeaways(
            latest_value, streak_len, cumulative, record_info, zscore, latest_date
        ),
        "confidence": {
            "level": "high",
            "reasons": [
                "數據來源為 JSDA 官方統計（公社債店頭売買高）",
                "計算邏輯透明可重現",
                "直接從原始 Excel 解析，無二手加工"
            ],
            "caveats": [
                "數據延遲約 T+1 個月",
                "僅包含店頭交易，不含交易所交易"
            ]
        }
    }


def generate_takeaways(
    latest_value: float,
    streak_len: int,
    cumulative: float,
    record_info: Dict,
    zscore: float,
    latest_date
) -> List[str]:
    """生成 headline takeaways"""
    takeaways = []

    # 1. 最新值解讀
    if record_info["is_record_sale"]:
        takeaways.append(
            f"✓ 驗證屬實：日本保險公司在 {latest_date.strftime('%Y/%m')} 創下歷史最大單月淨賣出"
            f"（{latest_value:,.0f} 億日圓 = {latest_value/10000:.2f} 兆日圓）"
        )
    else:
        direction = "淨賣出" if latest_value > 0 else "淨買入"
        takeaways.append(
            f"日本保險公司在 {latest_date.strftime('%Y/%m')} {direction}"
            f" {abs(latest_value):,.0f} 億日圓"
        )

    # 2. 連續賣超
    if streak_len > 0:
        takeaways.append(
            f"已連續 {streak_len} 個月淨賣出超長期國債，累積金額 {cumulative:,.0f} 億日圓"
            f"（{cumulative/10000:.2f} 兆日圓）"
        )

    # 3. 極端程度
    if zscore > 2:
        takeaways.append(
            f"當前淨賣出規模處於歷史極端區間（Z-score: {zscore:.2f}，超過 2 個標準差）"
        )
    elif zscore < -2:
        takeaways.append(
            f"當前淨買入規模處於歷史極端區間（Z-score: {zscore:.2f}）"
        )

    return takeaways


def format_markdown_report(result: Dict) -> str:
    """格式化為 Markdown 報告"""
    latest = result["latest_month"]
    record = result["record_analysis"]
    streak = result["streak_analysis"]
    stats = result["historical_stats"]
    params = result["parameters"]
    period = result["analysis_period"]

    report = f"""## 日本保險公司超長期 JGB 淨買賣驗證報告

**分析日期**：{result["as_of"]}
**數據來源**：{result["data_source"]["name"]}
**分析期間**：{period["start"]} ~ {period["end"]}（{period["months"]} 個月）

---

### 核心結論

| 指標 | 數值 | 說明 |
|------|------|------|
| 本月（{latest["date"]}）| **{latest["net_sale_100m_yen"]:,.0f} 億日圓** | {latest["interpretation"]} |
| 是否創歷史紀錄 | **{"✓ 是" if record["is_record_sale"] else "否"}** | {record["lookback_period"]} |
| 連續淨賣出月數 | **{streak["consecutive_net_sale_months"]} 個月** | 自 {streak["streak_start"]} 起 |
| 本輪累積淨賣出 | **{streak["cumulative_net_sale_100m_yen"]:,.0f} 億日圓** | {streak["cumulative_net_sale_trillion_yen"]:.2f} 兆日圓 |

---

### 歷史分布

| 統計量 | 數值 |
|--------|------|
| 樣本平均 | {stats["mean_100m_yen"]:,.0f} 億日圓/月 |
| 標準差 | {stats["std_100m_yen"]:,.0f} 億日圓 |
| 歷史最大淨賣出 | {record["record_sale_100m_yen"]:,.0f} 億日圓（{record["record_sale_date"]}）|
| 歷史最大淨買入 | {record["record_purchase_100m_yen"]:,.0f} 億日圓（{record["record_purchase_date"]}）|
| 當前值 Z-score | {stats["latest_zscore"]:.2f} |
| 當前值分位數 | {stats["latest_percentile"]:.2%} |

---

### 口徑說明

- **投資人分類**：{params["investor_label"]}
- **天期桶**：{params["maturity_label"]}
- **符號慣例**：{params["sign_convention"]}
- **單位**：{params["unit"]}

---

### Headline Takeaways
"""

    for i, takeaway in enumerate(result["headline_takeaways"], 1):
        report += f"\n{i}. {takeaway}"

    report += f"""

---

### 數據來源與可重現性

- **官方來源**：[JSDA 公社債店頭売買高]({result["data_source"]["url"]})
- **Sheet 名稱**：{result["data_source"]["sheet"]}
- **數據時點**：{result["data_source"]["data_version"]}
"""

    return report


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="分析日本保險公司超長期 JGB 淨買賣流量（JSDA 數據）"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="快速檢查模式（使用快取數據）"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="完整分析模式"
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=2018,
        help="起始財年（預設 2018）"
    )
    parser.add_argument(
        "--lookback",
        type=int,
        default=None,
        help="回溯月數（預設全樣本）"
    )
    parser.add_argument(
        "--format",
        type=str,
        default="markdown",
        choices=["json", "markdown"],
        help="輸出格式"
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="強制重新下載數據"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="輸出檔案路徑"
    )

    args = parser.parse_args()

    # 抓取數據
    df = fetch_jsda_data(
        start_year=args.start_year,
        refresh=args.refresh
    )

    if df.empty:
        print("錯誤：無法取得數據", file=sys.stderr)
        sys.exit(1)

    # 執行分析
    result = analyze(df, lookback_months=args.lookback)

    # 輸出結果
    if args.format == "json":
        output = json.dumps(result, ensure_ascii=False, indent=2, default=str)
    else:
        output = format_markdown_report(result)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"結果已保存至: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
