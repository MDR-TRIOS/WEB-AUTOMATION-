"""
preview_streamer.py — Live screenshot streaming for each browser tab.

Each tab is captured every INTERVAL seconds, encoded as base64,
and broadcast via a simple asyncio WebSocket server.

Clients connect to ws://localhost:<PORT> and receive JSON frames:
{
    "tab": "amazon",
    "status": "running",
    "last_action": "search:RTX 4060",
    "image_b64": "<base64-encoded PNG>"
}
"""

import asyncio
import base64
import io
import json
import os
from typing import Set

import websockets
from playwright.async_api import Page
from logger import get_logger

log = get_logger("preview")

INTERVAL = float(os.environ.get("PREVIEW_INTERVAL", "1.5"))   # seconds between frames
WS_PORT = int(os.environ.get("PREVIEW_WS_PORT", "8765"))


class PreviewStreamer:
    """
    Manages per-tab screenshot capture and broadcasts frames
    to all connected WebSocket clients.
    """

    def __init__(self):
        self._clients: Set[websockets.WebSocketServerProtocol] = set()
        self._running = False
        self._tasks: list[asyncio.Task] = []
        self._server = None

    # ── Server lifecycle ──────────────────────────────────────────────────────

    async def start_server(self) -> None:
        """Start the WebSocket server in the background."""
        self._server = await websockets.serve(
            self._ws_handler, "localhost", WS_PORT
        )
        log.info(f"Preview WebSocket server started on ws://localhost:{WS_PORT}")

    async def stop_server(self) -> None:
        """Stop all streaming and shut down the WebSocket server."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        log.info("Preview streamer stopped.")

    # ── Tab streaming ─────────────────────────────────────────────────────────

    def add_tab(
        self,
        tab_name: str,
        page: Page,
        status_fn,   # callable() → str: returns current status
        action_fn,   # callable() → str: returns last action string
    ) -> None:
        """
        Register a tab for streaming. Immediately starts a background capture loop.

        Args:
            tab_name:  Logical name for the tab.
            page:      Playwright Page to capture.
            status_fn: Zero-arg callable returning current status string.
            action_fn: Zero-arg callable returning last action string.
        """
        self._running = True
        task = asyncio.ensure_future(
            self._capture_loop(tab_name, page, status_fn, action_fn)
        )
        self._tasks.append(task)
        log.info(f"Started preview capture for tab '{tab_name}'")

    # ── Internals ─────────────────────────────────────────────────────────────

    async def _ws_handler(
        self, websocket: websockets.WebSocketServerProtocol, path: str
    ) -> None:
        """Handle a new WebSocket client connection."""
        self._clients.add(websocket)
        log.debug(f"Preview client connected: {websocket.remote_address}")
        try:
            await websocket.wait_closed()
        finally:
            self._clients.discard(websocket)
            log.debug(f"Preview client disconnected: {websocket.remote_address}")

    async def _capture_loop(
        self,
        tab_name: str,
        page: Page,
        status_fn,
        action_fn,
    ) -> None:
        """Continuously capture screenshots and broadcast to all clients."""
        while self._running:
            try:
                # Take compressed screenshot
                screenshot_bytes = await page.screenshot(
                    type="jpeg", quality=60, full_page=False
                )
                image_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

                frame = json.dumps({
                    "tab": tab_name,
                    "status": status_fn(),
                    "last_action": action_fn(),
                    "image_b64": image_b64,
                })

                # Broadcast to all connected clients
                if self._clients:
                    await asyncio.gather(
                        *[self._safe_send(client, frame) for client in list(self._clients)],
                        return_exceptions=True,
                    )

            except Exception as exc:
                log.warning(f"[{tab_name}] Screenshot error: {exc}")

            await asyncio.sleep(INTERVAL)

    async def _safe_send(
        self, client: websockets.WebSocketServerProtocol, data: str
    ) -> None:
        """Send data to a client, silently discard if the connection is closed."""
        try:
            await client.send(data)
        except websockets.ConnectionClosed:
            self._clients.discard(client)
        except Exception as exc:
            log.warning(f"WebSocket send error: {exc}")
