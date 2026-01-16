#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scenario Impact Simulation Module

Simulates the impact of policy scenarios (e.g., RKAB quota cuts)
on global nickel supply.

Author: Ricky Wang
License: MIT
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class Scenario:
    """Policy scenario definition."""
    name: str
    target_country: str
    policy_variable: str
    cut_type: str  # pct_global | pct_country | absolute
    cut_value: float
    start_year: int
    end_year: int
    execution_prob: float = 0.5


@dataclass
class Baseline:
    """Baseline production data."""
    country_prod: float  # Target country production (tonnes)
    global_prod: float   # Global production (tonnes)
    country_share: float # Country's share of global


def calculate_scenario_impact(
    scenario: Dict[str, Any],
    baseline: Dict[str, float]
) -> Dict[str, Any]:
    """
    Calculate the impact of a policy scenario.

    Args:
        scenario: Scenario definition dictionary
        baseline: Baseline production data dictionary

    Returns:
        Dictionary with impact results for hard/half/soft scenarios
    """
    # Parse inputs
    cut_type = scenario.get('cut_type', 'pct_country')
    cut_value = scenario.get('cut_value', 0.0)
    execution_prob = scenario.get('execution_prob', 0.5)

    country_prod = baseline.get('country_prod', baseline.get('indonesia_prod', 0))
    global_prod = baseline.get('global_prod', 0)

    if global_prod == 0:
        return {'error': 'Global production is zero'}

    # Calculate base cut amount
    if cut_type == 'pct_country':
        cut_amount = country_prod * cut_value
    elif cut_type == 'pct_global':
        cut_amount = global_prod * cut_value
    else:  # absolute
        cut_amount = cut_value

    # Calculate three scenarios
    results = {
        'hard_cut': _calculate_tier(
            name="完全執行",
            execution_rate=1.0,
            cut_amount=cut_amount,
            global_prod=global_prod,
            description="政策 100% 落地"
        ),
        'half_success': _calculate_tier(
            name="半成功",
            execution_rate=execution_prob,
            cut_amount=cut_amount,
            global_prod=global_prod,
            description=f"執行 {execution_prob:.0%}"
        ),
        'soft_landing': _calculate_tier(
            name="軟著陸",
            execution_rate=0.25,
            cut_amount=cut_amount,
            global_prod=global_prod,
            description="只延遲新增產能/部分執行"
        )
    }

    # Add sensitivity analysis
    results['sensitivity'] = _generate_sensitivity(cut_amount, global_prod)

    # Add unit warnings if applicable
    results['warnings'] = _check_unit_warnings(scenario)

    return results


def _calculate_tier(
    name: str,
    execution_rate: float,
    cut_amount: float,
    global_prod: float,
    description: str
) -> Dict[str, Any]:
    """
    Calculate metrics for a single execution tier.
    """
    actual_cut = cut_amount * execution_rate
    global_hit_pct = actual_cut / global_prod if global_prod > 0 else 0

    # Daily consumption estimate (~10kt/day for nickel)
    daily_consumption = global_prod / 365
    equivalent_days = actual_cut / daily_consumption if daily_consumption > 0 else 0

    # Risk classification
    if global_hit_pct < 0.02:
        risk_level = "低風險"
    elif global_hit_pct < 0.05:
        risk_level = "中等風險"
    elif global_hit_pct < 0.10:
        risk_level = "高風險"
    else:
        risk_level = "極高風險"

    return {
        'name': name,
        'execution_rate': execution_rate,
        'cut_amount_kt': actual_cut / 1000,  # Convert to kt
        'cut_amount_t': actual_cut,
        'global_hit_pct': global_hit_pct,
        'equivalent_days_consumption': round(equivalent_days, 1),
        'risk_level': risk_level,
        'description': description
    }


def _generate_sensitivity(
    base_cut: float,
    global_prod: float
) -> List[Dict[str, float]]:
    """
    Generate sensitivity analysis table.
    """
    execution_rates = [1.0, 0.75, 0.50, 0.25, 0.0]
    sensitivity = []

    for rate in execution_rates:
        actual_cut = base_cut * rate
        global_hit = actual_cut / global_prod if global_prod > 0 else 0

        sensitivity.append({
            'execution_rate': rate,
            'cut_kt': actual_cut / 1000,
            'global_hit_pct': global_hit
        })

    return sensitivity


def _check_unit_warnings(scenario: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Check for potential unit misalignment issues.
    """
    warnings = []

    policy_var = scenario.get('policy_variable', '')

    if policy_var == 'ore_quota_RKAB':
        warnings.append({
            'type': 'unit_mismatch',
            'code': 'RKAB_ORE_QUOTA',
            'message': 'RKAB ore quota is typically in ore wet tonnes, not nickel content',
            'impact': 'Direct percentage application to nickel content may underestimate actual impact',
            'recommendation': 'Consider ore-to-content conversion with grade assumptions (~1.5% Ni)'
        })

    if 'export' in policy_var.lower():
        warnings.append({
            'type': 'policy_scope',
            'code': 'EXPORT_RULE_SCOPE',
            'message': 'Export rules may affect different products differently',
            'impact': 'Ore exports vs processed product exports have different implications'
        })

    return warnings


def run_multiple_scenarios(
    scenarios: List[Dict[str, Any]],
    baseline: Dict[str, float]
) -> Dict[str, Any]:
    """
    Run multiple scenarios and aggregate results.

    Args:
        scenarios: List of scenario definitions
        baseline: Baseline production data

    Returns:
        Dictionary with results for all scenarios
    """
    all_results = {
        'scenarios': [],
        'combined': None
    }

    total_expected_cut = 0
    global_prod = baseline.get('global_prod', 0)

    for scenario in scenarios:
        result = calculate_scenario_impact(scenario, baseline)
        all_results['scenarios'].append({
            'name': scenario['name'],
            'parameters': scenario,
            'results': result
        })

        # Accumulate expected cuts (half_success)
        total_expected_cut += result['half_success']['cut_amount_t']

    # Combined impact
    if global_prod > 0:
        all_results['combined'] = {
            'total_expected_cut_kt': total_expected_cut / 1000,
            'combined_global_hit_pct': total_expected_cut / global_prod,
            'note': 'Combined assumes independent scenarios; actual interaction may differ'
        }

    return all_results


def convert_ore_to_content(
    ore_tonnes: float,
    ni_grade: float = 0.015,
    moisture: float = 0.30
) -> Dict[str, float]:
    """
    Convert ore wet tonnes to nickel content.

    Args:
        ore_tonnes: Ore wet tonnes
        ni_grade: Nickel grade (default 1.5%)
        moisture: Moisture content (default 30%)

    Returns:
        Dictionary with conversion results
    """
    dry_tonnes = ore_tonnes * (1 - moisture)
    ni_content = dry_tonnes * ni_grade

    return {
        'ore_wet_tonnes': ore_tonnes,
        'ore_dry_tonnes': dry_tonnes,
        'ni_content_tonnes': ni_content,
        'assumptions': {
            'ni_grade': ni_grade,
            'moisture': moisture
        }
    }


if __name__ == '__main__':
    # Test scenario
    test_scenario = {
        'name': 'ID_RKAB_cut_test',
        'target_country': 'Indonesia',
        'policy_variable': 'ore_quota_RKAB',
        'cut_type': 'pct_country',
        'cut_value': 0.20,  # 20% cut
        'start_year': 2026,
        'end_year': 2026,
        'execution_prob': 0.5
    }

    test_baseline = {
        'country_prod': 2_280_000,  # Indonesia 2024 (S&P)
        'global_prod': 3_780_000,   # Global 2024 (estimated)
        'country_share': 0.602
    }

    print("Testing scenario impact calculation...")
    results = calculate_scenario_impact(test_scenario, test_baseline)

    print("\n=== Hard Cut ===")
    print(f"Cut: {results['hard_cut']['cut_amount_kt']:.0f} kt")
    print(f"Global impact: {results['hard_cut']['global_hit_pct']:.1%}")
    print(f"Risk level: {results['hard_cut']['risk_level']}")

    print("\n=== Half Success ===")
    print(f"Cut: {results['half_success']['cut_amount_kt']:.0f} kt")
    print(f"Global impact: {results['half_success']['global_hit_pct']:.1%}")
    print(f"Equivalent days: {results['half_success']['equivalent_days_consumption']:.0f}")

    print("\n=== Warnings ===")
    for warning in results['warnings']:
        print(f"⚠️ {warning['type']}: {warning['message']}")

    # Test ore to content conversion
    print("\n=== Ore to Content Conversion ===")
    conversion = convert_ore_to_content(250_000_000)  # 250 Mt ore
    print(f"250 Mt ore wet → {conversion['ni_content_tonnes']/1e6:.2f} Mt Ni content")
