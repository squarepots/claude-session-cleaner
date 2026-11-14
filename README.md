# Claude Session Cleaner

An unofficial Windows 11 tool that periodically clicks **Delete sessions stored by Anthropic** in [Claude Code settings](https://claude.ai/settings/claude-code). It does not delete local `~/.claude` transcripts, Claude.ai chats, or Claude Code web/cloud sessions.

## How it works

- **Triggers:** Claude Code `SessionStart` (new and resumed local sessions), Windows sign-in, and a lightweight Windows check every 30 minutes.
- **Schedule:** each deletion attempt sets an independent random deadline **2–6 hours** later. Each trigger checks that deadline; before it, the process exits immediately. No persistent Python loop.
- **Deletion:** when due, a **headless** Playwright browser uses your separately signed-in Claude profile to click the existing Anthropic setting and confirm. You do not have to open the browser yourself each time.
- **Safety:** the tool does not touch your local Claude Code data, does not upload credentials, and refuses to click if the target or confirmation cannot be identified. Only one attempt can run at a time.

Actual execution may be up to about 30 minutes later than the random deadline when Claude Code isn't opened. Sleeping/offline computers can delay it further. The first `--check` after setup attempts immediately. After an unsuccessful attempt, the next retry also follows a random 2–6-hour deadline; see the log if authentication expires.

There is **no evidence** that deleting stored sessions prevents account restrictions or improves Anthropic's risk assessment. UI acceptance is not proof of full server-side erasure. Browser automation can break when Claude changes its interface. This is not an official Anthropic tool.

## Set up (Windows 11)

Install Python 3 (with the `py` launcher), then clone/download this repository.

1. Run `setup-and-login.cmd`. It installs dependencies, opens a browser for **manual** Claude login, then does a **dry run** that does not delete anything.
2. Run `test-once.cmd` once. It opens a visible browser and attempts one real deletion. Check that it targets **stored sessions**, never your account.
3. Run `powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1` to install both triggers for your Windows user. Administrator rights are not intended.

The installer edits only `SessionStart` in your **user-level** `~/.claude/settings.json`, preserving other hooks and backing up the settings file. It also registers the Windows task **Claude Session Cleaner** (at sign-in + 30-minute checks). The installer removes a legacy `Claude Session Cleaner.lnk` startup shortcut left by v1, which ran a permanent loop.

**You must run `install.ps1` on your own PC.** Committing a repo does not install a hook or scheduled task on your machine.

## Commands

Run these from the repository folder in PowerShell:

```powershell
.\.venv\Scripts\python.exe cleaner.py --status                   # local schedule
.\.venv\Scripts\python.exe cleaner.py --check                    # run only if due
.\.venv\Scripts\python.exe cleaner.py --once --dry-run --show-browser
.\.venv\Scripts\python.exe cleaner.py --once --show-browser      # force one real attempt
.\.venv\Scripts\python.exe cleaner.py --login                    # refresh browser login
```

For a custom interval, both the Claude hook and Windows task can pass `--min-hours 3 --max-hours 9` in their `args`/`-Argument` values. Default: 2–6 hours.

Logs and scheduling state: `%LOCALAPPDATA%\ClaudeSessionCleaner\`. Login cookies are stored separately in its `profile` directory. Never commit/share that profile. There are no GitHub Actions secrets, and CI does not access your Claude account.

## Uninstall

Run `powershell -NoProfile -ExecutionPolicy Bypass -File .\uninstall.ps1` from the same checkout. This removes the installed hook and Windows task, preserving unrelated hooks and your local login profile. Delete `%LOCALAPPDATA%\ClaudeSessionCleaner` manually if you also want to erase local credentials and logs.

## Implementation and limitations

- `cleaner.py`: `--check`, `--once`, `--login`, `--status`; persisted random deadline and one-instance lock.
- `install.ps1` / `uninstall.ps1`: user-level Claude Code Hook and Windows scheduled task.
- `setup-and-login.cmd`, `test-once.cmd`, `check-now.cmd`: Windows helpers.
- `tests/`: offline scheduler tests; **real Claude UI is not tested in CI**.

Sources: [Claude Code SessionStart hooks](https://code.claude.com/docs/en/hooks#sessionstart), [Windows Task Scheduler triggers](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtasktrigger), and [Playwright authentication](https://playwright.dev/python/docs/auth).

MIT License. Not affiliated with Anthropic.