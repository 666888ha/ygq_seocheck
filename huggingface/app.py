#!/usr/bin/env python3
"""SEO 分析 Agent - Hugging Face Spaces 版本 (Gradio)

Hugging Face Spaces 会自动运行此文件
"""

import gradio as gr
from seo_agent import SEOAnalyzer
from seo_report import generate_report


def analyze_url(url):
    if not url or not url.strip():
        return '<div style="padding:40px;text-align:center;color:#ef4444;font-size:18px;">请输入网站地址</div>'
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    try:
        analyzer = SEOAnalyzer(url)
        results = analyzer.run()
        return generate_report(results)
    except Exception as e:
        return f'<div style="padding:40px;text-align:center;color:#ef4444;font-size:18px;">分析失败: {str(e)}</div>'


custom_css = """
#header { text-align: center; margin-bottom: 20px; }
#header h1 { font-size: 28px; background: linear-gradient(135deg, #3b82f6, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; }
#header p { color: #94a3b8; margin-top: 4px; }
#footer { text-align: center; color: #64748b; font-size: 12px; margin-top: 16px; }
"""

with gr.Blocks(title="SEO 分析 Agent", theme=gr.themes.Soft(), css=custom_css) as demo:
    gr.HTML("""
    <div id="header">
        <h1>SEO 分析 Agent</h1>
        <p>输入网站 URL，一键生成专业 SEO 诊断报告</p>
    </div>
    """)

    with gr.Row():
        url_input = gr.Textbox(
            label="网站地址",
            placeholder="https://example.com",
            scale=4,
        )
        analyze_btn = gr.Button("分析", variant="primary", scale=1)

    examples = ["ausperbio.cn", "baidu.com", "taobao.com"]
    gr.Examples(examples=examples, inputs=url_input, label="快速测试")

    report_output = gr.HTML(
        value='<div style="padding:60px;text-align:center;color:#64748b;font-size:15px;">输入网址并点击「分析」按钮，SEO 报告将显示在此处</div>'
    )

    analyze_btn.click(fn=analyze_url, inputs=url_input, outputs=report_output)
    url_input.submit(fn=analyze_url, inputs=url_input, outputs=report_output)

    gr.HTML('<div id="footer">Powered by SEO Analysis Agent · TDK · robots/sitemap · 页面SEO · 技术问题 · 内容缺陷 · 整改建议</div>')

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
