#!/usr/bin/env python3
"""
Demographic-Fiscal Trap Analyzer
================================

Analyzes the interplay of aging demographics, debt dynamics, government bloat,
and inflation incentives to quantify "fiscal trap" risks for countries/regions.

Usage:
    python fiscal_trap_analyzer.py --entities JPN USA DEU --start-year 2010 --end-year 2023

Dependencies:
    pip install pandas numpy wbdata requests scipy
"""

import argparse
import json
import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict

import numpy as np
import pandas as pd

# Optional: wbdata for World Bank API
try:
    import wbdata
    HAS_WBDATA = True
except ImportError:
    HAS_WBDATA = False
    print("Warning: wbdata not installed. Using mock data for demo.")


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_WEIGHTS = {
    "aging": 0.35,
    "debt": 0.35,
    "bloat": 0.15,
    "growth_drag": 0.15
}

ENTITY_GROUPS = {
    "G7": ["USA", "JPN", "DEU", "GBR", "FRA", "ITA", "CAN"],
    "G20": ["USA", "JPN", "DEU", "GBR", "FRA", "ITA", "CAN", "CHN", "IND", "BRA",
            "RUS", "AUS", "KOR", "MEX", "IDN", "TUR", "SAU", "ARG", "ZAF"],
    "OECD": ["AUS", "AUT", "BEL", "CAN", "CHE", "CHL", "COL", "CRI", "CZE", "DEU",
             "DNK", "ESP", "EST", "FIN", "FRA", "GBR", "GRC", "HUN", "IRL", "ISL",
             "ISR", "ITA", "JPN", "KOR", "LTU", "LUX", "LVA", "MEX", "NLD", "NOR",
             "NZL", "POL", "PRT", "SVK", "SVN", "SWE", "TUR", "USA"],
    "EM_ASIA": ["CHN", "IND", "KOR", "TWN", "THA", "MYS", "IDN", "PHL", "VNM"],
}

WORLD_BANK_INDICATORS = {
    "old_age_dependency": "SP.POP.DPND.OL",
    "youth_dependency": "SP.POP.DPND.YG",
    "total_dependency": "SP.POP.DPND",
    "debt_to_gdp": "GC.DOD.TOTL.GD.ZS",
    "gov_consumption": "NE.CON.GOVT.ZS",
    "gov_expenditure": "GC.XPN.TOTL.GD.ZS",
    "real_gdp_growth": "NY.GDP.MKTP.KD.ZG",
    "cpi_inflation": "FP.CPI.TOTL.ZG",
    "lending_rate": "FR.INR.LEND",
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class EntityResult:
    """Results for a single entity."""
    entity: str
    entity_name: str = ""
    scores: Dict[str, float] = field(default_factory=dict)
    risk_level: str = ""
    quadrant: Dict[str, str] = field(default_factory=dict)
    key_metrics: Dict[str, Any] = field(default_factory=dict)
    interpretation: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisResult:
    """Complete analysis results."""
    metadata: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    results: Any = None
    data_notes: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Data Fetching
# =============================================================================

def expand_entity_groups(entities: List[str]) -> List[str]:
    """Expand entity group names to individual country codes."""
    expanded = []
    for entity in entities:
        if entity.upper() in ENTITY_GROUPS:
            expanded.extend(ENTITY_GROUPS[entity.upper()])
        else:
            expanded.append(entity)
    return list(set(expanded))


def fetch_worldbank_data(
    entities: List[str],
    indicators: Dict[str, str],
    start_year: int,
    end_year: int
) -> pd.DataFrame:
    """
    Fetch data from World Bank API.

    Parameters:
        entities: List of ISO3 country codes
        indicators: Dict mapping indicator names to WB codes
        start_year: Start year
        end_year: End year

    Returns:
        DataFrame with MultiIndex (entity, year) and indicator columns
    """
    if not HAS_WBDATA:
        return _generate_mock_data(entities, indicators, start_year, end_year)

    date_range = (
        datetime.datetime(start_year, 1, 1),
        datetime.datetime(end_year, 12, 31)
    )

    indicator_map = {v: k for k, v in indicators.items()}

    try:
        data = wbdata.get_dataframe(
            indicators,
            country=entities,
            date=date_range
        )
        data = data.reset_index()
        data.columns = ["entity", "year"] + list(indicators.keys())
        return data
    except Exception as e:
        print(f"Warning: Failed to fetch World Bank data: {e}")
        return _generate_mock_data(entities, indicators, start_year, end_year)


def _generate_mock_data(
    entities: List[str],
    indicators: Dict[str, str],
    start_year: int,
    end_year: int
) -> pd.DataFrame:
    """Generate mock data for demonstration purposes."""
    np.random.seed(42)
    years = list(range(start_year, end_year + 1))

    # Base values for different country profiles
    country_profiles = {
        "JPN": {"aging": 45, "debt": 250, "gov_cons": 20, "growth": 1.0},
        "ITA": {"aging": 35, "debt": 150, "gov_cons": 19, "growth": 0.5},
        "DEU": {"aging": 32, "debt": 65, "gov_cons": 20, "growth": 1.5},
        "USA": {"aging": 24, "debt": 120, "gov_cons": 14, "growth": 2.5},
        "GBR": {"aging": 28, "debt": 100, "gov_cons": 18, "growth": 1.8},
        "FRA": {"aging": 30, "debt": 110, "gov_cons": 24, "growth": 1.2},
        "CAN": {"aging": 25, "debt": 70, "gov_cons": 21, "growth": 2.0},
        "CHN": {"aging": 18, "debt": 75, "gov_cons": 16, "growth": 6.0},
        "IND": {"aging": 10, "debt": 85, "gov_cons": 11, "growth": 7.0},
    }

    default_profile = {"aging": 25, "debt": 80, "gov_cons": 18, "growth": 2.5}

    records = []
    for entity in entities:
        profile = country_profiles.get(entity, default_profile)
        for year in years:
            year_offset = year - start_year
            record = {
                "entity": entity,
                "year": year,
                "old_age_dependency": profile["aging"] + year_offset * 0.8 + np.random.normal(0, 1),
                "youth_dependency": max(15, 30 - year_offset * 0.3 + np.random.normal(0, 1)),
                "total_dependency": profile["aging"] + 25 + year_offset * 0.5,
                "debt_to_gdp": profile["debt"] + year_offset * 1.5 + np.random.normal(0, 3),
                "gov_consumption": profile["gov_cons"] + np.random.normal(0, 0.5),
                "gov_expenditure": profile["gov_cons"] * 2 + np.random.normal(0, 1),
                "real_gdp_growth": profile["growth"] + np.random.normal(0, 1.5),
                "cpi_inflation": 2 + np.random.normal(0, 1),
                "lending_rate": 3 + np.random.normal(0, 1),
            }
            records.append(record)

    return pd.DataFrame(records)


# =============================================================================
# Analysis Functions
# =============================================================================

def compute_zscore(values: pd.Series) -> pd.Series:
    """Compute cross-sectional z-scores."""
    mean = values.mean()
    std = values.std()
    if std == 0:
        return pd.Series(0, index=values.index)
    return (values - mean) / std


def linear_slope(series: pd.Series) -> float:
    """Compute linear regression slope."""
    if len(series) < 2:
        return 0.0
    x = np.arange(len(series))
    y = series.values
    mask = ~np.isnan(y)
    if mask.sum() < 2:
        return 0.0
    slope, _ = np.polyfit(x[mask], y[mask], 1)
    return float(slope)


def compute_aging_pressure(
    entity_data: pd.DataFrame,
    end_year: int,
    cross_section_data: pd.DataFrame
) -> Tuple[float, Dict[str, float]]:
    """
    Compute aging pressure score.

    Returns:
        Tuple of (score, metrics_dict)
    """
    # Get end year value
    end_data = entity_data[entity_data["year"] == end_year]
    if end_data.empty:
        return 0.0, {}

    aging_level = end_data["old_age_dependency"].values[0]

    # Compute 10-year slope
    recent_data = entity_data[entity_data["year"] >= end_year - 10]
    aging_slope = linear_slope(recent_data.set_index("year")["old_age_dependency"])

    # Z-scores from cross-section
    cross_end = cross_section_data[cross_section_data["year"] == end_year]
    level_zscore = (aging_level - cross_end["old_age_dependency"].mean()) / cross_end["old_age_dependency"].std()

    # For slope, we'd need cross-sectional slope data - simplify for now
    slope_zscore = aging_slope / 0.5  # Normalize by typical slope

    score = 0.5 * level_zscore + 0.5 * slope_zscore

    metrics = {
        "aging_level": aging_level,
        "aging_slope_10y": aging_slope,
        "level_zscore": level_zscore,
        "slope_zscore": slope_zscore,
    }

    return float(score), metrics


def compute_debt_dynamics(
    entity_data: pd.DataFrame,
    end_year: int,
    cross_section_data: pd.DataFrame
) -> Tuple[float, Dict[str, float]]:
    """
    Compute debt dynamics score.

    Returns:
        Tuple of (score, metrics_dict)
    """
    end_data = entity_data[entity_data["year"] == end_year]
    if end_data.empty:
        return 0.0, {}

    debt_level = end_data["debt_to_gdp"].values[0]

    # 5-year slope
    recent_data = entity_data[entity_data["year"] >= end_year - 5]
    debt_slope = linear_slope(recent_data.set_index("year")["debt_to_gdp"])

    # r - g approximation (using lending rate as proxy)
    nominal_rate = end_data["lending_rate"].values[0] if "lending_rate" in end_data else 3.0
    nominal_growth = end_data["real_gdp_growth"].values[0] + end_data["cpi_inflation"].values[0]
    r_minus_g = nominal_rate - nominal_growth

    # Z-scores
    cross_end = cross_section_data[cross_section_data["year"] == end_year]
    level_zscore = (debt_level - cross_end["debt_to_gdp"].mean()) / max(cross_end["debt_to_gdp"].std(), 1)

    score = 0.5 * level_zscore + 0.3 * (debt_slope / 3.0) + 0.2 * (r_minus_g / 2.0)

    metrics = {
        "debt_level": debt_level,
        "debt_slope_5y": debt_slope,
        "r_minus_g": r_minus_g,
        "nominal_rate": nominal_rate,
        "nominal_growth": nominal_growth,
    }

    return float(score), metrics


def compute_bloat_index(
    entity_data: pd.DataFrame,
    end_year: int,
    cross_section_data: pd.DataFrame
) -> Tuple[float, Dict[str, float]]:
    """
    Compute bureaucracy bloat index.

    Returns:
        Tuple of (score, metrics_dict)
    """
    end_data = entity_data[entity_data["year"] == end_year]
    if end_data.empty:
        return 0.0, {}

    gov_cons = end_data["gov_consumption"].values[0]
    gov_exp = end_data["gov_expenditure"].values[0] if "gov_expenditure" in end_data else gov_cons * 2

    cross_end = cross_section_data[cross_section_data["year"] == end_year]
    cons_zscore = (gov_cons - cross_end["gov_consumption"].mean()) / max(cross_end["gov_consumption"].std(), 1)
    exp_zscore = (gov_exp - cross_end["gov_expenditure"].mean()) / max(cross_end["gov_expenditure"].std(), 1)

    score = 0.6 * cons_zscore + 0.4 * exp_zscore

    metrics = {
        "gov_consumption": gov_cons,
        "gov_expenditure": gov_exp,
    }

    return float(score), metrics


def compute_growth_drag(
    entity_data: pd.DataFrame,
    end_year: int,
    cross_section_data: pd.DataFrame
) -> Tuple[float, Dict[str, float]]:
    """
    Compute growth drag score.

    Returns:
        Tuple of (score, metrics_dict)
    """
    end_data = entity_data[entity_data["year"] == end_year]
    if end_data.empty:
        return 0.0, {}

    real_growth = end_data["real_gdp_growth"].values[0]
    cpi = end_data["cpi_inflation"].values[0]
    nominal_growth = real_growth + cpi

    cross_end = cross_section_data[cross_section_data["year"] == end_year]
    growth_zscore = (nominal_growth - cross_end["real_gdp_growth"].mean() - cross_end["cpi_inflation"].mean()) / 3.0

    # Negative because low growth = high drag
    score = -growth_zscore

    metrics = {
        "real_gdp_growth": real_growth,
        "nominal_gdp_growth": nominal_growth,
    }

    return float(score), metrics


def compute_inflation_incentive(
    debt_level: float,
    r_minus_g: float,
    bloat_index: float,
    neg_real_rate_share: float = 0.5
) -> float:
    """Compute inflation incentive score."""
    return (
        0.40 * (debt_level / 100 - 1)  # Normalize around 100% debt
        + 0.20 * (r_minus_g / 2)
        + 0.20 * neg_real_rate_share
        + 0.20 * bloat_index
    )


def classify_quadrant(aging_pressure: float, debt_dynamics: float) -> Dict[str, str]:
    """Classify entity into quadrant based on aging and debt scores."""
    threshold = 1.0

    if aging_pressure > threshold and debt_dynamics > threshold:
        return {
            "code": "Q1",
            "name": "HighAging_HighDebt",
            "description": "雙高危機：老化壓力與債務動態均處於高風險區"
        }
    elif aging_pressure > threshold and debt_dynamics <= threshold:
        return {
            "code": "Q2",
            "name": "HighAging_LowDebt",
            "description": "老化主導：老化壓力高但債務相對可控"
        }
    elif aging_pressure <= threshold and debt_dynamics > threshold:
        return {
            "code": "Q3",
            "name": "LowAging_HighDebt",
            "description": "債務主導：債務壓力高但人口結構相對年輕"
        }
    else:
        return {
            "code": "Q4",
            "name": "LowAging_LowDebt",
            "description": "相對健康：老化與債務壓力均相對較低"
        }


def classify_risk_level(fiscal_trap_score: float) -> str:
    """Classify risk level based on fiscal trap score."""
    if fiscal_trap_score > 2.0:
        return "CRITICAL"
    elif fiscal_trap_score > 1.5:
        return "HIGH"
    elif fiscal_trap_score > 1.0:
        return "ELEVATED"
    elif fiscal_trap_score > 0.5:
        return "MODERATE"
    else:
        return "LOW"


def analyze_entity(
    entity: str,
    data: pd.DataFrame,
    end_year: int,
    weights: Dict[str, float]
) -> EntityResult:
    """
    Perform full analysis for a single entity.

    Parameters:
        entity: ISO3 country code
        data: Full dataset with all entities
        end_year: Analysis end year
        weights: Pillar weights

    Returns:
        EntityResult with all scores and metrics
    """
    entity_data = data[data["entity"] == entity].copy()

    if entity_data.empty:
        return EntityResult(entity=entity, entity_name=entity)

    # Compute each pillar
    aging_score, aging_metrics = compute_aging_pressure(entity_data, end_year, data)
    debt_score, debt_metrics = compute_debt_dynamics(entity_data, end_year, data)
    bloat_score, bloat_metrics = compute_bloat_index(entity_data, end_year, data)
    growth_score, growth_metrics = compute_growth_drag(entity_data, end_year, data)

    # Fiscal trap score
    fiscal_trap_score = (
        weights["aging"] * aging_score +
        weights["debt"] * debt_score +
        weights["bloat"] * bloat_score +
        weights["growth_drag"] * growth_score
    )

    # Inflation incentive
    inflation_incentive = compute_inflation_incentive(
        debt_metrics.get("debt_level", 100),
        debt_metrics.get("r_minus_g", 0),
        bloat_score
    )

    # Classification
    quadrant = classify_quadrant(aging_score, debt_score)
    risk_level = classify_risk_level(fiscal_trap_score)

    return EntityResult(
        entity=entity,
        entity_name=entity,  # Would ideally look up full name
        scores={
            "fiscal_trap_score": round(fiscal_trap_score, 2),
            "inflation_incentive_score": round(inflation_incentive, 2),
            "aging_pressure": round(aging_score, 2),
            "debt_dynamics": round(debt_score, 2),
            "bloat_index": round(bloat_score, 2),
            "growth_drag": round(growth_score, 2),
        },
        risk_level=risk_level,
        quadrant=quadrant,
        key_metrics={
            "demographics": aging_metrics,
            "debt": debt_metrics,
            "expenditure": bloat_metrics,
            "growth": growth_metrics,
        }
    )


# =============================================================================
# Main Analysis
# =============================================================================

def analyze_demographic_fiscal_trap(
    entities: List[str],
    start_year: int,
    end_year: int,
    forecast_end_year: int = 2050,
    weights: Optional[Dict[str, float]] = None
) -> AnalysisResult:
    """
    Main entry point for demographic-fiscal trap analysis.

    Parameters:
        entities: List of ISO3 country codes or group names
        start_year: Historical data start year
        end_year: Historical data end year
        forecast_end_year: Projection end year (for aging forecasts)
        weights: Custom pillar weights

    Returns:
        AnalysisResult with full analysis
    """
    # Apply defaults
    weights = weights or DEFAULT_WEIGHTS

    # Expand entity groups
    entities = expand_entity_groups(entities)

    # Fetch data
    print(f"Fetching data for {len(entities)} entities...")
    data = fetch_worldbank_data(entities, WORLD_BANK_INDICATORS, start_year, end_year)

    # Analyze each entity
    results = []
    for entity in entities:
        result = analyze_entity(entity, data, end_year, weights)
        results.append(result)

    # Sort by fiscal trap score
    results.sort(key=lambda x: x.scores.get("fiscal_trap_score", 0), reverse=True)

    # Build output
    if len(entities) == 1:
        # Single entity: detailed result
        output_results = asdict(results[0])
    else:
        # Multiple entities: comparison
        output_results = {
            "comparison_group": "Custom" if len(entities) > 7 else "Selected",
            "entities_analyzed": entities,
            "ranking": [
                {
                    "rank": i + 1,
                    "entity": r.entity,
                    "fiscal_trap_score": r.scores.get("fiscal_trap_score"),
                    "inflation_incentive_score": r.scores.get("inflation_incentive_score"),
                    "quadrant": r.quadrant.get("code"),
                    "risk_level": r.risk_level,
                }
                for i, r in enumerate(results)
            ],
            "detailed_scores": {r.entity: r.scores for r in results},
        }

    return AnalysisResult(
        metadata={
            "skill": "demographic-fiscal-trap-analyzer",
            "version": "0.1.0",
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "workflow": "full-analysis" if len(entities) == 1 else "cross-country",
        },
        parameters={
            "entities": entities,
            "start_year": start_year,
            "end_year": end_year,
            "forecast_end_year": forecast_end_year,
            "weights": weights,
        },
        results=output_results,
        data_notes={
            "sources": {
                "primary": "World Bank WDI",
                "fallback": "IMF WEO",
            },
            "mock_data_used": not HAS_WBDATA,
        }
    )


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Demographic-Fiscal Trap Analyzer"
    )
    parser.add_argument(
        "--entities", "-e",
        nargs="+",
        required=True,
        help="Country codes (ISO3) or groups (G7, OECD, etc.)"
    )
    parser.add_argument(
        "--start-year", "-s",
        type=int,
        required=True,
        help="Historical data start year"
    )
    parser.add_argument(
        "--end-year", "-y",
        type=int,
        required=True,
        help="Historical data end year"
    )
    parser.add_argument(
        "--forecast-end-year", "-f",
        type=int,
        default=2050,
        help="Projection end year (default: 2050)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output JSON file path"
    )
    parser.add_argument(
        "--weights",
        type=str,
        default=None,
        help="Custom weights as JSON string"
    )

    args = parser.parse_args()

    # Parse custom weights if provided
    weights = None
    if args.weights:
        weights = json.loads(args.weights)

    # Run analysis
    result = analyze_demographic_fiscal_trap(
        entities=args.entities,
        start_year=args.start_year,
        end_year=args.end_year,
        forecast_end_year=args.forecast_end_year,
        weights=weights,
    )

    # Output
    output_json = json.dumps(asdict(result), indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Results saved to {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
