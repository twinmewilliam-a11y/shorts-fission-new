#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright

async def html_to_pdf():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"file:///root/.openclaw/workspace/projects/shorts-fission/research_report.html")
        await page.wait_for_timeout(3000)
        await page.pdf(
            path="/root/.openclaw/workspace/projects/shorts-fission/TikTok_Deduplication_Research_Report.pdf",
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
        )
        await browser.close()
        print("PDF 生成完成!")

if __name__ == "__main__":
    asyncio.run(html_to_pdf())
