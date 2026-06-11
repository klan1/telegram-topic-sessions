# Inline Keyboard Integration

This document details how Telegram inline keyboards are used to provide a
button-based topic switching interface.

## Overview

Instead of typing "switch to topic General", users can tap a button. This is
implemented using Telegram's `InlineKeyboardMarkup` and callback query system.

## Callback Data Format

All topic callbacks use the prefix `ts:` followed by the user ID and topic ID:

```
ts:<user_id>:<topic_id>
ts:<user_id>:__new__
```

Examples:
- `ts:123456789:topic_general` — Switch to General
- `ts:123456789:topic_abc123` — Switch to Project X
- `ts:123456789:__new__` — Create new topic

## Components

### 1. `topics_inline.py` — Keyboard Sender

This script builds and sends (or edits) the inline keyboard. It is called
from the terminal tool when the user requests to see their topics.

**API calls used:**
- `sendMessage` — Sends a new message with `reply_markup` (inline keyboard)
- `editMessageText` — Updates an existing message's text and keyboard

**Keyboard layout:**
```
┌──────────────────────────────┐
│ ✅ General                   │
│ • Project X                  │
│ 📦 Archive 2025              │
│                              │
│ [➕ New topic]               │
└──────────────────────────────┘
```

### 2. Gateway Callback Handler

The existing `_handle_callback_query` in `gateway/platforms/telegram.py`
is extended with a `ts:` prefix handler. The handler flow:

```
1. Parse callback data → user_id, topic_id
2. Verify caller authorization
3. If "__new__":
   a. Answer with toast "✏️ Type the new topic name"
   b. Edit message to show prompt, remove keyboard
   c. Return (user's next text message becomes the topic name)
4. If regular topic:
   a. Answer with toast "✅ Switching topic…"
   b. Run switch_topic.py via subprocess
   c. Edit message to show switch confirmation (no buttons)
   d. Inject context via inject_clarify_text()
```

### 3. Authorization

The callback handler uses the existing `_is_callback_user_authorized()`
method, which checks:

- DM: The user is the chat owner
- Group: The user is an authorized member (configurable per chat)

## How to Add New Features

### Add a new button (e.g., "Rename")

1. Add a new callback prefix in `make_topic_keyboard()`
2. Add a corresponding `if data.startswith("tr:")` handler in
   `_handle_callback_query`

### Add a confirmation step

Use `editMessageText` to replace the keyboard with a confirmation prompt
and a second set of buttons (`ts:confirm:yes`, `ts:confirm:no`). Handle
the second callback in the same `ts:` handler.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Button tap does nothing | Gateway not patched | Apply `gateway_patch.py` |
| "⛔ Not authorized" | User not in auth list | Check chat config |
| Buttons show stale data | `index.json` not updated | Check switch_topic.py permissions |
| "✏️ Type…" but no response | `__new__` callback not caught | Check `ts:` handler order |
| Markdown broken in edit | Unescaped chars in topic name | Use `format_message()` or `esc()` |
