"""
logger.py — Centralized logging system for the AI browser agent.
Logs to both console (with color) and execution.log file.
"""

import logging
import os
import sys
from datetime import datetime


LOG_FILE = os.path.join(os.path.dirname(__file__), "execution.log")

# ANSI color codes for console output
COLORS = {
    "DEBUG":    "\033[36m",   # Cyan
    "INFO":     "\033[32m",   # Green
    "WARNING":  "\033[33m",   # Yellow
    "ERROR":    "\033[31m",   # Red
    "CRITICAL": "\033[35m",   # Magenta
    "RESET":    "\033[0m",
}


class ColorFormatter(logging.Formatter):
    """Formatter that adds ANSI color codes to console log levels."""

    def format(self, record: logging.LogRecord) -> str:
        color = COLORS.get(record.levelname, COLORS["RESET"])
        reset = COLORS["RESET"]
        record.levelname = f"{color}{record.levelname:<8}{reset}"
        return super().format(record)


def get_logger(name: str = "agent") -> logging.Logger:
    """
    Return a named logger instance configured with:
    - Console handler (with color)
    - File handler (plain text, appended to execution.log)
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers on re-import
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    # --- Console handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(ColorFormatter(fmt, datefmt=date_fmt))

    # --- File handler ---
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(fmt, datefmt=date_fmt))

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Module-level default logger
log = get_logger("agent")
