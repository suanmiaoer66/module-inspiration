#!/usr/bin/env python3
"""Classify staged images with an optional DeepSeek vision endpoint.

When no API key is configured, the script keeps items as pending_review instead
of inventing labels. The scheduled Codex workflow can classify the same
manifest later, or a compatible vision endpoint can be enabled in Actions.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
TAGS_PATH = ROOT / "config" / "tags.json"
MANIFEST_PATH = ROOT / "staging" / "manifest.json"


def load_json(path: Path, fallback):
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def image_data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/webp"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def parse_json_content(content: str) -> dict:
    cleaned = content.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    return json.loads(cleaned)


def classify_remote(path: Path, allowed_tags: list[str]) -> list[str]:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        return []
    base_url = (os.environ.get("DEEPSEEK_BASE_URL", "").strip() or "https://api.deepseek.com").rstrip("/")
    model = os.environ.get("DEEPSEEK_VISION_MODEL", "deepseek-flash")
    prompt = (
        "你是 UI 设计素材分类器。只从给定标签中选择 1 到 3 个最匹配的标签。"
        "只返回 JSON，例如 {\"tags\":[\"弹窗\"]}。"
        f"给定标签：{json.dumps(allowed_tags, ensure_ascii=False)}。"
        "判断图片中最主要的界面模块，不要根据品牌或应用名称猜测。"
    )
    body = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": [
                {"type": "text", "text": "请为这张 UI 灵感图选择模块标签。"},
                {"type": "image_url", "image_url": {"url": image_data_uri(path)}},
            ]},
        ],
    }
    request = Request(
        f"{base_url}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=90) as response:
        result = json.loads(response.read().decode("utf-8"))
    content = result["choices"][0]["message"]["content"]
    parsed = parse_json_content(content)
    return [tag for tag in parsed.get("tags", []) if tag in allowed_tags][:3]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    manifest = load_json(args.manifest, {"items": []})
    items = manifest.get("items", []) if isinstance(manifest, dict) else []
    tag_config = load_json(TAGS_PATH, {"primary": [], "aliases": {}})
    allowed_tags = tag_config.get("primary", [])
    aliases = tag_config.get("aliases", {})

    if not os.environ.get("DEEPSEEK_API_KEY", "").strip():
        print("DEEPSEEK_API_KEY is not configured; keeping collected items as pending_review.")

    classified = 0
    for item in items:
        path = ROOT / item.get("largeImagePath", "")
        try:
            tags = classify_remote(path, allowed_tags) if path.exists() else []
        except Exception as error:
            print(f"Classification skipped for {item.get('id', 'unknown')}: {error}")
            tags = []
        normalized = []
        for tag in tags:
            tag = aliases.get(tag, tag)
            if tag in allowed_tags and tag not in normalized:
                normalized.append(tag)
        item["tags"] = normalized[:3]
        item["status"] = "published" if item["tags"] else "pending_review"
        classified += bool(item["tags"])

    args.manifest.write_text(json.dumps({"items": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Classified {classified}/{len(items)} item(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
