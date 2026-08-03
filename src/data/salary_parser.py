"""Salary parser — chuẩn hóa lương từ các định dạng Việt Nam thực tế.

Xử lý các pattern phổ biến:
- "10-15 triệu" → min=10, max=15
- "10 – 15 triệu" (en dash) → min=10, max=15
- "tới 20 triệu", "đến 20 triệu" → max=20
- "từ 15 triệu", "từ 15tr" → min=15
- "80-120 triệu/năm" → /12
- "1200-1800 USD" → *25000
- "$1500-2000" → *25000
- "cạnh tranh", "thỏa thuận", "negotiable", "face to face" → hidden=True
- "15M", "20M", "15tr", "20tr" → parse số
"""

import re
import logging
from typing import Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
import pandas as pd

logger = logging.getLogger(__name__)


class SalaryType(Enum):
    RANGE = "range"           # "10-15 triệu"
    UP_TO = "up_to"           # "tới 20 triệu"
    FROM = "from"             # "từ 15 triệu"
    YEARLY = "yearly"         # "100 triệu/năm"
    USD = "usd"               # "1500-2000 USD"
    HIDDEN = "hidden"         # "cạnh tranh", "thỏa thuận"
    SINGLE = "single"         # "15 triệu"
    UNKNOWN = "unknown"


@dataclass
class ParsedSalary:
    """Kết quả parse lương."""
    salary_min: Optional[float] = None      # triệu VND/tháng
    salary_max: Optional[float] = None      # triệu VND/tháng
    salary_mid: Optional[float] = None      # (min+max)/2
    is_hidden: bool = False                 # "cạnh tranh", "thỏa thuận"
    salary_type: SalaryType = SalaryType.UNKNOWN
    original_text: str = ""
    confidence: float = 0.0                 # 0-1


# ============================================================
# REGEX PATTERNS
# ============================================================

# Hidden salary keywords
HIDDEN_KEYWORDS = [
    r"cạnh tranh", r"thỏa thuận", r"thoả thuận", r"thoa thuan", r"thỏa thuận", r"negotiable",
    r"face.?to.?face", r"f2f", r"liên hệ", r"lien he", r"contact",
    r"đề xuất", r"de xuat", r"theo năng lực", r"theo nang luc",
    r"tùy kinh nghiệm", r"tuy kinh nghiem", r"based on experience",
    r"updated", r"cập nhật", r"cap nhat", r"chính sách", r"chinh sach",
]

HIDDEN_PATTERN = re.compile("|".join(HIDDEN_KEYWORDS), re.IGNORECASE)

# Currency units
VND_UNITS = {
    "triệu": 1.0,
    "trieu": 1.0,
    "tr": 1.0,
    "m": 1.0,
    "million": 1.0,
    "nghìn": 0.001,
    "nghin": 0.001,
    "k": 0.001,
    "ngàn": 0.001,
    "ngan": 0.001,
    "tỷ": 1000.0,
    "ty": 1000.0,
    "billion": 1000.0,
}

USD_TO_VND_RATE = 25000  # 1 USD = 25,000 VND (approx)


# Main patterns (ordered by specificity)
PATTERNS = [
    # Yearly salary: "80-120 triệu/năm", "100-150 triệu / nam"
    {
        "type": SalaryType.YEARLY,
        "regex": re.compile(
            r"(?:từ\s*)?(?P<min>\d[\d.,]*)\s*[-–—]\s*(?P<max>\d[\d.,]*)\s*(?P<unit>triệu|tr|m|million)?\s*/\s*(?:năm|nam|year)",
            re.IGNORECASE
        ),
        "groups": ("min", "max", "unit"),
    },
    {
        "type": SalaryType.YEARLY,
        "regex": re.compile(
            r"(?:từ\s*)?(?P<min>\d[\d.,]*)\s*(?P<unit>triệu|tr|m|million)?\s*/\s*(?:năm|nam|year)",
            re.IGNORECASE
        ),
        "groups": ("min", "unit"),
    },

    # USD salary: "1200-1800 USD", "$1,500 - $2,000", "1500-2000 USD/tháng"
    # Leading $ makes trailing unit optional; otherwise require USD suffix
    {
        "type": SalaryType.USD,
        "regex": re.compile(
            r"\$(?P<min>\d[\d.,]*)\s*[-–—]\s*(?:\$)?(?P<max>\d[\d.,]*)(?:\s*(?:usd|\$))?(?:\s*/tháng|\s*/thang|\s*/month)?",
            re.IGNORECASE
        ),
        "groups": ("min", "max"),
    },
    {
        "type": SalaryType.USD,
        "regex": re.compile(
            r"(?P<min>\d[\d.,]*)\s*[-–—]\s*(?:\$)?(?P<max>\d[\d.,]*)\s*(?:usd|\$)(?:\s*/tháng|\s*/thang|\s*/month)?",
            re.IGNORECASE
        ),
        "groups": ("min", "max"),
    },
    {
        "type": SalaryType.USD,
        "regex": re.compile(
            r"(?:\$|usd\s*)?(?P<min>\d[\d.,]*)\s*(?:usd|\$)(?:\s*/tháng|\s*/thang|\s*/month)?",
            re.IGNORECASE
        ),
        "groups": ("min",),
    },

    # Range: "10-15 triệu", "10 – 15 triệu", "10-15tr", "10 - 15 triệu/tháng"
    {
        "type": SalaryType.RANGE,
        "regex": re.compile(
            r"(?:từ\s*)?(?P<min>\d[\d.,]*)\s*[-–—]\s*(?P<max>\d[\d.,]*)\s*(?P<unit>triệu|tr|trieu|m|million|nghìn|nghin|k|ngàn|ngan)?\s*(?:/tháng|/thang|/month)?",
            re.IGNORECASE
        ),
        "groups": ("min", "max", "unit"),
    },
    # Range lặp unit: "8 Tr - 12 Tr VND", "50 Tr - 60 Tr VND", "20tr - 30tr"
    {
        "type": SalaryType.RANGE,
        "regex": re.compile(
            r"(?:từ\s*)?(?P<min>\d[\d.,]*)\s*(?P<unit1>triệu|tr|trieu|m|million|nghìn|nghin|k|ngàn|ngan|usd|đ)\s*[-–—]\s*(?P<max>\d[\d.,]*)\s*(?P<unit2>triệu|tr|trieu|m|million|nghìn|nghin|k|ngàn|ngan|usd|đ)?\s*(?:vnd|vnđ)?\s*(?:/tháng|/thang|/month)?",
            re.IGNORECASE
        ),
        "groups": ("min", "max", "unit1", "unit2"),
    },
    # Trên/Dưới X Tr VND: "Trên 25 Tr VND", "Trên 15 Tr", "Under 10tr"
    {
        "type": SalaryType.FROM,
        "regex": re.compile(
            r"(?:trên|tren|hơn|hon|from|trên\s*23|over)\s*(?P<min>\d[\d.,]*)\s*(?P<unit>triệu|tr|trieu|m|million|usd)?\s*(?:vnd|vnđ)?",
            re.IGNORECASE
        ),
        "groups": ("min", "unit"),
    },

    # Up to: "tới 20 triệu", "đến 20 triệu", "tối đa 20 triệu", "max 20 triệu"
    {
        "type": SalaryType.UP_TO,
        "regex": re.compile(
            r"(?:tới|đến|toi|den|tối đa|toi da|max|tối đa)\s*(?P<max>\d[\d.,]*)\s*(?P<unit>triệu|tr|trieu|m|million|nghìn|nghin|k|ngàn|ngan)?\s*(?:/tháng|/thang|/month)?",
            re.IGNORECASE
        ),
        "groups": ("max", "unit"),
    },

    # From: "từ 15 triệu", "từ 15tr", "min 15 triệu", "tối thiều 15 triệu"
    {
        "type": SalaryType.FROM,
        "regex": re.compile(
            r"(?:từ|tu|min|tối thiều|toi thieu)\s*(?P<min>\d[\d.,]*)\s*(?P<unit>triệu|tr|trieu|m|million|nghìn|nghin|k|ngàn|ngan)?\s*(?:/tháng|/thang|/month)?",
            re.IGNORECASE
        ),
        "groups": ("min", "unit"),
    },

    # Single number: "15 triệu", "15tr", "20 triệu/tháng"
    {
        "type": SalaryType.SINGLE,
        "regex": re.compile(
            r"^(?P<value>\d[\d.,]*)\s*(?P<unit>triệu|tr|trieu|m|million|nghìn|nghin|k|ngàn|ngan)?\s*(?:/tháng|/thang|/month)?$",
            re.IGNORECASE
        ),
        "groups": ("value", "unit"),
    },
]


def parse_number(num_str: str) -> float:
    """Parse số có thể có dấu phẩy/thập phân: '10', '10.5', '10,5', '1,000'."""
    if not num_str:
        return 0.0
    cleaned = num_str.replace(",", "")
    # Handle "1.000" (thousand sep) vs "1.5" (decimal)
    # If pattern \d{1,3}\.\d{3} → thousand separator; else decimal dot
    if re.match(r'^\d{1,3}\.\d{3}$', cleaned):
        cleaned = cleaned.replace(".", "")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def get_unit_multiplier(unit: Optional[str]) -> float:
    """Get multiplier for currency unit."""
    if not unit:
        return 1.0  # Default to triệu
    unit_lower = unit.lower().strip()
    return VND_UNITS.get(unit_lower, 1.0)


def parse_salary(salary_text: str) -> ParsedSalary:
    """Parse một chuỗi lương thành ParsedSalary.

    Returns:
        ParsedSalary với salary_min, salary_max (triệu VND/tháng),
        is_hidden, salary_type, confidence.
    """
    if not salary_text or not isinstance(salary_text, str):
        return ParsedSalary(
            original_text=str(salary_text) if salary_text else "",
            salary_type=SalaryType.UNKNOWN,
            confidence=0.0,
        )

    text = salary_text.strip()
    original = text

    # Check hidden first
    if HIDDEN_PATTERN.search(text):
        return ParsedSalary(
            original_text=original,
            is_hidden=True,
            salary_type=SalaryType.HIDDEN,
            confidence=0.95,
        )

    # Try each pattern
    for pattern_def in PATTERNS:
        match = pattern_def["regex"].search(text)
        if match:
            groups = pattern_def["groups"]
            salary_type = pattern_def["type"]

            if salary_type == SalaryType.YEARLY:
                if "min" in groups and "max" in groups:
                    min_val = parse_number(match.group("min")) * get_unit_multiplier(match.group("unit"))
                    max_val = parse_number(match.group("max")) * get_unit_multiplier(match.group("unit"))
                    # Convert yearly to monthly
                    min_val = min_val / 12
                    max_val = max_val / 12
                    return ParsedSalary(
                        salary_min=round(min_val, 1),
                        salary_max=round(max_val, 1),
                        salary_mid=round((min_val + max_val) / 2, 1),
                        original_text=original,
                        salary_type=salary_type,
                        confidence=0.9,
                    )
                elif "min" in groups:
                    min_val = parse_number(match.group("min")) * get_unit_multiplier(match.group("unit"))
                    min_val = min_val / 12
                    return ParsedSalary(
                        salary_min=round(min_val, 1),
                        salary_mid=round(min_val, 1),
                        original_text=original,
                        salary_type=salary_type,
                        confidence=0.8,
                    )

            elif salary_type == SalaryType.USD:
                if "min" in groups and "max" in groups:
                    min_usd = parse_number(match.group("min"))
                    max_usd = parse_number(match.group("max"))
                    min_vnd = min_usd * USD_TO_VND_RATE / 1_000_000  # Convert to triệu VND
                    max_vnd = max_usd * USD_TO_VND_RATE / 1_000_000
                    return ParsedSalary(
                        salary_min=round(min_vnd, 1),
                        salary_max=round(max_vnd, 1),
                        salary_mid=round((min_vnd + max_vnd) / 2, 1),
                        original_text=original,
                        salary_type=salary_type,
                        confidence=0.9,
                    )
                elif "min" in groups:
                    min_usd = parse_number(match.group("min"))
                    min_vnd = min_usd * USD_TO_VND_RATE / 1_000_000
                    return ParsedSalary(
                        salary_min=round(min_vnd, 1),
                        salary_mid=round(min_vnd, 1),
                        original_text=original,
                        salary_type=salary_type,
                        confidence=0.8,
                    )

            elif salary_type == SalaryType.RANGE:
                if "unit1" in match.groupdict() and match.group("unit1"):
                    # Range lặp unit: "8 Tr - 12 Tr VND"
                    min_unit = match.group("unit1")
                    max_unit = match.group("unit2") or min_unit
                    is_usd = "usd" in min_unit.lower() or "usd" in max_unit.lower()
                    min_val = parse_number(match.group("min"))
                    max_val = parse_number(match.group("max"))
                    if is_usd:
                        min_val = min_val * USD_TO_VND_RATE / 1_000_000
                        max_val = max_val * USD_TO_VND_RATE / 1_000_000
                    else:
                        min_val *= get_unit_multiplier(min_unit)
                        max_val *= get_unit_multiplier(max_unit)
                    if min_val > max_val:
                        min_val, max_val = max_val, min_val
                    return ParsedSalary(
                        salary_min=round(min_val, 1),
                        salary_max=round(max_val, 1),
                        salary_mid=round((min_val + max_val) / 2, 1),
                        original_text=original,
                        salary_type=salary_type,
                        confidence=0.9,
                    )
                min_val = parse_number(match.group("min")) * get_unit_multiplier(match.group("unit"))
                max_val = parse_number(match.group("max")) * get_unit_multiplier(match.group("unit"))
                # Ensure min <= max
                if min_val > max_val:
                    min_val, max_val = max_val, min_val
                return ParsedSalary(
                    salary_min=round(min_val, 1),
                    salary_max=round(max_val, 1),
                    salary_mid=round((min_val + max_val) / 2, 1),
                    original_text=original,
                    salary_type=salary_type,
                    confidence=0.9,
                )

            elif salary_type == SalaryType.UP_TO:
                max_val = parse_number(match.group("max")) * get_unit_multiplier(match.group("unit"))
                return ParsedSalary(
                    salary_max=round(max_val, 1),
                    salary_mid=round(max_val * 0.7, 1),  # Estimate mid as 70% of max
                    original_text=original,
                    salary_type=salary_type,
                    confidence=0.8,
                )

            elif salary_type == SalaryType.FROM:
                min_val = parse_number(match.group("min")) * get_unit_multiplier(match.group("unit"))
                return ParsedSalary(
                    salary_min=round(min_val, 1),
                    salary_mid=round(min_val * 1.3, 1),  # Estimate mid as 130% of min
                    original_text=original,
                    salary_type=salary_type,
                    confidence=0.8,
                )

            elif salary_type == SalaryType.SINGLE:
                val = parse_number(match.group("value")) * get_unit_multiplier(match.group("unit"))
                return ParsedSalary(
                    salary_min=round(val, 1),
                    salary_max=round(val, 1),
                    salary_mid=round(val, 1),
                    original_text=original,
                    salary_type=salary_type,
                    confidence=0.7,
                )

    # No pattern matched
    logger.warning(f"[SalaryParser] Could not parse: '{original}'")
    return ParsedSalary(
        original_text=original,
        salary_type=SalaryType.UNKNOWN,
        confidence=0.0,
    )


class SalaryParser:
    """Salary parser class với logging."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def parse(self, salary_text: str) -> ParsedSalary:
        """Parse một chuỗi lương."""
        return parse_salary(salary_text)

    def parse_column(self, df, col: str, new_min_col: str = "salary_min",
                     new_max_col: str = "salary_max", new_hidden_col: str = "salary_hidden",
                     new_mid_col: str = "salary_mid") -> pd.DataFrame:
        """Apply parse_salary to a DataFrame column.

        Args:
            df: DataFrame
            col: tên cột chứa lương raw
            new_min_col, new_max_col, new_hidden_col, new_mid_col: tên cột output

        Returns:
            DataFrame với 4 cột mới thêm vào
        """
        import pandas as pd

        df = df.copy()
        results = df[col].apply(lambda x: parse_salary(str(x) if pd.notna(x) else ""))

        df[new_min_col] = [r.salary_min for r in results]
        df[new_max_col] = [r.salary_max for r in results]
        df[new_hidden_col] = [r.is_hidden for r in results]
        df[new_mid_col] = [r.salary_mid for r in results]

        # Log parsing stats
        parsed_count = sum(1 for r in results if r.salary_type != SalaryType.UNKNOWN)
        hidden_count = sum(1 for r in results if r.is_hidden)
        self.logger.info(f"[SalaryParser] Parsed {parsed_count}/{len(df)} salaries, {hidden_count} hidden")

        return df


# For backward compatibility
def normalize_column(df, col: str) -> pd.DataFrame:
    """Wrapper function for backward compatibility."""
    parser = SalaryParser()
    return parser.parse_column(df, col)


if __name__ == "__main__":
    # Test cases
    test_cases = [
        "10-15 triệu",
        "10 – 15 triệu",
        "10-15tr",
        "tới 20 triệu",
        "đến 20 triệu",
        "từ 15 triệu",
        "80-120 triệu/năm",
        "1200-1800 USD",
        "$1500-2000",
        "cạnh tranh",
        "thỏa thuận",
        "negotiable",
        "15 triệu",
        "20M",
        "1000-2000 USD/tháng",
        "tối đa 30 triệu",
        "min 10 triệu",
        "5000-8000 USD",
    ]

    print("Testing Salary Parser:")
    print("-" * 60)
    for tc in test_cases:
        result = parse_salary(tc)
        print(f"Input: '{tc}'")
        print(f"  min={result.salary_min}, max={result.salary_max}, mid={result.salary_mid}, hidden={result.is_hidden}, type={result.salary_type.value}, conf={result.confidence}")
        print()