"""
Posting client for Bluesky.
Credentials come from environment variables (GitHub Secrets).

Required env vars:
  BSKY_HANDLE       — e.g. yourhandle.bsky.social
  BSKY_APP_PASSWORD — from Bluesky Settings → App Passwords
"""

import os
from atproto import Client as BskyClient


def post_bluesky(text: str, reply_ref=None) -> dict:
    """Posts to Bluesky. Returns the post ref (uri + cid) for thread replies."""
    client = BskyClient()
    client.login(os.environ["BSKY_HANDLE"], os.environ["BSKY_APP_PASSWORD"])
    kwargs = {"text": text}
    if reply_ref:
        kwargs["reply_to"] = reply_ref
    return client.send_post(**kwargs)


def publish(post_text: str, reply_text: str | None):
    """Publishes to Bluesky. Handles threads for dialogues."""
    try:
        ref = post_bluesky(post_text)
        if reply_text:
            post_bluesky(reply_text, reply_ref=ref)
        print("Bluesky: posted")
    except Exception as e:
        print(f"Bluesky error: {e}")
