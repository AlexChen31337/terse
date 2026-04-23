#!/usr/bin/env python3
"""Publish AI Coding Agents article to Payhip as free digital product."""
import asyncio, sys, os, json, time
from pathlib import Path

OUT = Path("/media/DATA/.openclaw/workspace/tmp/payhip-ai-coding-agents-2026-04-23")
PDF = OUT / "ai-coding-agents.pdf"
EPUB = OUT / "ai-coding-agents.epub"
COVER = OUT / "cover.png"
CREDS = json.load(open("/media/DATA/.openclaw/workspace/memory/encrypted/payhip-credentials-plaintext.json"))

TITLE = "How to Utilize AI Coding Agents for Production-Grade Software"
TEASER = (
    "A practitioner's guide to shipping real production software with AI coding agents — "
    "not toy demos, not weekend hackathons, but actual systems that handle money, user data, and uptime commitments.\n\n"
    "Inside: the PBR (Plan → Build → Review) pipeline, model selection matrix, context engineering, "
    "VBR (Verify Before Reporting) discipline, guardrails that actually work, and the real pitfalls to avoid. "
    "Everything learned from eighteen months of shipping production code with Claude, GPT-5, and local models."
)

async def main():
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        ctx = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
        page = await ctx.new_page()
        result = {"login": False, "product_url": None, "errors": []}

        try:
            # --- Login
            print("LOGIN: navigating", flush=True)
            await page.goto("https://payhip.com/login", wait_until="networkidle", timeout=45000)
            await page.screenshot(path=str(OUT / "s1_login_page.png"))
            await page.fill('input[name="login"]', CREDS["email"])
            await page.fill('input[name="password"]', CREDS["password"])
            await page.screenshot(path=str(OUT / "s2_login_filled.png"))
            async with page.expect_navigation(wait_until="networkidle", timeout=45000):
                await page.click('button[type="submit"]')
            cur = page.url
            print(f"LOGIN: post url = {cur}", flush=True)
            await page.screenshot(path=str(OUT / "s3_post_login.png"))
            if "login" in cur:
                result["errors"].append(f"login failed, still at {cur}")
                return result
            result["login"] = True

            # --- Navigate to product creation
            print("PRODUCT: navigating to /products/add", flush=True)
            await page.goto("https://payhip.com/products/add", wait_until="networkidle", timeout=45000)
            await page.screenshot(path=str(OUT / "s4_add_product.png"))

            # Try to click "Digital Product" card if a type picker appears
            try:
                await page.get_by_text("Digital", exact=False).first.click(timeout=5000)
                print("PRODUCT: clicked Digital type", flush=True)
                await page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                print("PRODUCT: no type picker (or already past it)", flush=True)

            await page.screenshot(path=str(OUT / "s5_product_form.png"))

            # Fill title — try common selectors
            filled_title = False
            for sel in [
                'input[name="name"]',
                'input[name="title"]',
                'input[placeholder*="name" i]',
                'input[placeholder*="title" i]',
            ]:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        await el.fill(TITLE)
                        filled_title = True
                        print(f"PRODUCT: title filled via {sel}", flush=True)
                        break
                except Exception:
                    pass
            if not filled_title:
                result["errors"].append("could not locate title input")

            # Price = 0 (free)
            for sel in [
                'input[name="price"]',
                'input[name="price_usd"]',
                'input[placeholder*="price" i]',
            ]:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        await el.fill("0")
                        print(f"PRODUCT: price filled via {sel}", flush=True)
                        break
                except Exception:
                    pass

            # Description/teaser — look for contenteditable or textarea
            for sel in [
                'div.ql-editor',
                'div[contenteditable="true"]',
                'textarea[name="description"]',
                'textarea',
            ]:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        await el.click()
                        await page.keyboard.type(TEASER, delay=5)
                        print(f"PRODUCT: desc filled via {sel}", flush=True)
                        break
                except Exception:
                    pass

            await page.screenshot(path=str(OUT / "s6_form_filled.png"))

            # Upload digital file(s)
            try:
                file_inputs = await page.query_selector_all('input[type="file"]')
                print(f"PRODUCT: found {len(file_inputs)} file inputs", flush=True)
                uploaded = False
                for fi in file_inputs:
                    try:
                        await fi.set_input_files([str(PDF), str(EPUB)])
                        uploaded = True
                        print("PRODUCT: uploaded PDF+EPUB to one file input", flush=True)
                        break
                    except Exception as e:
                        try:
                            await fi.set_input_files(str(PDF))
                            uploaded = True
                            print("PRODUCT: uploaded PDF only", flush=True)
                            break
                        except Exception as e2:
                            continue
                if not uploaded:
                    result["errors"].append("could not upload product files")
            except Exception as e:
                result["errors"].append(f"file upload error: {e}")

            # Cover upload — try a different file input if there are multiple
            try:
                file_inputs = await page.query_selector_all('input[type="file"]')
                if len(file_inputs) > 1:
                    await file_inputs[-1].set_input_files(str(COVER))
                    print("PRODUCT: uploaded cover via last file input", flush=True)
            except Exception as e:
                print(f"COVER upload skipped: {e}", flush=True)

            # Wait for uploads to settle
            await page.wait_for_timeout(8000)
            await page.screenshot(path=str(OUT / "s7_uploads_done.png"))

            # Save/publish button
            clicked = False
            for text in ["Publish", "Save and Publish", "Save", "Create product"]:
                try:
                    btn = page.get_by_role("button", name=text)
                    if await btn.count() > 0:
                        await btn.first.click(timeout=5000)
                        clicked = True
                        print(f"PRODUCT: clicked '{text}'", flush=True)
                        break
                except Exception:
                    pass
            if not clicked:
                # fallback: submit button
                try:
                    await page.click('button[type="submit"]')
                    clicked = True
                    print("PRODUCT: clicked submit button", flush=True)
                except Exception as e:
                    result["errors"].append(f"no publish button found: {e}")

            await page.wait_for_timeout(8000)
            await page.screenshot(path=str(OUT / "s8_after_publish.png"))
            print(f"PRODUCT: final url = {page.url}", flush=True)

            # Try to find the product URL on the resulting page
            try:
                # Go to products listing
                await page.goto("https://payhip.com/products", wait_until="networkidle", timeout=30000)
                await page.screenshot(path=str(OUT / "s9_products_list.png"))
                # Find link containing the product title
                link = await page.query_selector(f'a:has-text("{TITLE[:30]}")')
                if link:
                    href = await link.get_attribute("href")
                    if href:
                        result["product_url"] = href if href.startswith("http") else f"https://payhip.com{href}"
                        print(f"PRODUCT: url = {result['product_url']}", flush=True)
                if not result["product_url"]:
                    # Fallback: get all product links and return first
                    links = await page.query_selector_all('a[href*="/b/"]')
                    for l in links[:5]:
                        h = await l.get_attribute("href")
                        t = (await l.inner_text()).strip()
                        print(f"  candidate: {h} text={t[:40]}", flush=True)
                        if "ai" in t.lower() or "coding" in t.lower() or "agent" in t.lower():
                            result["product_url"] = h if h.startswith("http") else f"https://payhip.com{h}"
                            break
            except Exception as e:
                result["errors"].append(f"url lookup failed: {e}")

        except Exception as e:
            import traceback
            result["errors"].append(f"fatal: {e}\n{traceback.format_exc()}")
        finally:
            await browser.close()

        print("\n=== RESULT ===")
        print(json.dumps(result, indent=2))
        return result

if __name__ == "__main__":
    asyncio.run(main())
