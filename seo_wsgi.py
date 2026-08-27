#!/usr/bin/env python3
"""SEO 分析 Agent - WSGI 生产版本

用 gunicorn 运行:
    pip install gunicorn
    gunicorn -w 4 -b 0.0.0.0:8888 seo_wsgi:app
"""

from urllib.parse import parse_qs
from seo_agent import SEOAnalyzer
from seo_report import generate_report

# 复用 seo_web.py 中的 HTML
from seo_web import INDEX_HTML


def app(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET")
    path = environ.get("PATH_INFO", "/")

    if method == "GET" and path in ("/", "/index.html"):
        body = INDEX_HTML.encode("utf-8")
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [body]

    if method == "POST" and path == "/analyze":
        try:
            content_length = int(environ.get("CONTENT_LENGTH", 0))
            raw = environ["wsgi.input"].read(content_length)
            params = parse_qs(raw.decode("utf-8"))
            url = params.get("url", [""])[0].strip()

            if not url:
                start_response("400 Bad Request", [("Content-Type", "text/plain")])
                return [b"URL is required"]

            if not url.startswith("http"):
                url = "https://" + url

            analyzer = SEOAnalyzer(url)
            results = analyzer.run()
            html = generate_report(results)
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            return [html.encode("utf-8")]
        except Exception as e:
            start_response("500 Internal Server Error", [("Content-Type", "text/plain")])
            return [str(e).encode("utf-8")]

    start_response("404 Not Found", [("Content-Type", "text/plain")])
    return [b"Not Found"]
