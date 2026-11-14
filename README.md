# Claude Session Cleaner

Automatically request deletion of **Anthropic-stored Claude Code sessions** on a randomized schedule.

This is an independent, unofficial tool. It uses the **Delete sessions stored by Anthropic** control at [Claude Code settings](https://claude.ai/settings/claude-code) through Playwright. It does **not** use undocumented Anthropic APIs.

## What it does

- Opens the Claude Code settings page with a dedicated, persistent browser profile.
- Finds the exact session-deletion setting and confirms only a session-related deletion dialog.
- Repeats at a **newly sampled interval after every attempt** (default **2–6 hours**), including a randomized delay before the first attempt.
- Leaves local Claude Code sessions (`~/.claude`) untouched.
- Stores authentication **locally**, never in GitHub Actions or repository files.
- Stops the current attempt if authentication expires or UI selectors become ambiguous; keeps a local, rotating log.
- Prevents two instances from using the same browser profile at once.

**Not covered:** Claude Code on the web sessions, Claude.ai chat history, local session transcripts, and any data Anthropic is required to retain under its policies.

**Important:** Deleting a stored session does **not** establish that Anthropic immediately purges every copy or log. There is **no evidence** that scheduling these deletions improves account standing or prevents account restrictions. Automation itself may fail or trigger service restrictions. Do not treat it as a risk-control bypass.

## Windows 11 quick start

Install [Python 3](https://www.python.org/downloads/windows/) (enable the `py` launcher), then:

1. Download or clone this repository.
2. Double-click **`setup-and-login.cmd`**. It creates a project-local `.venv`, installs Playwright/Chromium, and opens a browser for a **manual** Claude login.
3. The setup script runs a **dry run** to check the exact deletion control without clicking it.
4. Double-click **`test-once.cmd`** to run **one real deletion request** with the browser visible. Check its output before scheduling.
5. Double-click **`start-now.cmd`** to keep it running in the foreground. To start automatically when you sign into Windows, run `powershell -NoProfile -ExecutionPolicy Bypass -File .\register-startup.ps1`.

You can also invoke the Python entrypoint yourself:

```powershell
.\.venv\Scripts\python.exe cleaner.py --login
.\.venv\Scripts\python.exe cleaner.py --once --dry-run --show-browser
.\.venv\Scripts\python.exe cleaner.py --once --show-browser
.\.venv\Scripts\python.exe cleaner.py --loop --min-hours 2 --max-hours 6
```

To use a different interval, for example 3–9 hours:

```powershell
.\.venv\Scripts\python.exe cleaner.py --loop --min-hours 3 --max-hours 9
```

All delays are independently sampled from a uniform distribution; this is **not** a fixed cron schedule with a small random offset. Sleeping or shutting down your PC prevents execution until it resumes or you launch the app again.

## Stop / uninstall

- Foreground: press **Ctrl+C**.
- Startup: run `powershell -NoProfile -ExecutionPolicy Bypass -File .\unregister-startup.ps1`; also stop any already running instance.
- Authentication profile: `%LOCALAPPDATA%\ClaudeSessionCleaner\profile`.
- Logs: `%LOCALAPPDATA%\ClaudeSessionCleaner\logs\cleaner.log`.
- To completely remove the local tool, close it and delete its repo folder and `%LOCALAPPDATA%\ClaudeSessionCleaner`.

Do not upload the browser profile, cookies, or local logs to GitHub. GitHub Actions is used only to test the code, **never** to sign into Claude or delete sessions.

## Safety and troubleshooting

The cleaner requires an exact visible label, a uniquely scoped delete button, and an explicit confirmation about **sessions**, not account deletion. It refuses to click unfamiliar text-entry confirmations. A successful attempt means the **UI accepted the deletion request**; it is not independent verification of server erasure.

The browser UI can change without notice. If you see a `SafeStop` message or a failure in the log, run `--once --dry-run --show-browser`, verify the page manually, and adjust selectors only after inspecting the new UI. The project intentionally does not bypass captchas, 2FA, or other access controls.

## Project files

```text
cleaner.py                 Main CLI, scheduler, and guarded browser automation
requirements.txt           Python dependencies
setup-and-login.cmd        Windows setup and manual sign-in
test-once.cmd              One visible deletion attempt
start-now.cmd              Foreground randomized loop
register-startup.ps1       Run after Windows user sign-in
unregister-startup.ps1     Remove startup registration
tests/                     Offline tests (no Claude account required)
.github/workflows/test.yml Lightweight tests, no Claude credentials
```

## Background

The target setting is located at [Claude Code settings](https://claude.ai/settings/claude-code). This tool only automates that specific UI control; verify its current wording and behavior in your own signed-in browser.

Not affiliated with Anthropic. Use at your own risk.
