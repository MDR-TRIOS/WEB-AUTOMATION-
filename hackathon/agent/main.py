"""
main.py — AI Multi-Tab Browser Agent — Orchestration Entry Point.

Usage:
    python main.py --task "Compare RTX 4060 laptop prices on Amazon and Flipkart"
    python main.py --task "..." --headless --no-preview
    python main.py --sites amazon flipkart --query "RTX 4060" --fallback

Environment variables:
    GEMINI_API_KEY      Gemini API key (default: hardcoded dev key)
    PREVIEW_WS_PORT     WebSocket port for live previews (default: 8765)
    PREVIEW_INTERVAL    Seconds between screenshots (default: 1.5)
    HEADLESS            Set to "true" for headless mode
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional

from playwright.async_api import async_playwright, Browser, BrowserContext

# ── Local modules ─────────────────────────────────────────────────────────────
from logger import get_logger
from memory import SessionMemory
from planner import plan_task, build_fallback_plan
from tab_manager import TabManager
from locator_engine import safe_fill, safe_click, find_element
from preview_streamer import PreviewStreamer

log = get_logger("main")

# ── Site URL registry ─────────────────────────────────────────────────────────
SITE_URLS: Dict[str, str] = {
    "amazon":       "https://www.amazon.in",
    "flipkart":     "https://www.flipkart.com",
    "ebay":         "https://www.ebay.com",
    "walmart":      "https://www.walmart.com",
    "bestbuy":      "https://www.bestbuy.com",
    "google":       "https://www.google.com",
    "bing":         "https://www.bing.com",
    "duckduckgo":   "https://www.duckduckgo.com",
    "wikipedia":    "https://www.wikipedia.org",
    "youtube":      "https://www.youtube.com",
}

# ── Search / Extract configurations per site ────────────────────────────────
SITE_CONFIGS: Dict[str, Dict] = {
    "amazon": {
        "search_box":   {"css": "#twotabsearchtextbox"},
        "search_btn":   {"css": "#nav-search-submit-button"},
        "results": {
            "name":     {"css": "h2 span.a-size-base-plus, h2 span.a-size-medium"},
            "price":    {"css": ".a-price-whole"},
            "rating":   {"css": "span.a-icon-alt"},
        },
    },
    "flipkart": {
        "search_box":   {"css": "input[title='Search for products, brands and more']"},
        "search_btn":   {"css": "button[type='submit']"},
        "close_popup":  {"css": "button._2KpZ6l._2doB4z"},   # optional login popup
        "results": {
            "name":     {"css": "._4rR01T, .s1Q9rs"},
            "price":    {"css": "._30jeq3._1_WHN1, ._30jeq3"},
            "rating":   {"css": "._3LWZlK"},
        },
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Execution Engine
# ═══════════════════════════════════════════════════════════════════════════════

class AgentExecutor:
    """
    Executes a structured task plan across multiple browser tabs.
    Manages the full lifecycle: planning → execution → comparison → output.
    """

    def __init__(
        self,
        memory: SessionMemory,
        tab_manager: TabManager,
        streamer: Optional[PreviewStreamer],
        headless: bool,
    ):
        self.memory = memory
        self.tm = tab_manager
        self.streamer = streamer
        self.headless = headless

    async def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run all steps in the plan.
        Steps targeting the same tab are grouped and run concurrently
        across different tabs where possible.
        """
        steps = plan.get("steps", [])
        self.memory.set_task_plan(plan)

        log.info(f"Executing plan with {len(steps)} steps")

        # ── Group steps into batches by dependency ──────────────────────────
        # Simple grouping: open_tab steps run first sequentially,
        # then per-tab tasks run concurrently, then compare runs last.
        open_steps  = [s for s in steps if s["action"] == "open_tab"]
        tab_steps   = [s for s in steps if s["action"] not in ("open_tab", "compare_prices")]
        compare_steps = [s for s in steps if s["action"] == "compare_prices"]

        # Phase 1 — Open tabs
        for step in open_steps:
            await self._exec_step(step)

        # Phase 2 — Per-tab tasks concurrently
        if tab_steps:
            # Group by tab and run each tab's steps sequentially within the tab,
            # but all tabs concurrently.
            tab_groups: Dict[str, List] = {}
            for step in tab_steps:
                tab = step.get("tab", "default")
                tab_groups.setdefault(tab, []).append(step)

            await asyncio.gather(
                *[self._run_tab_steps(tab, steps) for tab, steps in tab_groups.items()],
                return_exceptions=True,
            )

        # Phase 3 — Comparison
        for step in compare_steps:
            await self._exec_step(step)

        final = self._build_output()
        log.info(f"Execution complete. Results: {json.dumps(final, indent=2)}")
        return final

    async def _run_tab_steps(self, tab_name: str, steps: List[Dict]) -> None:
        """Run a list of steps sequentially on a single tab."""
        for step in steps:
            try:
                await self._exec_step(step)
            except Exception as exc:
                log.error(f"[{tab_name}] Step failed: {step} — {exc}")
                self.memory.log_error(tab_name, step.get("action", "?"), str(exc))

    async def _exec_step(self, step: Dict) -> None:
        action = step["action"]
        tab_name = step.get("tab") or step.get("site", "default")

        log.info(f"→ [{tab_name}] {action}")

        if action == "open_tab":
            site = step["site"]
            url = SITE_URLS.get(site, f"https://www.{site}.com")
            page = await self.tm.open_tab(site, url)

            # Register with preview streamer
            if self.streamer:
                self.streamer.add_tab(
                    site, page,
                    status_fn=lambda s=site: self.tm.list_tabs().get(s, "pending"),
                    action_fn=lambda s=site: (self.tm.get_tab_state(s) or {}).get("last_action", ""),
                )

            # Dismiss popups / cookie banners if applicable
            await self._dismiss_popups(site, page)

        elif action == "search":
            query = step.get("query", "")
            await self._do_search(tab_name, query)

        elif action == "extract":
            fields = step.get("fields", ["name", "price", "rating"])
            await self._do_extract(tab_name, fields)

        elif action == "compare_prices":
            self._do_compare()

        elif action == "navigate":
            url = step.get("url", "")
            await self.tm.navigate(tab_name, url)

        elif action == "click":
            page = self.tm.get_page(tab_name)
            desc = step.get("description", "element")
            await safe_click(page, description=desc, css=step.get("css"), tab_name=tab_name)

        elif action == "scroll":
            page = self.tm.get_page(tab_name)
            await page.evaluate("window.scrollBy(0, 600)")
            self.tm.update_last_action(tab_name, "scroll")

        elif action == "wait":
            ms = int(step.get("ms", 2000))
            await asyncio.sleep(ms / 1000)

        elif action == "close_tab":
            await self.tm.close_tab(tab_name)

    async def _dismiss_popups(self, site: str, page) -> None:
        """Try to close common cookie/login popups."""
        cfg = SITE_CONFIGS.get(site, {})
        popup_css = cfg.get("close_popup", {}).get("css")
        if popup_css:
            try:
                locator = page.locator(popup_css).first
                await locator.click(timeout=4000)
                log.debug(f"[{site}] Dismissed popup")
            except Exception:
                pass  # Popup not present, ignore

    async def _do_search(self, tab_name: str, query: str) -> None:
        """Type a search query and submit it."""
        page = self.tm.get_page(tab_name)
        cfg = SITE_CONFIGS.get(tab_name, {})

        filled = await safe_fill(
            page, query,
            description="search box",
            css=cfg.get("search_box", {}).get("css"),
            tab_name=tab_name,
        )
        if not filled:
            return

        # Try clicking search button; fallback to pressing Enter
        btn_css = cfg.get("search_btn", {}).get("css")
        clicked = await safe_click(page, description="search button", css=btn_css, tab_name=tab_name)
        if not clicked:
            await page.keyboard.press("Enter")
            log.info(f"[{tab_name}] Submitted search via Enter key")

        try:
            await page.wait_for_load_state("domcontentloaded", timeout=15_000)
        except Exception:
            pass

        self.tm.set_tab_status(tab_name, "running")
        self.tm.update_last_action(tab_name, f"search:{query}")

    async def _do_extract(self, tab_name: str, fields: List[str]) -> None:
        """Extract specified fields from the first result on the page."""
        page = self.tm.get_page(tab_name)
        cfg = SITE_CONFIGS.get(tab_name, {})
        result_cfg = cfg.get("results", {})
        extracted: Dict[str, str] = {}

        for field in fields:
            field_cfg = result_cfg.get(field, {})
            css = field_cfg.get("css")
            if not css:
                log.warning(f"[{tab_name}] No selector config for field '{field}'")
                extracted[field] = "N/A"
                continue

            locator = await find_element(page, css=css, description=f"{tab_name} {field}")
            if locator:
                try:
                    extracted[field] = (await locator.inner_text()).strip()
                except Exception:
                    extracted[field] = "N/A"
            else:
                extracted[field] = "N/A"
                self.memory.log_error(tab_name, f"extract:{field}", "Element not found")

        self.memory.set_result(tab_name, extracted)
        self.tm.set_tab_status(tab_name, "completed")
        self.tm.update_last_action(tab_name, f"extract:{','.join(fields)}")
        log.info(f"[{tab_name}] Extracted: {extracted}")

    def _do_compare(self) -> None:
        """Compare price results across all tabs and find the cheapest."""
        results = self.memory.get_all_results()
        cheapest_site = None
        cheapest_price = float("inf")

        for site, data in results.items():
            raw_price = data.get("price", "N/A")
            price_val = _parse_price(raw_price)
            if price_val is not None and price_val < cheapest_price:
                cheapest_price = price_val
                cheapest_site = site

        comparison = {"cheapest": cheapest_site or "unknown"}
        self.memory.set_comparison(comparison)
        log.info(f"Comparison result: {comparison}")

    def _build_output(self) -> Dict[str, Any]:
        """Assemble the final structured output dict."""
        output: Dict[str, Any] = {}
        for site, data in self.memory.get_all_results().items():
            output[site] = data
        output.update(self.memory.get_comparison())
        return output


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_price(price_str: str) -> Optional[float]:
    """Extract a numeric value from a price string like '₹1,23,456' or '$999.99'."""
    import re
    cleaned = re.sub(r"[^\d.]", "", price_str)
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# Main entry point
# ═══════════════════════════════════════════════════════════════════════════════

async def run(
    task: str,
    headless: bool = False,
    enable_preview: bool = True,
    fallback: bool = False,
    sites: Optional[List[str]] = None,
    query: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main async runner.

    Args:
        task:           Natural language task description.
        headless:       Run browser headless.
        enable_preview: Start WebSocket preview streamer.
        fallback:       Use rule-based fallback planner instead of AI.
        sites:          Sites for fallback planner.
        query:          Query for fallback planner.

    Returns:
        Final structured result dict.
    """
    memory = SessionMemory()
    log.info(f"Session started: {memory.store['task_id']}")

    # ── Plan ────────────────────────────────────────────────────────────────
    if fallback and sites and query:
        plan = build_fallback_plan(query, sites)
        log.info("Using fallback plan.")
    else:
        plan = plan_task(task)

    log.info(f"Plan:\n{json.dumps(plan, indent=2)}")

    # ── Browser ─────────────────────────────────────────────────────────────
    async with async_playwright() as pw:
        browser: Browser = await pw.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context: BrowserContext = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        tab_manager = TabManager(context, memory)
        streamer = PreviewStreamer() if enable_preview else None

        if streamer:
            try:
                await streamer.start_server()
            except Exception as exc:
                log.warning(f"Could not start preview server: {exc}. Disabling preview.")
                streamer = None

        executor = AgentExecutor(memory, tab_manager, streamer, headless)

        try:
            result = await executor.execute_plan(plan)
        finally:
            # Graceful shutdown
            for tab_name in list(tab_manager.list_tabs().keys()):
                try:
                    await tab_manager.close_tab(tab_name)
                except Exception:
                    pass
            if streamer:
                await streamer.stop_server()
            await context.close()
            await browser.close()

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI Multi-Tab Browser Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--task", type=str,
                        default="Compare RTX 4060 laptop prices on Amazon and Flipkart",
                        help="Natural language task description")
    parser.add_argument("--headless", action="store_true",
                        help="Run browser in headless mode")
    parser.add_argument("--no-preview", action="store_true",
                        help="Disable live WebSocket preview")
    parser.add_argument("--fallback", action="store_true",
                        help="Use rule-based planner instead of AI")
    parser.add_argument("--sites", nargs="+",
                        help="Sites for fallback planner (e.g. amazon flipkart)")
    parser.add_argument("--query", type=str,
                        help="Search query for fallback planner")

    args = parser.parse_args()

    headless = args.headless or os.environ.get("HEADLESS", "").lower() == "true"

    result = asyncio.run(
        run(
            task=args.task,
            headless=headless,
            enable_preview=not args.no_preview,
            fallback=args.fallback,
            sites=args.sites,
            query=args.query,
        )
    )

    print("\n" + "═" * 60)
    print("FINAL RESULT:")
    print("═" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
