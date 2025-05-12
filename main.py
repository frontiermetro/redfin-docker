from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright
import uvicorn
import re

app = FastAPI()

@app.get("/redfin")
async def get_redfin_estimate(address: str = Query(...)):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Step 1: Google Search with Redfin filter
            search_url = f"https://www.google.com/search?q={address.replace(' ', '+')}+site:redfin.com"
            await page.goto(search_url)
            await page.wait_for_selector("a[href]", timeout=10000)

            # Step 2: Find first Redfin URL from Google result (redirect format)
            links = await page.query_selector_all("a[href*='redfin.com']")
            redfin_url = None

            for link in links:
                href = await link.get_attribute("href")
                if href and "redfin.com" in href:
                    match = re.search(r"/url\?q=(https://www.redfin.com[^\&]+)", href)
                    if match:
                        redfin_url = match.group(1)
                        break
                    elif href.startswith("https://www.redfin.com"):
                        redfin_url = href
                        break

            if not redfin_url:
                await browser.close()
                return JSONResponse(content={"error": "No Redfin link found"}, status_code=404)

            # Step 3: Visit the Redfin listing page
            await page.goto(redfin_url)
            await page.wait_for_selector('[data-rf-test-id="avmEstimate"]', timeout=10000)
            estimate_elem = await page.query_selector('[data-rf-test-id="avmEstimate"]')
            estimate_text = await estimate_elem.inner_text()

            await browser.close()
            return {
                "address": address,
                "redfin_estimate": estimate_text,
                "redfin_url": redfin_url
            }

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)