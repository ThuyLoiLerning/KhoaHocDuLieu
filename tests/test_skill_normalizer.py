"""Unit tests for SkillNormalizer."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.cleaning.skill_normalizer import SkillNormalizer
from src.domain.skill import SKILL_SYNONYM_MAP


def test_js_to_javascript():
    n = SkillNormalizer()
    r = n.normalize("JS")
    assert r.canonical == "JavaScript"
    assert r.matched


def test_reactjs_to_react():
    n = SkillNormalizer()
    r = n.normalize("ReactJS")
    assert r.canonical == "React"


def test_python3_to_python():
    n = SkillNormalizer()
    r = n.normalize("Python3")
    assert r.canonical == "Python"


def test_golang_to_go():
    n = SkillNormalizer()
    r = n.normalize("golang")
    assert r.canonical == "Go"


def test_k8s_to_kubernetes():
    n = SkillNormalizer()
    r = n.normalize("k8s")
    assert r.canonical == "Kubernetes"


def test_ml_to_machine_learning():
    n = SkillNormalizer()
    r = n.normalize("ML")
    assert r.canonical == "Machine Learning"


def test_english_to_english():
    n = SkillNormalizer()
    r = n.normalize("English")
    assert r.canonical == "English"
    assert r.skill_group == "Language"


def test_tieng_anh():
    n = SkillNormalizer()
    r = n.normalize("tiếng anh")
    assert r.canonical == "English"


def test_unknown_skill():
    n = SkillNormalizer()
    r = n.normalize("CompletelyUnknownSkill123")
    assert not r.matched
    assert r.canonical == "CompletelyUnknownSkill123"


def test_skill_group_programming():
    n = SkillNormalizer()
    r = n.normalize("Python")
    assert r.skill_group == "Programming Language"


def test_skill_group_database():
    n = SkillNormalizer()
    r = n.normalize("PostgreSQL")
    assert r.skill_group == "Database"


def test_skill_group_cloud():
    n = SkillNormalizer()
    r = n.normalize("AWS")
    assert r.skill_group == "Cloud"


def test_case_insensitive():
    n = SkillNormalizer()
    r1 = n.normalize("python")
    r2 = n.normalize("PYTHON")
    r3 = n.normalize("Python")
    assert r1.canonical == r2.canonical == r3.canonical == "Python"


def test_synonym_map_has_35_entries():
    """Yêu cầu C6: ≥20 kỹ năng chuẩn hóa"""
    unique_canonicals = set(SKILL_SYNONYM_MAP.values())
    assert len(unique_canonicals) >= 20, f"Only {len(unique_canonicals)} canonical skills"


def test_empty_input():
    n = SkillNormalizer()
    r = n.normalize("")
    assert not r.matched


def test_none_input():
    n = SkillNormalizer()
    r = n.normalize(None)
    assert not r.matched


def test_dataframe_normalize():
    import pandas as pd
    n = SkillNormalizer()
    df = pd.DataFrame({"skill_name": ["JS", "ReactJS", "Python3", "UnknownSkill"]})
    result = n.normalize_dataframe(df, "skill_name")
    assert result["skill_name_canonical"].tolist() == ["JavaScript", "React", "Python", "UnknownSkill"]
    assert result["skill_matched"].tolist() == [True, True, True, False]


def test_add_custom_synonym():
    n = SkillNormalizer()
    n.add_synonym("newskill", "NewSkill", group="Programming Language")
    r = n.normalize("newskill")
    assert r.canonical == "NewSkill"
    assert r.skill_group == "Programming Language"


if __name__ == "__main__":
    tests = [
        test_js_to_javascript, test_reactjs_to_react, test_python3_to_python,
        test_golang_to_go, test_k8s_to_kubernetes, test_ml_to_machine_learning,
        test_english_to_english, test_tieng_anh,
        test_unknown_skill, test_skill_group_programming, test_skill_group_database,
        test_skill_group_cloud, test_case_insensitive, test_synonym_map_has_35_entries,
        test_empty_input, test_none_input, test_dataframe_normalize, test_add_custom_synonym,
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