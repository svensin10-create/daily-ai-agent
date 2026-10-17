# Free Daily AI Agent (GitHub Actions + Gemini)

Runs once a day for free, reads news feeds, and writes a brief into `outputs/`.

## Setup (about 10 minutes)
1. **Get a free API key:** go to https://aistudio.google.com, sign in, and create a Gemini API key.
2. **Make a GitHub repo** and upload everything in this folder. Keep the folder structure:
   the workflow must live at `.github/workflows/agent.yml`.
3. **Add your key as a secret:** repo → Settings → Secrets and variables → Actions →
   New repository secret. Name: `GEMINI_API_KEY`, value: your key.
4. **Test it:** repo → Actions tab → "Daily AI Agent" → Run workflow.
   When it finishes, check the `outputs/` folder for today's report.

## Customize
- `task.txt` = what the agent should do (plain English).
- `sources.txt` = which feeds it reads (change `q=` in the Google News links for any topic).
- Schedule = the `cron` line in `.github/workflows/agent.yml` (times are UTC).
- Model = optional repo variable `GEMINI_MODEL` (Settings → Variables) if Google renames models.

## Good to know
- Never paste your API key into a file. Keep it only in GitHub Secrets.
- GitHub may delay scheduled runs a bit, and pauses schedules in repos with no activity for 60 days.
- Free tiers have limits; one run a day is far below them.
- Later you can swap `ask_model()` for the Claude API when you want a smarter agent.
