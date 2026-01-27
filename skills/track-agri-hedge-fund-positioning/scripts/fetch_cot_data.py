#!/usr/bin/env python3
"""
CFTC COT 資料抓取腳本

從 CFTC 官網抓取 Commitments of Traders 報告資料。
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

# 預設合約對照表
DEFAULT_CONTRACTS_MAP = {
    "CORN": "grains",
    "WHEAT-SRW": "grains",
    "WHEAT-HRW": "grains",
    "SOYBEANS": "oilseeds",
    "SOYBEAN OIL": "oilseeds",
    "SOYBEAN MEAL": "oilseeds",
    "LIVE CATTLE": "meats",
    "LEAN HOGS": "meats",
    "FEEDER CATTLE": "meats",
    "COFFEE C": "softs",
    "SUGAR NO. 11": "softs",
    "COCOA": "softs",
    "COTTON NO. 2": "softs",
}

# CFTC COT 下載 URL
COT_URLS = {
    "legacy": {
        "current": "https://www.cftc.gov/dea/newcot/deafut.txt",
        "history": "https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip",
    },
    "disaggregated": {
        "current": "https://www.cftc.gov/dea/newcot/f_disagg.txt",
        "history": "https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip",
    },
}


def fetch_cot_current(report_type: str = "legacy") -> pd.DataFrame:
    """抓取當年 COT 資料"""
    url = COT_URLS[report_type]["current"]

    print(f"Fetching current COT data from {url}...")

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    df = pd.read_csv(StringIO(response.text))
    return df


def parse_cot_legacy(df: pd.DataFrame, contracts_map: dict = None) -> pd.DataFrame:
    """解析 Legacy COT 資料"""
    if contracts_map is None:
        contracts_map = DEFAULT_CONTRACTS_MAP

    # 標準化欄位名稱
    df.columns = df.columns.str.strip()

    # 提取農產品
    agri_keywords = list(contracts_map.keys())

    def match_contract(name):
        name_upper = str(name).upper()
        for keyword in agri_keywords:
            if keyword in name_upper:
                return keyword
        return None

    df["contract"] = df["Market_and_Exchange_Names"].apply(match_contract)
    df = df[df["contract"].notna()].copy()

    # 解析日期
    df["date"] = pd.to_datetime(df["As_of_Date_In_Form_YYMMDD"], format="%y%m%d")

    # 提取需要的欄位
    result = df[
        [
            "date",
            "contract",
            "Open_Interest_All",
            "NonComm_Positions_Long_All",
            "NonComm_Positions_Short_All",
            "NonComm_Positions_Spread_All",
        ]
    ].copy()

    result.columns = ["date", "contract", "open_interest", "long", "short", "spreading"]

    # 加入群組
    result["group"] = result["contract"].map(contracts_map)

    return result


def calculate_flows(df: pd.DataFrame, metric: str = "net") -> pd.DataFrame:
    """計算資金流"""
    df = df.sort_values(["contract", "date"]).copy()

    # 計算部位
    if metric == "net":
        df["pos"] = df["long"] - df["short"]
    elif metric == "long":
        df["pos"] = df["long"]
    elif metric == "short":
        df["pos"] = df["short"]

    # 計算流量（週變化）
    df["flow"] = df.groupby("contract")["pos"].diff()

    return df


def aggregate_by_group(df: pd.DataFrame) -> pd.DataFrame:
    """按群組彙總"""
    # 流量彙總
    flows = df.groupby(["date", "group"])["flow"].sum().unstack(fill_value=0)

    # 確保所有群組存在
    for group in ["grains", "oilseeds", "meats", "softs"]:
        if group not in flows.columns:
            flows[group] = 0

    flows["total"] = flows[["grains", "oilseeds", "meats", "softs"]].sum(axis=1)

    # 淨部位彙總
    positions = df.groupby(["date", "group"])["pos"].sum().unstack(fill_value=0)
    for group in ["grains", "oilseeds", "meats", "softs"]:
        if group not in positions.columns:
            positions[group] = 0
    positions["total"] = positions[["grains", "oilseeds", "meats", "softs"]].sum(axis=1)

    return flows, positions


def main():
    parser = argparse.ArgumentParser(description="Fetch CFTC COT data")
    parser.add_argument(
        "--report",
        type=str,
        default="legacy",
        choices=["legacy", "disaggregated"],
        help="COT report type",
    )
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--output", type=str, default="cache/cot_data.parquet", help="Output file path"
    )
    parser.add_argument(
        "--contracts-map", type=str, help="JSON file with contracts map"
    )

    args = parser.parse_args()

    # 載入合約對照表
    contracts_map = DEFAULT_CONTRACTS_MAP
    if args.contracts_map:
        with open(args.contracts_map, "r") as f:
            contracts_map = json.load(f)

    # 抓取資料
    raw_df = fetch_cot_current(args.report)

    # 解析資料
    if args.report == "legacy":
        df = parse_cot_legacy(raw_df, contracts_map)
    else:
        raise NotImplementedError(f"Report type {args.report} not yet implemented")

    # 過濾日期
    if args.start:
        df = df[df["date"] >= args.start]
    if args.end:
        df = df[df["date"] <= args.end]

    # 計算流量
    df = calculate_flows(df)

    # 確保輸出目錄存在
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 儲存
    df.to_parquet(output_path, index=False)
    print(f"COT data saved to {output_path}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Contracts: {df['contract'].nunique()}")
    print(f"Records: {len(df)}")


if __name__ == "__main__":
    main()
