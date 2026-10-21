# 自动采集脚本

`collect.py` 和 `classify.py` 目前是安全的接入骨架：

```bash
python3 scripts/collect.py --dry-run
python3 scripts/collect.py --source applore --dry-run
python3 scripts/classify.py
```

下一步为每个来源增加独立 adapter，并在确认公开访问规则后再开启下载。采集器输出统一写入 `data/items.json`，图片缩略图和大图上传腾讯云 COS。
