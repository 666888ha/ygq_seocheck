#!/usr/bin/env python3
"""SEO Analysis Agent - 输入URL，自动完成整套SEO诊断

Usage:
    python seo_agent.py <url> [--output report.html]
"""

import re
import sys
import time
import argparse
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 SEO-Audit-Agent/1.0"


class SEOAnalyzer:
    def __init__(self, url, timeout=15):
        self.url = url if url.startswith("http") else "https://" + url
        self.parsed = urlparse(self.url)
        self.base_url = f"{self.parsed.scheme}://{self.parsed.netloc}"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": UA})
        self.results = {
            "url": self.url,
            "tdk": {},
            "robots_sitemap": {},
            "page_seo": {},
            "technical": {},
            "content": {},
            "suggestions": [],
            "score": 0,
        }

    def run(self):
        resp = self._fetch_page()
        if not resp:
            self._generate_suggestions()
            return self.results

        soup = BeautifulSoup(resp.text, "html.parser")
        self._check_tdk(soup)
        self._check_robots_sitemap()
        self._check_page_seo(soup, resp)
        self._check_technical(resp, soup)
        self._check_content(soup, resp)
        self._calc_score()
        self._generate_suggestions()
        return self.results

    # ── Fetch ──────────────────────────────────────────────

    def _fetch_page(self):
        try:
            start = time.time()
            resp = self.session.get(self.url, timeout=self.timeout, allow_redirects=True)
            elapsed = round(time.time() - start, 2)
            t = self.results["technical"]
            t["response_time_s"] = elapsed
            t["status_code"] = resp.status_code
            t["final_url"] = resp.url
            t["redirected"] = resp.url != self.url
            t["redirect_chain"] = [h.url for h in resp.history] if resp.history else []
            t["page_size_kb"] = round(len(resp.content) / 1024, 1)
            t["gzip"] = "gzip" in resp.headers.get("Content-Encoding", "")
            t["https"] = resp.url.startswith("https://")
            server = resp.headers.get("Server", "")
            t["server"] = server

            if resp.status_code != 200:
                t["error"] = f"HTTP {resp.status_code}"
                return None

            # Auto-detect encoding: chardet first, then HTML5 meta charset, then Content-Type meta
            if resp.apparent_encoding and resp.apparent_encoding.lower() not in ("iso-8859-1", "ascii"):
                resp.encoding = resp.apparent_encoding
            else:
                m = re.search(rb'<meta\s+charset=["\']?([\w-]+)', resp.content, re.I)
                if not m:
                    m = re.search(rb'charset=([\w-]+)', resp.content, re.I)
                if m:
                    resp.encoding = m.group(1).decode("ascii", errors="ignore")
            t["encoding"] = resp.encoding
            return resp
        except Exception as e:
            self.results["technical"]["error"] = str(e)
            return None

    # ── TDK ───────────────────────────────────────────────

    def _check_tdk(self, soup):
        title_tag = soup.find("title")
        title = title_tag.text.strip() if title_tag else ""
        tlen = len(title)
        self.results["tdk"]["title"] = {
            "value": title,
            "length": tlen,
            "ideal": "30-60 字符",
            "status": "pass" if 30 <= tlen <= 60 else ("warn" if tlen > 0 else "fail"),
            "msg": "长度合适" if 30 <= tlen <= 60 else (
                f"标题过短({tlen}字符)" if tlen < 30 and tlen > 0 else "缺少 title 标签" if tlen == 0 else f"标题过长({tlen}字符)"
            ),
        }

        desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        desc = desc_tag.get("content", "").strip() if desc_tag else ""
        dlen = len(desc)
        self.results["tdk"]["description"] = {
            "value": desc,
            "length": dlen,
            "ideal": "120-160 字符",
            "status": "pass" if 120 <= dlen <= 160 else ("warn" if dlen > 0 else "fail"),
            "msg": "长度合适" if 120 <= dlen <= 160 else (
                f"描述过短({dlen}字符)" if dlen < 120 and dlen > 0 else "缺少 description 标签" if dlen == 0 else f"描述过长({dlen}字符)"
            ),
        }

        kw_tag = soup.find("meta", attrs={"name": re.compile(r"^keywords$", re.I)})
        kw = kw_tag.get("content", "").strip() if kw_tag else ""
        self.results["tdk"]["keywords"] = {
            "value": kw,
            "status": "pass" if kw else "info",
            "msg": "已设置 keywords 标签" if kw else "未设置 keywords（现代SEO影响较小）",
        }

    # ── robots.txt & sitemap ──────────────────────────────

    def _check_robots_sitemap(self):
        # robots.txt
        robots_url = urljoin(self.base_url, "/robots.txt")
        try:
            resp = self.session.get(robots_url, timeout=self.timeout)
            if resp.status_code == 200:
                content = resp.text
                rp = RobotFileParser()
                rp.parse(content.splitlines())
                sitemap_refs = re.findall(r"^Sitemap:\s*(.+)", content, re.M)
                self.results["robots_sitemap"]["robots"] = {
                    "exists": True,
                    "url": robots_url,
                    "sitemap_refs": sitemap_refs,
                    "content_preview": content[:500],
                    "status": "pass",
                    "msg": "robots.txt 正常" + (f"，引用了 {len(sitemap_refs)} 个 sitemap" if sitemap_refs else "，未引用 sitemap"),
                }
            else:
                self.results["robots_sitemap"]["robots"] = {
                    "exists": False,
                    "url": robots_url,
                    "status": "fail",
                    "msg": f"robots.txt 返回 HTTP {resp.status_code}",
                }
        except Exception as e:
            self.results["robots_sitemap"]["robots"] = {"exists": False, "status": "fail", "msg": str(e)}

        # sitemap.xml
        sitemap_url = urljoin(self.base_url, "/sitemap.xml")
        try:
            resp = self.session.get(sitemap_url, timeout=self.timeout)
            if resp.status_code == 200:
                urls = re.findall(r"<loc>(.+?)</loc>", resp.text)
                self.results["robots_sitemap"]["sitemap"] = {
                    "exists": True,
                    "url": sitemap_url,
                    "url_count": len(urls),
                    "status": "pass",
                    "msg": f"sitemap.xml 正常，包含 {len(urls)} 个 URL",
                }
            else:
                self.results["robots_sitemap"]["sitemap"] = {
                    "exists": False,
                    "url": sitemap_url,
                    "status": "fail",
                    "msg": f"sitemap.xml 返回 HTTP {resp.status_code}",
                }
        except Exception as e:
            self.results["robots_sitemap"]["sitemap"] = {"exists": False, "status": "fail", "msg": str(e)}

    # ── Page SEO ──────────────────────────────────────────

    def _check_page_seo(self, soup, resp):
        ps = self.results["page_seo"]

        # H1
        h1s = soup.find_all("h1")
        ps["h1"] = {
            "count": len(h1s),
            "texts": [h1.text.strip()[:80] for h1 in h1s],
            "status": "pass" if len(h1s) == 1 else ("warn" if len(h1s) == 0 else "warn"),
            "msg": "存在1个H1标签" if len(h1s) == 1 else ("缺少H1标签" if len(h1s) == 0 else f"存在{len(h1s)}个H1标签（建议仅1个）"),
        }

        # H2-H6 hierarchy
        headings = {}
        for level in range(2, 7):
            tags = soup.find_all(f"h{level}")
            if tags:
                headings[f"h{level}"] = len(tags)
        ps["headings"] = {"counts": headings, "status": "pass" if headings else "warn", "msg": f"存在H2-H6标签结构" if headings else "缺少H2-H6标签"}

        # Images alt
        imgs = soup.find_all("img")
        total_imgs = len(imgs)
        missing_alt = sum(1 for img in imgs if not img.get("alt"))
        ps["images"] = {
            "total": total_imgs,
            "missing_alt": missing_alt,
            "status": "pass" if missing_alt == 0 and total_imgs > 0 else ("warn" if missing_alt > 0 else "info"),
            "msg": f"{total_imgs}张图片，{missing_alt}张缺少alt属性" if total_imgs > 0 else "无图片",
        }

        # Canonical
        canonical = soup.find("link", rel="canonical")
        ps["canonical"] = {
            "exists": bool(canonical),
            "href": canonical.get("href", "") if canonical else "",
            "status": "pass" if canonical else "warn",
            "msg": "已设置 canonical" if canonical else "缺少 canonical 标签",
        }

        # Open Graph
        og_tags = {}
        for prop in ["og:title", "og:description", "og:image", "og:url", "og:type"]:
            tag = soup.find("meta", attrs={"property": prop})
            if tag:
                og_tags[prop] = tag.get("content", "")[:100]
        ps["open_graph"] = {
            "tags": og_tags,
            "status": "pass" if len(og_tags) >= 3 else ("warn" if len(og_tags) > 0 else "fail"),
            "msg": f"已设置 {len(og_tags)} 个 OG 标签" if og_tags else "缺少 Open Graph 标签",
        }

        # Twitter Cards
        tw_tags = {}
        for name in ["twitter:card", "twitter:title", "twitter:description", "twitter:image"]:
            tag = soup.find("meta", attrs={"name": name})
            if tag:
                tw_tags[name] = tag.get("content", "")[:100]
        ps["twitter_cards"] = {
            "tags": tw_tags,
            "status": "pass" if tw_tags else "warn",
            "msg": f"已设置 {len(tw_tags)} 个 Twitter Card 标签" if tw_tags else "缺少 Twitter Card 标签",
        }

        # Structured Data (JSON-LD)
        json_ld = soup.find_all("script", type="application/ld+json")
        schemas = []
        for s in json_ld:
            try:
                import json
                data = json.loads(s.string)
                if isinstance(data, list):
                    schemas.extend([d.get("@type", "unknown") for d in data])
                else:
                    schemas.append(data.get("@type", "unknown"))
            except Exception:
                schemas.append("parse_error")
        ps["structured_data"] = {
            "count": len(json_ld),
            "types": schemas,
            "status": "pass" if schemas else "warn",
            "msg": f"检测到 {len(schemas)} 个结构化数据: {', '.join(schemas)}" if schemas else "缺少结构化数据 (JSON-LD)",
        }

        # Links
        all_links = soup.find_all("a", href=True)
        internal = []
        external = []
        broken_hint = []
        for a in all_links:
            href = a["href"]
            if href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:") or href.startswith("tel:"):
                continue
            abs_url = urljoin(resp.url, href)
            if self.parsed.netloc in urlparse(abs_url).netloc:
                internal.append(abs_url)
            elif abs_url.startswith("http"):
                external.append(abs_url)

        # Check a sample of external links (max 5)
        ext_sample = external[:5]
        broken_count = 0
        for url in ext_sample:
            try:
                r = self.session.head(url, timeout=10, allow_redirects=True)
                if r.status_code >= 400:
                    broken_count += 1
                    broken_hint.append(f"{url} -> {r.status_code}")
            except Exception:
                broken_count += 1
                broken_hint.append(f"{url} -> error")

        ps["links"] = {
            "internal_count": len(internal),
            "external_count": len(external),
            "broken_external_sample": broken_hint,
            "broken_external_count": broken_count,
            "checked_sample": len(ext_sample),
            "status": "pass" if broken_count == 0 else "warn",
            "msg": f"内链{len(internal)}，外链{len(external)}" + (f"，{broken_count}个外链异常(抽样{len(ext_sample)})" if broken_count else ""),
        }

        # URL structure
        path = self.parsed.path
        has_params = bool(self.parsed.query)
        url_clean = not has_params and not re.search(r"[A-Z]", path) and len(path) < 100
        ps["url_structure"] = {
            "path": path,
            "has_params": has_params,
            "status": "pass" if url_clean else "warn",
            "msg": "URL结构简洁" if url_clean else ("URL包含查询参数" if has_params else "URL路径过长或含大写字母"),
        }

    # ── Technical ─────────────────────────────────────────

    def _check_technical(self, resp, soup):
        t = self.results["technical"]

        # Mobile viewport
        viewport = soup.find("meta", attrs={"name": re.compile(r"^viewport$", re.I)})
        t["mobile_viewport"] = {
            "exists": bool(viewport),
            "content": viewport.get("content", "") if viewport else "",
            "status": "pass" if viewport else "fail",
            "msg": "已设置 viewport" if viewport else "缺少 viewport meta 标签（移动端不友好）",
        }

        # HTTPS
        t["https"] = {
            "status": "pass" if t.get("https") else "fail",
            "msg": "使用 HTTPS" if t.get("https") else "未使用 HTTPS",
        }

        # Page speed indicators
        size_kb = t.get("page_size_kb", 0)
        t["page_speed"] = {
            "page_size_kb": size_kb,
            "response_time_s": t.get("response_time_s", 0),
            "status": "pass" if size_kb < 500 and t.get("response_time_s", 99) < 2 else "warn",
            "msg": f"页面{size_kb}KB，响应{t.get('response_time_s', 0)}s" + ("，加载正常" if size_kb < 500 else "，页面过大"),
        }

        # HTML lang
        html_tag = soup.find("html")
        lang = html_tag.get("lang", "") if html_tag else ""
        t["html_lang"] = {
            "value": lang,
            "status": "pass" if lang else "warn",
            "msg": f"html lang={lang}" if lang else "缺少 html lang 属性",
        }

        # Gzip
        t["compression"] = {
            "status": "pass" if t.get("gzip") else "warn",
            "msg": "已启用 gzip 压缩" if t.get("gzip") else "未启用 gzip 压缩",
        }

        # Favicon
        favicon = soup.find("link", rel=re.compile(r"icon", re.I))
        t["favicon"] = {
            "exists": bool(favicon),
            "href": favicon.get("href", "") if favicon else "",
            "status": "pass" if favicon else "warn",
            "msg": "已设置 favicon" if favicon else "缺少 favicon",
        }

        # robots meta
        robots_meta = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
        if robots_meta:
            content = robots_meta.get("content", "")
            t["robots_meta"] = {"value": content, "status": "warn" if "noindex" in content.lower() else "pass", "msg": f"robots meta: {content}"}
        else:
            t["robots_meta"] = {"value": "", "status": "pass", "msg": "未设置 robots meta（默认可索引）"}

    # ── Content ───────────────────────────────────────────

    def _check_content(self, soup, resp):
        c = self.results["content"]

        # Strip scripts/styles, get text
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        words = text.split()
        word_count = len(words)

        c["word_count"] = {
            "count": word_count,
            "status": "pass" if word_count >= 300 else ("warn" if word_count >= 100 else "fail"),
            "msg": f"正文约 {word_count} 词" + ("，内容丰富" if word_count >= 300 else ("，内容偏少" if word_count >= 100 else "，内容过少(单薄内容)")),
        }

        # Text-to-HTML ratio
        html_size = len(resp.text)
        text_size = len(text)
        ratio = round(text_size / html_size * 100, 1) if html_size > 0 else 0
        c["text_html_ratio"] = {
            "ratio": f"{ratio}%",
            "status": "pass" if ratio >= 10 else "warn",
            "msg": f"文本/HTML比 {ratio}%" + ("，正常" if ratio >= 10 else "，偏低（建议>10%）"),
        }

        # Heading count
        total_headings = len(soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]))
        c["heading_count"] = {
            "count": total_headings,
            "status": "pass" if total_headings >= 3 else "warn",
            "msg": f"{total_headings} 个标题标签" + ("，结构合理" if total_headings >= 3 else "，标题过少"),
        }

        # Paragraph count
        paragraphs = soup.find_all("p")
        p_with_text = sum(1 for p in paragraphs if p.text.strip())
        c["paragraphs"] = {
            "total": len(paragraphs),
            "with_text": p_with_text,
            "status": "pass" if p_with_text >= 3 else "warn",
            "msg": f"{p_with_text} 个有内容的段落",
        }

        # Image to text balance
        imgs = len(soup.find_all("img"))
        c["media"] = {
            "images": imgs,
            "status": "info",
            "msg": f"{imgs} 张图片",
        }

    # ── Score ─────────────────────────────────────────────

    def _calc_score(self):
        weights = {"tdk": 20, "robots_sitemap": 15, "page_seo": 25, "technical": 20, "content": 20}
        score = 0
        for section, weight in weights.items():
            checks = self.results.get(section, {})
            if not checks:
                continue
            total = len(checks)
            passed = sum(1 for v in checks.values() if isinstance(v, dict) and v.get("status") == "pass")
            warned = sum(1 for v in checks.values() if isinstance(v, dict) and v.get("status") == "warn")
            section_score = (passed + warned * 0.5) / total * weight if total > 0 else 0
            score += section_score
        self.results["score"] = round(score)

    # ── Suggestions ───────────────────────────────────────

    def _generate_suggestions(self):
        suggestions = []
        r = self.results

        # TDK
        tdk = r.get("tdk", {})
        if tdk.get("title", {}).get("status") != "pass":
            suggestions.append({"priority": "high", "section": "TDK", "msg": f"优化 title 标签: {tdk.get('title', {}).get('msg', '')}"})
        if tdk.get("description", {}).get("status") != "pass":
            suggestions.append({"priority": "high", "section": "TDK", "msg": f"补充 description 标签: {tdk.get('description', {}).get('msg', '')}"})

        # robots/sitemap
        rs = r.get("robots_sitemap", {})
        if rs.get("robots", {}).get("status") == "fail":
            suggestions.append({"priority": "medium", "section": "robots.txt", "msg": "添加 robots.txt 文件，指导搜索引擎爬取"})
        if rs.get("sitemap", {}).get("status") == "fail":
            suggestions.append({"priority": "medium", "section": "sitemap", "msg": "创建 sitemap.xml 并提交至搜索引擎站长平台"})

        # Page SEO
        ps = r.get("page_seo", {})
        if ps.get("h1", {}).get("status") != "pass":
            suggestions.append({"priority": "high", "section": "页面SEO", "msg": f"修正 H1 标签: {ps.get('h1', {}).get('msg', '')}"})
        if ps.get("images", {}).get("missing_alt", 0) > 0:
            suggestions.append({"priority": "medium", "section": "页面SEO", "msg": f"为 {ps['images']['missing_alt']} 张图片添加 alt 属性"})
        if ps.get("canonical", {}).get("status") != "pass":
            suggestions.append({"priority": "medium", "section": "页面SEO", "msg": "添加 canonical 标签防止重复内容"})
        if ps.get("open_graph", {}).get("status") != "pass":
            suggestions.append({"priority": "low", "section": "页面SEO", "msg": "添加 Open Graph 标签提升社交媒体分享效果"})
        if ps.get("structured_data", {}).get("status") != "pass":
            suggestions.append({"priority": "medium", "section": "页面SEO", "msg": "添加 JSON-LD 结构化数据增强搜索结果展示"})

        # Technical
        tech = r.get("technical", {})
        if tech.get("https", {}).get("status") == "fail":
            suggestions.append({"priority": "high", "section": "技术", "msg": "迁移至 HTTPS，配置 SSL 证书"})
        if tech.get("mobile_viewport", {}).get("status") == "fail":
            suggestions.append({"priority": "high", "section": "技术", "msg": "添加 viewport meta 标签确保移动端适配"})
        if tech.get("compression", {}).get("status") == "warn":
            suggestions.append({"priority": "low", "section": "技术", "msg": "启用 gzip/brotli 压缩减少传输体积"})
        if tech.get("html_lang", {}).get("status") == "warn":
            suggestions.append({"priority": "low", "section": "技术", "msg": "在 <html> 标签添加 lang 属性"})
        if tech.get("favicon", {}).get("status") == "warn":
            suggestions.append({"priority": "low", "section": "技术", "msg": "添加 favicon 提升品牌识别度"})

        # Content
        content = r.get("content", {})
        if content.get("word_count", {}).get("status") == "fail":
            suggestions.append({"priority": "high", "section": "内容", "msg": "增加页面正文内容量，避免单薄内容(<100词)"})
        elif content.get("word_count", {}).get("status") == "warn":
            suggestions.append({"priority": "medium", "section": "内容", "msg": "适当增加正文内容量(建议>300词)"})
        if content.get("text_html_ratio", {}).get("status") == "warn":
            suggestions.append({"priority": "low", "section": "内容", "msg": "提高文本/HTML比例至10%以上，减少冗余代码"})

        r["suggestions"] = sorted(suggestions, key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["priority"]])


def main():
    parser = argparse.ArgumentParser(description="SEO Analysis Agent")
    parser.add_argument("url", help="目标网站 URL")
    parser.add_argument("--output", "-o", default="seo_report.html", help="报告输出路径")
    args = parser.parse_args()

    print(f"开始分析: {args.url}")
    analyzer = SEOAnalyzer(args.url)
    results = analyzer.run()

    from seo_report import generate_report
    html = generate_report(results)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"SEO 得分: {results['score']}/100")
    print(f"报告已生成: {args.output}")


if __name__ == "__main__":
    main()
