#!/usr/bin/env python3
"""使用 Playwright 将 HTML 转换为 PDF"""

import asyncio
from playwright.async_api import async_playwright

async def html_to_pdf():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # 加载 HTML 文件
        await page.goto(f"file:///root/.openclaw/workspace/projects/shorts-fission/validation_report.html")
        
        # 等待字体加载
        await page.wait_for_timeout(3000)
        
        # 生成 PDF
        await page.pdf(
            path="/root/.openclaw/workspace/projects/shorts-fission/TikTok_Video_Deduplication_Validation_Report.pdf",
            format="A4",
            print_background=True,
            margin={
                "top": "0",
                "right": "0",
                "bottom": "0",
                "left": "0"
            }
        )
        
        await browser.close()
        print("PDF 生成完成!")

if __name__ == "__main__":
    asyncio.run(html_to_pdf())
