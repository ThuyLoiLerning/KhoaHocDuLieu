"""Unit tests for RecommendationEngine."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from src.ml.recommendation import RecommendationEngine, Recommendation


def make_sample_data():
    skills = pd.DataFrame({
        "job_id": ["j1", "j1", "j1", "j2", "j2", "j3", "j3", "j3", "j3"],
        "skill_name": ["Python", "SQL", "Django",
                        "Java", "Spring",
                        "Python", "SQL", "ML", "Docker"],
        "required_level": ["Required"] * 9,
    })
    jobs = pd.DataFrame({
        "job_id": ["j1", "j2", "j3"],
        "job_title": ["Backend Dev", "Java Dev", "Data Scientist"],
        "company_name": ["FPT", "VNG", "VNG"],
        "city": ["HCMC", "Hanoi", "HCMC"],
        "salary_mid": [20.0, 18.0, 25.0],
    })
    return skills, jobs


def test_fit_shape():
    """Fit → matrix with correct dimensions"""
    skills, _ = make_sample_data()
    eng = RecommendationEngine()
    eng.fit(skills)
    rows, cols = eng.get_matrix_shape()
    assert rows == 3  # 3 jobs
    assert cols >= 6  # At least 6 unique skills


def test_recommend_top_n():
    """recommend returns top_n results"""
    skills, jobs = make_sample_data()
    eng = RecommendationEngine()
    eng.fit(skills)
    recs = eng.recommend(["Python", "SQL"], jobs, top_n=3)
    assert len(recs) <= 3


def test_similarity_in_range():
    """Similarity scores ∈ [0, 1]"""
    skills, jobs = make_sample_data()
    eng = RecommendationEngine()
    eng.fit(skills)
    recs = eng.recommend(["Python", "SQL"], jobs, top_n=3)
    for r in recs:
        assert 0.0 <= r.similarity_score <= 1.0, f"Score {r.similarity_score} out of range"


def test_matched_skills():
    """recommend returns matched skills"""
    skills, jobs = make_sample_data()
    eng = RecommendationEngine()
    eng.fit(skills)
    recs = eng.recommend(["Python"], jobs, top_n=3)
    top = recs[0]
    assert "Python" in top.matched_skills


def test_best_match_first():
    """Best match should be the one with most matching skills"""
    skills, jobs = make_sample_data()
    eng = RecommendationEngine()
    eng.fit(skills)
    # Python + SQL → j1 and j3 match best (both have Python + SQL)
    recs = eng.recommend(["Python", "SQL", "Django"], jobs, top_n=3)
    assert recs[0].job_id == "j1"  # j1 has Python + SQL + Django


def test_recommend_by_job_id():
    """recommend_by_job_id returns similar jobs"""
    skills, jobs = make_sample_data()
    eng = RecommendationEngine()
    eng.fit(skills)
    recs = eng.recommend_by_job_id("j1", jobs, top_n=2)
    assert len(recs) <= 2
    # Should not recommend itself
    for r in recs:
        assert r.job_id != "j1"


def test_empty_skills():
    """Empty user skills → lowest importance, still runs"""
    skills, jobs = make_sample_data()
    eng = RecommendationEngine()
    eng.fit(skills)
    recs = eng.recommend([], jobs, top_n=3)
    assert len(recs) == 3
    # All should have low similarity
    for r in recs:
        assert r.similarity_score == 0.0


def test_format_recommendations():
    """format_recommendations returns string"""
    skills, jobs = make_sample_data()
    eng = RecommendationEngine()
    eng.fit(skills)
    recs = eng.recommend(["Python"], jobs, top_n=2)
    output = eng.format_recommendations(recs)
    assert isinstance(output, str)
    assert "Job Recommendations" in output


def test_job_skill_count():
    skills, _ = make_sample_data()
    eng = RecommendationEngine()
    eng.fit(skills)
    assert eng.get_job_skill_count() >= 6


def test_unknown_job_recommend():
    """recommend_by_job_id with unknown ID raises ValueError"""
    skills, jobs = make_sample_data()
    eng = RecommendationEngine()
    eng.fit(skills)
    try:
        eng.recommend_by_job_id("nonexistent_job", jobs)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


if __name__ == "__main__":
    tests = [
        test_fit_shape, test_recommend_top_n, test_similarity_in_range,
        test_matched_skills, test_best_match_first, test_recommend_by_job_id,
        test_empty_skills, test_format_recommendations, test_job_skill_count,
        test_unknown_job_recommend,
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