"""Chuẩn hóa tên vị trí công việc (Yêu cầu E3).

Map: "Frontend Dev" -> "Frontend Developer", "Data Eng" -> "Data Engineer".
"""

import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Map viết tắt -> đầy đủ
TITLE_ABBREVIATIONS: Dict[str, str] = {
    "dev": "Developer", "devel": "Developer", "devloper": "Developer",
    "eng": "Engineer", "engr": "Engineer", "engineer": "Engineer",
    "mgmt": "Management", "mgr": "Manager", "manag": "Manager",
    "arch": "Architect", "archt": "Architect",
    "analyst": "Analyst", "anlst": "Analyst",
    "admin": "Administrator", "adm": "Administrator",
    "coord": "Coordinator", "coor": "Coordinator",
    "spec": "Specialist", "specalist": "Specialist",
    "consult": "Consultant", "conslt": "Consultant",
    "intern": "Intern", "internship": "Intern",
    "jr": "Junior", "jr.": "Junior", "jun": "Junior",
    "sr": "Senior", "sr.": "Senior", "snr": "Senior",
    "lead": "Lead",
    "principal": "Principal",
    "staff": "Staff",
    "fresher": "Fresher",
}

# Map từ viết tắt vai trò -> chuẩn
ROLE_NORMALIZATION: Dict[str, str] = {
    "fe": "Frontend", "front-end": "Frontend", "front end": "Frontend",
    "be": "Backend", "back-end": "Backend", "back end": "Backend",
    "fs": "Fullstack", "full-stack": "Fullstack", "full stack": "Fullstack",
    "fullstack": "Fullstack",
    "ml": "Machine Learning", "machinelearning": "Machine Learning",
    "ai": "AI", "artificial intelligence": "AI",
    "ui": "UI", "ux": "UX", "ui/ux": "UI/UX", "ui ux": "UI/UX",
    "devops": "DevOps", "dev ops": "DevOps",
    "data": "Data", "big data": "Data",
    "cloud": "Cloud",
    "blockchain": "Blockchain",
    "mobile": "Mobile",
    "game": "Game",
    "embedded": "Embedded",
    "sre": "SRE", "site reliability": "SRE",
    "qa": "QA", "quality assurance": "QA",
    "tester": "Tester", "test": "Tester",
    "bi": "BI", "business intelligence": "BI",
    "erp": "ERP",
    "crm": "CRM",
    "sap": "SAP",
    "hr": "HR", "human resources": "HR",
    "it": "IT", "information technology": "IT",
}

# Domain-specific role phrases to keep
TECH_PREFIXES = [
    "Senior", "Junior", "Lead", "Principal", "Staff", "Head of",
    "Fresher", "Intern", "Expert",
]

SENIORITY_ORDER = ["Fresher", "Intern", "Junior", "Senior", "Lead", "Principal", "Staff", "Head of"]


def normalize_title(title: str) -> str:
    """Chuẩn hóa tên vị trí công việc.

    >>> normalize_title("frontend dev")
    'Frontend Developer'
    >>> normalize_title("sr data engineer")
    'Senior Data Engineer'
    >>> normalize_title("fe developer")
    'Frontend Developer'
    """
    if not title or not isinstance(title, str):
        return title

    title = title.strip()

    # Lowercase for processing
    lower = title.lower()

    # 1. Normalize seniroty prefixes
    for abbr, full in sorted(TITLE_ABBREVIATIONS.items(), key=lambda x: -len(x[0])):
        # Word boundary replacement
        lower = re.sub(r'\b' + re.escape(abbr) + r'\b', full.lower(), lower)

    # 2. Normalize role names
    for abbr, full in ROLE_NORMALIZATION.items():
        lower = re.sub(r'\b' + re.escape(abbr) + r'\b', full.lower(), lower)

    # 3. Title case
    tokens = lower.split()
    result = []
    for token in tokens:
        # Keep common acronyms uppercase
        if token.upper() in ("AI", "UI", "UX", "BI", "QA", "ERP", "CRM", "SAP", "HR", "IT", "SRE", "ML", "AWS", "GCP"):
            result.append(token.upper())
        elif token in ("and", "or", "the", "of", "in", "at", "&"):
            result.append(token.lower())
        else:
            result.append(token.capitalize())

    normalized = " ".join(result)

    # 4. Fix common casing patterns
    normalized = normalized.replace("Ui/", "UI/").replace("Ux", "UX")
    normalized = normalized.replace("Ai ", "AI ").replace(" Ml ", " ML ")

    return normalized


class TitleNormalizer:
    """Normalize job titles to canonical forms."""

    def __init__(self):
        self.stats = {"total": 0, "changed": 0}

    def normalize(self, title: str) -> str:
        """Normalize a single job title."""
        self.stats["total"] += 1
        normalized = normalize_title(title)
        if normalized != title:
            self.stats["changed"] += 1
            logger.debug(f"  Title: '{title}' -> '{normalized}'")
        return normalized

    def normalize_dataframe(self, df, column: str = "job_title") -> dict:
        """Normalize a column in DataFrame.

        Returns dict with stats.
        """
        from tqdm import tqdm

        titles_orig = df[column].dropna().unique()
        mapping = {}
        for t in tqdm(titles_orig, desc="Normalizing titles"):
            mapping[t] = self.normalize(t)

        df[column] = df[column].map(lambda x: mapping.get(x, x))

        logger.info(
            f"Title normalization: {self.stats['changed']}/{self.stats['total']} "
            f"({self.stats['changed']/max(self.stats['total'],1)*100:.1f}%) changed"
        )
        return dict(self.stats)


if __name__ == "__main__":
    # Quick test
    samples = [
        "Frontend Dev",
        "Sr Data Engineer",
        "fe developer",
        "Back-end Developer",
        "ML Engineer",
        "QA Tester",
        "UI/UX Designer",
        "DevOps Lead",
        "Full Stack Developer",
        "Data Analyst",
        "AI Engineer",
        "Sr. Software Architect",
        "Jr Front-end Dev",
        "Blockchain Developer",
        "SRE Engineer",
    ]
    for s in samples:
        print(f"  '{s}' -> '{normalize_title(s)}'")
