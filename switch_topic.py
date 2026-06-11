#!/usr/bin/env python3
"""
CLI script to switch topic sessions.

Called by the Telegram gateway callback handler when a user taps a topic
button. Updates the filesystem and returns a formatted confirmation message.

Usage:
    python switch_topic.py <user_id> <topic_id> <user_display>

Example:
    python switch_topic.py 123456789 topic_abc123 Alejo
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/opt/data/session_topics")


def esc(text: str) -> str:
    """Escape MarkdownV2 special characters for Telegram."""
    return re.sub(r"([_*\[\]()~`>#+\-=|{}.!])", r"\\\1", text)


user_id = sys.argv[1] if len(sys.argv) > 1 else ""
topic_id = sys.argv[2] if len(sys.argv) > 2 else ""
user_display = sys.argv[3] if len(sys.argv) > 3 else "User"

# Resolve user name — use display name directly (deployment-specific mapping
# should be configured externally, not hardcoded in this script)
user_name = user_display
user_dir = BASE_DIR / user_name

if not user_dir.exists():
    print(f"⚠️ No topics found for *{user_name}*", file=sys.stderr)
    sys.exit(1)

index_path = user_dir / "index.json"
if not index_path.exists():
    print(f"⚠️ No index found for *{user_name}*", file=sys.stderr)
    sys.exit(1)

index = json.loads(index_path.read_text())

# Find the topic
target = None
for t in index["topics"]:
    if t["id"] == topic_id:
        target = t
        break

if not target:
    # Fallback: try by name (case-insensitive)
    for t in index["topics"]:
        if t["name"].lower() == topic_id.lower():
            target = t
            topic_id = t["id"]
            break

if not target:
    print(f"⚠️ Topic '{topic_id}' not found for *{user_name}*", file=sys.stderr)
    sys.exit(1)

# Perform the switch
old_active = index.get("active_topic")
old_name = "?"
for t in index["topics"]:
    if t["id"] == old_active:
        old_name = t["name"]
        break

index["active_topic"] = target["id"]
target["updated"] = datetime.now().isoformat()[:19]
index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False))

# Format confirmation output
print(f"*{esc(user_name)}* switched to **{esc(target['name'])}**")
print("")
print("📋 **Your topics:**")
for i, t in enumerate(index["topics"], 1):
    prefix = "✅" if t["id"] == topic_id else ("📦" if t.get("archived") else "•")
    arch = " (archived)" if t.get("archived") else ""
    print(f"   {prefix} **{esc(t['name'])}**{arch}")

summary = target.get("summary", "")
if summary:
    print("")
    print(f"📝 *Summary:* {esc(summary)}")
print("")
print(f"💡 Use /topics to see this list with inline buttons")

sys.exit(0)
