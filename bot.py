"""
Wodehouse Bot — main entry point.

Usage:
  python bot.py              # normal run (posts today's format)
  python bot.py --dry-run    # prints post without publishing
  python bot.py --format simile  # override today's format
"""

import json
import random
import argparse
from pathlib import Path

from scheduler import todays_format
from templates import render
from poster import publish

POSTED_FILE = Path("data/posted.json")


def load_posted() -> set[int]:
    if POSTED_FILE.exists():
        return set(json.loads(POSTED_FILE.read_text()))
    return set()


def save_posted(posted: set[int]):
    POSTED_FILE.write_text(json.dumps(sorted(posted)))


def load_quotes(fmt: str) -> list[dict]:
    data = json.loads(Path("data/quotes.json").read_text())
    pool = [q for q in data if q["format"] == fmt]
    if not pool:
        raise ValueError(f"No quotes found for format '{fmt}'")
    return pool


def pick_quote(quotes: list[dict], posted: set[int]) -> tuple[dict, bool]:
    """Pick an unposted quote. Returns (entry, reset) where reset=True means the history was cleared."""
    unposted = [q for q in quotes if q["id"] not in posted]
    if not unposted:
        # All quotes in this format have been posted — reset and start fresh
        print("All quotes in this format posted; resetting history for this format.")
        posted_ids_for_format = {q["id"] for q in quotes}
        posted -= posted_ids_for_format
        unposted = quotes
        return random.choice(unposted), True
    return random.choice(unposted), False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--format", default=None)
    args = parser.parse_args()

    fmt = args.format or todays_format()
    print(f"Format today: {fmt}")

    quotes = load_quotes(fmt)
    posted = load_posted()
    entry, _ = pick_quote(quotes, posted)

    post_text, reply_text = render(entry)

    print("\n--- POST ---")
    print(post_text)
    if reply_text:
        print("\n--- REPLY ---")
        print(reply_text)
    print("------------\n")

    if not args.dry_run:
        publish(post_text, reply_text)
        posted.add(entry["id"])
        save_posted(posted)
        print(f"Recorded quote id={entry['id']} to posted history.")
    else:
        print("Dry run — nothing posted.")


if __name__ == "__main__":
    main()
