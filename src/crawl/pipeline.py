"""Pipeline orchestrator for Crawler v2."""

from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.cleaning.deduplicator import Deduplicator
from src.crawl.fetchers import HttpClient, fetch_site
from src.crawl.normalizer import normalize_raw_jobs
from src.data.data_manager import JobDataManager
from src.domain.job_record import JobRecord

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
HISTORY_DIR = PROJECT_ROOT / "logs" / "crawl_history"
OUTPUT_CSV = PROCESSED_DIR / "combined.csv"


def run_crawl(
    sites: List[str],
    keywords: List[str],
    max_pages: int = 2,
    *,
    min_total_jobs: int = 0,
    client: Optional[Any] = None,
) -> Dict[str, Any]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    http_client = client or HttpClient()
    raw_jobs: List[Dict[str, Any]] = []
    src_counts: Dict[str, int] = {site: 0 for site in sites}

    for site in sites:
        for kw in keywords:
            try:
                fetched = fetch_site(site, kw, max_pages=max_pages, client=http_client)
                raw_jobs.extend(fetched)
                src_counts[site] = src_counts.get(site, 0) + len(fetched)
            except Exception as e:
                logger.error(f"Error crawling {site} for keyword '{kw}': {e}")
                raise

    records: List[JobRecord] = normalize_raw_jobs(raw_jobs)

    if len(records) < min_total_jobs:
        raise RuntimeError(
            f"Crawl below threshold: {len(records)} < {min_total_jobs} "
            f"({src_counts}). No CSV written."
        )

    # Save raw data (B6: data/raw/ CSV + JSON) before merge
    if records:
        dm = JobDataManager(raw_dir=str(DATA_DIR / "raw"), processed_dir=str(PROCESSED_DIR))
        try:
            per_site: Dict[str, List[JobRecord]] = {}
            for r in records:
                per_site.setdefault(r.source_site, []).append(r)
            for site, site_recs in per_site.items():
                job_postings = [r.to_job_posting() for r in site_recs]
                dm.save_raw_jobs(job_postings, site)
                all_skills = [s for r in site_recs for s in r.skills]
                if all_skills:
                    dm.save_raw_skills(all_skills, site)
                companies = {r.company_id: r.to_company() for r in site_recs}
                if companies:
                    dm.save_raw_companies(list(companies.values()), site)
            logger.info(f"Saved raw data: {len(records)} jobs -> data/raw/")
        except Exception as e:
            logger.warning(f"Could not save raw data: {e}")

    job_dicts = [r.to_job_dict() for r in records]
    new_df = pd.DataFrame(job_dicts)

    existing_df = pd.DataFrame()
    if OUTPUT_CSV.exists():
        try:
            existing_df = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")
        except Exception as e:
            logger.warning(f"Could not read existing combined.csv: {e}")

    if not existing_df.empty and not new_df.empty:
        merged_df = pd.concat([existing_df, new_df], ignore_index=True)
    elif not new_df.empty:
        merged_df = new_df
    else:
        merged_df = existing_df

    if not merged_df.empty:
        dedup = Deduplicator()
        dup_groups = dedup.find_duplicates(merged_df)
        final_df = dedup.remove_duplicates(merged_df, dup_groups)
    else:
        final_df = merged_df

    n_final = len(final_df)
    n_existing = len(existing_df)
    n_new = max(0, n_final - n_existing)

    final_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    history_path = HISTORY_DIR / f"crawl_{timestamp}.json"
    history_data = {
        "timestamp": timestamp,
        "n_jobs": n_final,
        "n_new": n_new,
        "src_counts": src_counts,
        "sites": sites,
        "keywords": keywords,
        "max_pages": max_pages,
    }
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)

    return {
        "jobs": records,
        "skills": [s for r in records for s in r.skills],
        "companies": [r.to_company_dict() for r in records],
        "summary": {
            "n_jobs": n_final,
            "n_new": n_new,
            "src_counts": src_counts,
            "sites": sites,
            "keywords": keywords,
            "max_pages": max_pages,
            "output_csv": str(OUTPUT_CSV),
            "history_path": str(history_path),
        },
    }
