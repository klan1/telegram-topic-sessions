#!/usr/bin/env python3
"""
Send topic selection as an inline keyboard via the Telegram Bot API.

This script sends or edits a message containing an InlineKeyboardMarkup
with one button per topic. Tapping a button sends a callback to the
gateway's `_handle_callback_query` method with data format `ts:user_id:topic_id`.

Usage:
    # Send a new inline keyboard message
    python topics_inline.py send <chat_id> <text> <topics_json> <active_id> <user_id>

    # Edit an existing message with updated buttons
    python topics_inline.py edit <chat_id> <msg_id> <text> <topics_json> <active_id> <user_id>

Example:
    python topics_inline.py send 123456789 "📋 Topics:" '[{"id":"a","name":"General"}]' a 123456789
"""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

# Load .env for bot token
env_path = Path("/opt/data/.env")
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
if not BOT_TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN not found", file=sys.stderr)
    sys.exit(1)

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"


def _api_call(method: str, payload: dict) -> dict:
    """Call the Telegram Bot API with a JSON payload."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/{method}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": str(e), "body": e.read().decode()}
    except urllib.error.URLError as e:
        return {"ok": False, "error": str(e)}


def make_topic_keyboard(topics: list, active_id: str, user_id: str) -> dict:
    """Build an inline keyboard markup for the topic list."""
    buttons = []
    for t in topics:
        name = t["name"]
        tid = t["id"]
        prefix = "✅ " if tid == active_id else ("📦 " if t.get("archived") else "")
        label = f"{prefix}{name}"
        callback_data = f"ts:{user_id}:{tid}"
        buttons.append([{"text": label, "callback_data": callback_data}])

    # Utility button for creating new topics
    buttons.append(
        [{"text": "➕ New topic", "callback_data": f"ts:{user_id}:__new__"}]
    )

    return {"inline_keyboard": buttons}


def send_topics_inline(
    chat_id: str, text: str, topics: list, active_id: str, user_id: str
) -> int | None:
    """Send a message with inline topic selection buttons."""
    keyboard = make_topic_keyboard(topics, active_id, user_id)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "MarkdownV2",
        "reply_markup": keyboard,
    }
    data = _api_call("sendMessage", payload)
    if not data.get("ok"):
        print(f"ERROR: {data.get('error', data)}", file=sys.stderr)
        return None
    return data["result"]["message_id"]


def edit_topics_inline(
    chat_id: str, message_id: int, text: str, topics: list, active_id: str, user_id: str
) -> bool:
    """Edit an existing message with updated topic buttons."""
    keyboard = make_topic_keyboard(topics, active_id, user_id)
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "MarkdownV2",
        "reply_markup": keyboard,
    }
    data = _api_call("editMessageText", payload)
    return data.get("ok", False)


def remove_keyboard(chat_id: str, message_id: int, text: str) -> bool:
    """Remove the inline keyboard from a message while keeping the text."""
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "MarkdownV2",
        "reply_markup": {"inline_keyboard": []},
    }
    data = _api_call("editMessageText", payload)
    return data.get("ok", False)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print(
            "  topics_inline.py send <chat_id> <text> <topics_json> <active_id> <user_id>"
        )
        print(
            "  topics_inline.py edit <chat_id> <msg_id> <text> <topics_json> <active_id> <user_id>"
        )
        sys.exit(1)

    action = sys.argv[1]

    if action == "send":
        chat_id = sys.argv[2]
        text = sys.argv[3]
        topics = json.loads(sys.argv[4])
        active_id = sys.argv[5]
        user_id = sys.argv[6]
        result = send_topics_inline(chat_id, text, topics, active_id, user_id)
        if result:
            print(f"OK message_id={result}")
        else:
            sys.exit(1)
    elif action == "edit":
        chat_id = sys.argv[2]
        msg_id = int(sys.argv[3])
        text = sys.argv[4]
        topics = json.loads(sys.argv[5])
        active_id = sys.argv[6]
        user_id = sys.argv[7]
        ok = edit_topics_inline(chat_id, msg_id, text, topics, active_id, user_id)
        print("OK" if ok else "FAIL")
    else:
        print(f"Unknown action: {action}", file=sys.stderr)
        sys.exit(1)
