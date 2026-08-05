"""Deduplicator — phát hiện và xử lý dữ liệu trùng lặp (exact + fuzzy)."""

import logging
import hashlib
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from difflib import SequenceMatcher
from collections import defaultdict
import pandas as pd

from src.data.data_manager import cleaning_logger

logger = logging.getLogger(__name__)


@dataclass
class DuplicateGroup:
    """Nhóm các bản ghi trùng lặp."""
    kept_index: int           # Index của bản ghi giữ lại
    duplicate_indices: List[int]  # Indices của các bản ghi trùng
    match_type: str           # "exact" | "near"
    score: float              # Độ tương đồng (0-1)
    matched_fields: List[str]  # Các field trùng


class Deduplicator:
    """Phát hiện trùng lặp (exact + fuzzy) và loại bỏ.

    Yêu cầu E6, N3:
    - Exact: job_id, title + company + date
    - Fuzzy: title (80%), description (70%)
    """

    def __init__(self, title_threshold: float = 0.8, desc_threshold: float = 0.7):
        self.title_threshold = title_threshold
        self.desc_threshold = desc_threshold

    def find_duplicates(self, df: pd.DataFrame, job_id_col: str = "job_id",
                        title_col: str = "job_title",
                        company_col: str = "company_name",
                        desc_col: str = "description_raw",
                        date_col: str = "posted_at") -> List[DuplicateGroup]:
        """Find duplicate records (exact + fuzzy).

        Strategy:
        1. Exact match by job_id
        2. Exact match by title + company
        3. Fuzzy match by title (SequenceMatcher > threshold)
        4. Fuzzy match by description (if available)

        Returns:
            List of DuplicateGroup
        """
        groups = []
        processed: Set[int] = set()  # Indices already assigned to a group

        n = len(df)

        # Phase 1: Exact by job_id
        job_id_map = defaultdict(list)
        for idx, row in df.iterrows():
            job_id = row.get(job_id_col, "")
            if pd.notna(job_id) and job_id:
                job_id_map[str(job_id)].append(idx)

        for job_id, indices in job_id_map.items():
            if len(indices) > 1:
                keep = indices[0]
                dups = indices[1:]
                valid_dups = [i for i in dups if i not in processed and i != keep]
                if valid_dups:
                    groups.append(DuplicateGroup(
                        kept_index=keep,
                        duplicate_indices=valid_dups,
                        match_type="exact",
                        score=1.0,
                        matched_fields=[job_id_col],
                    ))
                    processed.update(valid_dups)

        # Phase 2: Exact by title + company
        title_company_map = defaultdict(list)
        for idx, row in df.iterrows():
            if idx in processed:
                continue
            title = str(row.get(title_col, "")).lower().strip()
            company = str(row.get(company_col, "")).lower().strip()
            key = f"{title}|{company}"
            title_company_map[key].append(idx)

        for key, indices in title_company_map.items():
            if len(indices) > 1:
                keep = indices[0]
                dups = indices[1:]
                valid_dups = [i for i in dups if i not in processed]
                if valid_dups:
                    groups.append(DuplicateGroup(
                        kept_index=keep,
                        duplicate_indices=valid_dups,
                        match_type="exact",
                        score=1.0,
                        matched_fields=[title_col, company_col],
                    ))
                    processed.update(valid_dups)

        # Phase 3: Fuzzy by title (only within same company — different
        # companies legitimately post same/similar titles)
        company_buckets = defaultdict(list)
        for i in range(n):
            if i not in processed:
                company_buckets[str(df.iloc[i].get(company_col, "")).lower().strip()].append(i)

        for company, remaining in company_buckets.items():
            if not company:
                continue
            for i in range(len(remaining)):
                if remaining[i] in processed:
                    continue
                base_idx = remaining[i]
                base_title = str(df.iloc[base_idx].get(title_col, "")).lower().strip()
                if not base_title:
                    continue

                fuzzy_group = [base_idx]
                for j in range(i + 1, len(remaining)):
                    if remaining[j] in processed:
                        continue
                    comp_idx = remaining[j]
                    comp_title = str(df.iloc[comp_idx].get(title_col, "")).lower().strip()
                    if not comp_title:
                        continue

                    # Check if one contains the other
                    if base_title in comp_title or comp_title in base_title:
                        score = min(1.0, len(base_title) / max(len(comp_title), 1))
                        if score >= self.title_threshold:
                            fuzzy_group.append(comp_idx)
                            continue

                    # Sequence matcher
                    score = SequenceMatcher(None, base_title, comp_title).ratio()
                    if score >= self.title_threshold:
                        fuzzy_group.append(comp_idx)

                if len(fuzzy_group) > 1:
                    keep = fuzzy_group[0]
                    dups = fuzzy_group[1:]
                    valid_dups = [i for i in dups if i not in processed]
                    if valid_dups:
                        groups.append(DuplicateGroup(
                            kept_index=keep,
                            duplicate_indices=valid_dups,
                            match_type="near",
                            score=score,  # Last score
                            matched_fields=[title_col],
                        ))
                        processed.update(valid_dups)

        # Phase 4: Fuzzy by description (only within same company, expensive, skip if too many)
        if desc_col and desc_col in df.columns and len(remaining) < 500:
            company_buckets = defaultdict(list)
            for i in range(n):
                if i not in processed:
                    company_buckets[str(df.iloc[i].get(company_col, "")).lower().strip()].append(i)

            for company, remaining in company_buckets.items():
                if not company:
                    continue
                for i in range(len(remaining)):
                    if remaining[i] in processed:
                        continue
                    base_idx = remaining[i]
                    base_desc = str(df.iloc[base_idx].get(desc_col, "")).lower().strip()
                    if len(base_desc) < 30:  # Too short
                        continue

                    desc_group = [base_idx]
                    for j in range(i + 1, len(remaining)):
                        if remaining[j] in processed:
                            continue
                        comp_idx = remaining[j]
                        comp_desc = str(df.iloc[comp_idx].get(desc_col, "")).lower().strip()
                        if len(comp_desc) < 30:
                            continue

                        score = SequenceMatcher(None, base_desc, comp_desc).ratio()
                        if score >= self.desc_threshold:
                            desc_group.append(comp_idx)

                    if len(desc_group) > 1:
                        keep = desc_group[0]
                        dups = desc_group[1:]
                        valid_dups = [i for i in dups if i not in processed]
                        if valid_dups:
                            groups.append(DuplicateGroup(
                                kept_index=keep,
                                duplicate_indices=valid_dups,
                                match_type="near",
                                score=score,
                                matched_fields=[desc_col],
                            ))
                            processed.update(valid_dups)

        logger.info(f"[Deduplicator] Found {len(groups)} duplicate groups, removing {len(processed)} records")
        return groups

    def remove_duplicates(self, df: pd.DataFrame, groups: List[DuplicateGroup],
                          keep: str = "first") -> pd.DataFrame:
        """Remove duplicate records from DataFrame.

        Args:
            df: DataFrame
            groups: List of DuplicateGroup from find_duplicates()
            keep: Which to keep ("first" | "last" — currently always first)

        Returns:
            Deduplicated DataFrame
        """
        drop_indices = set()
        for group in groups:
            drop_indices.update(group.duplicate_indices)

        result = df.drop(index=list(drop_indices)).reset_index(drop=True)
        logger.info(f"[Deduplicator] Removed {len(drop_indices)} duplicates, {len(result)} remaining")
        return result

    def log_duplicates(self, df: pd.DataFrame, groups: List[DuplicateGroup],
                       job_id_col: str = "job_id",
                       title_col: str = "job_title"):
        """Log all detected duplicates to cleaning_errors.log."""
        for group in groups:
            keep_row = df.iloc[group.kept_index]
            keep_id = str(keep_row.get(job_id_col, ""))

            for dup_idx in group.duplicate_indices:
                dup_row = df.iloc[dup_idx]
                dup_id = str(dup_row.get(job_id_col, ""))
                dup_title = str(dup_row.get(title_col, ""))

                cleaning_logger.info(
                    f"DUPLICATE|{dup_id}|{group.match_type}|{group.score:.2f}|matched_on:{','.join(group.matched_fields)}|keep:{keep_id}|dup_title:{dup_title}"
                )

    def analyze_duplicates(self, df: pd.DataFrame, groups: List[DuplicateGroup]) -> Dict:
        """Phân tích thống kê trùng lặp."""
        return {
            "total_groups": len(groups),
            "total_duplicates": sum(len(g.duplicate_indices) for g in groups),
            "exact_duplicates": sum(1 for g in groups if g.match_type == "exact"),
            "near_duplicates": sum(1 for g in groups if g.match_type == "near"),
            "avg_score": sum(g.score for g in groups) / len(groups) if groups else 0,
        }


if __name__ == "__main__":
    # Test
    import pandas as pd

    data = pd.DataFrame({
        "job_id": ["job_1", "job_2", "job_1", "job_3", "job_4"],
        "job_title": ["Backend Developer", "Frontend Developer", "Backend Developer",
                       "Backend Dev", "Frontend Developer"],
        "company_name": ["FPT", "VNG", "FPT", "FPT", "VNG Corp"],
        "description_raw": [
            "Python Django REST API",
            "React TypeScript CSS",
            "Python Django REST API",
            "Python Django",
            "React TypeScript and CSS for web",
        ],
        "posted_at": ["2025-06-01", "2025-06-02", "2025-06-01", "2025-06-03", "2025-06-02"],
    })

    dedup = Deduplicator()
    groups = dedup.find_duplicates(data)
    for g in groups:
        print(f"  Type={g.match_type}, Score={g.score:.2f}, Fields={g.matched_fields}")
        print(f"    Keep idx={g.kept_index}: {data.iloc[g.kept_index]['job_title']}")
        for d in g.duplicate_indices:
            print(f"    Drop idx={d}: {data.iloc[d]['job_title']}")

    result = dedup.remove_duplicates(data, groups)
    print(f"\nOriginal: {len(data)}, After dedup: {len(result)}")