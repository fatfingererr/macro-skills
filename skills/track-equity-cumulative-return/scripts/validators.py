#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Input and Data Validators

Provides validation functions for tickers, dates, and data quality.
This module improves robustness by catching errors early.

Version: 1.0.0
Last Updated: 2026-01-28
"""

import re
from datetime import datetime
from typing import List, Optional, Tuple, Union

import pandas as pd
import numpy as np


# ========== Version Info ==========
__version__ = "1.0.0"
__updated__ = "2026-01-28"


# ========== Ticker Validation ==========

# Valid ticker patterns
TICKER_PATTERN = re.compile(r'^[A-Z0-9\.\-\^]{1,10}$')

# Known invalid/delisted tickers (can be extended)
KNOWN_INVALID_TICKERS = {
    "TEST", "FAKE", "XXX", "DELETED",
}

# Common ticker corrections
TICKER_CORRECTIONS = {
    "BRK.B": "BRK-B",
    "BRK.A": "BRK-A",
    "BRKB": "BRK-B",
    "BRKA": "BRK-A",
    "FB": "META",  # Meta was renamed from FB
}


def validate_ticker(ticker: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validate a single ticker symbol

    Parameters
    ----------
    ticker : str
        Ticker symbol to validate

    Returns
    -------
    Tuple[bool, str, Optional[str]]
        (is_valid, validated_ticker_or_error_message, correction_if_applied)

    Examples
    --------
    >>> validate_ticker("NVDA")
    (True, "NVDA", None)
    >>> validate_ticker("brk.b")
    (True, "BRK-B", "BRK-B")  # Corrected
    >>> validate_ticker("invalid!!!")
    (False, "Invalid ticker format: invalid!!!", None)
    """
    if not ticker:
        return False, "Empty ticker", None

    # Convert to uppercase
    ticker_upper = ticker.strip().upper()

    # Apply corrections
    correction = None
    if ticker_upper in TICKER_CORRECTIONS:
        correction = TICKER_CORRECTIONS[ticker_upper]
        ticker_upper = correction

    # Check pattern
    if not TICKER_PATTERN.match(ticker_upper):
        return False, f"Invalid ticker format: {ticker}", None

    # Check known invalid tickers
    if ticker_upper in KNOWN_INVALID_TICKERS:
        return False, f"Known invalid ticker: {ticker_upper}", None

    return True, ticker_upper, correction


def validate_tickers(tickers: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """
    Validate multiple tickers

    Parameters
    ----------
    tickers : List[str]
        List of ticker symbols

    Returns
    -------
    Tuple[List[str], List[str], List[str]]
        (valid_tickers, invalid_tickers, corrections_applied)
    """
    valid = []
    invalid = []
    corrections = []

    for ticker in tickers:
        is_valid, result, correction = validate_ticker(ticker)
        if is_valid:
            valid.append(result)
            if correction:
                corrections.append(f"{ticker} → {correction}")
        else:
            invalid.append(result)

    return valid, invalid, corrections


# ========== Year Validation ==========

MIN_YEAR = 1970  # Yahoo Finance data starts around here
MAX_YEAR = datetime.now().year + 1  # Allow next year for testing


def validate_year(year: int) -> Tuple[bool, str]:
    """
    Validate year parameter

    Parameters
    ----------
    year : int
        Year to validate

    Returns
    -------
    Tuple[bool, str]
        (is_valid, error_message_if_invalid)

    Examples
    --------
    >>> validate_year(2024)
    (True, "")
    >>> validate_year(1800)
    (False, "Year 1800 is too old. Minimum: 1970")
    """
    if not isinstance(year, int):
        return False, f"Year must be an integer, got: {type(year).__name__}"

    if year < MIN_YEAR:
        return False, f"Year {year} is too old. Minimum: {MIN_YEAR}"

    if year > MAX_YEAR:
        return False, f"Year {year} is in the future. Maximum: {MAX_YEAR}"

    return True, ""


# ========== Data Validation ==========

def validate_price_data(
    df: pd.DataFrame,
    ticker: str,
    min_rows: int = 10,
    max_nan_pct: float = 0.1,
) -> Tuple[bool, str, Optional[pd.DataFrame]]:
    """
    Validate price data quality

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame
    ticker : str
        Ticker symbol (for error messages)
    min_rows : int
        Minimum required rows
    max_nan_pct : float
        Maximum allowed NaN percentage (0-1)

    Returns
    -------
    Tuple[bool, str, Optional[pd.DataFrame]]
        (is_valid, error_message_if_invalid, cleaned_dataframe_if_valid)
    """
    if df is None:
        return False, f"{ticker}: No data returned", None

    if df.empty:
        return False, f"{ticker}: Empty DataFrame", None

    if len(df) < min_rows:
        return False, f"{ticker}: Insufficient data ({len(df)} rows, need {min_rows})", None

    # Check for NaN values
    if "Close" not in df.columns:
        return False, f"{ticker}: Missing 'Close' column", None

    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    nan_count = close.isna().sum()
    nan_pct = nan_count / len(close)

    if nan_pct > max_nan_pct:
        return False, f"{ticker}: Too many NaN values ({nan_pct:.1%})", None

    # Check for invalid prices
    if (close <= 0).any():
        invalid_count = (close <= 0).sum()
        return False, f"{ticker}: {invalid_count} invalid (non-positive) prices found", None

    # Clean the data (drop NaN rows)
    df_clean = df.dropna(subset=["Close"])

    return True, "", df_clean


def validate_date_range(
    df: pd.DataFrame,
    expected_start: str,
    expected_end: str,
    tolerance_days: int = 5,
) -> Tuple[bool, str]:
    """
    Validate that data covers the expected date range

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with DatetimeIndex
    expected_start : str
        Expected start date (YYYY-MM-DD)
    expected_end : str
        Expected end date (YYYY-MM-DD)
    tolerance_days : int
        Allowed tolerance in days

    Returns
    -------
    Tuple[bool, str]
        (is_valid, warning_message_if_any)
    """
    if df.empty:
        return False, "Empty DataFrame"

    actual_start = df.index[0]
    actual_end = df.index[-1]

    expected_start_dt = pd.Timestamp(expected_start)
    expected_end_dt = pd.Timestamp(expected_end)

    warnings = []

    # Check start date
    start_diff = (actual_start - expected_start_dt).days
    if start_diff > tolerance_days:
        warnings.append(
            f"Data starts {start_diff} days after expected "
            f"(expected: {expected_start}, actual: {actual_start.strftime('%Y-%m-%d')})"
        )

    # Check end date
    end_diff = (expected_end_dt - actual_end).days
    if end_diff > tolerance_days:
        warnings.append(
            f"Data ends {end_diff} days before expected "
            f"(expected: {expected_end}, actual: {actual_end.strftime('%Y-%m-%d')})"
        )

    if warnings:
        return True, "; ".join(warnings)  # Still valid, but with warnings

    return True, ""


# ========== Index Validation ==========

SUPPORTED_INDICES = ["nasdaq100", "sp100", "dow30", "sox"]


def validate_index(index_key: str) -> Tuple[bool, str]:
    """
    Validate index key

    Parameters
    ----------
    index_key : str
        Index key to validate

    Returns
    -------
    Tuple[bool, str]
        (is_valid, error_message_if_invalid)
    """
    if not index_key:
        return False, "Index key cannot be empty"

    index_lower = index_key.lower()

    if index_lower not in SUPPORTED_INDICES:
        return False, (
            f"Unsupported index: {index_key}. "
            f"Supported: {', '.join(SUPPORTED_INDICES)}"
        )

    return True, ""


# ========== Top N Validation ==========

def validate_top_n(top_n: int, max_n: int = 100) -> Tuple[bool, str]:
    """
    Validate Top N parameter

    Parameters
    ----------
    top_n : int
        Top N value
    max_n : int
        Maximum allowed value

    Returns
    -------
    Tuple[bool, str]
        (is_valid, error_message_if_invalid)
    """
    if not isinstance(top_n, int):
        return False, f"top_n must be an integer, got: {type(top_n).__name__}"

    if top_n < 1:
        return False, f"top_n must be at least 1, got: {top_n}"

    if top_n > max_n:
        return False, f"top_n exceeds maximum ({max_n}), got: {top_n}"

    return True, ""


# ========== Utility Functions ==========

def print_validation_report(
    valid_tickers: List[str],
    invalid_tickers: List[str],
    corrections: List[str],
) -> None:
    """Print validation report to console"""
    if corrections:
        print(f"  [Correction] Applied {len(corrections)} ticker corrections:")
        for c in corrections:
            print(f"    - {c}")

    if invalid_tickers:
        print(f"  [Warning] {len(invalid_tickers)} invalid tickers skipped:")
        for inv in invalid_tickers:
            print(f"    - {inv}")

    print(f"  [Valid] {len(valid_tickers)} tickers to analyze")


if __name__ == "__main__":
    # Test validation functions
    print("Testing validators...")

    # Test ticker validation
    test_tickers = ["NVDA", "amd", "brk.b", "invalid!!!", "FB", "TEST"]
    valid, invalid, corrections = validate_tickers(test_tickers)
    print_validation_report(valid, invalid, corrections)

    # Test year validation
    for year in [2024, 1800, 2030, "abc"]:
        try:
            is_valid, msg = validate_year(year)
            print(f"  Year {year}: valid={is_valid}, msg={msg}")
        except Exception as e:
            print(f"  Year {year}: Error - {e}")
