"""
planner.py — Natural Language → Structured JSON task planner.
Uses Google Gemini to parse and validate browser automation steps.
"""

import json
import os
import re
from typing import Dict, List, Any

from google import genai
from logger import get_logger

log = get_logger("planner")

# ── Allowed domains (safety constraint) ──────────────────────────────────────
ALLOWED_DOMAINS = {
    "amazon", "flipkart", "ebay", "walmart", "bestbuy",
    "google", "bing", "duckduckgo", "wikipedia",
    "youtube", "reddit", "github", "stackoverflow",
}

VALID_ACTIONS = {
    "open_tab", "search", "extract", "compare_prices",
    "click", "navigate", "scroll", "wait", "close_tab",
}

# ── Gemini client ─────────────────────────────────────────────────────────────
_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyC_Q1cIU0ba4iMCU1RnBGtbszv0XCfIWuw")
_client = genai.Client(api_key=_API_KEY)

# ── Prompt template ───────────────────────────────────────────────────────────
PLANNER_PROMPT = """
You are a browser automation task planner.
Convert the following natural language instruction into a strictly structured JSON execution plan.

Rules:
- Only use these actions: open_tab, search, extract, compare_prices, click, navigate, scroll, wait, close_tab
- Sites must be lowercase domain names: amazon, flipkart, google, youtube, wikipedia, etc.
- Fields for "extract" must be from: name, price, rating, description, image, url, reviews
- Steps must follow a logical order (open tab before searching, search before extracting)
- Return ONLY valid JSON with a "steps" array. No prose, no markdown fences.

Example output:
{{
  "steps": [
    {{"action": "open_tab", "site": "amazon"}},
    {{"action": "search", "query": "RTX 4060 laptop", "tab": "amazon"}},
    {{"action": "extract", "fields": ["name", "price", "rating"], "tab": "amazon"}},
    {{"action": "compare_prices"}}
  ]
}}

User instruction: {instruction}
"""


def plan_task(instruction: str) -> Dict[str, Any]:
    """
    Convert a natural language instruction into a validated JSON execution plan.

    Args:
        instruction: Free-text user task description.

    Returns:
        dict with key "steps" containing a list of action dicts.

    Raises:
        ValueError: If the plan cannot be parsed or contains invalid steps.
    """
    log.info(f"Planning task: {instruction!r}")

    prompt = PLANNER_PROMPT.format(instruction=instruction)

    try:
        response = _client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        raw = response.text.strip()
        log.debug(f"Planner raw response: {raw}")
    except Exception as exc:
        log.error(f"Gemini API error: {exc}")
        raise

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        plan = json.loads(raw)
    except json.JSONDecodeError as exc:
        log.error(f"JSON parse error: {exc}\nRaw: {raw}")
        raise ValueError(f"Planner returned invalid JSON: {exc}") from exc

    _validate_plan(plan)
    log.info(f"Plan validated: {len(plan['steps'])} steps")
    return plan


def _validate_plan(plan: Dict[str, Any]) -> None:
    """Raise ValueError if plan is structurally invalid."""
    if not isinstance(plan, dict):
        raise ValueError("Plan must be a JSON object.")
    if "steps" not in plan or not isinstance(plan["steps"], list):
        raise ValueError("Plan must contain a 'steps' list.")
    if not plan["steps"]:
        raise ValueError("Plan has no steps.")

    for i, step in enumerate(plan["steps"]):
        if "action" not in step:
            raise ValueError(f"Step {i} missing 'action' key.")
        action = step["action"]
        if action not in VALID_ACTIONS:
            raise ValueError(
                f"Step {i} has unknown action '{action}'. "
                f"Allowed: {sorted(VALID_ACTIONS)}"
            )
        # Validate site names for domain safety
        if "site" in step and step["site"] not in ALLOWED_DOMAINS:
            log.warning(
                f"Step {i}: site '{step['site']}' not in allowed domain list. "
                "Proceeding with caution."
            )


def build_fallback_plan(query: str, sites: List[str]) -> Dict[str, Any]:
    """
    Build a minimal comparison plan without calling the AI.
    Useful when the AI planner fails or as a hardcoded fallback.

    Args:
        query: Product search query.
        sites: List of site names to search.

    Returns:
        Structured plan dict.
    """
    steps = []
    for site in sites:
        steps.append({"action": "open_tab", "site": site, "tab": site})
        steps.append({"action": "search", "query": query, "tab": site})
        steps.append({
            "action": "extract",
            "fields": ["name", "price", "rating"],
            "tab": site,
        })
    if len(sites) > 1:
        steps.append({"action": "compare_prices"})
    return {"steps": steps}
