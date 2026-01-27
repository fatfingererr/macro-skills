#!/usr/bin/env python3
"""
CFTC COT 資料抓取腳本

從 CFTC Socrata API 抓取 Commitments of Traders 報告資料。
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlencode

import pandas as pd
import requests

# CFTC Socrata API endpoint
CFTC_API_URL = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"

# CFTC 原生分組對照表（commodity_subgroup_name -> group key）
CFTC_GROUP_MAP = {
    "GRAINS": "grains",
    "OILSEED and PRODUCTS": "oilseeds",
    "LIVESTOCK/MEAT PRODUCTS": "meats",
    "FOODSTUFFS/SOFTS": "softs",
    "FIBER": "fiber",
    "DAIRY PRODUCTS": "dairy",
}

# 所有群組列表
ALL_GROUPS = ["grains", "oilseeds", "meats", "softs", "fiber", "dairy"]


def fetch_cot_from_api(
    start_date: str,
    end_date: str,
    limit: int = 50000,
) -> pd.DataFrame:
    """
    從 CFTC Socrata API 抓取農產品 COT 資料

    Args:
        start_date: 起始日期 (YYYY-MM-DD)
        end_date: 結束日期 (YYYY-MM-DD)
        limit: 最大回傳筆數

    Returns:
        DataFrame with COT data
    """
    # 建構查詢參數
    where_clause = (
        f"commodity_group_name='AGRICULTURE' AND "
        f"report_date_as_yyyy_mm_dd >= '{start_date}' AND "
        f"report_date_as_yyyy_mm_dd <= '{end_date}'"
    )

    params = {
        "$limit": limit,
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$where": where_clause,
    }

    # URL encode 參數
    encoded_params = urlencode(params, safe="$'<>=")
    url = f"{CFTC_API_URL}?{encoded_params}"

    print(f"Fetching COT data from CFTC API...")
    print(f"  Date range: {start_date} to {end_date}")

    response = requests.get(url, timeout=120)
    response.raise_for_status()

    data = response.json()
    print(f"  Records fetched: {len(data)}")

    if not data:
        print("  Warning: No data returned from API")
        return pd.DataFrame()

    df = pd.DataFrame(data)
    return df


def parse_cot_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    解析 COT 資料，提取需要的欄位並計算淨部位

    Args:
        df: Raw DataFrame from API

    Returns:
        Parsed DataFrame with standardized columns
    """
    if df.empty:
        return pd.DataFrame()

    # 提取並重命名欄位
    result = pd.DataFrame({
        "date": pd.to_datetime(df["report_date_as_yyyy_mm_dd"]).dt.date,
        "contract": df["contract_market_name"],
        "cftc_code": df["cftc_contract_market_code"],
        "subgroup_name": df["commodity_subgroup_name"],
        "open_interest": pd.to_numeric(df["open_interest_all"], errors="coerce"),
        "long": pd.to_numeric(df["noncomm_positions_long_all"], errors="coerce"),
        "short": pd.to_numeric(df["noncomm_positions_short_all"], errors="coerce"),
        "spreading": pd.to_numeric(df.get("noncomm_postions_spread_all", 0), errors="coerce"),
    })

    # 映射到標準群組
    result["group"] = result["subgroup_name"].map(CFTC_GROUP_MAP)

    # 過濾掉未知群組
    unknown = result[result["group"].isna()]
    if len(unknown) > 0:
        print(f"  Warning: {len(unknown)} records with unknown subgroup:")
        for sg in unknown["subgroup_name"].unique():
            print(f"    - {sg}")
        result = result[result["group"].notna()].copy()

    # 計算淨部位
    result["net_pos"] = result["long"] - result["short"]

    return result


def calculate_flows(df: pd.DataFrame) -> pd.DataFrame:
    """
    計算資金流（週變化）

    Args:
        df: Parsed COT DataFrame

    Returns:
        DataFrame with flow column added
    """
    if df.empty:
        return df

    df = df.sort_values(["contract", "date"]).copy()

    # 計算每個合約的週變化
    df["flow"] = df.groupby("contract")["net_pos"].diff()

    return df


def aggregate_by_group(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    按群組彙總流量與淨部位

    Args:
        df: COT DataFrame with flows

    Returns:
        Tuple of (flows_df, positions_df) pivoted by group
    """
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # 流量彙總
    flows = df.groupby(["date", "group"])["flow"].sum().unstack(fill_value=0)
    for g in ALL_GROUPS:
        if g not in flows.columns:
            flows[g] = 0
    flows["total"] = flows[ALL_GROUPS].sum(axis=1)

    # 淨部位彙總
    positions = df.groupby(["date", "group"])["net_pos"].sum().unstack(fill_value=0)
    for g in ALL_GROUPS:
        if g not in positions.columns:
            positions[g] = 0
    positions["total"] = positions[ALL_GROUPS].sum(axis=1)

    return flows.sort_index(), positions.sort_index()


def get_latest_week_summary(df: pd.DataFrame) -> Dict:
    """
    取得最新一週的摘要

    Args:
        df: COT DataFrame with flows

    Returns:
        Dictionary with latest week metrics
    """
    if df.empty:
        return {}

    latest_date = df["date"].max()
    latest = df[df["date"] == latest_date]

    # 按群組彙總
    group_summary = latest.groupby("group").agg({
        "net_pos": "sum",
        "flow": "sum",
        "long": "sum",
        "short": "sum",
        "open_interest": "sum",
    }).to_dict("index")

    # 計算總計
    total_net = latest["net_pos"].sum()
    total_flow = latest["flow"].sum()

    return {
        "date": str(latest_date),
        "total_net_pos": int(total_net),
        "total_flow": int(total_flow) if pd.notna(total_flow) else None,
        "by_group": {
            g: {
                "net_pos": int(v["net_pos"]),
                "flow": int(v["flow"]) if pd.notna(v["flow"]) else None,
                "long": int(v["long"]),
                "short": int(v["short"]),
                "open_interest": int(v["open_interest"]),
            }
            for g, v in group_summary.items()
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch CFTC COT data via Socrata API")
    parser.add_argument(
        "--start",
        type=str,
        default=(datetime.now() - timedelta(days=365 * 3)).strftime("%Y-%m-%d"),
        help="Start date (YYYY-MM-DD), default: 3 years ago",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="End date (YYYY-MM-DD), default: today",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="cache/cot_data.parquet",
        help="Output file path",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print latest week summary",
    )

    args = parser.parse_args()

    # 抓取資料
    raw_df = fetch_cot_from_api(args.start, args.end)

    if raw_df.empty:
        print("Error: No data fetched")
        return 1

    # 解析資料
    df = parse_cot_data(raw_df)

    # 計算流量
    df = calculate_flows(df)

    # 確保輸出目錄存在
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 儲存
    df.to_parquet(output_path, index=False)
    print(f"\nCOT data saved to {output_path}")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"  Unique contracts: {df['contract'].nunique()}")
    print(f"  Total records: {len(df)}")

    # 顯示最新週摘要
    if args.summary:
        summary = get_latest_week_summary(df)
        print(f"\n{'='*50}")
        print(f"Latest Week Summary ({summary['date']})")
        print(f"{'='*50}")
        print(f"Total Net Position: {summary['total_net_pos']:,}")
        print(f"Total Weekly Flow:  {summary['total_flow']:,}" if summary['total_flow'] else "Total Weekly Flow:  N/A (first week)")
        print(f"\nBy Group:")
        for g, v in summary.get("by_group", {}).items():
            flow_str = f"{v['flow']:+,}" if v['flow'] is not None else "N/A"
            print(f"  {g:12} | Net: {v['net_pos']:>10,} | Flow: {flow_str:>10} | OI: {v['open_interest']:>12,}")

    return 0


if __name__ == "__main__":
    exit(main())
