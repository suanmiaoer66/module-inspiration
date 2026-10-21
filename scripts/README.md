# 自动采集脚本

`collect.py` 和 `classify.py` 目前是安全的接入骨架。采集器只对已标记为 `enabled_candidate` 的公开页面运行：

```bash
python3 scripts/collect.py --dry-run
python3 scripts/collect.py --source applore --dry-run
python3 scripts/collect.py --source applore --limit 3 --delay 2
python3 scripts/classify.py
```

采集器输出统一写入 `staging/manifest.json`，并将下载的预览图放到 `staging/images/`。`staging/` 已加入 `.gitignore`，不会上传到 GitHub。确认素材授权和标签后，再运行 COS 同步。

## COS manifest 格式

采集器可以写入 `staging/manifest.json`：

```json
{
  "items": [
    {
      "id": "ap-001",
      "thumbnailPath": "staging/images/ap-001-thumb.webp",
      "largeImagePath": "staging/images/ap-001-large.webp",
      "tags": ["二级 Tab", "标签栏"],
      "curated": true
    }
  ]
}
```

运行 `python3 scripts/sync_cos.py` 会将两张图片上传到 COS，并更新 `data/items.json`。如果没有 manifest，脚本会安全跳过。
