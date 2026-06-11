# Architecture — Telegram Topic Sessions

## Overview

Telegram conversations are strictly linear — there is no concept of parallel
sessions or tabs. This system emulates virtual topics by storing conversation
contexts as JSON files on disk and switching between them on demand.

```
┌─────────────────────────────────────────────┐
│              Telegram User Chat              │
│  ┌───────────────────────────────────────┐   │
│  │ User: /topics                         │   │
│  │ Bot:  [📋 Topics] ┌─────┐ ┌─────┐   │   │
│  │         │General │ │ProjX│          │   │
│  │         └─────┘ └─────┘            │   │
│  │         ┌────────────┐              │   │
│  │         │➕ New topic │              │   │
│  │         └────────────┘              │   │
│  └───────────────────────────────────────┘   │
└─────────────────────┬───────────────────────┘
                      │ tap button
                      ▼
┌─────────────────────────────────────────────┐
│         Hermes Gateway (telegram.py)         │
│  _handle_callback_query detects "ts:" prefix │
│  → runs switch_topic.py                     │
│  → edits inline message with confirmation    │
│  → injects clarify context for next turn     │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│         Filesystem (session_topics/)         │
│                                             │
│  Alejo/                                      │
│  ├── index.json       ← updated active_topic │
│  ├── topic_general.jsonl                     │
│  └── topic_project_x.jsonl                   │
│                                             │
│  Sara/                                       │
│  ├── index.json                              │
│  └── topic_general.jsonl                     │
└─────────────────────────────────────────────┘
```

## Components

### 1. `topic_manager.py` — Core Engine

The central library for topic operations. Pure Python, no external
dependencies. Handles:

- **Index management** — load/save per-user topic registries
- **Topic CRUD** — create, read, update, archive, rename
- **Context persistence** — read/write conversation history (JSONL)
- **Topic discovery** — find by ID, name, or numeric index
- **Markdown formatting** — produce Telegram-compatible topic lists

### 2. `switch_topic.py` — CLI Switch Script

Called by the gateway's callback handler when a user taps a topic button.
A standalone script (not a module) that:

1. Reads the user's `index.json`
2. Finds the target topic by ID or name
3. Updates `active_topic` in the index
4. Prints a formatted Markdown confirmation to stdout
5. Exits with code 0 on success, 1 on error

### 3. `topics_inline.py` — Inline Keyboard Sender

Sends Telegram messages with `InlineKeyboardMarkup` via the Bot API.
Supports both `sendMessage` (new) and `editMessageText` (update).
Handles:

- Building the keyboard from a topic list
- Marking the active topic with ✅
- Marking archived topics with 📦
- The "➕ New topic" utility button
- Proper error handling and logging

### 4. `gateway_patch.py` — Gateway Integration

Documents the exact code to insert into Hermes Agent's
`gateway/platforms/telegram.py` to handle `ts:` callback queries.
The handler:

- **Authorization check** — only chat-authorized users may switch topics
- **"__new__" action** — removes keyboard, prompts user to type a name
- **Topic switch** — runs `switch_topic.py`, edits the inline message,
  injects context via `inject_clarify_text()`

## Data Flow

```
User taps "General" button
        │
        ▼
Telegram sends callback: ts:123456789:topic_general
        │
        ▼
gateway/platforms/telegram.py
  _handle_callback_query(query)
        │
        ├─ Verify authorization
        ├─ query.answer("✅ Switching topic…")  ← toast notification
        │
        ▼
subprocess.run(["python3", "switch_topic.py", "123456789", "topic_general", "Alejo"])
        │
        ▼
switch_topic.py
  ├─ Reads /opt/data/session_topics/Alejo/index.json
  ├─ Sets active_topic = "topic_general"
  └─ Writes updated index.json
        │
        ▼
[stdout] "Alejo switched to General\n📋 Topics:\n ✅ General\n • Project X"
        │
        ▼
query.edit_message_text(result)  ← replaces buttons with confirmation
inject_clarify_text("[System: ...]")  ← sets context for next agent turn
```

## Storage Format

### Index File (`index.json`)

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

### Context File (`topic_<id>.jsonl`)

JSONL format, one message per line:

```json
{"role": "user", "content": "Hello!", "ts": "2026-06-11T16:00:00"}
{"role": "assistant", "content": "Hi!", "ts": "2026-06-11T16:00:05"}
```

## Security & Isolation

- **Per-user isolation**: Each user has their own directory under
  `session_topics/`. Alejo's topics are invisible to Sara.
- **Authorization check**: The gateway verifies the callback's `from_user.id`
  matches the chat's authorized users before switching topics.
- **No remote access**: All data is local filesystem; no network storage.

## Edge Cases

| Scenario | Behavior |
|---|---|
| Switch to already-active topic | Gateway shows toast "Already there" |
| Topic doesn't exist | Gateway shows error; no state change |
| First-time user | `index.json` initialized with a "General" topic |
| Archive active topic | Switches to first non-archived topic |
| No topics left unarchived | Keeps the archived one active (edge case warning) |
| Gateway restarts mid-switch | Index write is atomic; next turn recovers cleanly |
