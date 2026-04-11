"""
Maps day-of-week (0=Monday) to a format type.
Similes run twice (Mon + Sat) — they're the most shareable.
"""

import datetime

SCHEDULE = {
    0: "simile",             # Monday
    1: "setup_quote",        # Tuesday
    2: "dialogue",           # Wednesday
    3: "character_spotlight",# Thursday
    4: "situation",          # Friday
    5: "simile",             # Saturday
    6: "wildcard",           # Sunday
}


def todays_format() -> str:
    day = datetime.datetime.utcnow().weekday()
    return SCHEDULE[day]
