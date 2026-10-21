#!/usr/bin/env python3
"""Collection entry point.

The first version is deliberately dry-run friendly. Source-specific adapters
will be added only after each site's public access rules are checked.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = ROOT / "config" / "sources.json"


def load_sources() -> list[dict]:
    return json.loads(SOURCES_PATH.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="List and later collect configured inspiration sources.")
    parser.add_argument("--source", help="Only inspect one source by id.")
    parser.add_argument("--dry-run", action="store_true", help="Only list enabled sources; do not download anything.")
    args = parser.parse_args()

    sources = [source for source in load_sources() if source.get("enabled")]
    if args.source:
        sources = [source for source in sources if source["id"] == args.source]

    if not sources:
        print("No enabled source matched.")
        return 1

    for source in sources:
        mode = "dry-run" if args.dry_run else source.get("status", "needs_adapter")
        print(f"[{mode}] {source['id']}: {source['name']} -> {source['url']}")

    if not args.dry_run:
        print("No downloader ran yet. Add and validate a source adapter before enabling downloads.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
