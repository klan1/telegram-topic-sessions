#!/usr/bin/env python3
"""
Topic Sessions Manager — virtual topic/session management for linear Telegram chats.

Each user gets isolated topics stored as JSON files. Topics can be created,
switched, archived, and renamed. Conversation history is persisted per topic
in JSONL format.
"""

import json
import uuid
import os
from pathlib import Path
from datetime import datetime, timezone

# Configurable base directory for topic storage
BASE_DIR = Path(os.environ.get("TOPIC_SESSIONS_DIR", "/opt/data/session_topics"))


def _now() -> str:
    """Return current UTC timestamp as ISO string (seconds precision)."""
    return datetime.now(timezone.utc).isoformat()[:19]


def _ensure_user_dir(user_name: str) -> Path:
    """Create user directory if it doesn't exist; return path."""
    p = BASE_DIR / user_name
    p.mkdir(parents=True, exist_ok=True)
    return p


def _index_path(user_name: str) -> Path:
    """Return path to user's index.json."""
    return _ensure_user_dir(user_name) / "index.json"


def _topic_path(user_name: str, topic_id: str) -> Path:
    """Return path to a topic's conversation history file."""
    return _ensure_user_dir(user_name) / f"topic_{topic_id}.jsonl"


def load_index(user_name: str) -> dict:
    """
    Load a user's topic index.

    If the index doesn't exist (first time), initializes with a default
    "General" topic.
    """
    path = _index_path(user_name)
    if path.exists():
        with open(path) as f:
            data = json.load(f)
            # Ensure all topics have the 'archived' field (migration)
            for t in data.get("topics", []):
                t.setdefault("archived", False)
                t.setdefault("msg_count", 0)
            return data

    # First-time initialization
    default_id = uuid.uuid4().hex[:8]
    index = {
        "active_topic": default_id,
        "topics": [
            {
                "id": default_id,
                "name": "General",
                "created": _now(),
                "updated": _now(),
                "summary": "Main topic",
                "msg_count": 0,
                "archived": False,
            }
        ],
    }
    save_index(user_name, index)
    return index


def save_index(user_name: str, index: dict) -> None:
    """Save a user's topic index to disk."""
    path = _index_path(user_name)
    with open(path, "w") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def get_active_topic(user_name: str) -> tuple:
    """
    Get the currently active topic and full index.

    Returns (topic_dict, index_dict). Falls back to the first topic if
    active_topic points to a non-existent ID.
    """
    index = load_index(user_name)
    for t in index["topics"]:
        if t["id"] == index["active_topic"]:
            return t, index
    # Fallback: activate the first topic
    if index["topics"]:
        index["active_topic"] = index["topics"][0]["id"]
        save_index(user_name, index)
        return index["topics"][0], index
    return None, index


def list_topics(user_name: str) -> list:
    """Return all topics for a user."""
    index = load_index(user_name)
    return index["topics"]


def create_topic(user_name: str, name: str, summary: str = "") -> dict:
    """
    Create a new topic and set it as active.

    Args:
        user_name: Display name of the user
        name: Topic name
        summary: Optional short description

    Returns:
        The newly created topic dict
    """
    index = load_index(user_name)
    new_id = uuid.uuid4().hex[:8]
    now = _now()
    topic = {
        "id": new_id,
        "name": name,
        "created": now,
        "updated": now,
        "summary": summary or name,
        "msg_count": 0,
        "archived": False,
    }
    index["topics"].append(topic)
    index["active_topic"] = new_id
    save_index(user_name, index)
    return topic


def switch_topic(user_name: str, topic_id: str) -> dict:
    """
    Switch to an existing topic by ID or name.

    Args:
        user_name: Display name of the user
        topic_id: Topic ID (prefixed) or exact name (case-insensitive)

    Returns:
        The target topic dict, or None if not found
    """
    index = load_index(user_name)
    for t in index["topics"]:
        if t["id"] == topic_id or t["name"].lower() == topic_id.lower():
            index["active_topic"] = t["id"]
            t["updated"] = _now()
            save_index(user_name, index)
            return t
    return None


def find_topic(user_name: str, query: str) -> dict:
    """
    Find a topic by ID, name (case-insensitive), or 1-based index.

    Matching priority:
    1. Numeric index (1-based, e.g., "2" for second topic)
    2. Exact ID match
    3. Exact name match (case-insensitive)
    4. Name contains query (case-insensitive)

    Returns:
        The matched topic dict, or None
    """
    index = load_index(user_name)
    q = query.strip().lower()

    # Try numeric index (1-based)
    try:
        idx = int(q) - 1
        if 0 <= idx < len(index["topics"]):
            return index["topics"][idx]
    except ValueError:
        pass

    # Try exact ID
    for t in index["topics"]:
        if t["id"] == q:
            return t

    # Try exact name (case-insensitive)
    for t in index["topics"]:
        if t["name"].lower() == q:
            return t

    # Try name contains (case-insensitive)
    for t in index["topics"]:
        if q in t["name"].lower():
            return t

    return None


def archive_topic(user_name: str, topic_id: str) -> bool:
    """
    Archive a topic by ID or name.

    If the archived topic was active, switches to the first non-archived topic.
    At least one non-archived topic is guaranteed to exist after archiving
    (the "General" topic cannot be the only active topic).

    Returns:
        True on success, False if topic not found
    """
    index = load_index(user_name)
    for t in index["topics"]:
        if t["id"] == topic_id or t["name"].lower() == topic_id.lower():
            t["archived"] = True
            # If it was active, switch to first non-archived topic
            if index["active_topic"] == t["id"]:
                for t2 in index["topics"]:
                    if not t2["archived"]:
                        index["active_topic"] = t2["id"]
                        break
            save_index(user_name, index)
            return True
    return False


def rename_topic(user_name: str, topic_id: str, new_name: str) -> bool:
    """
    Rename a topic by ID or name.

    Returns:
        True on success, False if topic not found
    """
    index = load_index(user_name)
    for t in index["topics"]:
        if t["id"] == topic_id or t["name"].lower() == topic_id.lower():
            t["name"] = new_name
            save_index(user_name, index)
            return True
    return False


def save_messages(user_name: str, topic_id: str, messages: list) -> None:
    """
    Append messages to a topic's conversation history.

    Args:
        user_name: Display name of the user
        topic_id: Target topic ID
        messages: List of dicts with 'role' and 'content' keys
    """
    path = _topic_path(user_name, topic_id)
    now = _now()
    with open(path, "a") as f:
        for msg in messages:
            entry = {
                "role": msg.get("role", "unknown"),
                "content": msg.get("content", ""),
                "ts": now,
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Update message count in index
    index = load_index(user_name)
    for t in index["topics"]:
        if t["id"] == topic_id:
            t["msg_count"] = (t.get("msg_count", 0) or 0) + len(messages)
            t["updated"] = now
            break
    save_index(user_name, index)


def load_topic_context(user_name: str, topic_id: str, max_lines: int = 10) -> list:
    """
    Load the last N messages from a topic's conversation history.

    Useful for re-contextualizing the agent when switching back to a topic.

    Args:
        user_name: Display name of the user
        topic_id: Target topic ID
        max_lines: Maximum number of messages to return

    Returns:
        List of message dicts (most recent first)
    """
    path = _topic_path(user_name, topic_id)
    if not path.exists():
        return []

    with open(path) as f:
        lines = f.readlines()

    messages = []
    for line in lines[-max_lines:]:
        line = line.strip()
        if line:
            try:
                messages.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    return messages


def format_topic_list(user_name: str) -> str:
    """
    Format all topics as a human-readable list for Telegram/Markdown.

    Returns a Markdown-formatted string with emoji indicators:
    ✅ = active, 📦 = archived, • = available
    """
    index = load_index(user_name)
    active_id = index["active_topic"]

    lines = []
    for i, t in enumerate(index["topics"], 1):
        prefix = (
            "✅" if t["id"] == active_id else ("📦" if t["archived"] else "•")
        )
        name = t["name"]
        summary = t.get("summary", "")
        msgs = t.get("msg_count", 0)
        arch = " *(archived)*" if t["archived"] else ""
        lines.append(f"{prefix} **{i}. {name}**{arch}")
        if summary:
            lines.append(f"   └ {summary}")
        if msgs:
            plural = "message" if msgs == 1 else "messages"
            lines.append(f"   └ {msgs} {plural}")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: topic_manager.py <user_name> <action> [args...]")
        print("Actions: list, active, create, switch, archive, rename")
        sys.exit(1)

    user = sys.argv[1]
    action = sys.argv[2]

    if action == "list":
        print(format_topic_list(user))

    elif action == "active":
        topic, _ = get_active_topic(user)
        if topic:
            print(f"Active topic: {topic['name']} (id: {topic['id']})")
        else:
            print("No topics found.")

    elif action == "create":
        name = sys.argv[3] if len(sys.argv) > 3 else "New Topic"
        summary = sys.argv[4] if len(sys.argv) > 4 else ""
        topic = create_topic(user, name, summary)
        print(f"Created topic: {topic['name']} (id: {topic['id']})")
        sys.exit(0)

    elif action == "switch":
        topic_id = sys.argv[3]
        topic = switch_topic(user, topic_id)
        if topic:
            print(f"Switched to: {topic['name']} (id: {topic['id']})")
        else:
            print(f"Topic not found: {topic_id}")
            sys.exit(1)

    elif action == "archive":
        topic_id = sys.argv[3]
        ok = archive_topic(user, topic_id)
        if ok:
            print(f"Archived: {topic_id}")
        else:
            print(f"Topic not found: {topic_id}")
            sys.exit(1)

    elif action == "rename":
        topic_id = sys.argv[3]
        new_name = sys.argv[4]
        ok = rename_topic(user, topic_id, new_name)
        if ok:
            print(f"Renamed to: {new_name}")
        else:
            print(f"Topic not found: {topic_id}")
            sys.exit(1)

    else:
        print(f"Unknown action: {action}")
        print("Valid actions: list, active, create, switch, archive, rename")
        sys.exit(1)
