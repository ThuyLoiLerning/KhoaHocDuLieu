"""Experience normalizer — parse years of experience from various formats."""

import re
import logging
from dataclasses import dataclass
from typing import Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ExperienceResult:
    """Kết quả parse kinh nghiệm."""
    years: Optional[float]      # Số năm (float, midpoint cho range)
    experience_bin: str         # entry, junior, mid, senior, lead
    original: str               # Text gốc
    parsed: bool                # True nếu parse thành công


class ExperienceNormalizer:
    """Parse kinh nghiệm từ text: '2 năm', '3-5 năm', 'trên 5 năm', '5+ years', etc."""

    # Regex patterns
    PATTERNS = [
        # Range: "2-5 năm", "3 - 5 năm", "2–5 năm", "2 to 5 years"
        (re.compile(r"(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)\s*(?:năm|year|yr)", re.IGNORECASE), "range"),
        # From: "từ 3 năm", "from 3 years", "3+ năm", "3 năm trở lên"
        (re.compile(r"(?:từ|from|min\s*)\s*(\d+(?:\.\d+)?)\s*(?:năm|year|yr|tuổi|\+)", re.IGNORECASE), "from"),
        # Up to: "tới 5 năm", "đến 5 năm", "up to 5 years", "dưới 5 năm"
        (re.compile(r"(?:tới|đến|up\s*to|max\s*|dưới|under)\s*(\d+(?:\.\d+)?)\s*(?:năm|year|yr)", re.IGNORECASE), "to"),
        # Exact: "3 năm", "3 years", "5 yr", "10 năm kinh nghiệm"
        (re.compile(r"(\d+(?:\.\d+)?)\s*(?:năm|year|yr|tuổi)(?:\s*kinh\s*nghiệm)?", re.IGNORECASE), "exact"),
        # Vietnamese text: "hơn 5 năm", "trên 5 năm", "ít nhất 3 năm"
        (re.compile(r"(?:hơn|trên|ít\s*nhất|at\s*least)\s*(\d+(?:\.\d+)?)\s*(?:năm|year)", re.IGNORECASE), "from"),
        # Fresh/new grad
        (re.compile(r"(?:fresher|new\s*grad|mới\s*ra\s*trường|chưa\s*có\s*kinh\s*nghiệm|no\s*experience|0\s*năm)", re.IGNORECASE), "zero"),
    ]

    # Experience bins
    BINS = [
        (0, 1, "entry"),
        (1, 3, "junior"),
        (3, 5, "mid"),
        (5, 8, "senior"),
        (8, float("inf"), "lead"),
    ]

    def parse_years(self, text: str) -> ExperienceResult:
        """Parse text thành số năm kinh nghiệm."""
        if not text or not isinstance(text, str):
            return ExperienceResult(
                years=None,
                experience_bin="unknown",
                original=str(text) if text else "",
                parsed=False,
            )

        original = text.strip()
        lower = original.lower()

        # Check for zero experience
        if re.search(r"(?:fresher|new\s*grad|mới\s*ra\s*trường|chưa\s*có\s*kinh\s*nghiệm|no\s*experience|0\s*năm)", lower):
            return ExperienceResult(
                years=0.0,
                experience_bin="entry",
                original=original,
                parsed=True,
            )

        # Try patterns in order
        for pattern, ptype in self.PATTERNS:
            match = pattern.search(original)
            if match:
                if ptype == "range":
                    min_years = float(match.group(1))
                    max_years = float(match.group(2))
                    years = (min_years + max_years) / 2
                elif ptype == "from":
                    years = float(match.group(1))
                elif ptype == "to":
                    years = float(match.group(1)) / 2  # Estimate midpoint
                elif ptype == "exact":
                    years = float(match.group(1))
                elif ptype == "zero":
                    years = 0.0
                else:
                    years = float(match.group(1))

                return ExperienceResult(
                    years=years,
                    experience_bin=self.bin_experience(years),
                    original=original,
                    parsed=True,
                )

        # No pattern matched
        logger.warning(f"[ExperienceNormalizer] Could not parse: '{original}'")
        return ExperienceResult(
            years=None,
            experience_bin="unknown",
            original=original,
            parsed=False,
        )

    def bin_experience(self, years: float) -> str:
        """Phân nhóm kinh nghiệm theo số năm."""
        for min_y, max_y, label in self.BINS:
            if min_y <= years < max_y:
                return label
        return "lead"  # fallback

    def parse_dataframe(self, df: pd.DataFrame, col: str = "experience_raw",
                        years_col: str = "experience_years",
                        bin_col: str = "experience_bin",
                        parsed_col: str = "experience_parsed") -> pd.DataFrame:
        """Apply to DataFrame column."""
        df = df.copy()

        results = df[col].apply(lambda x: self.parse_years(str(x) if pd.notna(x) else ""))

        df[years_col] = [r.years for r in results]
        df[bin_col] = [r.experience_bin for r in results]
        df[parsed_col] = [r.parsed for r in results]

        # Stats
        total = len(df)
        parsed = df[parsed_col].sum()
        logger.info(f"[ExperienceNormalizer] Total: {total}, Parsed: {parsed}, Failed: {total - parsed}")

        return df


def parse_years(text: str) -> float:
    """Convenience function: parse text -> years (float). Returns None if failed."""
    normalizer = ExperienceNormalizer()
    result = normalizer.parse_years(text)
    return result.years


def bin_experience(years: float) -> str:
    """Convenience function: years -> bin label."""
    normalizer = ExperienceNormalizer()
    return normalizer.bin_experience(years)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    normalizer = ExperienceNormalizer()

    test_cases = [
        "2 năm", "3 năm kinh nghiệm", "5 năm",
        "2-5 năm", "3 - 5 năm", "2–5 năm",
        "từ 3 năm", "từ 5 năm kinh nghiệm",
        "tới 5 năm", "đến 3 năm", "dưới 2 năm",
        "hơn 5 năm", "trên 3 năm", "ít nhất 2 năm",
        "3+ năm", "5+ years",
        "fresher", "new grad", "mới ra trường", "chưa có kinh nghiệm",
        "1 year", "2 years", "5 yr",
        "10 năm", "15 năm",
        "unknown", "không rõ", "",
    ]

    print("Testing Experience Normalizer:")
    print("-" * 80)
    for tc in test_cases:
        result = normalizer.parse_years(tc)
        print(f"'{tc}' -> years={result.years}, bin={result.experience_bin}, parsed={result.parsed}")