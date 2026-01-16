#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Nickel Concentration Risk Analyzer - Main Pipeline

Usage:
    python nickel_pipeline.py analyze --asof=2026-01-16 --scope=mined
    python nickel_pipeline.py scenario --cut=20 --target=Indonesia --exec-prob=0.5
    python nickel_pipeline.py validate --claim="Indonesia 60% share"
    python nickel_pipeline.py ingest --data-level=free_nolimit

Author: Ricky Wang
License: MIT
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd
import numpy as np

# Local imports
from ingest_sources import ingest_all_sources
from compute_concentration import (
    calculate_country_share,
    calculate_CRn,
    calculate_HHI,
    classify_market_structure
)
from scenario_impact import calculate_scenario_impact


class NickelConcentrationAnalyzer:
    """
    Main analyzer class for nickel supply concentration risk analysis.
    """

    def __init__(
        self,
        asof_date: str = None,
        scope: Dict[str, str] = None,
        data_level: str = "free_nolimit",
        config_path: Optional[str] = None
    ):
        """
        Initialize the analyzer.

        Args:
            asof_date: Analysis reference date (ISO format)
            scope: Analysis scope configuration
            data_level: Data source tier preference
            config_path: Path to YAML config file
        """
        self.asof_date = asof_date or datetime.now().strftime("%Y-%m-%d")
        self.scope = scope or {
            "supply_type": "mined",
            "unit": "t_Ni_content"
        }
        self.data_level = data_level
        self.data: Optional[pd.DataFrame] = None
        self.results: Dict[str, Any] = {}

        if config_path:
            self._load_config(config_path)

    def _load_config(self, config_path: str):
        """Load configuration from YAML file."""
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        self.asof_date = config.get('asof_date', self.asof_date)
        self.scope = config.get('scope', self.scope)
        self.data_level = config.get('data_level', self.data_level)

    def ingest(self) -> pd.DataFrame:
        """
        Ingest data from all configured sources.

        Returns:
            DataFrame with standardized nickel supply data
        """
        print(f"Ingesting data (level: {self.data_level})...")

        self.data = ingest_all_sources(
            data_level=self.data_level,
            supply_type=self.scope.get("supply_type", "mined")
        )

        print(f"Ingested {len(self.data)} records")
        return self.data

    def compute_concentration(
        self,
        year: int = None
    ) -> Dict[str, Any]:
        """
        Compute concentration metrics.

        Args:
            year: Target year (default: latest available)

        Returns:
            Dictionary with concentration metrics
        """
        if self.data is None:
            self.ingest()

        year = year or self.data['year'].max()
        print(f"Computing concentration for {year}...")

        # Filter to mined nickel content
        df = self.data[
            (self.data['supply_type'] == 'mined') &
            (self.data['year'] == year)
        ]

        # Calculate metrics
        indonesia_share = calculate_country_share(df, 'Indonesia')
        cr_metrics = calculate_CRn(df, n=5)
        hhi = calculate_HHI(df)

        self.results['concentration'] = {
            'analysis_year': year,
            'indonesia_share': indonesia_share,
            'cr1': cr_metrics['CR1'],
            'cr3': cr_metrics['CR3'],
            'cr5': cr_metrics['CR5'],
            'hhi': hhi,
            'market_structure': classify_market_structure(hhi),
            'top_countries': cr_metrics['top_countries']
        }

        return self.results['concentration']

    def compute_time_series(
        self,
        start_year: int = 2015,
        end_year: int = None
    ) -> List[Dict]:
        """
        Compute concentration metrics over time.

        Returns:
            List of yearly concentration metrics
        """
        if self.data is None:
            self.ingest()

        end_year = end_year or self.data['year'].max()
        time_series = []

        for year in range(start_year, end_year + 1):
            df = self.data[
                (self.data['supply_type'] == 'mined') &
                (self.data['year'] == year)
            ]

            if len(df) == 0:
                continue

            indonesia_share = calculate_country_share(df, 'Indonesia')
            hhi = calculate_HHI(df)

            time_series.append({
                'year': year,
                'indonesia_share': indonesia_share,
                'hhi': hhi,
                'market_structure': classify_market_structure(hhi)
            })

        self.results['time_series'] = time_series
        return time_series

    def run_scenario(
        self,
        scenario: Dict[str, Any],
        baseline: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Run policy scenario analysis.

        Args:
            scenario: Scenario definition
            baseline: Baseline production data (optional)

        Returns:
            Scenario impact results
        """
        # Default baseline (S&P Global 2024 data)
        if baseline is None:
            baseline = {
                'indonesia_prod': 2_280_000,  # tonnes Ni content
                'global_prod': 3_780_000,     # tonnes Ni content
                'indonesia_share': 0.602
            }

        results = calculate_scenario_impact(scenario, baseline)

        self.results['scenarios'] = self.results.get('scenarios', [])
        self.results['scenarios'].append({
            'name': scenario['name'],
            'parameters': scenario,
            'results': results
        })

        return results

    def generate_output(
        self,
        output_format: str = 'json',
        output_dir: str = './output'
    ) -> str:
        """
        Generate output in specified format.

        Args:
            output_format: 'json' or 'markdown'
            output_dir: Output directory

        Returns:
            Path to output file
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        output = {
            'metadata': {
                'skill': 'nickel-concentration-risk-analyzer',
                'version': '0.1.0',
                'generated_at': datetime.now().isoformat(),
                'asof_date': self.asof_date,
                'workflow': 'analyze'
            },
            'scope': self.scope,
            **self.results,
            'data_sources_used': self._get_data_sources_used(),
            'warnings': [],
            'errors': []
        }

        if output_format == 'json':
            output_path = Path(output_dir) / 'analysis_result.json'
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False, default=str)
        else:
            output_path = Path(output_dir) / 'analysis_report.md'
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(self._generate_markdown(output))

        print(f"Output saved to: {output_path}")
        return str(output_path)

    def _get_data_sources_used(self) -> List[Dict]:
        """Get list of data sources used in analysis."""
        sources = [
            {'name': 'USGS MCS (Nickel)', 'tier': 0, 'confidence': 0.95},
            {'name': 'INSG World Nickel Statistics', 'tier': 0, 'confidence': 0.90}
        ]
        if self.data_level in ['paid_low', 'paid_high']:
            sources.append({
                'name': 'S&P Global Market Intelligence',
                'tier': 2,
                'confidence': 0.90
            })
        return sources

    def _generate_markdown(self, output: Dict) -> str:
        """Generate Markdown report."""
        conc = output.get('concentration', {})

        md = f"""## 全球鎳供給集中度分析報告

**生成日期**: {output['metadata']['generated_at']}
**分析基準日**: {output['metadata']['asof_date']}
**數據口徑**: {output['scope'].get('supply_type', 'mined')} ({output['scope'].get('unit', 't_Ni_content')})

---

### 關鍵發現

| 指標 | 數值 | 解讀 |
|------|------|------|
| Indonesia share ({conc.get('analysis_year', 2024)}) | {conc.get('indonesia_share', 0):.1%} | 主導供給國 |
| CR5 (前五國集中度) | {conc.get('cr5', 0):.1%} | 高度集中 |
| HHI | {conc.get('hhi', 0):.0f} | {conc.get('market_structure', 'N/A')} |

---

*Generated by nickel-concentration-risk-analyzer v{output['metadata']['version']}*
"""
        return md


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Nickel Concentration Risk Analyzer'
    )
    parser.add_argument(
        'workflow',
        choices=['analyze', 'scenario', 'validate', 'ingest'],
        help='Workflow to execute'
    )
    parser.add_argument(
        '--asof', '--asof-date',
        default=datetime.now().strftime("%Y-%m-%d"),
        help='Analysis reference date (ISO format)'
    )
    parser.add_argument(
        '--scope',
        default='mined',
        help='Supply type: mined or refined'
    )
    parser.add_argument(
        '--data-level',
        default='free_nolimit',
        choices=['free_nolimit', 'free_limit', 'paid_low', 'paid_high'],
        help='Data source tier preference'
    )
    parser.add_argument(
        '--cut',
        type=float,
        help='Cut percentage for scenario (e.g., 20 for 20%%)'
    )
    parser.add_argument(
        '--target',
        default='Indonesia',
        help='Target country for scenario'
    )
    parser.add_argument(
        '--exec-prob',
        type=float,
        default=0.5,
        help='Execution probability (0-1)'
    )
    parser.add_argument(
        '--claim',
        help='Claim to validate'
    )
    parser.add_argument(
        '--output', '-o',
        default='./output/nickel',
        help='Output directory'
    )
    parser.add_argument(
        '--format',
        default='json',
        choices=['json', 'markdown'],
        help='Output format'
    )

    args = parser.parse_args()

    # Initialize analyzer
    analyzer = NickelConcentrationAnalyzer(
        asof_date=args.asof,
        scope={'supply_type': args.scope, 'unit': 't_Ni_content'},
        data_level=args.data_level
    )

    # Execute workflow
    if args.workflow == 'analyze':
        analyzer.ingest()
        analyzer.compute_concentration()
        analyzer.compute_time_series()
        analyzer.generate_output(args.format, args.output)

    elif args.workflow == 'scenario':
        if args.cut is None:
            parser.error("--cut is required for scenario workflow")

        scenario = {
            'name': f"{args.target}_cut_{args.cut:.0f}pct",
            'target_country': args.target,
            'policy_variable': 'ore_quota_RKAB',
            'cut_type': 'pct_country',
            'cut_value': args.cut / 100,
            'start_year': 2026,
            'end_year': 2026,
            'execution_prob': args.exec_prob
        }
        results = analyzer.run_scenario(scenario)
        print(json.dumps(results, indent=2))

    elif args.workflow == 'validate':
        if args.claim is None:
            parser.error("--claim is required for validate workflow")
        print(f"Validating claim: {args.claim}")
        # Validation logic would go here

    elif args.workflow == 'ingest':
        data = analyzer.ingest()
        output_path = Path(args.output) / 'nickel_supply.parquet'
        Path(args.output).mkdir(parents=True, exist_ok=True)
        data.to_parquet(output_path)
        print(f"Data saved to: {output_path}")


if __name__ == '__main__':
    main()
