# SEO 分析 Agent

输入网站 URL，自动完成全套 SEO 诊断，输出结构化分析报告。

## 使用方式

### 本地运行（Web 界面）
```bash
pip install -r requirements.txt
python seo_web.py
# 浏览器打开 http://localhost:8888
```

### 本地运行（命令行）
```bash
python seo_agent.py https://example.com --output report.html
```

### 部署到云端

| 平台 | 目录 | 说明 |
|------|------|------|
| Hugging Face Spaces | `huggingface/` | 完全免费，推荐 |
| Vercel | `vercel/` | 免费额度，10s 超时限制 |
| Render | 根目录 + `render.yaml` | 免费版休眠 |
| 自建服务器 | `deploy.sh` | Ubuntu/Debian 一键部署 |

## 检测维度

- **TDK 检测**：Title / Description / Keywords
- **robots/sitemap**：robots.txt / sitemap.xml 校验
- **页面基础 SEO**：H1 / 图片alt / Canonical / OG / JSON-LD / 链接
- **技术问题**：HTTPS / 移动端 / 性能 / 压缩 / lang / favicon
- **内容缺陷**：字数 / 文本比 / 标题 / 段落
- **整改建议**：按优先级排序
