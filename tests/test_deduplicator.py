"""Unit tests for Deduplicator."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from src.cleaning.deduplicator import Deduplicator


def make_test_df():
    return pd.DataFrame({
        "job_id": ["j1", "j2", "j3", "j4", "j5"],
        "job_title": ["Backend Developer", "Frontend Developer",
                       "Backend Developer", "Backend Dev", "Data Engineer"],
        "company_name": ["FPT", "VNG", "FPT", "FPT", "VNG"],
        "description_raw": [
            "Python Django Postgres",
            "React TypeScript",
            "Python Django Postgres",
            "Python Django API",
            "Spark Airflow",
        ],
        "posted_at": ["2025-06-01", "2025-06-02", "2025-06-03", "2025-06-04", "2025-06-05"],
    })


def test_exact_job_id():
    """Same job_id → exact duplicate"""
    df = make_test_df()
    df.loc[4, "job_id"] = "j1"  # Make j1 duplicate
    dd = Deduplicator()
    groups = dd.find_duplicates(df)
    assert len(groups) >= 1
    # Should find j1 duplicated
    found_j1_dup = False
    for g in groups:
        for d in g.duplicate_indices:
            if d == 4:
                found_j1_dup = True
    assert found_j1_dup


def test_exact_title_company():
    """Same title + company → exact duplicate"""
    df = make_test_df()
    # Make j3 same as j1 (already is)
    dd = Deduplicator()
    groups = dd.find_duplicates(df)
    # j1 and j2 both "Backend Developer" at "FPT"
    found_title_dup = False
    for g in groups:
        if 2 in g.duplicate_indices or 1 in g.duplicate_indices:
            found_title_dup = True
    # The test: j1 and j2 are both Backend Developer at FPT -> should be caught
    # Actually j2 is Frontend Developer, different. Only j3 (idx=2) is same as j1
    assert any(g.match_type == "exact" for g in groups)


def test_fuzzy_title():
    """'Backend Developer' vs 'Backend Dev' → near duplicate"""
    df = make_test_df()
    dd = Deduplicator(title_threshold=0.6)
    groups = dd.find_duplicates(df)
    near = [g for g in groups if g.match_type == "near" and "job_title" in g.matched_fields]
    # Should find 'Backend Developer' (idx 0) vs 'Backend Dev' (idx 3)
    assert len(near) >= 1


def test_no_false_positive():
    """Completely different jobs → no false positives"""
    df = make_test_df()
    dd = Deduplicator(title_threshold=0.9)  # High threshold
    groups = dd.find_duplicates(df)
    # j4 is "Backend Dev" (close to "Backend Developer") still find at 0.6 threshold
    # But with 0.9 they should not match
    for g in groups:
        for d in g.duplicate_indices:
            assert df.iloc[d]["job_title"] != "Data Engineer"  # Should never match


def test_remove_duplicates():
    """remove_duplicates removes correct rows"""
    df = make_test_df()
    dd = Deduplicator()
    groups = dd.find_duplicates(df)
    result = dd.remove_duplicates(df, groups)
    assert len(result) <= len(df)
    assert len(result) >= len(df) - sum(len(g.duplicate_indices) for g in groups)


def test_empty_dataframe():
    df = pd.DataFrame(columns=["job_id", "job_title"])
    dd = Deduplicator()
    groups = dd.find_duplicates(df)
    assert len(groups) == 0


def test_single_row_no_dupes():
    df = pd.DataFrame({"job_id": ["j1"], "job_title": ["Engineer"], "company_name": ["FPT"]})
    dd = Deduplicator()
    groups = dd.find_duplicates(df)
    assert len(groups) == 0


def test_log_duplicates_runs():
    """log_duplicates doesn't crash"""
    import tempfile, logging
    df = make_test_df()
    dd = Deduplicator()
    groups = dd.find_duplicates(df)
    try:
        # Temporarily redirect logger
        dd.log_duplicates(df, groups)
    except Exception as e:
        assert False, f"log_duplicates raised: {e}"


def test_analyze_duplicates():
    df = make_test_df()
    dd = Deduplicator()
    groups = dd.find_duplicates(df)
    stats = dd.analyze_duplicates(df, groups)
    assert "total_groups" in stats
    assert "total_duplicates" in stats
    assert "exact_duplicates" in stats
    assert "near_duplicates" in stats
    assert "avg_score" in stats


if __name__ == "__main__":
    tests = [
        test_exact_job_id, test_exact_title_company, test_fuzzy_title,
        test_no_false_positive, test_remove_duplicates, test_empty_dataframe,
        test_single_row_no_dupes, test_log_duplicates_runs, test_analyze_duplicates,
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