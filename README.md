# Telegram Topic Sessions

**Virtual topic/session management for linear Telegram chats.**

Since Telegram conversations are strictly linear (no parallel sessions), this system implements **virtual topics** — each topic is a self-contained context stored as JSON files. Users can create, switch, archive, and rename topics through natural language commands or inline keyboard buttons.

## Features

- ✅ **Multiple virtual topics per user** — isolated contexts in a single chat
- ✅ **Inline keyboard switching** — tap a button to change topics (no typing)
- ✅ **Persistent context** — each topic stores its own conversation history
- ✅ **Per-user isolation** — Alejo's topics ≠ Sara's topics
- ✅ **Archivable topics** — close topics without losing data
- ✅ **Markdown-formatted output** — clean Telegram-compatible rendering

## How It Works

```
User chat (Telegram, linear)
│
├── [Topic: General]  ← default, always available
│   ├── messages...
│   └── context saved to disk on switch
│
├── [Topic: Project X]  ← created on demand
│   ├── messages...
│   └── context saved to disk on switch
│
└── [Topic: Research]  ← archived, read-only
    └── context preserved
```

## Repository Structure

```
telegram-topic-sessions/
├── topic_manager.py                  # Core engine — topic CRUD, context persistence
├── switch_topic.py                   # CLI script: switch topics via terminal
├── topics_inline.py                  # Telegram Bot API inline keyboard sender
├── gateway_patch.py                  # Patch for Hermes Telegram gateway (callback handler)
├── SKILL.md                          # Hermes Agent skill definition
├── docs/
│   ├── architecture.md               # System architecture overview
│   └── inline-keyboard-integration.md # Inline keyboard implementation details
├── examples/
│   └── index.example.json            # Sample topic index file
├── LICENSE
└── README.md
```

## Quick Start

### 1. Prerequisites

- Python 3.8+
- A Telegram bot token (`TELEGRAM_BOT_TOKEN`)
- (Optional) Hermes Agent gateway with Telegram adapter

### 2. Install

```bash
git clone https://github.com/klan1/telegram-topic-sessions.git
cd telegram-topic-sessions
```

### 3. Configure

Ensure `TELEGRAM_BOT_TOKEN` is set in your environment or `.env` file:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
```

### 4. Usage via Hermes Agent

The system integrates with Hermes Agent as a skill. When loaded, users interact naturally:

| User says | Action |
|---|---|
| `/topics` or "show me my topics" | Sends inline keyboard with all topics |
| "new topic: Project Alpha" | Creates and switches to new topic |
| "switch to topic General" | Switches context to General |
| "close topic Research" | Archives a topic |
| "rename topic Old to New" | Renames a topic |

### 5. Standalone Usage

```python
from topic_manager import (
    load_index, create_topic, switch_topic,
    archive_topic, list_topics, format_topic_list
)

# List topics for a user
index = load_index("Alejo")
print(format_topic_list("Alejo"))

# Create a new topic
create_topic("Alejo", "Project Alpha", summary="Planning sprint 1")

# Switch to a topic by ID
switch_topic("Alejo", "topic_abc123")
```

### 6. CLI Topic Switch

```bash
# Switch from the terminal
python switch_topic.py <user_id> <topic_id> "<user_display>"
```

### 7. Send Inline Keyboard

```bash
python topics_inline.py send <chat_id> "📋 Your topics:" '<json_topics>' <active_id> <user_id>
```

## Data Storage

Topics are stored per-user under a configurable base directory:

```
session_topics/
├── Alejo/
│   ├── index.json               # {active_topic, topics: [...]}
│   ├── topic_general.jsonl       # Saved conversation history
│   └── topic_project_alpha.jsonl
├── Sara/
│   ├── index.json
│   └── topic_general.jsonl
└── ...
```

### index.json format

```json
{
  "active_topic": "topic_abc123",
  "topics": [
    {
      "id": "topic_abc123",
      "name": "General",
      "created": "2026-06-11T16:00:00",
      "updated": "2026-06-11T16:30:00",
      "summary": "General discussion",
      "msg_count": 15,
      "archived": false
    }
  ]
}
```

### topic_<id>.jsonl format

JSONL, one message per line:

```json
{"role": "user", "content": "Hello, what's new?", "ts": "2026-06-11T16:00:00"}
{"role": "assistant", "content": "Here's the update...", "ts": "2026-06-11T16:00:05"}
```

## Telegram Inline Keyboard Integration

The system uses Telegram's `InlineKeyboardMarkup` to present topics as tappable buttons. When a user taps a topic button:

1. The gateway's `_handle_callback_query` catches the `ts:` callback data
2. It runs `switch_topic.py` to update the filesystem
3. The inline message is edited to show the switch confirmation
4. Context is injected via `inject_clarify_text` for the next agent turn

See `docs/inline-keyboard-integration.md` for full implementation details.

## Gateway Integration (Hermes Agent)

The patch in `gateway_patch.py` adds a `ts:` handler to the existing `_handle_callback_query` method in `gateway/platforms/telegram.py`. It handles:

- **Topic selection** (`ts:user_id:topic_id`) — switches to the selected topic
- **New topic** (`ts:user_id:__new__`) — prompts the user to type a name
- **Authorization** — only the chat's authorized users may switch topics

## Shell Completion / Quick Reference

```
TOPIC COMMANDS (natural language):
  /topics, show topics          → list with inline keyboard
  new topic: <name>            → create & switch
  switch to topic <name/id>    → switch context
  close topic <name>           → archive
  rename topic <old> to <new>  → rename

TOPIC DATA FILES:
  session_topics/<User>/index.json        → topic registry
  session_topics/<User>/topic_<id>.jsonl  → message history
```

## License

MIT — See [LICENSE](LICENSE) for details.
