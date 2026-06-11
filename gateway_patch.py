"""
Gateway Patch — Telegram Inline Keyboard Callback Handler for Topic Sessions.

This patch adds a ``ts:`` prefix handler to the existing ``_handle_callback_query``
method in ``gateway/platforms/telegram.py`` of the Hermes Agent gateway.

The handler supports two callback data formats:
  - ``ts:<user_id>:<topic_id>``  → Switch to the specified topic
  - ``ts:<user_id>:__new__``     → Prompt user to type a new topic name
"""

# ===== INSTALLATION =====
#
# 1. Open ``gateway/platforms/telegram.py``
# 2. Find the ``_handle_callback_query`` method
# 3. Insert the code below AFTER the clarify section (after "cl:" handler,
#    around line 2900) and BEFORE the update-prompt section (before
#    "update_prompt:" handler, around line 2974).
#
# ===== CODE TO INSERT =====

#         # --- Topic Session callbacks (ts:user_id:topic_id) ---
#         if data.startswith("ts:"):
#             parts = data.split(":", 2)
#             if len(parts) == 3:
#                 ts_user_id = parts[1]
#                 ts_topic_id = parts[2]
#
#                 caller_id = str(getattr(query.from_user, "id", ""))
#                 if not self._is_callback_user_authorized(
#                     caller_id,
#                     chat_id=query_chat_id,
#                     chat_type=(str(query_chat_type)
#                                if query_chat_type is not None else None),
#                     thread_id=(str(query_thread_id)
#                                if query_thread_id is not None else None),
#                     user_name=query_user_name,
#                 ):
#                     await query.answer(text="⛔ You are not authorized.")
#                     return
#
#                 user_display = getattr(query.from_user, "first_name", "User") or "User"
#
#                 if ts_topic_id == "__new__":
#                     await query.answer(
#                         text="✏️ Type the new topic name in the chat."
#                     )
#                     try:
#                         await query.edit_message_text(
#                             text=(f"{query.message.text or '📋 Topics'}\n\n"
#                                   f"✏️ *Type the new topic name…*"),
#                             parse_mode=ParseMode.MARKDOWN_V2,
#                             reply_markup=None,
#                         )
#                     except Exception:
#                         pass
#                     return
#
#                 # Switch to selected topic
#                 await query.answer(text="✅ Switching topic…")
#
#                 try:
#                     import subprocess
#                     script = "/opt/data/session_topics/switch_topic.py"
#                     result = subprocess.run(
#                         [sys.executable, script, ts_user_id, ts_topic_id, user_display],
#                         capture_output=True, text=True, timeout=10,
#                     )
#                     output = result.stdout.strip()
#                     error = result.stderr.strip()
#                     if result.returncode == 0 and output:
#                         try:
#                             await query.edit_message_text(
#                                 text=self.format_message(output),
#                                 parse_mode=ParseMode.MARKDOWN_V2,
#                                 reply_markup=None,
#                             )
#                         except Exception:
#                             pass
#                         try:
#                             from tools.clarify_gateway import inject_clarify_text
#                             inject_clarify_text(
#                                 f"[System: {user_display} switched to topic "
#                                 f"'{ts_topic_id}'. Topic context loaded. "
#                                 f"Continue conversation in this topic.]"
#                             )
#                         except Exception:
#                             pass
#                     else:
#                         await query.answer(
#                             text=f"Error: {error or 'unknown'}"
#                         )
#                 except Exception as exc:
#                     logger.error(
#                         "[%s] Topic session callback failed: %s",
#                         self.name, exc
#                     )
#                     await query.answer(text="Error switching topic.")
#             return

# ===== VERIFICATION =====
#
# After applying the patch, restart the gateway and test:
#
#   1. Send an inline keyboard using topics_inline.py
#   2. Tap a topic button  →  should switch context
#   3. Tap "➕ New topic"  →  should prompt for name
#   4. Check gateway logs:
#      tail -f /opt/data/logs/gateway.log | grep -i topic
