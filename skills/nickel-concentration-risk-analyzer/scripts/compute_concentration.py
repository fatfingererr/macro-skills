#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Concentration Metrics Computation Module

Computes:
- Country share
- CR_n (n-firm concentration ratio)
- HHI (Herfindahl-Hirschman Index)
- Policy leverage

Author: Ricky Wang
License: MIT
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


def calculate_country_share(
    df: pd.DataFrame,
    country: str,
    supply_type: str = "mined"
) -> float:
    """
    Calculate a country's share of global production.

    Args:
        df: DataFrame with supply data (must have 'country', 'value' columns)
        country: Target country name
        supply_type: Filter by supply type (default: mined)

    Returns:
        Share as float (0-1)
    """
    # Filter by supply type if column exists
    if 'supply_type' in df.columns:
        df = df[df['supply_type'] == supply_type]

    # Calculate share
    country_prod = df[df['country'] == country]['value'].sum()
    global_prod = df['value'].sum()

    if global_prod == 0:
        return 0.0

    return country_prod / global_prod


def calculate_CRn(
    df: pd.DataFrame,
    n: int = 5,
    supply_type: str = "mined"
) -> Dict[str, Any]:
    """
    Calculate n-firm concentration ratio.

    Args:
        df: DataFrame with supply data
        n: Number of top producers to include
        supply_type: Filter by supply type

    Returns:
        Dictionary with CR1, CR3, CR5, CRn, and top_countries
    """
    # Filter by supply type
    if 'supply_type' in df.columns:
        df = df[df['supply_type'] == supply_type]

    # Calculate shares by country
    country_prod = df.groupby('country')['value'].sum()
    total_prod = country_prod.sum()

    if total_prod == 0:
        return {
            'CR1': 0.0,
            'CR3': 0.0,
            'CR5': 0.0,
            f'CR{n}': 0.0,
            'top_countries': {}
        }

    shares = (country_prod / total_prod).sort_values(ascending=False)

    # Calculate CRs
    result = {
        'CR1': shares.iloc[0] if len(shares) >= 1 else 0.0,
        'CR3': shares.head(3).sum() if len(shares) >= 3 else shares.sum(),
        'CR5': shares.head(5).sum() if len(shares) >= 5 else shares.sum(),
        f'CR{n}': shares.head(n).sum() if len(shares) >= n else shares.sum(),
        'top_countries': shares.head(n).to_dict()
    }

    return result


def calculate_HHI(
    df: pd.DataFrame,
    by: str = "country",
    supply_type: str = "mined"
) -> float:
    """
    Calculate Herfindahl-Hirschman Index.

    HHI = Σ(share_i² × 10000)

    Interpretation:
    - < 1500: Unconcentrated
    - 1500-2500: Moderately Concentrated
    - > 2500: Highly Concentrated

    Args:
        df: DataFrame with supply data
        by: Group by field (default: country)
        supply_type: Filter by supply type

    Returns:
        HHI value (0-10000)
    """
    # Filter by supply type
    if 'supply_type' in df.columns:
        df = df[df['supply_type'] == supply_type]

    # Calculate shares
    group_prod = df.groupby(by)['value'].sum()
    total_prod = group_prod.sum()

    if total_prod == 0:
        return 0.0

    shares = group_prod / total_prod

    # HHI = Σ(share² × 10000)
    hhi = (shares ** 2).sum() * 10000

    return round(hhi, 0)


def classify_market_structure(hhi: float) -> str:
    """
    Classify market structure based on HHI.

    Args:
        hhi: Herfindahl-Hirschman Index value

    Returns:
        Market structure classification string
    """
    if hhi < 1500:
        return "低集中 (Unconcentrated)"
    elif hhi < 2500:
        return "中等集中 (Moderately Concentrated)"
    else:
        return "高集中 (Highly Concentrated)"


def calculate_policy_leverage(
    cut_amount: float,
    global_prod: float
) -> Dict[str, Any]:
    """
    Calculate policy leverage metrics.

    Args:
        cut_amount: Amount of supply reduction (in tonnes Ni)
        global_prod: Global production (in tonnes Ni)

    Returns:
        Dictionary with leverage metrics
    """
    if global_prod == 0:
        leverage = 0.0
    else:
        leverage = cut_amount / global_prod

    # Equivalent days of consumption (assuming ~10 kt/day global consumption)
    daily_consumption = global_prod / 365
    equivalent_days = cut_amount / daily_consumption if daily_consumption > 0 else 0

    # Risk classification
    if leverage < 0.02:
        risk_level = "低風險"
    elif leverage < 0.05:
        risk_level = "中等風險"
    elif leverage < 0.10:
        risk_level = "高風險"
    else:
        risk_level = "極高風險"

    return {
        'global_hit_pct': leverage,
        'equivalent_days': equivalent_days,
        'risk_level': risk_level
    }


def compute_concentration_time_series(
    df: pd.DataFrame,
    years: List[int],
    country: str = "Indonesia"
) -> List[Dict]:
    """
    Compute concentration metrics over multiple years.

    Args:
        df: DataFrame with supply data
        years: List of years to analyze
        country: Country to track (default: Indonesia)

    Returns:
        List of yearly concentration metrics
    """
    results = []

    for year in years:
        year_df = df[df['year'] == year]

        if len(year_df) == 0:
            continue

        share = calculate_country_share(year_df, country)
        hhi = calculate_HHI(year_df)

        results.append({
            'year': year,
            f'{country.lower()}_share': share,
            'hhi': hhi,
            'market_structure': classify_market_structure(hhi)
        })

    return results


def sanity_check_values(
    value: float,
    unit: str,
    country: str,
    year: int
) -> Dict[str, Any]:
    """
    Perform sanity check on data values.

    Args:
        value: Production value
        unit: Unit of measurement
        country: Country name
        year: Year of data

    Returns:
        Dictionary with check result and any warnings
    """
    warnings = []

    # Check for nickel content values
    if unit == 't_Ni_content':
        # Global total shouldn't exceed ~5 Mt
        if country == 'World' and value > 5_000_000:
            warnings.append({
                'type': 'SUSPICIOUS_VALUE',
                'message': f"Global Ni content {value:,.0f} seems too high"
            })

        # Single country shouldn't exceed ~3 Mt
        if country != 'World' and value > 3_000_000:
            warnings.append({
                'type': 'POSSIBLE_ORE_NOT_CONTENT',
                'message': f"{country} Ni content {value:,.0f} may be ore not content"
            })

        # Indonesia specific checks (rapid growth)
        if country == 'Indonesia':
            expected_ranges = {
                2020: (600_000, 1_000_000),
                2021: (900_000, 1_200_000),
                2022: (1_400_000, 1_800_000),
                2023: (1_700_000, 2_200_000),
                2024: (2_000_000, 2_500_000),
            }
            if year in expected_ranges:
                low, high = expected_ranges[year]
                if value < low * 0.7 or value > high * 1.3:
                    warnings.append({
                        'type': 'VALUE_OUTSIDE_EXPECTED',
                        'message': f"Indonesia {year} value {value:,.0f} outside expected range"
                    })

    result = {
        'status': 'WARNING' if warnings else 'OK',
        'warnings': warnings
    }

    return result


if __name__ == '__main__':
    # Test with sample data
    test_data = pd.DataFrame([
        {'country': 'Indonesia', 'value': 2200000, 'supply_type': 'mined'},
        {'country': 'Philippines', 'value': 400000, 'supply_type': 'mined'},
        {'country': 'Russia', 'value': 210000, 'supply_type': 'mined'},
        {'country': 'Canada', 'value': 150000, 'supply_type': 'mined'},
        {'country': 'Australia', 'value': 140000, 'supply_type': 'mined'},
        {'country': 'Other', 'value': 700000, 'supply_type': 'mined'},
    ])

    print("Testing concentration metrics...")
    print(f"Indonesia share: {calculate_country_share(test_data, 'Indonesia'):.1%}")
    print(f"CR5: {calculate_CRn(test_data)}")
    print(f"HHI: {calculate_HHI(test_data):.0f}")
    print(f"Market structure: {classify_market_structure(calculate_HHI(test_data))}")
