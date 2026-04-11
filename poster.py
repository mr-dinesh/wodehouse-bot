"""
Posting clients for Mastodon and Bluesky.
Credentials come from environment variables (GitHub Secrets).

Required env vars:
  MASTODON_ACCESS_TOKEN   — from mastodon.social account settings
  MASTODON_API_BASE_URL   — e.g. https://mastodon.social
  BSKY_HANDLE             — e.g. yourhandle.bsky.social
  BSKY_APP_PASSWORD       — from Bluesky Settings → App Passwords
"""

import os
from mastodon import Mastodon
from atproto import Client as BskyClient


def post_mastodon(text: str, reply_to_id=None) -> str:
    """Posts to Mastodon. Returns the new post ID (for thread replies)."""
    m = Mastodon(
        access_token=os.environ["MASTODON_ACCESS_TOKEN"],
        api_base_url=os.environ["MASTODON_API_BASE_URL"],
    )
    kwargs = {"status": text, "visibility": "public"}
    if reply_to_id:
        kwargs["in_reply_to_id"] = reply_to_id
    result = m.status_post(**kwargs)
    return result["id"]


def post_bluesky(text: str, reply_ref=None) -> dict:
    """Posts to Bluesky. Returns the post ref (uri + cid) for thread replies."""
    client = BskyClient()
    client.login(os.environ["BSKY_HANDLE"], os.environ["BSKY_APP_PASSWORD"])
    kwargs = {"text": text}
    if reply_ref:
        kwargs["reply_to"] = reply_ref
    return client.send_post(**kwargs)


def publish(post_text: str, reply_text: str | None):
    """Publishes to both platforms. Handles threads for dialogues."""
    # Mastodon
    try:
        post_id = post_mastodon(post_text)
        if reply_text:
            post_mastodon(reply_text, reply_to_id=post_id)
        print("Mastodon: posted")
    except Exception as e:
        print(f"Mastodon error: {e}")

    # Bluesky
    try:
        ref = post_bluesky(post_text)
        if reply_text:
            post_bluesky(reply_text, reply_ref=ref)
        print("Bluesky: posted")
    except Exception as e:
        print(f"Bluesky error: {e}")
