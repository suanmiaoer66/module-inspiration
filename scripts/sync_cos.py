#!/usr/bin/env python3
"""Upload a collected manifest to Tencent Cloud COS and normalize items.json.

Collectors write staging/manifest.json. The manifest can be a list or an
object with an `items` list. Each item may contain:

  id, thumbnailPath, largeImagePath, tags, curated, recent

No source URL is exposed to the frontend. COS URLs are generated from the
configured CDN/domain value.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "staging" / "manifest.json"
ITEMS_PATH = ROOT / "data" / "items.json"
TAGS_PATH = ROOT / "config" / "tags.json"


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def load_json(path: Path, fallback):
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_domain(value: str) -> str:
    return value.rstrip("/")


def normalize_tags(raw_tags, allowed: set[str], aliases: dict[str, str]) -> list[str]:
    tags = []
    for raw_tag in raw_tags or []:
        tag = aliases.get(str(raw_tag), str(raw_tag))
        if tag in allowed and tag not in tags:
            tags.append(tag)
    return tags[:3]


def upload(client: CosS3Client, bucket: str, path: Path, key: str) -> None:
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    client.put_object_from_local_file(
        Bucket=bucket,
        LocalFilePath=str(path),
        Key=key,
        ContentType=content_type,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--items", type=Path, default=ITEMS_PATH)
    args = parser.parse_args()

    if not args.manifest.exists():
        print(f"No manifest found at {args.manifest}; COS sync skipped.")
        return 0

    from qcloud_cos import CosConfig, CosS3Client

    secret_id = required_env("TENCENT_SECRET_ID")
    secret_key = required_env("TENCENT_SECRET_KEY")
    region = required_env("COS_REGION")
    bucket = required_env("COS_BUCKET")
    domain = normalize_domain(required_env("COS_DOMAIN"))

    tag_config = load_json(TAGS_PATH, {"primary": [], "aliases": {}})
    allowed_tags = set(tag_config.get("primary", []))
    aliases = tag_config.get("aliases", {})
    manifest = load_json(args.manifest, [])
    incoming = manifest.get("items", []) if isinstance(manifest, dict) else manifest
    if not isinstance(incoming, list):
        raise RuntimeError("Manifest must contain an items list.")

    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Scheme="https")
    client = CosS3Client(config)
    existing = load_json(args.items, [])
    by_id = {item.get("id"): item for item in existing if item.get("id")}
    today = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    synced = 0

    for item in incoming:
        item_id = str(item.get("id", "")).strip()
        if not item_id:
            print("Skipping manifest item without id.")
            continue
        tags = normalize_tags(item.get("tags"), allowed_tags, aliases)
        thumb_path = Path(item.get("thumbnailPath", ""))
        large_path = Path(item.get("largeImagePath", ""))
        if not thumb_path.is_absolute():
            thumb_path = ROOT / thumb_path
        if not large_path.is_absolute():
            large_path = ROOT / large_path
        if not thumb_path.exists() or not large_path.exists():
            print(f"Skipping {item_id}: thumbnailPath or largeImagePath is missing.")
            continue

        thumb_key = f"inspiration/{today}/{item_id}-thumb{thumb_path.suffix.lower()}"
        large_key = f"inspiration/{today}/{item_id}-large{large_path.suffix.lower()}"
        upload(client, bucket, thumb_path, thumb_key)
        upload(client, bucket, large_path, large_key)
        by_id[item_id] = {
            "id": item_id,
            "imageUrl": f"{domain}/{thumb_key}",
            "largeImageUrl": f"{domain}/{large_key}",
            "tags": tags,
            "curated": bool(item.get("curated", False)),
            "recent": True,
            "status": "published" if tags else "pending_review",
            "createdAt": item.get("createdAt", datetime.now(timezone.utc).isoformat()),
        }
        synced += 1

    args.items.write_text(json.dumps(list(by_id.values()), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"COS sync complete: {synced} item(s) uploaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
