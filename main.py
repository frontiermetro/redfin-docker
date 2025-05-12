from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright
import uvicorn

app = FastAPI()

@app.get("/redfin")
async def get_redfin_estimate(address: str = Query(...)):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Step 1: Search Redfin using the address in Google
            search_url = f"https://www.google.com/search?q={address.replace(' ', '+')}+site:redfin.com"
            await page.goto(search_url)
            await page.wait_for_selector("a")  # Wait for search results

            # Step 2: Click the first Redfin link in results
            redfin_link = await page.query_selector("a[href*='redfin.com']")
            if redfin_link:
                redfin_url = await redfin_link.get_attribute("href")
                if not redfin_url.startswith("http"):
                    redfin_url = "https://www.google.com" + redfin_url
                await page.goto(redfin_url)
            else:
                await browser.close()
                return JSONResponse(content={"error": "No Redfin link found"}, status_code=404)

            # Step 3: Wait for Redfin Estimate to appear
            await page.wait_for_selector('[data-rf-test-id="avmEstimate"]', timeout=10000)
            estimate_elem = await page.query_selector('[data-rf-test-id="avmEstimate"]')
            estimate_text = await estimate_elem.inner_text()

            await browser.close()
            return {
                "address": address,
                "redfin_estimate": estimate_text
            }

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)