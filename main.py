from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, HTMLResponse
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

            # Google Search with Redfin filter
            search_url = f"https://www.google.com/search?q={address.replace(' ', '+')}+site:redfin.com"
            await page.goto(search_url)
            await page.wait_for_selector("body", timeout=10000)

            # Get and return the raw HTML for inspection
            html_content = await page.content()
            await browser.close()

            return HTMLResponse(content=html_content)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)