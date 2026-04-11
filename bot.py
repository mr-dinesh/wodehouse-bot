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


def load_quotes(fmt: str) -> list[dict]:
    data = json.loads(Path("data/quotes.json").read_text())
    pool = [q for q in data if q["format"] == fmt]
    if not pool:
        raise ValueError(f"No quotes found for format '{fmt}'")
    return pool


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--format", default=None)
    args = parser.parse_args()

    fmt = args.format or todays_format()
    print(f"Format today: {fmt}")

    quotes = load_quotes(fmt)
    entry = random.choice(quotes)
    post_text, reply_text = render(entry)

    print("\n--- POST ---")
    print(post_text)
    if reply_text:
        print("\n--- REPLY ---")
        print(reply_text)
    print("------------\n")

    if not args.dry_run:
        publish(post_text, reply_text)
    else:
        print("Dry run — nothing posted.")


if __name__ == "__main__":
    main()
