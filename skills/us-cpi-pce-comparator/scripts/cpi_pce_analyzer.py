#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CPI-PCE Comparator 核心分析模組

此模組整合 FRED 和 BLS 資料，執行 CPI/PCE 通膨比較分析。

主要功能：
1. 計算通膨率（YoY, MoM SAAR, QoQ SAAR）
2. 識別低波動高權重桶位
3. 計算加權通膨與權重效應
4. 產生分析報告

用法:
    python cpi_pce_analyzer.py --start 2020-01-01 --end 2024-12-01 --measure yoy

或作為模組:
    from cpi_pce_analyzer import CPIPCEAnalyzer
    analyzer = CPIPCEAnalyzer()
    result = analyzer.analyze('2020-01-01', '2024-12-01', measure='yoy')
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Literal, Any, Tuple
import json
from pathlib import Path

# 本地模組
try:
    from fetch_fred_data import FREDFetcher
    from fetch_bls_data import BLSFetcher
except ImportError:
    # 如果直接運行，需要調整路徑
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from fetch_fred_data import FREDFetcher
    from fetch_bls_data import BLSFetcher


class InflationCalculator:
    """通膨率計算器"""

    @staticmethod
    def yoy(series: pd.Series) -> pd.Series:
        """計算年增率 (Year-over-Year)"""
        return series.pct_change(12) * 100

    @staticmethod
    def mom_saar(series: pd.Series) -> pd.Series:
        """計算月增年化率 (Month-over-Month SAAR)"""
        mom = series.pct_change(1)
        return ((1 + mom) ** 12 - 1) * 100

    @staticmethod
    def qoq_saar(series: pd.Series) -> pd.Series:
        """計算季增年化率 (Quarter-over-Quarter SAAR)"""
        qoq = series.pct_change(3)
        return ((1 + qoq) ** 4 - 1) * 100

    @classmethod
    def calculate(cls, series: pd.Series, measure: str) -> pd.Series:
        """
        計算指定類型的通膨率

        Args:
            series: 價格指數序列
            measure: 'yoy' | 'mom_saar' | 'qoq_saar'
        """
        if measure == 'yoy':
            return cls.yoy(series)
        elif measure == 'mom_saar':
            return cls.mom_saar(series)
        elif measure == 'qoq_saar':
            return cls.qoq_saar(series)
        else:
            raise ValueError(f"不支援的通膨計算方式: {measure}")


class VolatilityAnalyzer:
    """波動度分析器"""

    @staticmethod
    def rolling_std(series: pd.Series, window: int = 24) -> pd.Series:
        """計算滾動標準差"""
        return series.rolling(window).std()

    @staticmethod
    def identify_low_vol_buckets(
        inflation_dict: Dict[str, pd.Series],
        weights: Dict[str, float],
        vol_window: int = 24,
        vol_quantile: float = 0.4
    ) -> List[Dict]:
        """
        識別低波動高權重桶位

        Args:
            inflation_dict: {桶位名: 通膨序列}
            weights: {桶位名: 權重}
            vol_window: 波動度計算視窗（月）
            vol_quantile: 低波動分位數門檻

        Returns:
            低波動高權重桶位列表
        """
        # 計算各桶的波動度
        volatility = {}
        for bucket, series in inflation_dict.items():
            vol = series.rolling(vol_window).std().iloc[-1]
            if not pd.isna(vol):
                volatility[bucket] = vol

        if not volatility:
            return []

        # 計算波動度門檻
        vol_values = list(volatility.values())
        vol_threshold = np.quantile(vol_values, vol_quantile)

        # 計算權重中位數
        weight_values = [weights.get(b, 0) for b in volatility.keys()]
        weight_median = np.median(weight_values) if weight_values else 0

        # 篩選低波動高權重桶位
        candidates = []
        for bucket in volatility:
            vol = volatility[bucket]
            weight = weights.get(bucket, 0)

            if vol <= vol_threshold and weight > weight_median:
                # 計算最新通膨與動能
                series = inflation_dict[bucket]
                latest = series.iloc[-1] if len(series) > 0 else None
                momentum_3m = (series.iloc[-1] - series.iloc[-4]) if len(series) > 3 else None

                candidates.append({
                    'bucket': bucket,
                    'volatility': round(vol, 4),
                    'weight': round(weight, 4),
                    'latest_inflation': round(latest, 2) if latest else None,
                    'momentum_3m': round(momentum_3m, 2) if momentum_3m else None,
                    'signal': 'upside' if momentum_3m and momentum_3m > 0 else 'neutral'
                })

        # 按權重排序
        candidates.sort(key=lambda x: x['weight'], reverse=True)
        return candidates


class CPIPCEAnalyzer:
    """
    CPI-PCE 比較分析器

    核心分析類，整合資料抓取與分析邏輯。
    """

    # PCE 權重近似值（基於 BEA 2024 數據）
    DEFAULT_PCE_WEIGHTS = {
        'pce_goods': 0.31,
        'pce_services': 0.69,
        'pce_housing': 0.18,
        'pce_medical': 0.17,
        'pce_durable_goods': 0.11,
        'pce_nondurable_goods': 0.20,
    }

    # CPI 權重近似值（基於 BLS 2024 數據）
    DEFAULT_CPI_WEIGHTS = {
        'cpi_shelter': 0.36,
        'cpi_services': 0.62,
        'cpi_medical': 0.07,
        'cpi_food': 0.14,
        'cpi_energy': 0.07,
    }

    def __init__(self, cache_dir: Optional[str] = None):
        """
        初始化分析器

        Args:
            cache_dir: 快取目錄
        """
        self.fred_fetcher = FREDFetcher(cache_dir=cache_dir)
        self.bls_fetcher = BLSFetcher(cache_dir=cache_dir)
        self.cache_dir = cache_dir

    def fetch_data(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, pd.Series]:
        """
        抓取分析所需的所有資料

        Args:
            start_date: 起始日期
            end_date: 結束日期

        Returns:
            包含所有序列的字典
        """
        # 抓取 FRED 資料（主要來源）
        fred_data = self.fred_fetcher.fetch_cpi_pce_data(start_date, end_date)

        return fred_data

    def calculate_headline_divergence(
        self,
        data: Dict[str, pd.Series],
        measure: str
    ) -> Dict[str, float]:
        """
        計算 Headline level 的 CPI/PCE 分歧

        Args:
            data: 資料字典
            measure: 通膨計算方式

        Returns:
            分歧數據
        """
        cpi = data.get('cpi_headline')
        pce = data.get('pce_headline')
        cpi_core = data.get('cpi_core')
        pce_core = data.get('pce_core')

        result = {}

        # Headline
        if cpi is not None and pce is not None:
            cpi_inf = InflationCalculator.calculate(cpi, measure).iloc[-1]
            pce_inf = InflationCalculator.calculate(pce, measure).iloc[-1]
            result['cpi_headline'] = round(cpi_inf, 2)
            result['pce_headline'] = round(pce_inf, 2)
            result['headline_gap_bps'] = round((pce_inf - cpi_inf) * 100, 0)

        # Core
        if cpi_core is not None and pce_core is not None:
            cpi_core_inf = InflationCalculator.calculate(cpi_core, measure).iloc[-1]
            pce_core_inf = InflationCalculator.calculate(pce_core, measure).iloc[-1]
            result['cpi_core'] = round(cpi_core_inf, 2)
            result['pce_core'] = round(pce_core_inf, 2)
            result['core_gap_bps'] = round((pce_core_inf - cpi_core_inf) * 100, 0)

        return result

    def calculate_bucket_contributions(
        self,
        data: Dict[str, pd.Series],
        measure: str,
        weights: Optional[Dict[str, float]] = None
    ) -> List[Dict]:
        """
        計算各桶位的加權通膨貢獻

        Args:
            data: 資料字典
            measure: 通膨計算方式
            weights: 權重字典（預設使用 PCE 權重）

        Returns:
            貢獻列表
        """
        if weights is None:
            weights = self.DEFAULT_PCE_WEIGHTS

        contributions = []

        for bucket, weight in weights.items():
            if bucket in data:
                series = data[bucket]
                inflation = InflationCalculator.calculate(series, measure).iloc[-1]

                if not pd.isna(inflation):
                    contribution = weight * inflation
                    contributions.append({
                        'bucket': bucket,
                        'weight': round(weight, 4),
                        'inflation': round(inflation, 2),
                        'contribution': round(contribution, 4)
                    })

        # 按貢獻排序
        contributions.sort(key=lambda x: abs(x['contribution']), reverse=True)
        return contributions

    def calculate_weight_effect(
        self,
        data: Dict[str, pd.Series],
        measure: str,
        pce_weights: Optional[Dict[str, float]] = None,
        cpi_weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        計算權重效應（PCE 動態權重 vs CPI 固定權重）

        Args:
            data: 資料字典
            measure: 通膨計算方式
            pce_weights: PCE 權重
            cpi_weights: CPI 權重

        Returns:
            權重效應（bps）
        """
        if pce_weights is None:
            pce_weights = self.DEFAULT_PCE_WEIGHTS
        if cpi_weights is None:
            cpi_weights = self.DEFAULT_CPI_WEIGHTS

        # 找出共同桶位
        common_buckets = set(pce_weights.keys()) & set(cpi_weights.keys()) & set(data.keys())

        weight_effect = 0.0
        for bucket in common_buckets:
            series = data[bucket]
            inflation = InflationCalculator.calculate(series, measure).iloc[-1]

            if not pd.isna(inflation):
                delta_weight = pce_weights[bucket] - cpi_weights.get(bucket, 0)
                weight_effect += delta_weight * inflation

        return round(weight_effect * 100, 0)  # 轉換為 bps

    def apply_baseline_adjustment(
        self,
        series: pd.Series,
        baseline_start: str,
        baseline_end: str,
        mode: str = 'subtract_mean'
    ) -> pd.Series:
        """
        應用 Baseline 調整

        Args:
            series: 通膨序列
            baseline_start: 基準期起始
            baseline_end: 基準期結束
            mode: 'subtract_mean' 或 'subtract_end'

        Returns:
            調整後的序列
        """
        mask = (series.index >= baseline_start) & (series.index <= baseline_end)
        baseline_data = series[mask]

        if baseline_data.empty:
            return series

        if mode == 'subtract_mean':
            baseline_level = baseline_data.mean()
        else:  # subtract_end
            baseline_level = baseline_data.iloc[-1]

        return series - baseline_level

    def analyze(
        self,
        start_date: str,
        end_date: str,
        measure: str = 'yoy',
        focus_buckets: Optional[List[str]] = None,
        baseline_period: Optional[Dict[str, str]] = None,
        vol_window_months: int = 24,
        signal_thresholds: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        執行完整的 CPI-PCE 比較分析

        Args:
            start_date: 起始日期
            end_date: 結束日期
            measure: 通膨計算方式
            focus_buckets: 聚焦桶位列表
            baseline_period: 基準期設定
            vol_window_months: 波動度視窗
            signal_thresholds: 訊號門檻

        Returns:
            完整分析結果
        """
        print("=" * 60)
        print("CPI-PCE Comparator Analysis")
        print(f"期間: {start_date} 至 {end_date}")
        print(f"計算方式: {measure}")
        print("=" * 60)

        # 1. 抓取資料
        print("\n[Step 1] 抓取資料...")
        data = self.fetch_data(start_date, end_date)

        if not data:
            return {"error": "無法取得資料"}

        # 2. 計算 Headline 分歧
        print("\n[Step 2] 計算 Headline 分歧...")
        headline = self.calculate_headline_divergence(data, measure)

        # 3. 計算桶位通膨
        print("\n[Step 3] 計算桶位通膨...")
        bucket_data = {}
        for key, series in data.items():
            if key.startswith('pce_') or key.startswith('cpi_'):
                bucket_data[key] = InflationCalculator.calculate(series, measure)

        # 4. 識別低波動高權重桶位
        print("\n[Step 4] 識別低波動高權重桶位...")
        pce_buckets = {k: v for k, v in bucket_data.items() if k.startswith('pce_')}
        low_vol_buckets = VolatilityAnalyzer.identify_low_vol_buckets(
            pce_buckets,
            self.DEFAULT_PCE_WEIGHTS,
            vol_window_months
        )

        # 5. 計算貢獻
        print("\n[Step 5] 計算各桶貢獻...")
        contributions = self.calculate_bucket_contributions(data, measure)

        # 6. 計算權重效應
        weight_effect = self.calculate_weight_effect(data, measure)

        # 7. Baseline 調整（如有）
        baseline_result = None
        if baseline_period and baseline_period.get('range'):
            print("\n[Step 6] 應用 Baseline 調整...")
            base_range = baseline_period['range'].split(':')
            if len(base_range) == 2:
                base_start, base_end = base_range
                mode = baseline_period.get('mode', 'subtract_mean')

                # 對 PCE core 做 baseline 調整
                pce_core_inf = bucket_data.get('pce_core')
                if pce_core_inf is not None:
                    adjusted = self.apply_baseline_adjustment(
                        pce_core_inf, base_start, base_end, mode
                    )
                    baseline_result = {
                        'baseline_range': baseline_period['range'],
                        'mode': mode,
                        'latest_deviation': round(adjusted.iloc[-1], 2) if not adjusted.empty else None
                    }

        # 8. 組裝結果
        print("\n[Step 7] 組裝分析結果...")
        result = {
            'metadata': {
                'analysis_time': datetime.now().isoformat(),
                'start_date': start_date,
                'end_date': end_date,
                'measure': measure,
                'as_of_date': data.get('pce_headline', pd.Series()).index[-1].strftime('%Y-%m-%d')
                    if 'pce_headline' in data and len(data['pce_headline']) > 0 else None
            },
            'headline': headline,
            'low_vol_high_weight_buckets': low_vol_buckets,
            'attribution': {
                'top_contributors': contributions[:5],
                'weight_effect_bps': weight_effect
            },
            'interpretation': self._generate_interpretation(headline, low_vol_buckets, weight_effect),
            'caveats': [
                "權重為近似值，基於 BEA/BLS 2024 年數據",
                "部分桶位對應可能有誤差",
                "此為權重效應的工程近似，非完整 BEA/BLS 方法論調和"
            ]
        }

        if baseline_result:
            result['baseline_adjustment'] = baseline_result

        print("\n" + "=" * 60)
        print("分析完成！")
        print("=" * 60)

        return result

    def _generate_interpretation(
        self,
        headline: Dict,
        low_vol_buckets: List[Dict],
        weight_effect: float
    ) -> List[str]:
        """生成解讀文字"""
        interpretations = []

        # Headline 解讀
        gap = headline.get('headline_gap_bps', 0)
        if gap > 0:
            interpretations.append(
                f"PCE 通膨高於 CPI 約 {abs(gap):.0f} bps，Fed 關注的通膨指標比 CPI 更具黏性。"
            )
        elif gap < 0:
            interpretations.append(
                f"PCE 通膨低於 CPI 約 {abs(gap):.0f} bps，罕見情況，可能與能源/食品價格波動有關。"
            )

        # 低波動高權重桶位解讀
        upside_buckets = [b for b in low_vol_buckets if b.get('signal') == 'upside']
        if upside_buckets:
            bucket_names = ', '.join([b['bucket'] for b in upside_buckets])
            interpretations.append(
                f"低波動高權重桶位 ({bucket_names}) 顯示上行訊號，若趨勢延續將推升 PCE。"
            )

        # 權重效應解讀
        if abs(weight_effect) > 10:
            direction = "上行" if weight_effect > 0 else "下行"
            interpretations.append(
                f"權重效應貢獻約 {abs(weight_effect):.0f} bps 的 {direction}壓力。"
            )

        # 風險提示
        interpretations.append(
            "監控重點：core_goods 和 core_services_ex_housing 的 3M 動能 vs 12M 趨勢。"
        )

        return interpretations

    def quick_check(self) -> Dict[str, Any]:
        """
        快速檢查最新 CPI/PCE 分歧

        Returns:
            簡要分析結果
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now().replace(year=datetime.now().year - 2)).strftime('%Y-%m-%d')

        # 只抓取 headline 資料
        data = {
            'cpi_headline': self.fred_fetcher.fetch_single_series('CPIAUCSL', start_date, end_date),
            'pce_headline': self.fred_fetcher.fetch_single_series('PCEPI', start_date, end_date),
            'cpi_core': self.fred_fetcher.fetch_single_series('CPILFESL', start_date, end_date),
            'pce_core': self.fred_fetcher.fetch_single_series('PCEPILFE', start_date, end_date),
        }

        # 計算 YoY
        result = {
            'as_of': end_date,
            'headline': {},
            'core': {},
            'momentum': {}
        }

        # Headline YoY
        if 'cpi_headline' in data and 'pce_headline' in data:
            cpi_yoy = InflationCalculator.yoy(data['cpi_headline']).iloc[-1]
            pce_yoy = InflationCalculator.yoy(data['pce_headline']).iloc[-1]
            result['headline'] = {
                'cpi_yoy': round(cpi_yoy, 2),
                'pce_yoy': round(pce_yoy, 2),
                'gap_bps': round((pce_yoy - cpi_yoy) * 100, 0)
            }

        # Core YoY
        if 'cpi_core' in data and 'pce_core' in data:
            cpi_core_yoy = InflationCalculator.yoy(data['cpi_core']).iloc[-1]
            pce_core_yoy = InflationCalculator.yoy(data['pce_core']).iloc[-1]
            result['core'] = {
                'cpi_core_yoy': round(cpi_core_yoy, 2),
                'pce_core_yoy': round(pce_core_yoy, 2),
                'gap_bps': round((pce_core_yoy - cpi_core_yoy) * 100, 0)
            }

        # 3M SAAR
        if 'cpi_headline' in data and 'pce_headline' in data:
            cpi_3m = InflationCalculator.qoq_saar(data['cpi_headline']).iloc[-1]
            pce_3m = InflationCalculator.qoq_saar(data['pce_headline']).iloc[-1]
            result['momentum'] = {
                'cpi_3m_saar': round(cpi_3m, 2),
                'pce_3m_saar': round(pce_3m, 2),
                'momentum_divergence': round(pce_3m - cpi_3m, 2)
            }

        return result


def main():
    """主程式：命令列介面"""
    import argparse

    parser = argparse.ArgumentParser(description='CPI-PCE Comparator')
    parser.add_argument('--start', type=str, default='2020-01-01', help='起始日期')
    parser.add_argument('--end', type=str, default=datetime.now().strftime('%Y-%m-%d'), help='結束日期')
    parser.add_argument('--measure', type=str, default='yoy', choices=['yoy', 'mom_saar', 'qoq_saar'])
    parser.add_argument('--output', type=str, default='cpi_pce_analysis.json', help='輸出檔案')
    parser.add_argument('--cache-dir', type=str, help='快取目錄')
    parser.add_argument('--quick', action='store_true', help='快速檢查模式')
    parser.add_argument('--baseline', type=str, help='Baseline 期間 (e.g., 2018-10-01:2018-12-31)')

    args = parser.parse_args()

    analyzer = CPIPCEAnalyzer(cache_dir=args.cache_dir)

    if args.quick:
        result = analyzer.quick_check()
    else:
        baseline_period = None
        if args.baseline:
            baseline_period = {
                'mode': 'subtract_mean',
                'range': args.baseline
            }

        result = analyzer.analyze(
            start_date=args.start,
            end_date=args.end,
            measure=args.measure,
            baseline_period=baseline_period
        )

    # 輸出
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n結果已儲存至: {args.output}")

    # 也輸出到 console
    print("\n" + "=" * 60)
    print("分析結果摘要")
    print("=" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
