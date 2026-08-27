"""SEO 分析 Agent - Vercel Serverless Function"""

import json
from seo_agent import SEOAnalyzer
from seo_report import generate_report


def handler(request):
    if request.method != "POST":
        return {"statusCode": 405, "body": "Method Not Allowed"}

    try:
        body = request.json() if hasattr(request, "json") else json.loads(request.body or "{}")
    except Exception:
        body = {}

    url = (body.get("url") or "").strip()
    if not url:
        return {"statusCode": 400, "body": json.dumps({"error": "URL is required"})}
    if not url.startswith("http"):
        url = "https://" + url

    try:
        analyzer = SEOAnalyzer(url, timeout=10)
        results = analyzer.run()
        html = generate_report(results)
        return {"statusCode": 200, "headers": {"Content-Type": "text/html; charset=utf-8"}, "body": html}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
