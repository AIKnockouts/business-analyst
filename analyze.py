#!/usr/bin/env python3
"""Website analyzer using browser-use + Claude."""

import asyncio
import sys
from dotenv import load_dotenv
from browser_use import Agent, Browser, ChatBrowserUse, Tools, ActionResult

load_dotenv()


async def analyze(url: str) -> str:
    result = {}

    tools = Tools()

    @tools.action("Save the completed website analysis report")
    async def save_analysis(analysis: str) -> ActionResult:
        result["analysis"] = analysis
        return ActionResult(extracted_content=analysis)

    task = f"""Analyze this website thoroughly: {url}

Steps:
1. Go to {url}
2. Explore the site — check the homepage, navigation, and a few key pages
3. Analyze and report on:
   - Purpose / what the site is about
   - Main products, features, or services
   - Target audience
   - Pricing (if visible)
   - Key content or messaging
   - Technology / platform hints (if visible)
   - Contact info or company details
   - Anything else notable
4. Call save_analysis with a well-structured, readable report of your findings

Be thorough. Use markdown formatting in the report."""

    browser = Browser(headless=True, use_cloud=True)
    llm = ChatBrowserUse()

    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        tools=tools,
        use_vision="auto",
    )

    try:
        await agent.run(max_steps=15)
    finally:
        try:
            await browser.close()
        except Exception:
            pass

    return result.get("analysis", "(No analysis was saved by the agent.)")


def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Website URL to analyze: ").strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    print(f"\nAnalyzing: {url}\n" + "-" * 60 + "\n")

    report = asyncio.run(analyze(url))
    print(report)


if __name__ == "__main__":
    main()
