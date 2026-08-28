#!/usr/bin/env python3
"""SEO 报告生成器 - 将分析结果渲染为专业 HTML 报告"""

import html
from datetime import datetime

STATUS_CONFIG = {
    "pass": {"label": "通过", "color": "#16a34a", "bg": "#dcfce7", "icon": "&#10003;"},
    "warn": {"label": "警告", "color": "#d97706", "bg": "#fef3c7", "icon": "&#9888;"},
    "fail": {"label": "失败", "color": "#dc2626", "bg": "#fee2e2", "icon": "&#10007;"},
    "info": {"label": "信息", "color": "#2563eb", "bg": "#dbeafe", "icon": "&#8505;"},
}


def _badge(status):
    cfg = STATUS_CONFIG.get(status, STATUS_CONFIG["info"])
    return f'<span class="badge" style="color:{cfg["color"]};background:{cfg["bg"]}">{cfg["icon"]} {cfg["label"]}</span>'


def _esc(text):
    return html.escape(str(text)) if text else ""


def _score_color(score):
    if score >= 80:
        return "#16a34a"
    elif score >= 60:
        return "#d97706"
    else:
        return "#dc2626"


def _score_label(score):
    if score >= 80:
        return "优秀"
    elif score >= 60:
        return "需改进"
    else:
        return "问题较多"


def _render_check(name, item):
    if not isinstance(item, dict):
        return ""
    status = item.get("status", "info")
    msg = _esc(item.get("msg", ""))
    detail = ""

    if name == "标题 (Title)":
        detail = f'<div class="detail-value">{_esc(item.get("value", ""))}</div>'
        detail += f'<div class="detail-meta">当前长度: {item.get("length", 0)} 字符 | 理想: {item.get("ideal", "")}</div>'
    elif name == "描述 (Description)":
        detail = f'<div class="detail-value">{_esc(item.get("value", ""))}</div>'
        detail += f'<div class="detail-meta">当前长度: {item.get("length", 0)} 字符 | 理想: {item.get("ideal", "")}</div>'
    elif name == "关键词 (Keywords)":
        detail = f'<div class="detail-value">{_esc(item.get("value", ""))}</div>'
    elif name == "H1 标签":
        texts = item.get("texts", [])
        if texts:
            detail = f'<div class="detail-value">{"<br>".join(_esc(t) for t in texts)}</div>'
    elif name == "结构化数据 (JSON-LD)":
        types = item.get("types", [])
        if types:
            detail = f'<div class="detail-value">类型: {", ".join(_esc(t) for t in types)}</div>'
    elif name == "Open Graph":
        tags = item.get("tags", {})
        if tags:
            lines = [f"<code>{_esc(k)}</code>: {_esc(v)}" for k, v in tags.items()]
            detail = f'<div class="detail-value">{"<br>".join(lines)}</div>'
    elif name == "链接 (Links)":
        detail = f'<div class="detail-meta">内链: {item.get("internal_count", 0)} | 外链: {item.get("external_count", 0)}'
        if item.get("broken_external_count", 0) > 0:
            detail += f' | 异常外链: {item["broken_external_count"]}/{item["checked_sample"]}'
        detail += "</div>"
        broken = item.get("broken_external_sample", [])
        if broken:
            detail += '<div class="detail-warn">' + "<br>".join(_esc(b) for b in broken) + "</div>"
    elif name == "URL 结构":
        detail = f'<div class="detail-meta">路径: {_esc(item.get("path", ""))} | 含参数: {"是" if item.get("has_params") else "否"}</div>'
    elif name == "robots.txt":
        if item.get("content_preview"):
            detail = f'<pre class="detail-code">{_esc(item["content_preview"])}</pre>'
        refs = item.get("sitemap_refs", [])
        if refs:
            detail += '<div class="detail-meta">引用 Sitemap: ' + ", ".join(_esc(r) for r in refs) + "</div>"
    elif name == "sitemap.xml":
        detail = f'<div class="detail-meta">URL 数量: {item.get("url_count", 0)}</div>'
    elif name == "页面性能":
        detail = f'<div class="detail-meta">页面大小: {item.get("page_size_kb", 0)} KB | 响应时间: {item.get("response_time_s", 0)}s</div>'
    elif name == "HTML lang":
        detail = f'<div class="detail-meta">lang="{_esc(item.get("value", ""))}"</div>'
    elif name == "HTTPS":
        pass
    elif name == "移动端 Viewport":
        if item.get("content"):
            detail = f'<div class="detail-meta">content="{_esc(item.get("content", ""))}"</div>'
    elif name == "robots meta":
        if item.get("value"):
            detail = f'<div class="detail-meta">content="{_esc(item.get("value", ""))}"</div>'
    elif name == "压缩 (Gzip)":
        pass
    elif name == "Favicon":
        if item.get("href"):
            detail = f'<div class="detail-meta">href="{_esc(item.get("href", ""))}"</div>'
    elif name == "字数":
        pass
    elif name == "文本/HTML 比":
        pass
    elif name == "标题结构":
        counts = item.get("counts", {})
        if counts:
            detail = '<div class="detail-meta">' + " | ".join(f"{k}: {v}" for k, v in counts.items()) + "</div>"

    return f"""
    <div class="check-item">
        <div class="check-header">
            <span class="check-name">{name}</span>
            {_badge(status)}
        </div>
        <div class="check-msg">{msg}</div>
        {detail}
    </div>"""


def generate_report(results):
    url = results.get("url", "")
    score = results.get("score", 0)
    score_color = _score_color(score)
    score_label = _score_label(score)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Section definitions
    tdk_checks = [
        ("标题 (Title)", results.get("tdk", {}).get("title", {})),
        ("描述 (Description)", results.get("tdk", {}).get("description", {})),
        ("关键词 (Keywords)", results.get("tdk", {}).get("keywords", {})),
    ]
    rs_checks = [
        ("robots.txt", results.get("robots_sitemap", {}).get("robots", {})),
        ("sitemap.xml", results.get("robots_sitemap", {}).get("sitemap", {})),
    ]
    page_checks = [
        ("H1 标签", results.get("page_seo", {}).get("h1", {})),
        ("标题结构", results.get("page_seo", {}).get("headings", {})),
        ("图片 Alt", results.get("page_seo", {}).get("images", {})),
        ("Canonical", results.get("page_seo", {}).get("canonical", {})),
        ("Open Graph", results.get("page_seo", {}).get("open_graph", {})),
        ("Twitter Cards", results.get("page_seo", {}).get("twitter_cards", {})),
        ("结构化数据 (JSON-LD)", results.get("page_seo", {}).get("structured_data", {})),
        ("链接 (Links)", results.get("page_seo", {}).get("links", {})),
        ("URL 结构", results.get("page_seo", {}).get("url_structure", {})),
    ]
    tech_checks = [
        ("HTTPS", results.get("technical", {}).get("https", {})),
        ("移动端 Viewport", results.get("technical", {}).get("mobile_viewport", {})),
        ("页面性能", results.get("technical", {}).get("page_speed", {})),
        ("压缩 (Gzip)", results.get("technical", {}).get("compression", {})),
        ("HTML lang", results.get("technical", {}).get("html_lang", {})),
        ("Favicon", results.get("technical", {}).get("favicon", {})),
        ("robots meta", results.get("technical", {}).get("robots_meta", {})),
    ]
    content_checks = [
        ("字数", results.get("content", {}).get("word_count", {})),
        ("文本/HTML 比", results.get("content", {}).get("text_html_ratio", {})),
        ("标题结构", results.get("content", {}).get("heading_count", {})),
        ("段落", results.get("content", {}).get("paragraphs", {})),
        ("媒体", results.get("content", {}).get("media", {})),
    ]

    sections = [
        ("TDK 检测", "title-description-keywords meta tags", tdk_checks),
        ("robots.txt / sitemap", "搜索引擎爬取配置", rs_checks),
        ("页面基础 SEO", "H1/图片/Canonical/OG/结构化数据/链接", page_checks),
        ("技术问题", "HTTPS/移动端/性能/压缩/lang/favicon", tech_checks),
        ("内容缺陷", "字数/文本比/标题/段落", content_checks),
    ]

    # Suggestions
    suggestions = results.get("suggestions", [])
    pri_colors = {"high": "#dc2626", "medium": "#d97706", "low": "#2563eb"}
    pri_labels = {"high": "高优先", "medium": "中优先", "low": "低优先"}

    suggestions_html = ""
    for s in suggestions:
        c = pri_colors.get(s["priority"], "#6b7280")
        l = pri_labels.get(s["priority"], s["priority"])
        suggestions_html += f"""
        <div class="suggestion-item">
            <span class="priority-tag" style="background:{c}">{l}</span>
            <span class="suggestion-section">{_esc(s["section"])}</span>
            <span class="suggestion-msg">{_esc(s["msg"])}</span>
        </div>"""

    if not suggestions:
        suggestions_html = '<div class="suggestion-item"><span class="suggestion-msg">未发现需要整改的问题</span></div>'

    # Build section HTML
    sections_html = ""
    for idx, (title, subtitle, checks) in enumerate(sections, 1):
        checks_html = "".join(_render_check(name, item) for name, item in checks)
        # Section score
        total = len(checks)
        passed = sum(1 for _, v in checks if isinstance(v, dict) and v.get("status") == "pass")
        warned = sum(1 for _, v in checks if isinstance(v, dict) and v.get("status") == "warn")
        failed = sum(1 for _, v in checks if isinstance(v, dict) and v.get("status") == "fail")
        summary = f"通过 {passed} / 警告 {warned} / 失败 {failed}"

        sections_html += f"""
        <div class="section" id="section-{idx}">
            <div class="section-header" onclick="toggleSection({idx})">
                <h2><span class="section-num">{idx}</span> {title} <span class="section-sub">{subtitle}</span></h2>
                <span class="section-summary">{summary}</span>
                <span class="toggle-icon" id="toggle-{idx}">&#9660;</span>
            </div>
            <div class="section-body" id="body-{idx}">
                {checks_html}
            </div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SEO 分析报告 - {_esc(url)}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; background: #f8fafc; color: #1e293b; line-height: 1.6; }}

.report {{ max-width: 900px; margin: 0 auto; padding: 24px 16px; }}

.header {{ background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: #fff; border-radius: 16px; padding: 32px; margin-bottom: 24px; }}
.header h1 {{ font-size: 22px; margin-bottom: 8px; }}
.header .url {{ color: #94a3b8; font-size: 14px; word-break: break-all; }}
.header .meta {{ color: #64748b; font-size: 12px; margin-top: 8px; }}

.score-box {{ display: flex; align-items: center; gap: 24px; margin-top: 20px; }}
.score-circle {{ width: 100px; height: 100px; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; border: 4px solid {score_color}; background: rgba(255,255,255,0.05); flex-shrink: 0; }}
.score-num {{ font-size: 36px; font-weight: 700; color: {score_color}; line-height: 1; }}
.score-max {{ font-size: 14px; color: #94a3b8; }}
.score-label {{ font-size: 13px; color: {score_color}; margin-top: 4px; }}
.score-info {{ flex: 1; }}
.score-info p {{ color: #cbd5e1; font-size: 14px; }}

.quick-stats {{ display: flex; gap: 12px; flex-wrap: wrap; margin-top: 16px; }}
.stat {{ background: rgba(255,255,255,0.08); border-radius: 8px; padding: 8px 16px; }}
.stat-num {{ font-size: 20px; font-weight: 700; }}
.stat-label {{ font-size: 11px; color: #94a3b8; }}

.section {{ background: #fff; border-radius: 12px; margin-bottom: 16px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
.section-header {{ display: flex; align-items: center; padding: 16px 20px; cursor: pointer; user-select: none; border-bottom: 1px solid #e2e8f0; }}
.section-header h2 {{ font-size: 16px; font-weight: 600; flex: 1; display: flex; align-items: center; gap: 8px; }}
.section-num {{ background: #3b82f6; color: #fff; width: 24px; height: 24px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 13px; flex-shrink: 0; }}
.section-sub {{ font-size: 12px; color: #94a3b8; font-weight: 400; }}
.section-summary {{ font-size: 12px; color: #64748b; margin-right: 8px; }}
.toggle-icon {{ color: #94a3b8; font-size: 12px; transition: transform 0.2s; }}
.section-header.collapsed .toggle-icon {{ transform: rotate(-90deg); }}

.section-body {{ padding: 8px 20px 16px; }}
.section-body.collapsed {{ display: none; }}

.check-item {{ padding: 12px 0; border-bottom: 1px solid #f1f5f9; }}
.check-item:last-child {{ border-bottom: none; }}
.check-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }}
.check-name {{ font-weight: 600; font-size: 14px; }}
.check-msg {{ font-size: 13px; color: #475569; margin-bottom: 4px; }}

.badge {{ display: inline-flex; align-items: center; gap: 3px; padding: 2px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }}

.detail-value {{ font-size: 13px; color: #334155; background: #f8fafc; padding: 8px 12px; border-radius: 6px; margin: 4px 0; word-break: break-all; max-height: 120px; overflow-y: auto; }}
.detail-meta {{ font-size: 12px; color: #64748b; margin-top: 2px; }}
.detail-warn {{ font-size: 12px; color: #dc2626; margin-top: 4px; }}
.detail-code {{ font-size: 11px; color: #475569; background: #f1f5f9; padding: 8px 12px; border-radius: 6px; margin: 4px 0; white-space: pre-wrap; word-break: break-all; max-height: 200px; overflow-y: auto; font-family: "Cascadia Code", "Fira Code", monospace; }}

.suggestions {{ background: #fff; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
.suggestions h2 {{ font-size: 16px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }}
.suggestion-item {{ display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid #f1f5f9; }}
.suggestion-item:last-child {{ border-bottom: none; }}
.priority-tag {{ color: #fff; font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600; flex-shrink: 0; }}
.suggestion-section {{ font-size: 12px; color: #64748b; flex-shrink: 0; min-width: 80px; }}
.suggestion-msg {{ font-size: 13px; color: #334155; }}

.footer {{ text-align: center; color: #94a3b8; font-size: 12px; padding: 20px; }}

@media (max-width: 600px) {{
    .header {{ padding: 20px; }}
    .score-box {{ flex-direction: column; align-items: flex-start; }}
    .quick-stats {{ flex-direction: column; }}
}}
</style>
</head>
<body>
<div class="report">
    <div class="header">
        <h1>SEO 分析报告</h1>
        <div class="url">{_esc(url)}</div>
        <div class="meta">生成时间: {now} | Agent: SEO-Audit v1.0</div>
        <div class="score-box">
            <div class="score-circle">
                <div class="score-num">{score}</div>
                <div class="score-max">/ 100</div>
                <div class="score-label">{score_label}</div>
            </div>
            <div class="score-info">
                <p>本报告涵盖 TDK 检测、robots/sitemap 校验、页面基础 SEO、技术问题、内容缺陷及整改建议共 5 大维度。</p>
            </div>
        </div>
        <div class="quick-stats">
            <div class="stat"><div class="stat-num">{sum(1 for _, v in tdk_checks if isinstance(v, dict) and v.get("status") == "pass")}</div><div class="stat-label">TDK 通过</div></div>
            <div class="stat"><div class="stat-num">{sum(1 for _, v in page_checks if isinstance(v, dict) and v.get("status") == "pass")}</div><div class="stat-label">页面SEO通过</div></div>
            <div class="stat"><div class="stat-num">{sum(1 for _, v in tech_checks if isinstance(v, dict) and v.get("status") == "pass")}</div><div class="stat-label">技术通过</div></div>
            <div class="stat"><div class="stat-num">{len(suggestions)}</div><div class="stat-label">整改建议</div></div>
        </div>
    </div>

    {sections_html}

    <div class="suggestions">
        <h2>整改建议</h2>
        {suggestions_html}
    </div>

    <div class="footer">
        Powered by SEO Analysis Agent | 报告基于实时页面抓取与规则引擎分析
    </div>
</div>

<script>
function toggleSection(idx) {{
    var body = document.getElementById('body-' + idx);
    var header = body.previousElementSibling;
    var icon = document.getElementById('toggle-' + idx);
    body.classList.toggle('collapsed');
    header.classList.toggle('collapsed');
}}
</script>
</body>
</html>"""
