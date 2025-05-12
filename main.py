from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import uvicorn

app = FastAPI()

@app.get("/redfin")
async def get_redfin_estimate(address: str = Query(...)):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Go to Redfin homepage
            await page.goto("https://www.redfin.com", timeout=20000)
            try:
                await page.wait_for_selector("input#search-box-input", timeout=10000)
            except PlaywrightTimeout:
                # Try accepting cookies if the banner is present
                try:
                    accept_btn = await page.query_selector("button[aria-label='Accept Cookies']")
                    if accept_btn:
                        await accept_btn.click()
                        await page.wait_for_selector("input#search-box-input", timeout=10000)
                    else:
                        raise
                except:
                    await browser.close()
                    return JSONResponse(
                        content={"error": "Redfin search input not found. Possibly bot-blocked or redirected."},
                        status_code=500
                    )

            # Fill in the address and search
            await page.fill("input#search-box-input", address)
            await page.keyboard.press("Enter")

            # Wait for results page to load and extract the estimate
            await page.wait_for_load_state("networkidle")
            await page.wait_for_selector('[data-rf-test-id="avmEstimate"]', timeout=15000)
            estimate_elem = await page.query_selector('[data-rf-test-id="avmEstimate"]')
            estimate_text = await estimate_elem.inner_text()
            current_url = page.url

            await browser.close()
            return {
                "address": address,
                "redfin_estimate": estimate_text,
                "redfin_url": current_url
            }

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)