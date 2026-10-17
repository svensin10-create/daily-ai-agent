"""
Free starter AI agent for GitHub Actions.
- Reads RSS feeds listed in sources.txt
- Sends the headlines + your instructions (task.txt) to Google's Gemini API (free tier)
- Saves the result to outputs/YYYY-MM-DD.md
"""
import datetime
import os
import pathlib
import sys
import xml.etree.ElementTree as ET

import requests

API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash"
ROOT = pathlib.Path(__file__).parent
ATOM = "{http://www.w3.org/2005/Atom}"


def read_lines(name):
    """Read non-empty, non-comment lines from a text file."""
    path = ROOT / name
    if not path.exists():
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def fetch_headlines(url, limit=10):
    """Pull titles + links from an RSS or Atom feed."""
    resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0 (starter-agent)"})
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    headlines = []
    for item in root.iter("item"):  # RSS
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if title:
            headlines.append(f"- {title} ({link})")
    for entry in root.iter(f"{ATOM}entry"):  # Atom
        title = (entry.findtext(f"{ATOM}title") or "").strip()
        link_el = entry.find(f"{ATOM}link")
        link = link_el.get("href", "") if link_el is not None else ""
        if title:
            headlines.append(f"- {title} ({link})")
    return headlines[:limit]


def ask_model(prompt):
    """Send a prompt to Gemini and return the text reply."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    resp = requests.post(
        url,
        headers={"x-goog-api-key": API_KEY, "Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=120,
    )
    if resp.status_code != 200:
        sys.exit(f"Model request failed ({resp.status_code}): {resp.text[:500]}")
    data = resp.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        sys.exit(f"Unexpected model response: {str(data)[:500]}")


def main():
    if not API_KEY:
        sys.exit("Missing GEMINI_API_KEY. Add it as a GitHub Actions secret.")

    task = "\n".join(read_lines("task.txt")) or "Summarize the most important headlines."
    sources = read_lines("sources.txt")

    collected = []
    for url in sources:
        try:
            items = fetch_headlines(url)
            collected.append(f"Source: {url}\n" + "\n".join(items))
            print(f"Fetched {len(items)} items from {url}")
        except Exception as err:  # keep going if one feed fails
            print(f"Skipping {url}: {err}")

    if not collected:
        sys.exit("No headlines fetched. Check sources.txt.")

    today = datetime.date.today().isoformat()
    prompt = f"Today is {today}.\n\nYOUR TASK:\n{task}\n\nHEADLINES:\n" + "\n\n".join(collected)
    result = ask_model(prompt)

    out_dir = ROOT / "outputs"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"{today}.md"
    out_file.write_text(f"# Agent report: {today}\n\n{result}\n", encoding="utf-8")
    print(f"Saved {out_file}")


if __name__ == "__main__":
    main()
