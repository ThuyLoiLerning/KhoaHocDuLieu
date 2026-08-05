import json
from pathlib import Path

import pandas as pd
import pytest

from src.crawl import pipeline
from src.crawl.pipeline import run_crawl
from src.domain.job_record import JobRecord


def test_run_crawl_merges_dedupes_and_writes_csv(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(pipeline, "PROCESSED_DIR", tmp_path / "data" / "processed")
    monkeypatch.setattr(pipeline, "HISTORY_DIR", tmp_path / "logs" / "crawl_history")
    monkeypatch.setattr(pipeline, "OUTPUT_CSV", tmp_path / "data" / "processed" / "combined.csv")

    def fake_fetch_site(site_name, keyword, max_pages, client=None):
        return [
            {
                "job_id": "itviec_abcd1234",
                "job_title": "Backend Developer",
                "company_name": "FPT",
                "city": "HCMC",
                "source_site": site_name,
                "source_url": f"https://example.test/{site_name}/1",
                "salary_raw": "10-15 triệu",
                "description_raw": "Python Django",
                "skills_raw": ["Python"],
            }
        ]

    def fake_normalize_raw_jobs(raw_jobs):
        return [
            JobRecord(
                job_id=raw_jobs[0]["job_id"],
                job_title=raw_jobs[0]["job_title"],
                company_id="comp_1234abcd",
                company_name=raw_jobs[0]["company_name"],
                city=raw_jobs[0]["city"],
                source_site=raw_jobs[0]["source_site"],
                source_url=raw_jobs[0]["source_url"],
                salary_raw=raw_jobs[0]["salary_raw"],
                description_raw=raw_jobs[0]["description_raw"],
            )
        ]

    monkeypatch.setattr(pipeline, "fetch_site", fake_fetch_site)
    monkeypatch.setattr(pipeline, "normalize_raw_jobs", fake_normalize_raw_jobs)

    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    existing = pd.DataFrame([
        {
            "job_id": "itviec_abcd1234",
            "job_title": "Backend Developer",
            "company_name": "FPT",
            "company_id": "comp_1234abcd",
            "city": "HCMC",
            "source_site": "itviec",
            "source_url": "https://example.test/itviec/1",
            "salary_raw": "10-15 triệu",
            "description_raw": "Python Django",
        }
    ])
    existing.to_csv(processed_dir / "combined.csv", index=False, encoding="utf-8-sig")

    result = run_crawl(["itviec"], ["python"], 1)

    assert result["summary"]["n_jobs"] == 1
    assert result["summary"]["n_new"] == 0
    assert (processed_dir / "combined.csv").exists()
    assert not list(processed_dir.glob("*.parquet"))
    history_dir = tmp_path / "logs" / "crawl_history"
    assert history_dir.exists()
    assert len(list(history_dir.glob("crawl_*.json"))) == 1
    history = json.loads(list(history_dir.glob("crawl_*.json"))[0].read_text(encoding="utf-8"))
    assert history["n_jobs"] == 1


def test_run_crawl_raises_below_threshold(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(pipeline, "PROCESSED_DIR", tmp_path / "data" / "processed")
    monkeypatch.setattr(pipeline, "HISTORY_DIR", tmp_path / "logs" / "crawl_history")
    monkeypatch.setattr(pipeline, "OUTPUT_CSV", tmp_path / "data" / "processed" / "combined.csv")

    monkeypatch.setattr(pipeline, "fetch_site", lambda *a, **k: [])
    monkeypatch.setattr(pipeline, "normalize_raw_jobs", lambda raw_jobs: [])

    with pytest.raises(RuntimeError, match="below threshold"):
        run_crawl(["itviec"], ["python"], 1, min_total_jobs=1)
