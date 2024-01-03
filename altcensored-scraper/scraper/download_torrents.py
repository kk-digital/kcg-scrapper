import asyncio
import json
import sys
from io import TextIOWrapper
from pathlib import Path

from playwright.async_api import Browser, async_playwright
from playwright_stealth import stealth_async


async def download_torrent(item: dict, browser: Browser, dfp: TextIOWrapper):
    context = await browser.new_context()  # TODO set proxy config
    page = await context.new_page()
    await stealth_async(page)

    try:
        await page.goto(item["url"])
        async with page.expect_download() as download_info:
            await page.locator(
                ".pure-u-md-1-5 .h-box:nth-child(1) a:nth-child(3)"
            ).click()

        download = await download_info.value
        await download.save_as(Path(output_dir, download.suggested_filename))

        item["torrent_filename"] = f"full/{download.suggested_filename}"
        dfp.write(json.dumps(item) + "\n")

    finally:
        await page.close()
        await context.close()


async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)

        with open(data_file, "r", encoding="utf-8") as sfp:
            with Path(output_dir, "data.jsonl").open("w", encoding="utf-8") as dfp:
                coros = []
                for line in sfp:
                    line = json.loads(line)
                    coros.append(download_torrent(item=line, browser=browser, dfp=dfp))

                batch_size = 4
                for i in range(0, len(coros), batch_size):
                    await asyncio.gather(*coros[i : i + batch_size])


if __name__ == "__main__":
    data_file = sys.argv[1]
    output_dir = sys.argv[2]
    asyncio.run(main())
