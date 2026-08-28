"""SEO 分析 Agent - Vercel Serverless Function"""

import json
from http.server import BaseHTTPRequestHandler

from seo_agent import SEOAnalyzer
from seo_report import generate_report


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"

        try:
            data = json.loads(body)
        except Exception:
            data = {}

        url = (data.get("url") or "").strip()
        if not url:
            self._send(400, json.dumps({"error": "URL is required"}))
            return
        if not url.startswith("http"):
            url = "https://" + url

        try:
            analyzer = SEOAnalyzer(url, timeout=3)
            results = analyzer.run()
            html = generate_report(results)
            self._send(200, html, "text/html; charset=utf-8")
        except Exception as e:
            self._send(500, json.dumps({"error": str(e)}))

    def do_GET(self):
        if self.path == "/api/analyze":
            self._send(405, json.dumps({"error": "Use POST method"}))
        else:
            self._send(404, "Not Found")

    def _send(self, code, body, content_type="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, format, *args):
        pass
