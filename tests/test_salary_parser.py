"""Unit tests for SalaryParser (Yêu cầu I4)."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data.salary_parser import parse_salary, SalaryParser, SalaryType
import numpy as np


def assert_close(a, b, tol=0.01):
    assert abs(a - b) < tol, f"Expected {b}, got {a}"


def test_range_pattern():
    """'10-15 triệu' → min=10, max=15"""
    r = parse_salary("10-15 triệu")
    assert r.salary_type == SalaryType.RANGE
    assert_close(r.salary_min, 10.0)
    assert_close(r.salary_max, 15.0)
    assert not r.is_hidden
    assert r.confidence > 0.8


def test_range_en_dash():
    """'10 – 15 triệu' (en dash)"""
    r = parse_salary("10 – 15 triệu")
    assert r.salary_type == SalaryType.RANGE
    assert_close(r.salary_min, 10.0)


def test_range_tr():
    """'10-15tr'"""
    r = parse_salary("10-15tr")
    assert r.salary_type == SalaryType.RANGE
    assert_close(r.salary_min, 10.0)


def test_up_to():
    """'tới 20 triệu' → max=20"""
    r = parse_salary("tới 20 triệu")
    assert r.salary_type == SalaryType.UP_TO
    assert_close(r.salary_max, 20.0)


def test_up_to_den():
    """'đến 20 triệu'"""
    r = parse_salary("đến 20 triệu")
    assert r.salary_type == SalaryType.UP_TO
    assert_close(r.salary_max, 20.0)


def test_from():
    """'từ 15 triệu' → min=15"""
    r = parse_salary("từ 15 triệu")
    assert r.salary_type == SalaryType.FROM
    assert_close(r.salary_min, 15.0)


def test_yearly():
    """'80-120 triệu/năm' → /12"""
    r = parse_salary("80-120 triệu/năm")
    assert r.salary_type == SalaryType.YEARLY
    # Rounding to 1 decimal: 80/12=6.666... → 6.7
    assert_close(r.salary_min, 6.7, tol=0.1)
    assert_close(r.salary_max, 10.0, tol=0.1)


def test_usd():
    """'1200-1800 USD' → *25000 / 1e6 (triệu VND)"""
    r = parse_salary("1200-1800 USD")
    assert r.salary_type == SalaryType.USD
    assert_close(r.salary_min, 1200*25000/1e6)
    assert_close(r.salary_max, 1800*25000/1e6)


def test_usd_dollar_sign():
    """'$1500-2000'"""
    r = parse_salary("$1500-2000")
    assert r.salary_type == SalaryType.USD
    assert_close(r.salary_min, 1500*25000/1e6)
    assert_close(r.salary_max, 2000*25000/1e6)


def test_hidden_negotiable():
    """'cạnh tranh' → hidden=True"""
    r = parse_salary("cạnh tranh")
    assert r.is_hidden
    assert r.salary_type == SalaryType.HIDDEN


def test_hidden_thoa_thuan():
    r = parse_salary("thỏa thuận")
    assert r.is_hidden


def test_hidden_negotiable_en():
    r = parse_salary("negotiable")
    assert r.is_hidden


def test_single():
    """'15 triệu' → min=max=15"""
    r = parse_salary("15 triệu")
    assert r.salary_type == SalaryType.SINGLE
    assert_close(r.salary_min, 15.0)
    assert_close(r.salary_max, 15.0)


def test_single_m():
    """'20M'"""
    r = parse_salary("20M")
    assert r.salary_type in (SalaryType.SINGLE, SalaryType.RANGE)


def test_null_input():
    """None → unknown"""
    r = parse_salary(None)
    assert r.salary_type == SalaryType.UNKNOWN
    assert r.confidence == 0.0


def test_empty_input():
    r = parse_salary("")
    assert r.salary_type == SalaryType.UNKNOWN


def test_salary_mid():
    """salary_mid = average"""
    r = parse_salary("10-20 triệu")
    assert_close(r.salary_mid, 15.0)


def test_swap_min_max():
    """If min > max, swap"""
    # This happens in RANGE pattern - we swap inside the parser
    r = parse_salary("20-10 triệu")
    assert_close(r.salary_min, 10.0)
    assert_close(r.salary_max, 20.0)


def test_column_parse():
    """Test parse_column on DataFrame"""
    import pandas as pd
    df = pd.DataFrame({"salary_raw": ["10-15 triệu", "cạnh tranh", "20M", "", None]})
    parser = SalaryParser()
    result = parser.parse_column(df, "salary_raw")
    assert "salary_min" in result.columns
    assert "salary_max" in result.columns
    assert "salary_hidden" in result.columns
    assert "salary_mid" in result.columns
    assert_close(result.iloc[0]["salary_min"], 10.0)
    assert result.iloc[1]["salary_hidden"]
    assert_close(result.iloc[2]["salary_max"], 20.0)
    assert pd.isna(result.iloc[3]["salary_min"])


if __name__ == "__main__":
    tests = [
        test_range_pattern, test_range_en_dash, test_range_tr,
        test_up_to, test_up_to_den, test_from,
        test_yearly, test_usd, test_usd_dollar_sign,
        test_hidden_negotiable, test_hidden_thoa_thuan, test_hidden_negotiable_en,
        test_single, test_single_m, test_null_input, test_empty_input,
        test_salary_mid, test_swap_min_max, test_column_parse,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  FAIL {test.__name__}: {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"Total: {passed + failed}, Passed: {passed}, Failed: {failed}")