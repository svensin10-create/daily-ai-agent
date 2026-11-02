# Daily AI Agent (GitHub Actions + Claude)

Runs once a day, reads news feeds, checks the stories online, and writes a brief into `outputs/`.
On weekdays the Market Watcher writes a finance brief into `market/`.

## How the workflows connect
1. **Market Watcher** (weekdays 11:30 UTC) writes `market/YYYY-MM-DD.md`.
2. **Daily AI Agent** (12:00 UTC) writes `outputs/YYYY-MM-DD.md`.
3. **Claude Feedback** runs when the daily agent succeeds and opens a "Claude feedback" issue.
4. **Content Team** runs next and opens "Shorts script" and "LinkedIn draft" issues.
5. **Send to Typefully** saves the newest LinkedIn draft to Typefully (it never publishes).
6. **Weekly Analyst** (Sundays) reviews the week.

If a step fails, everything after it is skipped, so check the Actions tab when a draft is missing.

## Secrets
- `CLAUDE_CODE_OAUTH_TOKEN`: used by every Claude workflow (make one with `claude setup-token`).
- `TYPEFULLY_API_KEY`: used by Send to Typefully.

## Customize
- `task.txt` / `market_task.txt` = what each agent should write (plain English).
- `sources.txt` / `market_sources.txt` = which feeds they read (change `q=` in the Google News links for any topic).
- Schedules = the `cron` lines in `.github/workflows/` (times are UTC).

## Good to know
- Never paste a key or token into a file. Keep them only in GitHub Secrets.
- GitHub may delay scheduled runs a bit, and pauses schedules in repos with no activity for 60 days.
- Runs use your Claude plan's usage limits.
- `agent.py` and `market_agent.py` are the old Gemini versions. They are no longer used.
