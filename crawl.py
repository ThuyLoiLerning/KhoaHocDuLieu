import argparse
import json
import sys
from typing import List, Optional

from src.crawl import run_crawl, DEFAULT_KEYWORDS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crawler v2 CLI")
    parser.add_argument("--sites", required=True, help="Comma-separated sites: itviec,glints,...")
    parser.add_argument("--keywords", default=",".join(DEFAULT_KEYWORDS), help="Comma-separated keywords")
    parser.add_argument("--max-pages", type=int, default=2, help="Max pages per site/keyword")
    parser.add_argument("--min-total-jobs", type=int, default=0, help="Fail if jobs < threshold")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    sites = [s.strip() for s in args.sites.split(",") if s.strip()]
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]

    try:
        result = run_crawl(
            sites=sites,
            keywords=keywords,
            max_pages=args.max_pages,
            min_total_jobs=args.min_total_jobs,
        )
        print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
