# Business Analyst

Generates a McKinsey-style PDF report for any website in three automated steps:

1. **Crawl** — a `browser-use` agent visits every significant page and extracts raw intelligence
2. **Analyze** — Claude Opus writes a structured consultant report as HTML (cover page, TOC, SWOT, Porter's Five Forces, strategic recommendations, overall score)
3. **Render** — Playwright converts the HTML to a polished A4 PDF

## Requirements

- Python 3.10+
- [browser-use](https://github.com/browser-use/browser-use) API key
- Anthropic API key

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

Copy `.env.example` to `.env` and fill in the required keys:

```
ANTHROPIC_API_KEY=sk-ant-...
BROWSER_USE_API_KEY=...
```

## Usage

```bash
python analyze.py https://example.com
```

Or run without arguments to be prompted for a URL:

```bash
python analyze.py
```

The report is saved as `report_<domain>_<date>.pdf` in the project directory.

## Output

The PDF includes:
- Cover page
- Table of contents
- Company overview & business model
- Products & pricing analysis
- Target market & customer profile
- Competitive positioning
- SWOT analysis
- Porter's Five Forces
- Risk assessment
- Strategic recommendations (with implementation complexity)
- Overall score with justification
