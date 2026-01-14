#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BLS 資料抓取模組
使用 BLS Public Data API（無需 API key，但有限制）

限制：
- 每次請求最多 50 個系列
- 每個 IP 每日 500 次請求
- 無 API key 時，歷史資料限 20 年

用法:
    python fetch_bls_data.py --series CUUR0000SA0,CUUR0000SAH1 --start 2020 --end 2024

或作為模組:
    from fetch_bls_data import BLSFetcher
    fetcher = BLSFetcher()
    data = fetcher.fetch_series(['CUUR0000SA0'], 2020, 2024)
"""

import requests
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Union
import time
import random
import json
from pathlib import Path


# BLS 系列代碼對照表
BLS_SERIES_MAP = {
    # CPI-U (All Urban Consumers) - 季節調整
    'cpi_all_sa': 'CUSR0000SA0',           # All items
    'cpi_core_sa': 'CUSR0000SA0L1E',        # All items less food and energy
    'cpi_food_sa': 'CUSR0000SAF1',          # Food
    'cpi_energy_sa': 'CUSR0000SA0E',        # Energy
    'cpi_shelter_sa': 'CUSR0000SAH1',       # Shelter
    'cpi_services_sa': 'CUSR0000SAS',       # Services
    'cpi_medical_sa': 'CUSR0000SAM',        # Medical care

    # CPI-U (Not Seasonally Adjusted) - 用於權重計算
    'cpi_all_nsa': 'CUUR0000SA0',
    'cpi_shelter_nsa': 'CUUR0000SAH1',
    'cpi_medical_nsa': 'CUUR0000SAM',
}


class BLSFetcher:
    """
    BLS 資料抓取器
    使用 Public Data API v2
    """

    BASE_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

    # 模擬人類行為的 User-Agent
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]

    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        初始化 BLS 抓取器

        Args:
            api_key: BLS API key（可選，有 key 可以更多請求）
            cache_dir: 快取目錄路徑
        """
        self.api_key = api_key
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _random_delay(self, min_sec: float = 0.5, max_sec: float = 1.5):
        """模擬人類行為的隨機延遲"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    def _get_headers(self) -> Dict[str, str]:
        """取得 headers"""
        return {
            'Content-type': 'application/json',
            'User-Agent': random.choice(self.USER_AGENTS),
        }

    def _get_cache_path(self, series_id: str, start_year: int, end_year: int) -> Optional[Path]:
        """取得快取檔案路徑"""
        if not self.cache_dir:
            return None
        filename = f"bls_{series_id}_{start_year}_{end_year}.json"
        return self.cache_dir / filename

    def _load_from_cache(self, series_id: str, start_year: int, end_year: int) -> Optional[pd.Series]:
        """從快取載入資料"""
        cache_path = self._get_cache_path(series_id, start_year, end_year)
        if cache_path and cache_path.exists():
            cache_age = time.time() - cache_path.stat().st_mtime
            if cache_age < 86400:  # 24 hours
                try:
                    with open(cache_path, 'r') as f:
                        data = json.load(f)
                    dates = pd.to_datetime(data['dates'])
                    return pd.Series(data['values'], index=dates, name=series_id)
                except:
                    pass
        return None

    def _save_to_cache(self, series: pd.Series, series_id: str, start_year: int, end_year: int):
        """儲存資料到快取"""
        cache_path = self._get_cache_path(series_id, start_year, end_year)
        if cache_path:
            data = {
                'series_id': series_id,
                'dates': series.index.strftime('%Y-%m-%d').tolist(),
                'values': series.values.tolist()
            }
            with open(cache_path, 'w') as f:
                json.dump(data, f)

    def fetch_series(
        self,
        series_ids: Union[str, List[str]],
        start_year: int,
        end_year: int,
        use_cache: bool = True
    ) -> Dict[str, pd.Series]:
        """
        抓取 BLS 序列

        Args:
            series_ids: 系列代碼或列表（最多 50 個）
            start_year: 起始年份
            end_year: 結束年份
            use_cache: 是否使用快取

        Returns:
            {系列代碼: pandas Series} 字典
        """
        # 統一轉換為列表
        if isinstance(series_ids, str):
            series_ids = [series_ids]

        # 檢查快取
        results = {}
        series_to_fetch = []

        for sid in series_ids:
            if use_cache:
                cached = self._load_from_cache(sid, start_year, end_year)
                if cached is not None:
                    print(f"  ✓ {sid}: 從快取載入")
                    results[sid] = cached
                    continue
            series_to_fetch.append(sid)

        if not series_to_fetch:
            return results

        print(f"\n抓取 BLS 資料: {start_year} 至 {end_year}")
        print("-" * 50)

        # 建立請求
        payload = {
            "seriesid": series_to_fetch,
            "startyear": str(start_year),
            "endyear": str(end_year),
        }

        if self.api_key:
            payload["registrationkey"] = self.api_key

        # 隨機延遲
        self._random_delay()

        # 發送請求
        try:
            response = requests.post(
                self.BASE_URL,
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if data.get("status") != "REQUEST_SUCCEEDED":
                print(f"  ✗ BLS API 錯誤: {data.get('message', 'Unknown')}")
                return results

            # 解析結果
            for series_data in data.get("Results", {}).get("series", []):
                series_id = series_data.get("seriesID")
                data_points = series_data.get("data", [])

                if not data_points:
                    print(f"  ✗ {series_id}: 無資料")
                    continue

                # 轉換為 pandas Series
                records = []
                for point in data_points:
                    year = int(point["year"])
                    period = point["period"]

                    # 處理期間代碼（M01-M12 為月份）
                    if period.startswith("M"):
                        month = int(period[1:])
                        date = datetime(year, month, 1)
                        value = float(point["value"])
                        records.append((date, value))

                if records:
                    # 按日期排序
                    records.sort(key=lambda x: x[0])
                    dates, values = zip(*records)
                    series = pd.Series(values, index=pd.DatetimeIndex(dates), name=series_id)

                    results[series_id] = series
                    print(f"  ✓ {series_id}: 獲取 {len(series)} 筆資料")

                    # 儲存到快取
                    if use_cache:
                        self._save_to_cache(series, series_id, start_year, end_year)

        except Exception as e:
            print(f"  ✗ BLS API 請求失敗: {e}")

        return results

    def fetch_cpi_data(
        self,
        start_year: int,
        end_year: int
    ) -> Dict[str, pd.Series]:
        """
        抓取 CPI 相關完整資料

        Args:
            start_year: 起始年份
            end_year: 結束年份

        Returns:
            包含所有 CPI 序列的字典
        """
        series_to_fetch = [
            'CUSR0000SA0',      # CPI All items SA
            'CUSR0000SA0L1E',   # CPI Core SA
            'CUSR0000SAH1',     # CPI Shelter SA
            'CUSR0000SAM',      # CPI Medical SA
            'CUSR0000SAS',      # CPI Services SA
            'CUSR0000SAF1',     # CPI Food SA
            'CUSR0000SA0E',     # CPI Energy SA
        ]

        return self.fetch_series(series_to_fetch, start_year, end_year)

    def get_relative_importance(self, year: int) -> Dict[str, float]:
        """
        取得 CPI 相對重要性（權重）

        注意：BLS 每年 12 月發布 Relative Importance
        這裡提供近似值，實際值需要從 BLS 網站或報告取得

        Args:
            year: 年份

        Returns:
            {分項: 權重} 字典
        """
        # 近似值（基於 2024 年數據）
        # 實際值會隨年份變化
        weights = {
            'all_items': 100.0,
            'food': 13.5,
            'energy': 6.9,
            'core': 79.6,
            'shelter': 36.2,
            'medical_care': 7.3,
            'services': 62.3,
            'commodities': 20.9,
        }

        print(f"⚠️ 注意：CPI 權重為 {year} 年近似值，實際值請參考 BLS 報告")
        return weights


def main():
    """主程式：命令列介面"""
    import argparse

    parser = argparse.ArgumentParser(description='BLS 資料抓取工具')
    parser.add_argument('--series', type=str, help='BLS 系列代碼（逗號分隔）')
    parser.add_argument('--start', type=int, default=2020, help='起始年份')
    parser.add_argument('--end', type=int, default=datetime.now().year, help='結束年份')
    parser.add_argument('--output', type=str, default='bls_data.json', help='輸出檔案')
    parser.add_argument('--cache-dir', type=str, help='快取目錄')
    parser.add_argument('--api-key', type=str, help='BLS API key')
    parser.add_argument('--full', action='store_true', help='抓取完整 CPI 資料')

    args = parser.parse_args()

    fetcher = BLSFetcher(api_key=args.api_key, cache_dir=args.cache_dir)

    if args.full:
        data = fetcher.fetch_cpi_data(args.start, args.end)
    elif args.series:
        series_list = [s.strip() for s in args.series.split(',')]
        data = fetcher.fetch_series(series_list, args.start, args.end)
    else:
        print("請指定 --series 或使用 --full")
        return

    # 轉換為可序列化格式
    output_data = {
        'fetch_time': datetime.now().isoformat(),
        'start_year': args.start,
        'end_year': args.end,
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
