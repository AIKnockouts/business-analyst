#!/usr/bin/env python3
"""McKinsey-style website analysis → PDF.

Pipeline:
  1. browser-use agent crawls the site and extracts raw intelligence
  2. Claude Opus writes a structured consultant report as HTML
  3. Playwright renders the HTML to a polished PDF
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import anthropic
from browser_use import Agent, Browser, ChatBrowserUse, Tools, ActionResult


# ── Phase 1: Gather raw intelligence ─────────────────────────────────────────

async def gather_intelligence(url: str) -> str:
    gathered = {}

    tools = Tools()

    @tools.action("Save all gathered website intelligence")
    async def save_data(data: str) -> ActionResult:
        gathered["data"] = data
        return ActionResult(extracted_content=data)

    task = f"""You are a McKinsey business analyst doing deep due diligence on a company.

Visit: {url}

Explore every significant page you can find:
- Homepage
- About / Team / Company page
- All Products / Services / Features pages
- Pricing page
- Blog / Resources / Case studies / Customers page
- Careers page (signals growth stage, culture, hiring)
- Any partner, integration, or ecosystem pages
- Contact / footer (company details, location)

For each page, extract and document:
1. Company name, tagline, and precise description of what they do
2. Every product and service — names, descriptions, features
3. Pricing — exact plans, prices, trial terms, model (SaaS/one-time/usage-based/freemium)
4. Target customers — industry, company size, job title, B2B vs B2C
5. Key value propositions and differentiators vs competitors
6. Technology mentions — stack, integrations, APIs, platforms
7. Team members — names, titles, LinkedIn hints, backgrounds
8. Investors, funding rounds, accelerators if mentioned
9. Customer logos, testimonials, case studies, metrics cited
10. Geographic markets
11. Brand voice and messaging style
12. Any numbers cited (users, ARR, growth %, customers)

Be exhaustive. Call save_data with everything you found in a detailed structured dump."""

    browser = Browser(headless=True, use_cloud=True)
    llm = ChatBrowserUse()
    agent = Agent(task=task, llm=llm, browser=browser, tools=tools, use_vision="auto")

    try:
        await agent.run(max_steps=25)
    finally:
        try:
            await browser.close()
        except Exception:
            pass

    return gathered.get("data", "")


# ── Phase 2: Generate McKinsey-style HTML report via Claude Opus ──────────────

def generate_html_report(url: str, raw_data: str) -> str:
    client = anthropic.Anthropic()

    domain = url.replace("https://", "").replace("http://", "").split("/")[0]
    today = datetime.now().strftime("%B %d, %Y")

    prompt = f"""You are a Senior Partner at McKinsey & Company writing a confidential strategic assessment.

Target company website: {url}
Domain: {domain}
Date: {today}

Raw intelligence gathered by our analyst:
---
{raw_data}
---

Write a comprehensive, rigorous McKinsey-style business analysis as a complete, self-contained HTML document.
This will be rendered to PDF — make it look like a real consulting deliverable.

USE THIS EXACT HTML STRUCTURE AND CSS:

<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  /* Professional consulting report styles */
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Georgia', serif; font-size: 10pt; color: #1a1a1a; background: white; }}

  /* Cover page */
  .cover {{
    width: 100%; height: 100vh; min-height: 297mm;
    background: #1a2744; color: white;
    display: flex; flex-direction: column; justify-content: center;
    padding: 60px 70px; page-break-after: always;
  }}
  .cover .label {{ font-size: 9pt; letter-spacing: 3px; text-transform: uppercase; color: #7eb3e0; margin-bottom: 40px; }}
  .cover .company {{ font-size: 42pt; font-weight: bold; margin-bottom: 16px; line-height: 1.1; }}
  .cover .subtitle {{ font-size: 16pt; color: #a8c8e8; margin-bottom: 60px; font-style: italic; }}
  .cover .divider {{ width: 60px; height: 3px; background: #4a90d9; margin-bottom: 50px; }}
  .cover .meta {{ font-size: 9pt; color: #7eb3e0; line-height: 2; }}
  .cover .confidential {{
    position: absolute; bottom: 40px; right: 70px;
    font-size: 8pt; letter-spacing: 2px; text-transform: uppercase;
    color: #4a5a7a; border: 1px solid #4a5a7a; padding: 4px 12px;
  }}

  /* TOC page */
  .toc {{ padding: 60px 70px; page-break-after: always; }}
  .toc h2 {{ font-size: 18pt; color: #1a2744; border-bottom: 3px solid #1a2744; padding-bottom: 12px; margin-bottom: 30px; }}
  .toc-item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px dotted #ccc; font-size: 10pt; }}
  .toc-item .section-name {{ color: #1a2744; }}
  .toc-item .page-num {{ color: #888; }}

  /* Content pages */
  .page {{ padding: 50px 70px; page-break-after: always; }}
  .page:last-child {{ page-break-after: avoid; }}

  /* Section headers */
  .section-label {{ font-size: 8pt; letter-spacing: 3px; text-transform: uppercase; color: #4a90d9; margin-bottom: 8px; }}
  h1 {{ font-size: 22pt; color: #1a2744; margin-bottom: 6px; }}
  h2 {{ font-size: 16pt; color: #1a2744; margin-bottom: 20px; border-bottom: 2px solid #e8ecf0; padding-bottom: 8px; }}
  h3 {{ font-size: 11pt; color: #1a2744; margin: 20px 0 8px 0; font-weight: bold; }}
  h4 {{ font-size: 10pt; color: #4a90d9; margin: 14px 0 6px 0; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; }}

  /* Body text */
  p {{ line-height: 1.7; margin-bottom: 12px; color: #333; }}

  /* Callout / highlight box */
  .callout {{
    background: #f0f4f9; border-left: 4px solid #1a2744;
    padding: 16px 20px; margin: 20px 0; border-radius: 0 4px 4px 0;
  }}
  .callout.blue {{ background: #e8f2fc; border-left-color: #4a90d9; }}
  .callout.yellow {{ background: #fef9e7; border-left-color: #f39c12; }}
  .callout.red {{ background: #fdf2f2; border-left-color: #e74c3c; }}
  .callout.green {{ background: #f0faf4; border-left-color: #27ae60; }}

  /* Key stat box */
  .stat-grid {{ display: flex; gap: 16px; margin: 20px 0; flex-wrap: wrap; }}
  .stat-box {{
    flex: 1; min-width: 120px; background: #1a2744; color: white;
    padding: 16px; border-radius: 4px; text-align: center;
  }}
  .stat-box .stat-value {{ font-size: 20pt; font-weight: bold; color: #4a90d9; }}
  .stat-box .stat-label {{ font-size: 8pt; text-transform: uppercase; letter-spacing: 1px; color: #a8c8e8; margin-top: 4px; }}

  /* Tables */
  table {{ width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 9.5pt; }}
  th {{ background: #1a2744; color: white; padding: 10px 12px; text-align: left; font-weight: normal; letter-spacing: 0.5px; }}
  td {{ padding: 9px 12px; border-bottom: 1px solid #e8ecf0; vertical-align: top; }}
  tr:nth-child(even) td {{ background: #f8f9fb; }}

  /* SWOT grid */
  .swot {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 16px 0; }}
  .swot-box {{ padding: 18px; border-radius: 4px; }}
  .swot-box h3 {{ font-size: 10pt; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 12px; }}
  .swot-box ul {{ padding-left: 16px; }}
  .swot-box li {{ margin-bottom: 6px; line-height: 1.5; }}
  .swot-s {{ background: #e8f5e9; }} .swot-s h3 {{ color: #2e7d32; }}
  .swot-w {{ background: #fff3e0; }} .swot-w h3 {{ color: #e65100; }}
  .swot-o {{ background: #e3f2fd; }} .swot-o h3 {{ color: #1565c0; }}
  .swot-t {{ background: #fce4ec; }} .swot-t h3 {{ color: #880e4f; }}

  /* Rating stars / score */
  .score {{ display: inline-block; background: #1a2744; color: #4a90d9; font-size: 18pt; font-weight: bold; padding: 6px 16px; border-radius: 4px; margin-right: 8px; }}
  .score-label {{ font-size: 10pt; color: #888; vertical-align: middle; }}

  /* Recommendation cards */
  .rec {{ border: 1px solid #e0e8f0; border-radius: 6px; padding: 18px; margin-bottom: 16px; }}
  .rec-num {{ float: left; background: #1a2744; color: #4a90d9; font-size: 14pt; font-weight: bold; width: 36px; height: 36px; line-height: 36px; text-align: center; border-radius: 50%; margin-right: 14px; }}
  .rec-content {{ overflow: hidden; }}
  .rec h3 {{ font-size: 11pt; color: #1a2744; margin-bottom: 6px; }}
  .rec .complexity {{ display: inline-block; font-size: 8pt; padding: 2px 10px; border-radius: 10px; margin-top: 8px; font-weight: bold; }}
  .complexity-low {{ background: #e8f5e9; color: #2e7d32; }}
  .complexity-med {{ background: #fff3e0; color: #e65100; }}
  .complexity-high {{ background: #fce4ec; color: #c62828; }}

  /* Risk table */
  .risk-high {{ color: #c62828; font-weight: bold; }}
  .risk-med {{ color: #e65100; font-weight: bold; }}
  .risk-low {{ color: #2e7d32; font-weight: bold; }}

  /* Footer */
  .footer {{
    position: fixed; bottom: 20px; left: 70px; right: 70px;
    display: flex; justify-content: space-between;
    font-size: 7.5pt; color: #aaa; border-top: 1px solid #eee; padding-top: 6px;
  }}

  /* Porter's Five Forces */
  .forces {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 16px 0; }}
  .force-box {{ background: #f8f9fb; border: 1px solid #e0e8f0; padding: 14px; border-radius: 4px; }}
  .force-box h4 {{ font-size: 9pt; color: #1a2744; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 1px; }}
  .force-rating {{ font-size: 8pt; color: #888; }}

  /* Verdict box */
  .verdict {{
    background: #1a2744; color: white; padding: 30px;
    margin: 20px 0; border-radius: 6px;
  }}
  .verdict h3 {{ color: #4a90d9; margin-bottom: 12px; font-size: 12pt; text-transform: uppercase; letter-spacing: 2px; }}
  .verdict p {{ color: #d0dce8; line-height: 1.8; }}

  /* Print */
  @media print {{
    body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  }}
</style>
</head>
<body>

[YOUR FULL REPORT HTML HERE — all sections, fully populated with real analysis]

<div class="footer">
  <span>McKinsey & Company — Confidential</span>
  <span>Strategic Assessment: {domain}</span>
  <span>{today}</span>
</div>
</body>
</html>

INSTRUCTIONS:
- Replace [YOUR FULL REPORT HTML HERE] with the complete report content using the CSS classes above
- Cover page → Table of Contents → one section per page (use class="page")
- Be analytically rigorous. Make real inferences. Don't just describe — analyze, assess, judge.
- Where data is missing, say so and explain what it implies (e.g., "no pricing visible → likely enterprise sales motion")
- Use specific language: "strong", "weak", "concerning", "best-in-class", quantify wherever possible
- The SWOT must have 4+ bullets per quadrant
- Give 5 strategic recommendations minimum, each with Implementation Complexity tag
- Overall score must be X/10 with detailed justification
- Include Porter's Five Forces analysis
- This is for a PAYING CLIENT — make it worth $500,000

Output ONLY the complete HTML. No explanation. No markdown. Start with <!DOCTYPE html>"""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text


# ── Phase 3: Render HTML → PDF via Playwright ─────────────────────────────────

async def html_to_pdf(html: str, output_path: str):
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html, wait_until="networkidle")
        await page.pdf(
            path=output_path,
            format="A4",
            print_background=True,
            margin={"top": "0mm", "bottom": "12mm", "left": "0mm", "right": "0mm"},
        )
        await browser.close()


# ── Orchestrator ──────────────────────────────────────────────────────────────

async def run(url: str):
    domain = url.replace("https://", "").replace("http://", "").split("/")[0].replace(".", "_")
    date_str = datetime.now().strftime("%Y%m%d")
    output_path = Path(__file__).parent / f"report_{domain}_{date_str}.pdf"

    print(f"\n[1/3] Gathering intelligence from {url} ...")
    raw_data = await gather_intelligence(url)
    if not raw_data:
        print("  Warning: agent returned no data. Report will be based on limited info.")

    print("[2/3] Generating McKinsey-style analysis (Claude Opus) ...")
    html = generate_html_report(url, raw_data)

    # Sanity check — if Claude returned markdown fences, strip them
    if html.strip().startswith("```"):
        html = html.strip().lstrip("`").strip()
        if html.lower().startswith("html"):
            html = html[4:].strip()

    print("[3/3] Rendering PDF ...")
    await html_to_pdf(html, str(output_path))

    print(f"\n✓ Report saved → {output_path}\n")


def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Website URL to analyze: ").strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    asyncio.run(run(url))


if __name__ == "__main__":
    main()
