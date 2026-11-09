"""Command line entry point: python -m pl_analytics.download --start 2015 --end 2025"""
import argparse
from pathlib import Path

from .data import download_seasons


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Premier League season CSVs.")
    parser.add_argument("--start", type=int, default=2015, help="first season start year (2015 = 2015/16)")
    parser.add_argument("--end", type=int, default=2025, help="last season start year")
    parser.add_argument("--dest", type=Path, default=Path("data/raw"))
    args = parser.parse_args()
    files = download_seasons(args.start, args.end, args.dest)
    print(f"{len(files)} season file(s) available in {args.dest}")


if __name__ == "__main__":
    main()
