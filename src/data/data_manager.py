"""Data layer: đọc, ghi, merge, log dữ liệu."""

import pandas as pd
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from src.domain.job_posting import JobPosting
from src.domain.skill import Skill
from src.domain.company import Company

# Project root = ../../ from this file's directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _get_log_dir() -> Path:
    d = _PROJECT_ROOT / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


# Logger cho cleaning errors
cleaning_logger = logging.getLogger("cleaning_errors")
cleaning_logger.setLevel(logging.INFO)
cleaning_handler = logging.FileHandler(str(_get_log_dir() / "cleaning_errors.log"), encoding="utf-8")
cleaning_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
cleaning_logger.addHandler(cleaning_handler)

# Logger cho source metadata
source_logger = logging.getLogger("source_metadata")
source_logger.setLevel(logging.INFO)
source_handler = logging.FileHandler(str(_get_log_dir() / "source_metadata.log"), encoding="utf-8")
source_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
source_logger.addHandler(source_handler)


class JobDataManager:
    """Quản lý dữ liệu: load/save CSV/JSON/Parquet, merge, log."""

    def __init__(
        self,
        raw_dir: str = "data/raw",
        processed_dir: str = "data/processed",
    ):
        # Resolve relative paths from CWD; absolute paths as-is
        raw_path = Path(raw_dir)
        self.raw_dir = raw_path.resolve() if not raw_path.is_absolute() else raw_path
        proc_path = Path(processed_dir)
        self.processed_dir = proc_path.resolve() if not proc_path.is_absolute() else proc_path
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    # ========== SAVE RAW ==========
    def save_raw_jobs(self, jobs: List[JobPosting], source_site: str) -> Path:
        """Lưu raw jobs ra CSV + JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = self.raw_dir / f"raw_jobs_{source_site}_{timestamp}.csv"
        json_path = self.raw_dir / f"raw_jobs_{source_site}_{timestamp}.json"

        records = [job.to_dict() for job in jobs]
        df = pd.DataFrame(records)

        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

        # Log source metadata
        for job in jobs:
            source_logger.info(f"{job.job_id}|{source_site}|{job.source_url}|{job.crawled_at.isoformat()}")

        return csv_path

    def save_raw_skills(self, skills: List[Skill], source_site: str) -> Path:
        """Lưu raw skills ra CSV."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = self.raw_dir / f"raw_skills_{source_site}_{timestamp}.csv"

        records = [s.to_dict() for s in skills]
        df = pd.DataFrame(records)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        return csv_path

    def save_raw_companies(self, companies: List[Company], source_site: str) -> Path:
        """Lưu raw companies ra CSV."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = self.raw_dir / f"raw_companies_{source_site}_{timestamp}.csv"

        records = [c.to_dict() for c in companies]
        df = pd.DataFrame(records)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        return csv_path

    def save_raw_html(self, html: str, job_id: str, source_site: str) -> Path:
        """Lưu raw HTML để truy xuất lại."""
        html_dir = self.raw_dir / "html"
        html_dir.mkdir(exist_ok=True)
        html_path = html_dir / f"{source_site}_{job_id}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        return html_path

    # ========== LOAD RAW ==========
    def load_raw_jobs(self, pattern: str = "raw_jobs_*.csv") -> pd.DataFrame:
        """Load tất cả raw jobs CSV thành DataFrame."""
        files = list(self.raw_dir.glob(pattern))
        if not files:
            return pd.DataFrame()
        dfs = [pd.read_csv(f, encoding="utf-8-sig") for f in files]
        return pd.concat(dfs, ignore_index=True)

    def load_raw_skills(self, pattern: str = "raw_skills_*.csv") -> pd.DataFrame:
        files = list(self.raw_dir.glob(pattern))
        if not files:
            return pd.DataFrame()
        dfs = [pd.read_csv(f, encoding="utf-8-sig") for f in files]
        return pd.concat(dfs, ignore_index=True)

    def load_raw_companies(self, pattern: str = "raw_companies_*.csv") -> pd.DataFrame:
        files = list(self.raw_dir.glob(pattern))
        if not files:
            return pd.DataFrame()
        dfs = [pd.read_csv(f, encoding="utf-8-sig") for f in files]
        return pd.concat(dfs, ignore_index=True)

    # ========== MERGE & CLEAN ==========
    def merge_datasets(
        self,
        jobs_df: pd.DataFrame,
        skills_df: pd.DataFrame,
        companies_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Merge 3 bảng thành denormalized DataFrame cho EDA/ML."""
        # jobs + companies
        merged = jobs_df.merge(
            companies_df,
            on="company_id",
            how="left",
            suffixes=("", "_company"),
        )

        # jobs + skills (aggregate skills per job) - skip if already present from pipeline
        if not skills_df.empty and "skills" not in merged.columns:
            skills_agg = skills_df.groupby("job_id").agg({
                "skill_name": lambda x: list(x),
                "skill_group": lambda x: list(x),
                "required_level": lambda x: list(x),
                "original_name": lambda x: list(x),
            }).reset_index()
            skills_agg.columns = ["job_id", "skills", "skill_groups", "skill_levels", "skill_originals"]
            merged = merged.merge(skills_agg, on="job_id", how="left")

        return merged

    def save_processed(self, df: pd.DataFrame, name: str) -> Path:
        """Lưu processed data ra Parquet."""
        import numpy as np
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.processed_dir / f"{name}_{timestamp}.parquet"
        df_out = df.copy()
        # Convert list columns to numpy arrays for parquet compatibility
        list_cols = ["skills", "skill_groups", "skill_levels", "skill_originals"]
        for col in list_cols:
            if col in df_out.columns:
                df_out[col] = df_out[col].apply(
                    lambda x: np.array(x, dtype=object) if isinstance(x, (list, np.ndarray)) else x
                )
        df_out.to_parquet(path, index=False)
        return path

    def load_processed(self, pattern: str = "*.parquet") -> pd.DataFrame:
        """Load latest processed parquet."""
        import ast, numpy as np
        files = list(self.processed_dir.glob(pattern))
        if not files:
            return pd.DataFrame()
        latest = max(files, key=lambda f: f.stat().st_mtime)
        df = pd.read_parquet(latest)
        # Convert string repr of lists back to actual lists
        list_cols = ["skills", "skill_groups", "skill_levels", "skill_originals"]
        for col in list_cols:
            if col in df.columns and df[col].dtype == "object":
                sample = df[col].dropna().iloc[0] if df[col].notna().any() else None
                if sample is not None:
                    if isinstance(sample, str) and sample.startswith("["):
                        df[col] = df[col].apply(
                            lambda x: ast.literal_eval(x) if pd.notna(x) and isinstance(x, str) and x.startswith("[") else x
                        )
                    elif isinstance(sample, np.ndarray):
                        # Already array, keep as-is
                        pass
        return df

    # ========== LOGGING ==========
    def log_cleaning_error(self, job_id: str, field: str, issue: str, original_value: str, fixed_value: str):
        """Ghi lỗi làm sạch."""
        cleaning_logger.info(f"{job_id}|{field}|{issue}|{original_value}|{fixed_value}")

    def log_deduplication(self, job_id: str, dup_type: str, matched_job_id: str):
        """Ghi log trùng lặp."""
        cleaning_logger.info(f"DUPLICATE|{job_id}|{dup_type}|{matched_job_id}")

    def get_cleaning_stats(self) -> Dict:
        """Thống kê từ cleaning log."""
        log_path = _get_log_dir() / "cleaning_errors.log"
        if not log_path.exists():
            return {"total": 0}
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return {"total_lines": len(lines), "sample": lines[-5:] if len(lines) >= 5 else lines}

    # ========== INJECT DIRTY DATA (for A8) ==========
    def inject_dirty_data(
        self,
        jobs_df: pd.DataFrame,
        missing_rate: float = 0.15,
        duplicate_rate: float = 0.03,
        typo_rate: float = 0.05,
        random_seed: int = 42,
    ) -> pd.DataFrame:
        """Inject missing, duplicate, typo để có dữ liệu bẩn xử lý (Yêu cầu A8).

        Quan trọng: Giữ lại bản gốc trước khi inject, log những gì đã inject.
        """
        import numpy as np
        np.random.seed(random_seed)
        df = jobs_df.copy()
        n = len(df)

        # 1. Missing values
        n_missing = int(n * missing_rate)
        missing_indices = np.random.choice(n, n_missing, replace=False)
        missing_fields = ["salary_min", "salary_max", "experience_years", "education_level", "remote_option"]
        for idx in missing_indices:
            field = np.random.choice(missing_fields)
            original = df.iloc[idx][field]
            df.iloc[idx, df.columns.get_loc(field)] = np.nan
            self.log_cleaning_error(
                df.iloc[idx]["job_id"], field, "INJECTED_MISSING",
                str(original), "NaN"
            )

        # 2. Duplicates (exact + near)
        n_dup = int(n * duplicate_rate)
        dup_indices = np.random.choice(n, n_dup, replace=False)
        dup_rows = df.iloc[dup_indices].copy()
        # Modify slightly for near-duplicates
        for i, row in dup_rows.iterrows():
            # Change job_id slightly
            new_id = row["job_id"] + "_dup"
            dup_rows.at[i, "job_id"] = new_id
            # Maybe change salary slightly
            if pd.notna(row["salary_min"]):
                dup_rows.at[i, "salary_min"] = row["salary_min"] + np.random.uniform(-1, 1)
        df = pd.concat([df, dup_rows], ignore_index=True)
        for _, row in dup_rows.iterrows():
            self.log_deduplication(row["job_id"], "INJECTED_NEAR_DUP", row["job_id"].replace("_dup", ""))

        # 3. Typos in skill names (will be caught by skill_normalizer)
        # This is handled in skill cleaning, not here

        return df