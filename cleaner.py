"""Conservative UI automation for deleting Anthropic-stored Claude Code sessions.

Never calls private APIs or touches ~/.claude. No passwords or cookies in source.
A UI submission is NOT proof of complete server-side erasure.
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import secrets
import sys
import time
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path

from filelock import FileLock, Timeout as FileLockTimeout
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

SETTINGS_URL = "https://claude.ai/settings/claude-code"
TARGET_LABEL = "Delete sessions stored by Anthropic"
BASE_DIR = Path(os.getenv("LOCALAPPDATA") or Path.home() / ".local" / "share") / "ClaudeSessionCleaner"
PROFILE_DIR = BASE_DIR / "profile"
LOG_FILE = BASE_DIR / "logs" / "cleaner.log"
LOCK_FILE = BASE_DIR / "cleaner.lock"


class SafeStop(RuntimeError):
    """The tool cannot safely identify the target control or confirmation."""


def setup_logging() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            RotatingFileHandler(LOG_FILE, maxBytes=512_000, backupCount=3, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def validate_interval(min_hours: float, max_hours: float) -> None:
    if not (0.1 <= min_hours <= max_hours <= 168):
        raise ValueError("Require 0.1 <= min-hours <= max-hours <= 168")


def sample_delay_seconds(min_hours: float, max_hours: float) -> float:
    """Independent, unpredictable interval, not an attempt to evade access controls."""
    validate_interval(min_hours, max_hours)
    return secrets.SystemRandom().uniform(min_hours, max_hours) * 3600


def visible(locator) -> bool:
    try:
        return locator.is_visible(timeout=1000)
    except Exception:
        return False


def unique_visible(locator):
    matches = [locator.nth(i) for i in range(locator.count()) if visible(locator.nth(i))]
    return matches[0] if len(matches) == 1 else None


def target_button(page):
    """Require exact setting text and a unique Delete button in its small panel."""
    label = unique_visible(page.get_by_text(TARGET_LABEL, exact=True))
    if label is None:
        raise SafeStop("Setting label not found exactly once: login expired or UI changed")
    if label.evaluate("el => el.tagName.toLowerCase()") == "button":
        return label

    for depth in range(1, 7):
        panel = label.locator(f"xpath=ancestor::*[{depth}]")
        if panel.count() != 1:
            continue
        contents = panel.inner_text(timeout=2000)
        if len(contents) > 650 or TARGET_LABEL.lower() not in contents.lower():
            continue
        if re.search(r"delete\s+(?:your\s+)?account", contents, re.I):
            continue
        buttons = panel.get_by_role(
            "button", name=re.compile(r"^\s*delete(?:\s+(?:all\s+)?sessions)?\s*$", re.I)
        )
        candidate = unique_visible(buttons)
        if candidate is not None and candidate.is_enabled():
            return candidate
    raise SafeStop("No uniquely scoped session Delete button; refusing unrelated controls")


def confirmation_dialog(page):
    for role in ("alertdialog", "dialog"):
        dialog = unique_visible(page.get_by_role(role))
        if dialog is not None:
            return dialog
    return None


def confirm_html_dialog(page) -> None:
    dialog = confirmation_dialog(page)
    if dialog is None:
        raise SafeStop("No recognized session confirmation; outcome unknown")

    words = dialog.inner_text(timeout=2500)
    if not re.search(r"sessions?", words, re.I):
        raise SafeStop("Confirmation did not mention sessions")
    if re.search(r"delete\s+(?:your\s+)?account", words, re.I):
        raise SafeStop("Refusing account deletion")
    if dialog.locator("input:visible").count() > 0:
        raise SafeStop("Confirmation requires text input; manual review required")

    buttons = dialog.get_by_role(
        "button", name=re.compile(r"^\s*(?:delete|delete\s+(?:all\s+)?sessions|confirm)\s*$", re.I)
    )
    button = unique_visible(buttons)
    if button is None or not button.is_enabled():
        raise SafeStop("Confirmation Delete button missing or ambiguous")
    button.click(timeout=10_000)
    try:
        dialog.wait_for(state="hidden", timeout=15_000)
    except PlaywrightTimeoutError as exc:
        raise SafeStop("Confirmation did not close; request not confirmed by UI") from exc


def attempt_cleanup(*, dry_run: bool = False, show_browser: bool = False) -> None:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=not show_browser,
            viewport={"width": 1280, "height": 860},
        )
        try:
            page = context.new_page()
            page.goto(SETTINGS_URL, wait_until="domcontentloaded", timeout=45_000)
            if not page.url.startswith("https://claude.ai/"):
                raise SafeStop("Redirected outside claude.ai; manual login needed")
            page.get_by_text(TARGET_LABEL, exact=True).first.wait_for(state="visible", timeout=20_000)
            button = target_button(page)
            if dry_run:
                logging.info("DRY RUN: target button identified; nothing deleted")
                return

            native = {"accepted": False}
            def handle_native(dialog) -> None:
                if dialog.type == "confirm" and re.search(r"sessions?", dialog.message, re.I) and not re.search(
                    r"delete\s+(?:your\s+)?account", dialog.message, re.I
                ):
                    dialog.accept()
                    native["accepted"] = True
                else:
                    dialog.dismiss()
            page.on("dialog", handle_native)
            button.click(timeout=10_000)
            page.wait_for_timeout(500)
            if native["accepted"]:
                logging.info("Session deletion submitted through native confirmation; server erasure unverified")
                return
            confirm_html_dialog(page)
            logging.info("Session deletion accepted by UI; server erasure unverified")
        finally:
            context.close()


def login() -> None:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport={"width": 1280, "height": 860},
        )
        try:
            page = context.new_page()
            page.goto(SETTINGS_URL, wait_until="domcontentloaded", timeout=45_000)
            print("Sign in to Claude in this browser. Do not share your profile directory.")
            print("Once Claude Code settings are visible, return here and press Enter.")
            input()
        finally:
            context.close()


def run_loop(min_hours: float, max_hours: float, show_browser: bool) -> None:
    validate_interval(min_hours, max_hours)
    logging.info("Started, sampling a new random delay between %.2f and %.2f hours", min_hours, max_hours)
    while True:
        delay = sample_delay_seconds(min_hours, max_hours)
        when = datetime.now() + timedelta(seconds=delay)
        logging.info("Next attempt at %s (%.2f hours)", when.isoformat(timespec="seconds"), delay / 3600)
        time.sleep(delay)
        try:
            attempt_cleanup(show_browser=show_browser)
        except SafeStop as exc:
            logging.warning("Skipped safely: %s", exc)
        except Exception as exc:
            # Avoid logging browser error detail, page text, or authentication state.
            logging.error("Attempt failed (%s). Check login or UI with --dry-run.", type(exc).__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Randomized Claude Code stored-session cleanup")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--login", action="store_true", help="Manual sign-in to local browser profile")
    modes.add_argument("--once", action="store_true", help="One cleanup attempt")
    modes.add_argument("--loop", action="store_true", help="Repeated cleanup at independently random intervals")
    parser.add_argument("--dry-run", action="store_true", help="Locate control without deleting (once only)")
    parser.add_argument("--show-browser", action="store_true", help="Show browser for inspection")
    parser.add_argument("--min-hours", type=float, default=2)
    parser.add_argument("--max-hours", type=float, default=6)
    args = parser.parse_args()
    if args.dry_run and not args.once:
        parser.error("--dry-run requires --once")
    try:
        validate_interval(args.min_hours, args.max_hours)
    except ValueError as exc:
        parser.error(str(exc))

    setup_logging()
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(LOCK_FILE))
    try:
        with lock.acquire(timeout=0):
            if args.login:
                login()
            elif args.once:
                attempt_cleanup(dry_run=args.dry_run, show_browser=args.show_browser)
            else:
                run_loop(args.min_hours, args.max_hours, args.show_browser)
    except FileLockTimeout:
        logging.error("Another cleaner process is active. Stop it before starting another.")
        return 2
    except SafeStop as exc:
        logging.error("Skipped safely: %s", exc)
        return 1
    except KeyboardInterrupt:
        logging.info("Stopped by user")
        return 0
    except Exception as exc:
        logging.error("Failed (%s). Run a visible dry run to diagnose.", type(exc).__name__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
