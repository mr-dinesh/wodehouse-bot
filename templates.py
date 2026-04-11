"""
One function per format. Each returns (post_text, reply_text|None).
reply_text is only set for dialogues (posted as a thread reply).
"""

HASHTAGS = "#PGWodehouse #Wodehouse #ClassicLit"


def render(entry: dict) -> tuple[str, str | None]:
    fmt = entry["format"]
    if fmt == "simile":
        return _simile(entry), None
    elif fmt == "setup_quote":
        return _setup_quote(entry), None
    elif fmt == "dialogue":
        return _dialogue(entry)
    elif fmt == "character_spotlight":
        return _character_spotlight(entry), None
    elif fmt == "situation":
        return _situation(entry), None
    elif fmt == "wildcard":
        return _wildcard(entry), None
    else:
        raise ValueError(f"Unknown format: {fmt}")


def _simile(e):
    return (
        f'"{e["text"]}"\n\n'
        f'— {e["book"]} ({e["year"]})\n\n'
        f"{HASHTAGS}"
    )


def _setup_quote(e):
    return (
        f'_{e["setup"]}_\n\n'
        f'"{e["text"]}"\n\n'
        f'— {e["character"]}, {e["book"]} ({e["year"]})\n\n'
        f"{HASHTAGS}"
    )


def _dialogue(e) -> tuple[str, str]:
    post = (
        f'_{e["setup"]}_\n\n'
        f'**{e["character"]}:** "{e["text"]}"\n\n'
        f'— {e["book"]} ({e["year"]})\n\n'
        f"{HASHTAGS}"
    )
    reply = f'**{e["dialogue_response"]["character"]}:** "{e["dialogue_response"]["text"]}"'
    return post, reply


def _character_spotlight(e):
    return (
        f'**{e["character"]}**\n\n'
        f'"{e["text"]}"\n\n'
        f'— {e["book"]} ({e["year"]})\n\n'
        f"{HASHTAGS}"
    )


def _situation(e):
    return (
        f'{e["setup"]}\n\n'
        f'"{e["text"]}"\n\n'
        f'— {e["character"]}, {e["book"]} ({e["year"]})\n\n'
        f"{HASHTAGS}"
    )


def _wildcard(e):
    return (
        f'_{e["setup"]}_\n\n'
        f'"{e["text"]}"\n\n'
        f'— {e["character"]}, {e["book"]} ({e["year"]})\n\n'
        f"{HASHTAGS}"
    )
