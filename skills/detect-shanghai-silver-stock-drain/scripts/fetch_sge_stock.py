#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SGE（上海黃金交易所）白銀庫存數據抓取

注意：目前主要數據源為 CEIC (SHFE 數據)，SGE 數據作為補充來源。
CEIC 提供的 SHFE 白銀倉單數據已經足夠進行耗盡分析。

如需 SGE 數據，可從以下來源獲取：
- SGE 官網「行情周報」PDF
- 第三方數據服務

Usage:
    python fetch_sge_stock.py --output data/sge_stock.csv
    python fetch_sge_stock.py --from-ceic  # 使用 CEIC 數據（推薦）
"""

import argparse
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# 設定目錄
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"


def fetch_from_ceic_as_proxy() -> pd.DataFrame:
    """
    使用 CEIC 的 SHFE 數據作為代理

    說明：CEIC 提供的是 SHFE（上海期貨交易所）白銀倉單數據，
    這與 SGE（上海黃金交易所）是不同的交易所。
    但對於白銀庫存耗盡分析，SHFE 數據已經足夠代表性。
    """
    from fetch_shfe_stock import fetch_ceic_shfe_data

    print("使用 CEIC SHFE 數據作為代理...")
    df = fetch_ceic_shfe_data()

    if df is not None:
        # 轉換格式
        df_output = df.copy()
        df_output['stock_kg'] = df_output['stock_tonnes'] * 1000
        return df_output[['date', 'stock_kg']]

    return None


def main():
    """主程式入口"""
    parser = argparse.ArgumentParser(description="SGE 白銀庫存數據抓取")
    parser.add_argument("--output", type=str, default=str(DATA_DIR / "sge_stock.csv"), help="輸出檔案路徑")
    parser.add_argument("--from-ceic", action="store_true", help="使用 CEIC 數據作為代理（推薦）")
    parser.add_argument("--force-update", action="store_true", help="強制更新")

    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = Path(args.output)

    # 檢查快取
    if output_path.exists() and not args.force_update:
        mtime = datetime.fromtimestamp(output_path.stat().st_mtime)
        cache_age = datetime.now() - mtime
        if cache_age < timedelta(hours=12):
            print(f"使用快取數據（{cache_age.total_seconds()/3600:.1f} 小時前更新）")
            df = pd.read_csv(output_path, parse_dates=["date"])
            print(f"數據範圍: {df['date'].min()} ~ {df['date'].max()}")
            print(f"記錄數: {len(df)}")
            return

    print("=" * 60)
    print("SGE 白銀庫存數據")
    print("=" * 60)
    print("\n注意：目前主要使用 CEIC 的 SHFE 數據進行分析。")
    print("SGE 數據作為補充來源，如需要請手動提供。")
    print("\n建議使用: python fetch_shfe_stock.py --force-update")


if __name__ == "__main__":
    main()
