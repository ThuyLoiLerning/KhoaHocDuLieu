import json
import subprocess
import sys
from pathlib import Path

from crawl import main


def test_main_prints_summary_json(monkeypatch, tmp_path, capsys):
    def fake_run_crawl(sites, keywords, max_pages, **kwargs):
        return {
            "jobs": [],
            "skills": [],
            "companies": [],
            "summary": {
                "n_jobs": 1,
                "n_new": 1,
                "src_counts": {"itviec": 1},
                "sites": sites,
                "keywords": keywords,
                "max_pages": max_pages,
                "output_csv": str(tmp_path / "data" / "processed" / "combined.csv"),
                "history_path": str(tmp_path / "logs" / "crawl_history" / "crawl_20260804_120000.json"),
            },
        }

    monkeypatch.setattr("crawl.run_crawl", fake_run_crawl)
    code = main(["--sites", "itviec", "--max-pages", "2"])
    out = capsys.readouterr().out
    assert code == 0
    data = json.loads(out)
    assert data["n_jobs"] == 1
    assert data["sites"] == ["itviec"]


def test_cli_without_args_exits_nonzero():
    proc = subprocess.run([sys.executable, "crawl.py"], capture_output=True, text=True)
    assert proc.returncode != 0
    assert "usage:" in proc.stderr.lower()
