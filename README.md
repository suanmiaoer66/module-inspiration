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

## 腾讯云 COS 配置

`TENCENT_SECRET_ID` 和 `TENCENT_SECRET_KEY` 是腾讯云 CAM API 密钥，只放在本地 `.env` 或 GitHub Actions Secrets 中，不要提交到仓库。

当前项目的非敏感配置为：

```env
COS_REGION=ap-guangzhou
COS_BUCKET=design-images-1329527832
COS_DOMAIN=https://design-images-1329527832.cos.ap-guangzhou.myqcloud.com
```

## 手动验证 COS

仓库中的 `.github/workflows/cos-sync.yml` 当前只支持手动运行：

1. 打开 GitHub 仓库的 **Actions**。
2. 选择 **Sync inspiration images to COS**。
3. 点击 **Run workflow**。
4. 保持 `smoke_test` 为 `true`，点击运行。

成功后会在 COS 的 `system/codex-cos-healthcheck.txt` 写入一个很小的测试文件，并继续部署当前网站。没有 `staging/manifest.json` 时，素材同步会安全跳过，不会上传示例图片。

真正的每日采集会在 Applore 和美叶的来源适配器完成后再启用定时触发。
