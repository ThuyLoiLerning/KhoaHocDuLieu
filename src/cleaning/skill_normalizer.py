"""Skill normalizer — chuẩn hóa tên kỹ năng, nhóm kỹ năng.

Yêu cầu: ≥20 kỹ năng chuẩn hóa, synonym map 35+ entry.
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional, List, Dict, Set
from pathlib import Path
import pandas as pd

from src.domain.skill import SKILL_SYNONYM_MAP, SKILL_GROUP_MAP, Skill

logger = logging.getLogger(__name__)


@dataclass
class NormalizationResult:
    """Kết quả chuẩn hóa một skill."""
    original: str
    canonical: str
    skill_group: str
    matched: bool  # True nếu tìm thấy trong synonym map
    confidence: float  # 0-1


class SkillNormalizer:
    """Chuẩn hóa kỹ năng từ tên thô -> tên chuẩn (canonical)."""

    def __init__(self, custom_synonyms: Optional[Dict[str, str]] = None):
        # Base synonym map từ domain/skill.py
        self.synonym_map = dict(SKILL_SYNONYM_MAP)
        self.group_map = dict(SKILL_GROUP_MAP)

        # Add custom synonyms if provided
        if custom_synonyms:
            self.synonym_map.update(custom_synonyms)

        # Build reverse index for fast lookup
        self._build_index()

    def _build_index(self):
        """Build lookup index for fuzzy matching."""
        # Canonical names set
        self.canonical_names = set(self.synonym_map.values())
        # All known names (keys + values)
        self.all_known_names = set(self.synonym_map.keys()) | self.canonical_names

    def normalize(self, skill_name: str) -> NormalizationResult:
        """Chuẩn hóa một tên kỹ năng."""
        if not skill_name or not isinstance(skill_name, str):
            return NormalizationResult(
                original=str(skill_name) if skill_name else "",
                canonical="",
                skill_group="Other",
                matched=False,
                confidence=0.0,
            )

        original = skill_name.strip()
        lower = original.lower()

        # 1. Exact match in synonym map
        if lower in self.synonym_map:
            canonical = self.synonym_map[lower]
            return NormalizationResult(
                original=original,
                canonical=canonical,
                skill_group=self.group_map.get(canonical, "Other"),
                matched=True,
                confidence=1.0,
            )

        # 2. Exact match with canonical name
        for canon in self.canonical_names:
            if lower == canon.lower():
                return NormalizationResult(
                    original=original,
                    canonical=canon,
                    skill_group=self.group_map.get(canon, "Other"),
                    matched=True,
                    confidence=0.95,
                )

        # 3. Fuzzy match: contains/partial
        for key, canon in self.synonym_map.items():
            if key in lower or lower in key:
                return NormalizationResult(
                    original=original,
                    canonical=canon,
                    skill_group=self.group_map.get(canon, "Other"),
                    matched=True,
                    confidence=0.8,
                )

        # 4. Word boundary match for multi-word skills
        words = re.findall(r"\b\w+\b", lower)
        for word in words:
            if word in self.synonym_map:
                canonical = self.synonym_map[word]
                return NormalizationResult(
                    original=original,
                    canonical=canonical,
                    skill_group=self.group_map.get(canonical, "Other"),
                    matched=True,
                    confidence=0.7,
                )

        # 5. No match - return original as canonical, infer group
        inferred_group = self._infer_group_from_text(original)
        return NormalizationResult(
            original=original,
            canonical=original,  # Keep original if no match
            skill_group=inferred_group,
            matched=False,
            confidence=0.3,
        )

    def _infer_group_from_text(self, text: str) -> str:
        """Đoán nhóm kỹ năng từ text nếu không match."""
        text_lower = text.lower()

        # Programming language keywords
        if any(kw in text_lower for kw in ["language", "ngôn ngữ", "programming", "lập trình"]):
            return "Programming Language"

        # Framework keywords
        if any(kw in text_lower for kw in ["framework", "library", "thư viện", "framework"]):
            if any(kw in text_lower for kw in ["frontend", "ui", "react", "vue", "angular", "css", "html"]):
                return "Frontend Framework"
            return "Backend Framework"

        # Database keywords
        if any(kw in text_lower for kw in ["database", "db", "sql", "nosql", "cơ sở dữ liệu"]):
            return "Database"

        # Cloud/DevOps keywords
        if any(kw in text_lower for kw in ["cloud", "devops", "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd"]):
            return "Cloud" if "cloud" in text_lower else "DevOps"

        # Data Science keywords
        if any(kw in text_lower for kw in ["ml", "machine learning", "deep learning", "ai", "data science", "tensorflow", "pytorch"]):
            return "Data Science"

        # Mobile keywords
        if any(kw in text_lower for kw in ["mobile", "android", "ios", "flutter", "react native"]):
            return "Mobile"

        # Testing keywords
        if any(kw in text_lower for kw in ["test", "testing", "qa", "automation", "selenium", "cypress"]):
            return "Testing"

        # Language keywords
        if any(kw in text_lower for kw in ["english", "ielts", "toeic", "tiếng anh"]):
            return "Language"

        # Soft skill keywords
        if any(kw in text_lower for kw in ["communication", "teamwork", "leadership", "soft skill", "kỹ năng mềm", "giải quyết vấn đề", "problem solving"]):
            return "Soft Skill"

        return "Other"

    def normalize_dataframe(self, df: pd.DataFrame, col: str = "skill_name",
                            new_canonical_col: str = "skill_name_canonical",
                            new_group_col: str = "skill_group",
                            new_matched_col: str = "skill_matched",
                            log_file: Optional[str] = None) -> pd.DataFrame:
        """Apply normalization to a DataFrame column."""
        df = df.copy()

        results = df[col].apply(lambda x: self.normalize(str(x) if pd.notna(x) else ""))

        df[new_canonical_col] = [r.canonical for r in results]
        df[new_group_col] = [r.skill_group for r in results]
        df[new_matched_col] = [r.matched for r in results]

        # Logging
        total = len(df)
        matched = sum(1 for r in results if r.matched)
        unmatched = total - matched

        logger.info(f"[SkillNormalizer] Total: {total}, Matched: {matched}, Unmatched: {unmatched}")

        # Log unmatched skills for review
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            unmatched_skills = [r.original for r in results if not r.matched and r.original]
            if unmatched_skills:
                from collections import Counter
                unmatched_counts = Counter(unmatched_skills)
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(f"Unmatched skills ({len(unmatched_skills)} occurrences, {len(unmatched_counts)} unique):\n")
                    for skill, count in unmatched_counts.most_common():
                        f.write(f"  {skill}: {count}\n")

        return df

    def get_stats(self, df: pd.DataFrame, col: str = "skill_name") -> Dict:
        """Thống kê kỹ năng trong DataFrame."""
        results = df[col].apply(lambda x: self.normalize(str(x) if pd.notna(x) else ""))

        canonical_skills = [r.canonical for r in results if r.canonical]
        from collections import Counter
        skill_counts = Counter(canonical_skills)

        groups = [r.skill_group for r in results]
        group_counts = Counter(groups)

        matched = sum(1 for r in results if r.matched)

        return {
            "total_skills": len(results),
            "unique_canonical": len(skill_counts),
            "matched": matched,
            "unmatched": len(results) - matched,
            "top_skills": skill_counts.most_common(20),
            "group_distribution": dict(group_counts),
        }

    def add_synonym(self, original: str, canonical: str, group: str = "Other"):
        """Thêm synonym mới vào map."""
        self.synonym_map[original.lower().strip()] = canonical
        self.group_map[canonical] = group
        self._build_index()


def extract_skills_from_description(description: str, normalizer: Optional[SkillNormalizer] = None) -> List[Skill]:
    """Trích xuất skills từ job description text.

    Dùng keyword matching với synonym map.
    """
    if not description:
        return []

    if normalizer is None:
        normalizer = SkillNormalizer()

    desc_lower = description.lower()
    found_skills = []

    # Search for all known skill names in description
    for canonical in normalizer.canonical_names:
        canon_lower = canonical.lower()
        # Word boundary match
        pattern = r"\b" + re.escape(canon_lower) + r"\b"
        if re.search(pattern, desc_lower):
            # Also check for synonyms that map to this canonical
            synonyms = [k for k, v in normalizer.synonym_map.items() if v == canonical]
            original = synonyms[0] if synonyms else canonical

            skill = Skill(
                skill_name=canonical,
                original_name=original,
                skill_group=normalizer.group_map.get(canonical, "Other"),
                required_level="Not specified",
            )
            found_skills.append(skill)

    return found_skills


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    normalizer = SkillNormalizer()

    # Test cases
    test_skills = [
        "JavaScript", "JS", "java script", "ReactJS", "react.js", "vuejs",
        "Python3", "py", "golang", "Go", "C++", "cpp", "nodejs", "node.js",
        "postgresql", "postgres", "mysql", "mongo", "mongodb",
        "aws", "amazon web services", "docker", "k8s", "kubernetes",
        "machine learning", "ml", "deep learning", "tensorflow", "pytorch",
        "English", "tiếng anh", "ielts", "teamwork", "leadership",
        "UnknownSkill123", "RandomFrameworkXYZ",
    ]

    print("Testing Skill Normalizer:")
    print("-" * 80)
    for skill in test_skills:
        result = normalizer.normalize(skill)
        print(f"'{skill}' -> '{result.canonical}' [{result.skill_group}] matched={result.matched} conf={result.confidence}")