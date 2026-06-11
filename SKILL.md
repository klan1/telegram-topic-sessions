---
name: topic-sessions
description: Virtual topic/session management for linear Telegram chats — create, switch, archive topics per user via natural language or inline keyboards
version: 1.0.0
author: Klan1 Labs
license: MIT
---

# Topic Sessions

Virtual topic management for Telegram's linear chat model. Each topic is an
isolated conversation context stored as JSON files. Switching topics saves
the current context and loads the target topic's history.

## Quick Reference

| Action | User says |
|---|---|
| List topics | `/topics` or "show my topics" |
| Create topic | `new topic: <name>` |
| Switch topic | `switch to topic <name/id/number>` |
| Archive topic | `close topic <name>` or `archive topic <name>` |
| Rename topic | `rename topic <old> to <new>` |

## Inline Keyboard

When the user invokes `/topics`, send an inline keyboard via:

```bash
python /opt/data/scripts/topics_inline.py send \
  <chat_id> \
  "📋 **Topics:**" \
  '<topics_json>' \
  <active_id> \
  <user_id>
```

## Data Storage

```
session_topics/<UserName>/
  index.json              # {active_topic, topics: [...]}
  topic_<id>.jsonl        # Conversation history (JSONL)
```
