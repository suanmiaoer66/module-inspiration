# 模块灵感库

深色 UI 模块灵感归档站的第一版静态原型。

## 本地预览

```bash
python3 -m http.server 4173
```

打开 <http://localhost:4173>。

## 数据格式

前端读取 `data/items.json`。每条素材包含：

- `imageUrl`：腾讯云 COS/CDN 缩略图地址
- `largeImageUrl`：腾讯云 COS/CDN 大图地址，点击图片后在站内预览
- `tags`：固定的 UI 模块标签
- `curated`：是否进入今日精选
- `recent`：是否进入最近收录

后续采集脚本只需要持续生成同样结构的数据，即可接入当前页面。
