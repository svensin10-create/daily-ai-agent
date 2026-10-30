"""
Market Watcher agent (free, uses Gemini).
Reads market_sources.txt, follows market_task.txt, saves market/YYYY-MM-DD.md
"""
import datetime
import os
import pathlib
import sys
import time
import xml.etree.ElementTree as ET

import requests

API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = os.environ.get("GEMINI_MODEL") or "gemini-flash-latest"
FALLBACK_MODEL = os.environ.get("GEMINI_FALLBACK_MODEL") or "gemini-2.5-flash-lite"
RETRY_STATUSES = {429, 500, 502, 503, 504}
ATTEMPTS_PER_MODEL = 3
ROOT = pathlib.Path(__file__).parent
ATOM = "{http://www.w3.org/2005/Atom}"


def read_lines(name):
    path = ROOT / name
    if not path.exists():
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def fetch_headlines(url, limit=10):
    resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0 (market-agent)"})
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    out = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if title:
            out.append(f"- {title} ({link})")
    for entry in root.iter(f"{ATOM}entry"):
        title = (entry.findtext(f"{ATOM}title") or "").strip()
        link_el = entry.find(f"{ATOM}link")
        link = link_el.get("href", "") if link_el is not None else ""
        if title:
            out.append(f"- {title} ({link})")
    return out[:limit]


def ask_model(prompt):
    # Retry busy/slow Gemini responses, then fall back to a lighter model.
    last_error = "no attempts made"
    for model in dict.fromkeys([MODEL, FALLBACK_MODEL]):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        for attempt in range(1, ATTEMPTS_PER_MODEL + 1):
            try:
                resp = requests.post(
                    url,
                    headers={"x-goog-api-key": API_KEY, "Content-Type": "application/json"},
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    timeout=120,
                )
            except requests.exceptions.RequestException as err:
                last_error = f"{model}: {err}"
            else:
                if resp.status_code == 200:
                    data = resp.json()
                    try:
                        return data["candidates"][0]["content"]["parts"][0]["text"]
                    except (KeyError, IndexError):
                        sys.exit(f"Unexpected model response: {str(data)[:500]}")
                last_error = f"{model} ({resp.status_code}): {resp.text[:500]}"
                if resp.status_code not in RETRY_STATUSES:
                    break
            if attempt < ATTEMPTS_PER_MODEL:
                wait = 15 * 2 ** (attempt - 1)
                print(f"Attempt {attempt} with {model} failed, retrying in {wait}s: {last_error[:200]}")
                time.sleep(wait)
        print(f"Giving up on {model}: {last_error[:200]}")
    sys.exit(f"Model request failed: {last_error}")


def main():
    if not API_KEY:
        sys.exit("Missing GEMINI_API_KEY secret.")
    task = "\n".join(read_lines("market_task.txt")) or "Summarize today's market news."
    collected = []
    for url in read_lines("market_sources.txt"):
        try:
            items = fetch_headlines(url)
            collected.append(f"Source: {url}\n" + "\n".join(items))
            print(f"Fetched {len(items)} items from {url}")
        except Exception as err:
            print(f"Skipping {url}: {err}")
    if not collected:
        sys.exit("No headlines fetched. Check market_sources.txt.")
    today = datetime.date.today().isoformat()
    prompt = f"Today is {today}.\n\nYOUR TASK:\n{task}\n\nHEADLINES:\n" + "\n\n".join(collected)
    result = ask_model(prompt)
    out_dir = ROOT / "market"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"{today}.md"
    out_file.write_text(f"# Market report: {today}\n\n{result}\n", encoding="utf-8")
    print(f"Saved {out_file}")


if __name__ == "__main__":
    main()
