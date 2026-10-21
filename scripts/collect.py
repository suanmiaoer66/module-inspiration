#!/usr/bin/env python3
"""Collect a small batch of publicly rendered image previews.

This collector intentionally stays conservative:
- only configured enabled_candidate sources are touched by default;
- no login, API, search route, captcha, or bypass behavior;
- each run has an explicit item limit and a short delay between downloads;
- results are written to staging/manifest.json for review and COS sync.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import mimetypes
import re
import shutil
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = ROOT / "config" / "sources.json"
STAGING_PATH = ROOT / "staging"
MANIFEST_PATH = STAGING_PATH / "manifest.json"

SOURCE_RULES = {
    "applore": {
        "allowed_hosts": {"icon.uiboy.com"},
        "required_path": "/shots/",
    },
    "meiye": {
        "allowed_hosts": {"image.meiye.art", "zpjcdn.meiye.art"},
        "required_path": None,
    },
}

USER_AGENT = "module-inspiration-collector/0.1 (+public-preview-only)"
URL_RE = re.compile(r"""https?://[^"'<>\s]+""", re.IGNORECASE)
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".gif")


def load_json(path: Path, fallback):
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def fetch(url: str, accept: str) -> tuple[bytes, str]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urlopen(request, timeout=25) as response:
        content_type = response.headers.get("Content-Type", "")
        return response.read(), content_type


def source_allowed(url: str, source_id: str) -> bool:
    parsed = urlparse(url)
    rule = SOURCE_RULES.get(source_id)
    if not rule or parsed.scheme not in {"http", "https"}:
        return False
    if parsed.hostname not in rule["allowed_hosts"]:
        return False
    required_path = rule.get("required_path")
    if required_path and not parsed.path.startswith(required_path):
        return False
    if source_id == "meiye":
        if parsed.hostname == "zpjcdn.meiye.art":
            return parsed.path.startswith("/pins/")
        if parsed.hostname == "image.meiye.art":
            return parsed.path.startswith("/pic_")
    return True


def extract_urls(page: bytes, source_id: str) -> list[str]:
    text = html.unescape(page.decode("utf-8", errors="ignore"))
    text = text.replace("\\u0026", "&").replace("\\/", "/")
    found: list[str] = []
    seen: set[str] = set()
    for raw_url in URL_RE.findall(text):
        url = raw_url.rstrip("\\),;]}")
        if not source_allowed(url, source_id):
            continue
        path = urlparse(url).path.lower()
        if not path.endswith(IMAGE_EXTENSIONS) and "/shots/" not in path and "/pins/" not in path and "/pic_" not in path:
            continue
        if url not in seen:
            seen.add(url)
            found.append(url)
    return found


def item_id(source_id: str, url: str) -> str:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    return f"{source_id}-{digest}"


def file_extension(url: str, content_type: str) -> str:
    query = urlparse(url).query.lower()
    if "format=webp" in query or content_type.lower().split(";", 1)[0].strip() == "image/webp":
        return ".webp"
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return suffix
    guessed = mimetypes.guess_extension(content_type.split(";", 1)[0].strip())
    return guessed if guessed in IMAGE_EXTENSIONS else ".webp"


def collect_source(source: dict, limit: int, delay: float) -> list[dict]:
    source_id = source["id"]
    if source_id not in SOURCE_RULES:
        return []
    page, _ = fetch(source["url"], "text/html,application/xhtml+xml")
    urls = extract_urls(page, source_id)[:limit]
    raw_dir = STAGING_PATH / "raw" / source_id
    image_dir = STAGING_PATH / "images"
    raw_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    items: list[dict] = []

    for index, image_url in enumerate(urls, start=1):
        try:
            body, content_type = fetch(image_url, "image/avif,image/webp,image/png,image/jpeg,*/*;q=0.8")
            if not body or len(body) > 12 * 1024 * 1024:
                continue
            extension = file_extension(image_url, content_type)
            current_id = item_id(source_id, image_url)
            raw_path = raw_dir / f"{current_id}{extension}"
            thumb_path = image_dir / f"{current_id}-thumb{extension}"
            large_path = image_dir / f"{current_id}-large{extension}"
            raw_path.write_bytes(body)
            # Source pages already expose preview-sized assets. Keep both roles
            # separate in the manifest so a later resizer can replace this step.
            shutil.copyfile(raw_path, thumb_path)
            shutil.copyfile(raw_path, large_path)
            items.append({
                "id": current_id,
                "thumbnailPath": str(thumb_path.relative_to(ROOT)),
                "largeImagePath": str(large_path.relative_to(ROOT)),
                "tags": [],
                "curated": index <= max(1, limit // 4),
                "sourceId": source_id,
                "sourceImageUrl": image_url,
            })
            time.sleep(delay)
        except Exception as error:  # keep one bad image from stopping the batch
            print(f"Skipping {image_url}: {error}")
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect a low-volume public preview batch.")
    parser.add_argument("--source", action="append", help="Source id; repeat to select multiple sources.")
    parser.add_argument("--limit", type=int, default=6, help="Maximum images per source (default: 6).")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between image downloads in seconds.")
    parser.add_argument("--dry-run", action="store_true", help="List selected candidates without downloading.")
    parser.add_argument("--include-manual", action="store_true", help="Include sources marked manual review only after authorization.")
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 30:
        raise SystemExit("--limit must be between 1 and 30")

    sources = load_json(SOURCES_PATH, [])
    selected_ids = set(args.source or SOURCE_RULES.keys())
    sources = [
        source for source in sources
        if source.get("enabled")
        and source.get("id") in selected_ids
        and (source.get("status") == "enabled_candidate" or args.include_manual)
    ]
    if not sources:
        print("No enabled public candidate source matched.")
        return 1

    if args.dry_run:
        for source in sources:
            print(f"[dry-run] {source['id']}: {source['url']} (limit={args.limit})")
        return 0

    all_items: list[dict] = []
    for source in sources:
        try:
            items = collect_source(source, args.limit, args.delay)
            print(f"Collected {len(items)} preview(s) from {source['id']}.")
            all_items.extend(items)
        except Exception as error:
            print(f"Source failed {source['id']}: {error}")

    STAGING_PATH.mkdir(parents=True, exist_ok=True)
    previous = load_json(MANIFEST_PATH, {"items": []})
    previous_items = previous.get("items", []) if isinstance(previous, dict) else []
    merged = {item.get("id"): item for item in previous_items if item.get("id")}
    merged.update({item["id"]: item for item in all_items})
    output_items = list(merged.values())
    MANIFEST_PATH.write_text(json.dumps({"items": output_items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(all_items)} new item(s), {len(output_items)} total item(s) to {MANIFEST_PATH}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
