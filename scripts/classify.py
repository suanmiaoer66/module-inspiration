#!/usr/bin/env python3
"""Classification contract for collected images.

The classifier will read an image from COS, choose tags from config/tags.json,
and write the normalized item into data/items.json. Credentials and model
selection stay outside the repository.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TAGS_PATH = ROOT / "config" / "tags.json"


def main() -> int:
    tags = json.loads(TAGS_PATH.read_text(encoding="utf-8"))
    print(f"Loaded {len(tags['primary'])} allowed module tags.")
    print("Classifier adapter is ready for the configured vision model.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
