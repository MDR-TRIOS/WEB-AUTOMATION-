"""
tab_manager.py — Manages browser tabs in a Playwright async context.

Responsibilities:
- Open / close / switch tabs
- Track tab name → page object
- Track per-tab status and last action
"""

import asyncio
from typing import Dict, Optional, Any

from playwright.async_api import Browser, BrowserContext, Page
from logger import get_logger
from memory import SessionMemory

log = get_logger("tab_manager")

# Max concurrent tabs allowed
MAX_TABS = 5


class TabManager:
    """
    Manages a pool of named browser tabs backed by Playwright Pages.

    Usage:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            tm = TabManager(browser, memory)
            await tm.open_tab("amazon", "https://www.amazon.in")
            page = tm.get_page("amazon")
    """

    def __init__(self, context: BrowserContext, memory: SessionMemory):
        self.context = context
        self.memory = memory
        self._tabs: Dict[str, Page] = {}          # tab_name → Page
        self._statuses: Dict[str, str] = {}       # tab_name → status string
        self._lock = asyncio.Lock()

    # ── Public API ───────────────────────────────────────────────────────────

    async def open_tab(self, tab_name: str, url: Optional[str] = None) -> Page:
        """
        Open a new tab (browser page) with an optional starting URL.

        Args:
            tab_name: Logical name for this tab (e.g. "amazon").
            url: Optional URL to navigate to immediately.

        Returns:
            The Playwright Page object.
        """
        async with self._lock:
            if len(self._tabs) >= MAX_TABS:
                raise RuntimeError(
                    f"MAX_TABS ({MAX_TABS}) reached. Close a tab before opening another."
                )
            if tab_name in self._tabs:
                log.warning(f"Tab '{tab_name}' already exists. Returning existing page.")
                return self._tabs[tab_name]

            page = await self.context.new_page()
            self._tabs[tab_name] = page
            self._statuses[tab_name] = "pending"
            self.memory.init_tab(tab_name)
            log.info(f"Opened tab '{tab_name}'")

        if url:
            await self.navigate(tab_name, url)

        return page

    async def navigate(self, tab_name: str, url: str, timeout: int = 30_000) -> None:
        """Navigate the given tab to a URL."""
        page = self._require_tab(tab_name)
        log.info(f"[{tab_name}] Navigating → {url}")
        self._set_status(tab_name, "running")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            self.memory.update_tab(tab_name, url=url, last_action=f"navigate:{url}", status="running")
            self.memory.record_action(tab_name, f"navigate:{url}")
        except Exception as exc:
            log.error(f"[{tab_name}] Navigation failed: {exc}")
            self._set_status(tab_name, "error")
            self.memory.update_tab(tab_name, status="error")
            self.memory.log_error(tab_name, "navigate", str(exc))
            raise

    async def switch_tab(self, tab_name: str) -> Page:
        """
        Bring a tab to the foreground (bringToFront).
        Returns the Page for chaining.
        """
        page = self._require_tab(tab_name)
        await page.bring_to_front()
        log.debug(f"Switched to tab '{tab_name}'")
        return page

    async def close_tab(self, tab_name: str) -> None:
        """Close a tab by name."""
        async with self._lock:
            page = self._tabs.pop(tab_name, None)
            if page is None:
                log.warning(f"close_tab: Tab '{tab_name}' not found.")
                return
            await page.close()
            self._statuses.pop(tab_name, None)
            self.memory.update_tab(tab_name, status="closed")
            log.info(f"Closed tab '{tab_name}'")

    def get_page(self, tab_name: str) -> Page:
        """Return the Page object for a named tab."""
        return self._require_tab(tab_name)

    def get_tab_state(self, tab_name: str) -> Optional[Dict[str, Any]]:
        """Return current state dict for a tab from memory."""
        return self.memory.get_tab(tab_name)

    def list_tabs(self) -> Dict[str, str]:
        """Return a mapping of tab_name → status."""
        return dict(self._statuses)

    def set_tab_status(self, tab_name: str, status: str) -> None:
        """Update the status of a tab (running/completed/error/pending)."""
        self._set_status(tab_name, status)
        self.memory.update_tab(tab_name, status=status)

    def update_last_action(self, tab_name: str, action: str) -> None:
        """Store the most recent action on a tab."""
        self.memory.update_tab(tab_name, last_action=action)
        self.memory.record_action(tab_name, action)

    def all_pages(self) -> Dict[str, Page]:
        """Return the full tab_name → Page mapping."""
        return dict(self._tabs)

    # ── Internals ─────────────────────────────────────────────────────────────

    def _require_tab(self, tab_name: str) -> Page:
        page = self._tabs.get(tab_name)
        if page is None:
            raise KeyError(f"Tab '{tab_name}' does not exist. Open it first.")
        return page

    def _set_status(self, tab_name: str, status: str) -> None:
        self._statuses[tab_name] = status
