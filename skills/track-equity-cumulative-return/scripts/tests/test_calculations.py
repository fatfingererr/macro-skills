#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Calculation Tests for Cumulative Return Skill

Validates:
1. Core calculation formulas (cumulative return, CAGR)
2. Golden cases with expected ranges
3. Data validation functions

Usage:
    cd skills/track-equity-cumulative-return/scripts/tests
    python test_calculations.py

Version: 1.0.0
Last Updated: 2026-01-28
"""

import json
import sys
from pathlib import Path

# Add scripts directory to path (tests is inside scripts/)
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scripts_dir))


def test_cumulative_return_formula():
    """Test cumulative return formula"""
    from cumulative_return_analyzer import calculate_cumulative_return
    import pandas as pd

    print("\n=== Test: Cumulative Return Formula ===")

    # Test case 1: Simple 50% gain
    prices1 = pd.Series([100, 120, 150], index=pd.date_range("2024-01-01", periods=3))
    result1 = calculate_cumulative_return(prices1)
    expected1 = 50.0
    assert abs(result1 - expected1) < 0.01, f"Expected {expected1}, got {result1}"
    print(f"  [PASS] 100 -> 150 = {result1:.2f}% (expected {expected1}%)")

    # Test case 2: 100% gain (double)
    prices2 = pd.Series([100, 200], index=pd.date_range("2024-01-01", periods=2))
    result2 = calculate_cumulative_return(prices2)
    expected2 = 100.0
    assert abs(result2 - expected2) < 0.01, f"Expected {expected2}, got {result2}"
    print(f"  [PASS] 100 -> 200 = {result2:.2f}% (expected {expected2}%)")

    # Test case 3: 50% loss
    prices3 = pd.Series([100, 50], index=pd.date_range("2024-01-01", periods=2))
    result3 = calculate_cumulative_return(prices3)
    expected3 = -50.0
    assert abs(result3 - expected3) < 0.01, f"Expected {expected3}, got {result3}"
    print(f"  [PASS] 100 -> 50 = {result3:.2f}% (expected {expected3}%)")

    print("  [OK] All cumulative return formula tests passed")
    return True


def test_cagr_formula():
    """Test CAGR formula"""
    from cumulative_return_analyzer import calculate_cagr
    import pandas as pd

    print("\n=== Test: CAGR Formula ===")

    # Test case 1: Double in 1 year = 100% CAGR
    dates1 = pd.date_range("2024-01-01", "2025-01-01", periods=2)
    prices1 = pd.Series([100, 200], index=dates1)
    result1 = calculate_cagr(prices1)
    # 1 year: (200/100)^(1/1) - 1 = 100%
    expected1 = 100.0
    tolerance1 = 5.0  # Allow 5% tolerance due to day counting
    assert abs(result1 - expected1) < tolerance1, f"Expected ~{expected1}, got {result1}"
    print(f"  [PASS] 1-year double: CAGR = {result1:.2f}% (expected ~{expected1}%)")

    # Test case 2: Double in 2 years = ~41.4% CAGR
    dates2 = pd.date_range("2024-01-01", "2026-01-01", periods=2)
    prices2 = pd.Series([100, 200], index=dates2)
    result2 = calculate_cagr(prices2)
    # 2 years: (200/100)^(1/2) - 1 = 41.42%
    expected2 = 41.42
    tolerance2 = 2.0
    assert abs(result2 - expected2) < tolerance2, f"Expected ~{expected2}, got {result2}"
    print(f"  [PASS] 2-year double: CAGR = {result2:.2f}% (expected ~{expected2}%)")

    # Test case 3: Triple in 3 years = ~44.2% CAGR
    dates3 = pd.date_range("2024-01-01", "2027-01-01", periods=2)
    prices3 = pd.Series([100, 300], index=dates3)
    result3 = calculate_cagr(prices3)
    # 3 years: (300/100)^(1/3) - 1 = 44.22%
    expected3 = 44.22
    tolerance3 = 2.0
    assert abs(result3 - expected3) < tolerance3, f"Expected ~{expected3}, got {result3}"
    print(f"  [PASS] 3-year triple: CAGR = {result3:.2f}% (expected ~{expected3}%)")

    print("  [OK] All CAGR formula tests passed")
    return True


def test_cumulative_return_series():
    """Test cumulative return series calculation"""
    from cumulative_return_analyzer import calculate_cumulative_return_series
    import pandas as pd

    print("\n=== Test: Cumulative Return Series ===")

    prices = pd.Series(
        [100, 110, 120, 115, 130],
        index=pd.date_range("2024-01-01", periods=5)
    )
    result = calculate_cumulative_return_series(prices)

    # First value should be 0 (base)
    assert abs(result.iloc[0]) < 0.01, f"First value should be 0, got {result.iloc[0]}"
    print(f"  [PASS] First value = {result.iloc[0]:.2f}% (expected 0%)")

    # Last value should be 30% gain
    expected_last = 30.0
    assert abs(result.iloc[-1] - expected_last) < 0.01, f"Expected {expected_last}, got {result.iloc[-1]}"
    print(f"  [PASS] Last value = {result.iloc[-1]:.2f}% (expected {expected_last}%)")

    # Series length should match
    assert len(result) == len(prices), "Series length mismatch"
    print(f"  [PASS] Series length = {len(result)}")

    print("  [OK] All cumulative return series tests passed")
    return True


def test_validators():
    """Test validator functions"""
    from validators import (
        validate_ticker, validate_tickers,
        validate_year, validate_top_n, validate_index
    )

    print("\n=== Test: Validators ===")

    # Test ticker validation
    valid, result, correction = validate_ticker("NVDA")
    assert valid, f"NVDA should be valid: {result}"
    print("  [PASS] validate_ticker('NVDA') = valid")

    valid, result, correction = validate_ticker("brk.b")
    assert valid and result == "BRK-B", f"brk.b should be corrected to BRK-B: {result}"
    print("  [PASS] validate_ticker('brk.b') corrected to BRK-B")

    valid, result, correction = validate_ticker("invalid!!!")
    assert not valid, "invalid!!! should be invalid"
    print("  [PASS] validate_ticker('invalid!!!') = invalid")

    # Test year validation
    valid, msg = validate_year(2024)
    assert valid, f"2024 should be valid: {msg}"
    print("  [PASS] validate_year(2024) = valid")

    valid, msg = validate_year(1800)
    assert not valid, "1800 should be invalid"
    print("  [PASS] validate_year(1800) = invalid")

    # Test index validation
    valid, msg = validate_index("nasdaq100")
    assert valid, f"nasdaq100 should be valid: {msg}"
    print("  [PASS] validate_index('nasdaq100') = valid")

    valid, msg = validate_index("invalid")
    assert not valid, "invalid should be invalid"
    print("  [PASS] validate_index('invalid') = invalid")

    # Test top_n validation
    valid, msg = validate_top_n(20)
    assert valid, f"20 should be valid: {msg}"
    print("  [PASS] validate_top_n(20) = valid")

    valid, msg = validate_top_n(0)
    assert not valid, "0 should be invalid"
    print("  [PASS] validate_top_n(0) = invalid")

    print("  [OK] All validator tests passed")
    return True


def test_golden_cases_structure():
    """Test that golden cases file is valid"""
    print("\n=== Test: Golden Cases Structure ===")

    golden_file = Path(__file__).parent / "golden_cases.json"
    assert golden_file.exists(), f"Golden cases file not found: {golden_file}"
    print(f"  [PASS] Golden cases file exists")

    with open(golden_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "_metadata" in data, "Missing _metadata"
    assert "test_cases" in data, "Missing test_cases"
    assert len(data["test_cases"]) > 0, "No test cases defined"
    print(f"  [PASS] Found {len(data['test_cases'])} test cases")

    # Validate each test case structure
    required_fields = ["case_id", "description"]
    for case in data["test_cases"]:
        for field in required_fields:
            assert field in case, f"Missing field '{field}' in case"

    print("  [OK] Golden cases structure is valid")
    return True


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Cumulative Return Skill - Test Suite")
    print("=" * 60)

    results = {
        "cumulative_return_formula": test_cumulative_return_formula(),
        "cagr_formula": test_cagr_formula(),
        "cumulative_return_series": test_cumulative_return_series(),
        "validators": test_validators(),
        "golden_cases_structure": test_golden_cases_structure(),
    }

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {name}")

    print("-" * 60)
    print(f"  Total: {passed}/{total} passed")

    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print("\n[FAILURE] Some tests failed!")
        return 1


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    sys.exit(run_all_tests())
