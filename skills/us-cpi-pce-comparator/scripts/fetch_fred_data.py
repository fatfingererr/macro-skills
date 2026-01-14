#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FRED 資料抓取模組
使用 FRED CSV endpoint（無需 API key）

用法:
    python fetch_fred_data.py --series CPIAUCSL,PCEPI --start 2020-01-01 --end 2024-12-01

或作為模組:
    from fetch_fred_data import FREDFetcher
    fetcher = FREDFetcher()
    data = fetcher.fetch_series(['CPIAUCSL', 'PCEPI'], '2020-01-01', '2024-12-01')
"""

import requests
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Union
from io import StringIO
import time
import random
import json
from pathlib import Path


# FRED 系列代碼對照表
FRED_SERIES_MAP = {
    # Headline Indexes
    'cpi_headline': 'CPIAUCSL',
    'pce_headline': 'PCEPI',

    # Core Indexes
    'cpi_core': 'CPILFESL',
    'pce_core': 'PCEPILFE',

    # PCE Components (Price Indexes)
    'pce_goods': 'DGDSRG3M086SBEA',
    'pce_services': 'DSERRG3M086SBEA',
    'pce_durable_goods': 'DDURRG3M086SBEA',
    'pce_nondurable_goods': 'DNDGRG3M086SBEA',
    'pce_housing': 'DHUTRG3M086SBEA',  # Housing and utilities
    'pce_medical': 'DHLCRG3M086SBEA',   # Health care

    # CPI Components
    'cpi_shelter': 'CUSR0000SAH1',
    'cpi_medical': 'CUSR0000SAM',
    'cpi_services': 'CUSR0000SAS',
    'cpi_food': 'CUSR0000SAF1',
    'cpi_energy': 'CUSR0000SA0E',

    # PCE Nominal (for weights)
    'pce_nominal_total': 'PCE',
    'pce_nominal_goods': 'PCEDG',
    'pce_nominal_services': 'PCES',
}


class FREDFetcher:
    """
    FRED 資料抓取器
    使用 CSV endpoint 無需 API key
    """

    BASE_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

    # 模擬人類行為的 User-Agent
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    ]

    def __init__(self, cache_dir: Optional[str] = None):
        """
        初始化 FRED 抓取器

        Args:
            cache_dir: 快取目錄路徑，預設為 None（不快取）
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _random_delay(self, min_sec: float = 0.3, max_sec: float = 1.0):
        """模擬人類行為的隨機延遲"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    def _get_headers(self) -> Dict[str, str]:
        """取得隨機 headers"""
        return {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/csv,text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

    def _get_cache_path(self, series_id: str, start_date: str, end_date: str) -> Path:
        """取得快取檔案路徑"""
        if not self.cache_dir:
            return None
        filename = f"{series_id}_{start_date}_{end_date}.csv"
        return self.cache_dir / filename

    def _load_from_cache(self, series_id: str, start_date: str, end_date: str) -> Optional[pd.Series]:
        """從快取載入資料"""
        cache_path = self._get_cache_path(series_id, start_date, end_date)
        if cache_path and cache_path.exists():
            # 檢查快取是否過期（1天）
            cache_age = time.time() - cache_path.stat().st_mtime
            if cache_age < 86400:  # 24 hours
                try:
                    df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                    return df.iloc[:, 0]
                except:
                    pass
        return None

    def _save_to_cache(self, series: pd.Series, series_id: str, start_date: str, end_date: str):
        """儲存資料到快取"""
        cache_path = self._get_cache_path(series_id, start_date, end_date)
        if cache_path:
            series.to_frame(series_id).to_csv(cache_path)

    def fetch_single_series(
        self,
        series_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True
    ) -> pd.Series:
        """
        抓取單一 FRED 序列

        Args:
            series_id: FRED 系列代碼（如 CPIAUCSL）
            start_date: 起始日期（YYYY-MM-DD）
            end_date: 結束日期（YYYY-MM-DD）
            use_cache: 是否使用快取

        Returns:
            pandas Series，index 為日期
        """
        # 嘗試從快取載入
        if use_cache and start_date and end_date:
            cached = self._load_from_cache(series_id, start_date, end_date)
            if cached is not None:
                print(f"  ✓ {series_id}: 從快取載入")
                return cached

        # 建立 URL
        params = {'id': series_id}
        if start_date:
            params['cosd'] = start_date
        if end_date:
            params['coed'] = end_date

        url = f"{self.BASE_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

        # 隨機延遲
        self._random_delay()

        # 發送請求
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()

            # 解析 CSV
            df = pd.read_csv(
                StringIO(response.text),
                index_col=0,
                parse_dates=True,
                na_values=['.']
            )

            if df.empty:
                print(f"  ✗ {series_id}: 無資料")
                return pd.Series(dtype=float)

            series = df.iloc[:, 0]
            series.name = series_id

            # 儲存到快取
            if use_cache and start_date and end_date:
                self._save_to_cache(series, series_id, start_date, end_date)

            print(f"  ✓ {series_id}: 獲取 {len(series)} 筆資料")
            return series

        except Exception as e:
            print(f"  ✗ {series_id}: 抓取失敗 - {e}")
            return pd.Series(dtype=float)

    def fetch_series(
        self,
        series_ids: Union[List[str], Dict[str, str]],
        start_date: str,
        end_date: str,
        use_cache: bool = True
    ) -> Dict[str, pd.Series]:
        """
        批次抓取多個 FRED 序列

        Args:
            series_ids: 系列代碼列表或 {名稱: 代碼} 字典
            start_date: 起始日期
            end_date: 結束日期
            use_cache: 是否使用快取

        Returns:
            {系列代碼: pandas Series} 字典
        """
        print(f"\n抓取 FRED 資料: {start_date} 至 {end_date}")
        print("-" * 50)

        # 統一轉換為字典
        if isinstance(series_ids, list):
            series_dict = {sid: sid for sid in series_ids}
        else:
            series_dict = series_ids

        results = {}
        for name, series_id in series_dict.items():
            series = self.fetch_single_series(series_id, start_date, end_date, use_cache)
            if not series.empty:
                results[name] = series

        print(f"\n成功抓取 {len(results)}/{len(series_dict)} 個序列")
        return results

    def fetch_cpi_pce_data(
        self,
        start_date: str,
        end_date: str,
        include_components: bool = True
    ) -> Dict[str, pd.Series]:
        """
        抓取 CPI/PCE 比較分析所需的完整資料

        Args:
            start_date: 起始日期
            end_date: 結束日期
            include_components: 是否包含分項資料

        Returns:
            包含所有序列的字典
        """
        # 基本序列
        series_to_fetch = {
            'cpi_headline': 'CPIAUCSL',
            'pce_headline': 'PCEPI',
            'cpi_core': 'CPILFESL',
            'pce_core': 'PCEPILFE',
        }

        # 加入分項
        if include_components:
            series_to_fetch.update({
                # PCE 分項
                'pce_goods': 'DGDSRG3M086SBEA',
                'pce_services': 'DSERRG3M086SBEA',
                'pce_housing': 'DHUTRG3M086SBEA',
                'pce_medical': 'DHLCRG3M086SBEA',

                # CPI 分項
                'cpi_shelter': 'CUSR0000SAH1',
                'cpi_services': 'CUSR0000SAS',

                # PCE 名目值（用於計算權重）
                'pce_nominal_total': 'PCE',
                'pce_nominal_goods': 'PCEDG',
                'pce_nominal_services': 'PCES',
            })

        return self.fetch_series(series_to_fetch, start_date, end_date)


def main():
    """主程式：命令列介面"""
    import argparse

    parser = argparse.ArgumentParser(description='FRED 資料抓取工具')
    parser.add_argument('--series', type=str, help='FRED 系列代碼（逗號分隔）')
    parser.add_argument('--start', type=str, default='2020-01-01', help='起始日期')
    parser.add_argument('--end', type=str, default=datetime.now().strftime('%Y-%m-%d'), help='結束日期')
    parser.add_argument('--output', type=str, default='fred_data.json', help='輸出檔案')
    parser.add_argument('--cache-dir', type=str, help='快取目錄')
    parser.add_argument('--full', action='store_true', help='抓取完整 CPI/PCE 資料')

    args = parser.parse_args()

    fetcher = FREDFetcher(cache_dir=args.cache_dir)

    if args.full:
        # 抓取完整資料
        data = fetcher.fetch_cpi_pce_data(args.start, args.end)
    elif args.series:
        # 抓取指定序列
        series_list = [s.strip() for s in args.series.split(',')]
        data = fetcher.fetch_series(series_list, args.start, args.end)
    else:
        print("請指定 --series 或使用 --full")
        return

    # 轉換為可序列化格式
    output_data = {
        'fetch_time': datetime.now().isoformat(),
        'start_date': args.start,
        'end_date': args.end,
        'series': {}
    }

    for name, series in data.items():
        output_data['series'][name] = {
            'dates': series.index.strftime('%Y-%m-%d').tolist(),
            'values': series.values.tolist()
        }

    # 輸出
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n資料已儲存至: {args.output}")


if __name__ == '__main__':
    main()
