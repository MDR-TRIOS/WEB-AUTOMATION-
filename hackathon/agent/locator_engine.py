"""
locator_engine.py — Smart multi-strategy DOM element locator.

Strategy order:
  1. CSS selector
  2. XPath
  3. Text-based selector
  4. AI-regenerated selector (Gemini, if all above fail)

Retries up to MAX_RETRIES times before giving up.
"""

import asyncio
import os
from typing import List, Optional, Tuple

from playwright.async_api import Page, Locator, TimeoutError as PWTimeout
from google import genai
from logger import get_logger

log = get_logger("locator")

MAX_RETRIES = 3
TIMEOUT_MS = 8_000  # per locate attempt

_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyC_Q1cIU0ba4iMCU1RnBGtbszv0XCfIWuw")
_client = genai.Client(api_key=_API_KEY)


async def find_element(
    page: Page,
    css: Optional[str] = None,
    xpath: Optional[str] = None,
    text: Optional[str] = None,
    description: str = "element",
) -> Optional[Locator]:
    """
    Attempt to locate a DOM element using multiple strategies with retries.

    Args:
        page:        Playwright Page object.
        css:         CSS selector (tried first).
        xpath:       XPath expression (tried second).
        text:        Visible text (tried third).
        description: Human description used for AI regeneration prompt.

    Returns:
        A Playwright Locator if found, else None.
    """
    strategies = _build_strategies(page, css, xpath, text)

    for attempt in range(1, MAX_RETRIES + 1):
        log.debug(f"Locate attempt {attempt}/{MAX_RETRIES} for '{description}'")

        # Try each strategy in order
        for strategy_name, locator in strategies:
            result = await _try_locate(locator, strategy_name, description)
            if result is not None:
                return result

        # All strategies failed — try AI regeneration
        if attempt < MAX_RETRIES:
            ai_selector = await _ai_regenerate(page, description)
            if ai_selector:
                strategies = [("AI", page.locator(ai_selector))]
                log.info(f"Retrying with AI selector: {ai_selector!r}")
            else:
                log.warning("AI selector regeneration returned nothing. Waiting before retry.")
                await asyncio.sleep(1.5)

    log.error(f"Could not locate '{description}' after {MAX_RETRIES} attempts.")
    return None


async def safe_click(
    page: Page,
    description: str = "button",
    css: Optional[str] = None,
    xpath: Optional[str] = None,
    text: Optional[str] = None,
    tab_name: str = "",
) -> bool:
    """
    Locate and click an element. Returns True on success, False on failure.
    """
    locator = await find_element(page, css=css, xpath=xpath, text=text, description=description)
    if locator is None:
        log.error(f"[{tab_name}] Click failed: could not find '{description}'")
        return False
    try:
        await locator.click(timeout=TIMEOUT_MS)
        log.info(f"[{tab_name}] Clicked '{description}'")
        return True
    except Exception as exc:
        log.error(f"[{tab_name}] Click error on '{description}': {exc}")
        return False


async def safe_fill(
    page: Page,
    value: str,
    description: str = "input",
    css: Optional[str] = None,
    xpath: Optional[str] = None,
    text: Optional[str] = None,
    tab_name: str = "",
) -> bool:
    """
    Locate a field and fill it with a value. Returns True on success.
    """
    locator = await find_element(page, css=css, xpath=xpath, text=text, description=description)
    if locator is None:
        log.error(f"[{tab_name}] Fill failed: could not find '{description}'")
        return False
    try:
        await locator.fill(value, timeout=TIMEOUT_MS)
        log.info(f"[{tab_name}] Filled '{description}' with {value!r}")
        return True
    except Exception as exc:
        log.error(f"[{tab_name}] Fill error on '{description}': {exc}")
        return False


# ── Internals ─────────────────────────────────────────────────────────────────

def _build_strategies(
    page: Page,
    css: Optional[str],
    xpath: Optional[str],
    text: Optional[str],
) -> List[Tuple[str, Locator]]:
    """Build an ordered list of (name, locator) pairs from provided hints."""
    strategies = []
    if css:
        strategies.append(("CSS", page.locator(css)))
    if xpath:
        strategies.append(("XPath", page.locator(f"xpath={xpath}")))
    if text:
        strategies.append(("Text", page.get_by_text(text, exact=False)))
    return strategies


async def _try_locate(
    locator: Locator, strategy_name: str, description: str
) -> Optional[Locator]:
    """Return the locator if it is visible in the page, else None."""
    try:
        await locator.first.wait_for(state="visible", timeout=TIMEOUT_MS)
        log.debug(f"  [{strategy_name}] Found '{description}' ✓")
        return locator.first
    except PWTimeout:
        log.debug(f"  [{strategy_name}] Timeout for '{description}'")
        return None
    except Exception as exc:
        log.debug(f"  [{strategy_name}] Error for '{description}': {exc}")
        return None


async def _ai_regenerate(page: Page, description: str) -> Optional[str]:
    """
    Ask Gemini to generate a CSS selector for the described element
    based on the current page's simplified HTML.
    """
    try:
        html_snippet = await page.evaluate("""
            () => {
                const body = document.body.cloneNode(true);
                // Remove scripts, styles, svgs to reduce size
                body.querySelectorAll('script,style,svg,noscript').forEach(el => el.remove());
                return body.innerHTML.slice(0, 8000);
            }
        """)

        prompt = (
            f"Given this HTML snippet from a web page:\n\n{html_snippet}\n\n"
            f"Generate a single, reliable CSS selector to locate: '{description}'.\n"
            "Return ONLY the CSS selector string — nothing else."
        )

        response = _client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        selector = response.text.strip().strip("`").strip()
        log.info(f"AI generated selector for '{description}': {selector!r}")
        return selector if selector else None

    except Exception as exc:
        log.error(f"AI selector regeneration failed: {exc}")
        return None
