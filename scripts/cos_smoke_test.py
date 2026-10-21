#!/usr/bin/env python3
"""Upload a tiny non-user-facing health check to validate COS credentials."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from qcloud_cos import CosConfig, CosS3Client


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def main() -> int:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "codex-cos-healthcheck.txt"
        path.write_text("module-inspiration COS healthcheck\n", encoding="utf-8")
        config = CosConfig(
            Region=required("COS_REGION"),
            SecretId=required("TENCENT_SECRET_ID"),
            SecretKey=required("TENCENT_SECRET_KEY"),
            Scheme="https",
        )
        client = CosS3Client(config)
        client.put_object_from_local_file(
            Bucket=required("COS_BUCKET"),
            LocalFilePath=str(path),
            Key="system/codex-cos-healthcheck.txt",
            ContentType="text/plain; charset=utf-8",
        )
    print("COS smoke test uploaded successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
