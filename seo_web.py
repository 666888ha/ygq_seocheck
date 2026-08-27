#!/usr/bin/env python3
"""SEO 分析 Agent - Web 版本

启动后浏览器访问 http://localhost:8080 即可使用

Usage:
    python seo_web.py [--port 8080]
"""

import argparse
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs

from seo_agent import SEOAnalyzer
from seo_report import generate_report


INDEX_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SEO 分析 Agent</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; display: flex; align-items: center; justify-content: center; }

.container { max-width: 560px; width: 90%; padding: 40px; }

.logo { text-align: center; margin-bottom: 32px; }
.logo svg { width: 56px; height: 56px; }
.logo h1 { font-size: 24px; margin-top: 12px; font-weight: 700; background: linear-gradient(135deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.logo p { color: #94a3b8; font-size: 14px; margin-top: 4px; }

.card { background: #1e293b; border-radius: 16px; padding: 32px; box-shadow: 0 4px 24px rgba(0,0,0,0.3); }

label { display: block; font-size: 14px; color: #94a3b8; margin-bottom: 8px; }

.input-group { display: flex; gap: 8px; }
input[type="text"] { flex: 1; padding: 14px 16px; background: #0f172a; border: 1px solid #334155; border-radius: 10px; color: #e2e8f0; font-size: 15px; outline: none; transition: border-color 0.2s; }
input[type="text"]:focus { border-color: #38bdf8; }
input[type="text"]::placeholder { color: #475569; }

button { padding: 14px 28px; background: linear-gradient(135deg, #3b82f6, #6366f1); color: #fff; border: none; border-radius: 10px; font-size: 15px; font-weight: 600; cursor: pointer; white-space: nowrap; transition: opacity 0.2s, transform 0.1s; }
button:hover { opacity: 0.9; }
button:active { transform: scale(0.97); }
button:disabled { opacity: 0.5; cursor: not-allowed; }

.tips { margin-top: 20px; }
.tips h3 { font-size: 13px; color: #64748b; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
.tips ul { list-style: none; }
.tips li { font-size: 13px; color: #94a3b8; padding: 4px 0; }
.tips li::before { content: "•"; color: #3b82f6; margin-right: 8px; }

.examples { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
.example-btn { padding: 6px 12px; background: #334155; border: none; border-radius: 6px; color: #94a3b8; font-size: 12px; cursor: pointer; transition: all 0.2s; }
.example-btn:hover { background: #475569; color: #e2e8f0; }

.loading { display: none; text-align: center; margin-top: 24px; }
.loading.show { display: block; }
.spinner { width: 40px; height: 40px; border: 3px solid #334155; border-top-color: #3b82f6; border-radius: 50%; margin: 0 auto 12px; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.loading p { color: #94a3b8; font-size: 14px; }

.error { display: none; margin-top: 16px; padding: 12px 16px; background: rgba(220,38,38,0.1); border: 1px solid rgba(220,38,38,0.3); border-radius: 8px; color: #fca5a5; font-size: 14px; }
.error.show { display: block; }

.footer { text-align: center; margin-top: 24px; color: #475569; font-size: 12px; }
</style>
</head>
<body>
<div class="container">
    <div class="logo">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="11" cy="11" r="7" stroke="url(#g)" stroke-width="2.5"/>
            <path d="M16.5 16.5L21 21" stroke="url(#g)" stroke-width="2.5" stroke-linecap="round"/>
            <defs><linearGradient id="g" x1="0" y1="0" x2="24" y2="24"><stop stop-color="#38bdf8"/><stop offset="1" stop-color="#818cf8"/></linearGradient></defs>
        </svg>
        <h1>SEO 分析 Agent</h1>
        <p>输入网站 URL，一键生成专业 SEO 诊断报告</p>
    </div>
    <div class="card">
        <label>网站地址</label>
        <div class="input-group">
            <input type="text" id="url" placeholder="https://example.com" value="">
            <button id="btn" onclick="analyze()">分析</button>
        </div>
        <div class="examples">
            <button class="example-btn" onclick="setExample(this)">ausperbio.cn</button>
            <button class="example-btn" onclick="setExample(this)">baidu.com</button>
            <button class="example-btn" onclick="setExample(this)">taobao.com</button>
        </div>
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p id="loadingMsg">正在抓取页面并分析...</p>
        </div>
        <div class="error" id="error"></div>
        <div class="tips">
            <h3>检测维度</h3>
            <ul>
                <li>TDK 检测（Title / Description / Keywords）</li>
                <li>robots.txt / sitemap.xml 校验</li>
                <li>页面基础 SEO（H1 / 图片alt / Canonical / OG / 结构化数据 / 链接）</li>
                <li>技术问题（HTTPS / 移动端 / 性能 / 压缩 / lang / favicon）</li>
                <li>内容缺陷（字数 / 文本比 / 标题 / 段落）</li>
                <li>整改建议（按优先级排序）</li>
            </ul>
        </div>
    </div>
    <div class="footer">Powered by SEO Analysis Agent v1.0</div>
</div>
<script>
function setExample(btn) {
    document.getElementById('url').value = 'https://www.' + btn.textContent;
}

var loadingSteps = [
    '正在抓取页面...',
    '解析 HTML 结构...',
    '检测 TDK 标签...',
    '校验 robots/sitemap...',
    '检查页面 SEO 元素...',
    '分析技术问题...',
    '评估内容质量...',
    '生成整改建议...',
    '渲染报告...'
];
var stepIndex = 0;
var stepTimer = null;

function analyze() {
    var url = document.getElementById('url').value.trim();
    if (!url) { showError('请输入网站地址'); return; }
    if (!url.match(/^https?:\/\//)) { url = 'https://' + url; }

    document.getElementById('btn').disabled = true;
    document.getElementById('loading').classList.add('show');
    document.getElementById('error').classList.remove('show');

    stepIndex = 0;
    updateStep();
    stepTimer = setInterval(updateStep, 1500);

    var formData = 'url=' + encodeURIComponent(url);

    fetch('/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
    })
    .then(function(resp) {
        clearInterval(stepTimer);
        if (resp.ok) {
            return resp.text();
        } else {
            return resp.text().then(function(t) { throw new Error(t); });
        }
    })
    .then(function(html) {
        document.open();
        document.write(html);
        document.close();
    })
    .catch(function(err) {
        clearInterval(stepTimer);
        showError(err.message || '分析失败，请检查 URL 是否可访问');
        document.getElementById('btn').disabled = false;
        document.getElementById('loading').classList.remove('show');
    });
}

function updateStep() {
    if (stepIndex < loadingSteps.length) {
        document.getElementById('loadingMsg').textContent = loadingSteps[stepIndex];
        stepIndex++;
    }
}

function showError(msg) {
    var el = document.getElementById('error');
    el.textContent = msg;
    el.classList.add('show');
}

document.getElementById('url').addEventListener('keydown', function(e) {
    if (e.key === 'Enter') analyze();
});
</script>
</body>
</html>"""


class SEOHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(INDEX_HTML.encode("utf-8"))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/analyze":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            params = parse_qs(body)
            url = params.get("url", [""])[0].strip()

            if not url:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"URL is required")
                return

            if not url.startswith("http"):
                url = "https://" + url

            try:
                analyzer = SEOAnalyzer(url)
                results = analyzer.run()
                html = generate_report(results)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}", flush=True)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


def main():
    parser = argparse.ArgumentParser(description="SEO Analysis Agent - Web Server")
    parser.add_argument("--port", type=int, default=8888, help="监听端口（默认8888）")
    args = parser.parse_args()

    server = ThreadedHTTPServer(("127.0.0.1", args.port), SEOHandler)
    print(f"SEO 分析 Agent 已启动: http://localhost:{args.port}", flush=True)
    print("在浏览器中打开上述地址即可使用", flush=True)
    print("按 Ctrl+C 停止服务\n", flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
        server.shutdown()


if __name__ == "__main__":
    main()
