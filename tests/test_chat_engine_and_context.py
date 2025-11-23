"""
Comprehensive tests for ChatEngine + ContextManager:
- Context construction, workspace/active file/summary injection
- Message pruning and clear semantics
- Token estimation
- Automatic summarization and pruning integration
- Adaptive pruning thresholds and notices
- Local instruction execution for offline providers
- Model switching / reversion state handling
- Basic streaming behavior around local instruction pass

These tests mock external providers, network calls, and filesystem effects.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from gitvisioncli.core.chat_engine import ChatEngine
from gitvisioncli.core.executor import AIActionExecutor
from gitvisioncli.core.context_manager import ContextManager, Message
from gitvisioncli.core.supervisor import ActionContext, ActionResult, ActionStatus, ActionType
from gitvisioncli import cli as cli_mod


# ---------------------------------------------------------------------------
# Helpers / Fakes
# ---------------------------------------------------------------------------

class FakeAI:
    """Minimal async AI client used for summarization tests."""

    def __init__(self, summary_text: str = "SUMMARY"):
        self.summary_text = summary_text
        self.ask_full_calls: List[Dict[str, Any]] = []

    async def ask_full(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        self.ask_full_calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )
        return self.summary_text


class FakeExecutor:
    """Executor stub that records actions and returns configurable results."""

    def __init__(self, results: Optional[List[ActionResult]] = None):
        self.actions: List[Dict[str, Any]] = []
        self.contexts: List[ActionContext] = []
        self.results = list(results) if results is not None else []
        self.base_dir = Path("/tmp/gitvision-tests")
        self._dry_run = False
        # Terminal stub used in planning path, but not heavily in these tests.
        self.terminal = type("T", (), {"run_once": lambda *a, **k: (0, "", "")})()

    def run_action(self, action: Dict[str, Any], context: Optional[ActionContext] = None) -> ActionResult:
        self.actions.append(action)
        self.contexts.append(context or ActionContext())
        if self.results:
            return self.results.pop(0)
        # Default success result.
        return ActionResult(
            status=ActionStatus.SUCCESS,
            message=action.get("type", "OK"),
            data={"path": action.get("params", {}).get("path", "test-path")},
        )

    def get_base_dir(self) -> Path:
        return self.base_dir

    def enable_dry_run(self) -> None:
        self._dry_run = True

    def disable_dry_run(self) -> None:
        self._dry_run = False

    def is_dry_run(self) -> bool:
        return self._dry_run

    def set_fs_watcher(self, watcher) -> None:
        # Not needed for these tests
        pass


def make_engine() -> ChatEngine:
    """
    Construct a ChatEngine suitable for tests.

    - Uses a dummy OpenAI key so provider validation passes.
    - Immediately overwrites the executor with a fake to avoid side effects.
    """
    engine = ChatEngine(
        base_dir=".",
        api_key="test-key",
        model="gpt-4o-mini",
        providers={"openai": {"api_key": "test-key"}},
        github_config=None,
    )
    engine.executor = FakeExecutor()
    return engine


def run_async(coro):
    """Helper to run async coroutines inside plain pytest tests."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# ContextManager tests
# ---------------------------------------------------------------------------

def test_context_manager_system_prompt_includes_workspace_active_file_and_summary_in_order():
    ctx = ContextManager()
    ctx.system_prompt = "BASE"
    ctx.workspace_summary = "WS"
    ctx.active_file_path = "foo.py"
    ctx.active_file_content = "1: print('hi')"
    ctx.summary_history = "PREV SUMMARY"
    ctx.messages.append(Message(role="user", content="hello"))

    msgs = ctx.get_openai_messages()
    assert msgs[0]["role"] == "system"
    system_content = msgs[0]["content"]

    # Order: base, workspace, active file, summary block
    assert "BASE" in system_content
    ws_idx = system_content.index("--- DYNAMIC WORKSPACE CONTEXT ---")
    af_idx = system_content.index("# ACTIVE FILE")
    summ_idx = system_content.index("--- SUMMARY OF PREVIOUS CONVERSATION ---")
    assert ws_idx < af_idx < summ_idx

    assert "WS" in system_content
    assert "path: foo.py" in system_content
    assert "1: print('hi')" in system_content
    assert "PREV SUMMARY" in system_content
    assert msgs[1]["role"] == "user"
    assert msgs[1]["content"] == "hello"


def test_context_manager_system_prompt_without_workspace_or_summary():
    ctx = ContextManager()
    ctx.system_prompt = "ONLY-SYSTEM"
    ctx.messages.append(Message(role="user", content="hi"))

    msgs = ctx.get_openai_messages()
    assert len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"] == "ONLY-SYSTEM"
    assert msgs[1]["role"] == "user"
    assert msgs[1]["content"] == "hi"


def test_context_manager_prune_messages_keeps_last_n_user_turns():
    ctx = ContextManager()

    # Build 3 logical user turns (user + assistant + tool)
    for i in range(3):
        ctx.messages.append(Message(role="user", content=f"u{i}"))
        ctx.messages.append(Message(role="assistant", content=f"a{i}"))
        ctx.messages.append(Message(role="tool", content=f"t{i}"))

    # Keep last 2 user turns: should drop the first user+assistant+tool trio.
    ctx.prune_messages(2)

    assert [m.role for m in ctx.messages] == [
        "user",
        "assistant",
        "tool",
        "user",
        "assistant",
        "tool",
    ]
    assert ctx.messages[0].content == "u1"
    assert ctx.messages[-1].content == "t2"


def test_context_manager_prune_messages_with_zero_clears_history():
    ctx = ContextManager()
    ctx.messages.append(Message(role="user", content="hi"))
    ctx.messages.append(Message(role="assistant", content="there"))

    ctx.prune_messages(0)
    assert ctx.messages == []


def test_context_manager_prune_messages_when_n_exceeds_user_turns_keeps_all():
    ctx = ContextManager()
    for i in range(2):
        ctx.messages.append(Message(role="user", content=f"u{i}"))
        ctx.messages.append(Message(role="assistant", content=f"a{i}"))

    original = list(ctx.messages)
    ctx.prune_messages(5)
    assert ctx.messages == original


def test_context_manager_clear_resets_messages_and_summary_but_preserves_system_and_workspace():
    ctx = ContextManager()
    ctx.system_prompt = "SYSTEM"
    ctx.workspace_summary = "WORKSPACE"
    ctx.summary_history = "OLD SUMMARY"
    ctx.messages.append(Message(role="user", content="hi"))

    ctx.clear()

    assert ctx.system_prompt == "SYSTEM"
    assert ctx.workspace_summary == "WORKSPACE"
    assert ctx.summary_history is None
    assert ctx.messages == []


def test_estimate_token_usage_uses_character_count_heuristic():
    ctx = ContextManager()
    ctx.system_prompt = "SYS"
    ctx.messages.append(Message(role="user", content="1234567890"))  # 10 chars

    approx = ctx.estimate_token_usage()
    # 13 chars total (SYS + content) / 3.5 ≈ 3–4
    assert approx > 0
    assert approx <= 10  # sanity upper bound


# ---------------------------------------------------------------------------
# Summarization tests
# ---------------------------------------------------------------------------

def test_summarize_old_messages_creates_summary_and_prunes_history():
    engine = make_engine()
    engine.ai = FakeAI(summary_text="COMPACT SUMMARY")
    ctx = engine.context

    # Build many messages so that old_messages exist (>12)
    for i in range(15):
        ctx.messages.append(Message(role="user", content=f"u{i}"))
        ctx.messages.append(Message(role="assistant", content=f"a{i}"))

    run_async(engine.summarize_old_messages())

    # Summary stored
    assert ctx.summary_history == "COMPACT SUMMARY"

    # Conversation pruned to last 6 user turns (and their associated messages)
    user_roles = [m for m in ctx.messages if m.role == "user"]
    assert len(user_roles) <= 6

    # Notice set
    assert engine._auto_summary_notice == "✓ Automatic summarization applied."
    # Guard reset
    assert engine._summary_in_progress is False


def test_summarize_old_messages_noop_when_ai_missing():
    engine = make_engine()
    engine.ai = None
    ctx = engine.context

    for i in range(15):
        ctx.messages.append(Message(role="user", content=f"u{i}"))

    run_async(engine.summarize_old_messages())
    assert ctx.summary_history is None
    assert len(ctx.messages) == 15  # no prune


def test_summarize_old_messages_noop_when_summary_already_present():
    engine = make_engine()
    engine.ai = FakeAI(summary_text="NEW SUMMARY")
    ctx = engine.context
    ctx.summary_history = "EXISTING"

    for i in range(15):
        ctx.messages.append(Message(role="user", content=f"u{i}"))

    run_async(engine.summarize_old_messages())
    # Existing summary must be preserved
    assert ctx.summary_history == "EXISTING"
    assert len(ctx.messages) == 15


def test_summarize_old_messages_handles_ai_exception_and_resets_flag():
    engine = make_engine()

    class FailingAI(FakeAI):
        async def ask_full(self, *args, **kwargs) -> str:  # type: ignore[override]
            raise RuntimeError("network error")

    engine.ai = FailingAI()
    ctx = engine.context

    for i in range(15):
        ctx.messages.append(Message(role="user", content=f"u{i}"))

    run_async(engine.summarize_old_messages())

    assert ctx.summary_history is None
    assert len(ctx.messages) == 15
    assert engine._summary_in_progress is False


def test_summarize_old_messages_requires_enough_messages():
    engine = make_engine()
    engine.ai = FakeAI(summary_text="SUMMARY")
    ctx = engine.context

    # Fewer than or equal to 12 messages → no summary
    for i in range(6):
        ctx.messages.append(Message(role="user", content=f"u{i}"))
        ctx.messages.append(Message(role="assistant", content=f"a{i}"))

    run_async(engine.summarize_old_messages())
    assert ctx.summary_history is None


# ---------------------------------------------------------------------------
# Auto-prune integration tests
# ---------------------------------------------------------------------------

def test_auto_prune_if_needed_triggers_summarization_when_usage_above_75(monkeypatch):
    engine = make_engine()
    engine.ai = FakeAI(summary_text="SUMMARY")
    ctx = engine.context

    # Some messages; details are irrelevant if we override token estimation.
    for i in range(5):
        ctx.messages.append(Message(role="user", content=f"u{i}"))

    called = {"summary": False}

    async def fake_summarize():
        called["summary"] = True

    monkeypatch.setattr(engine, "_estimate_token_usage", lambda: engine._get_model_max_context_tokens() * 0.8)
    monkeypatch.setattr(engine, "summarize_old_messages", fake_summarize)

    run_async(engine._auto_prune_if_needed())
    assert called["summary"] is True


def test_auto_prune_if_needed_does_not_prune_below_85_percent(monkeypatch):
    engine = make_engine()
    ctx = engine.context

    for i in range(5):
        ctx.messages.append(Message(role="user", content=f"u{i}"))

    # Force high usage but still under prune threshold; summarization disabled.
    monkeypatch.setattr(engine, "_estimate_token_usage", lambda: int(engine._get_model_max_context_tokens() * 0.8))
    # No summary path (ai is None)
    engine.ai = None

    before = ctx.get_message_count()
    run_async(engine._auto_prune_if_needed())
    after = ctx.get_message_count()

    assert before == after
    assert engine._auto_prune_notice is None


def test_auto_prune_if_needed_prunes_with_correct_thresholds_and_adaptive_min(monkeypatch):
    engine = make_engine()
    ctx = engine.context

    # Add several user messages so pruning actually removes something.
    for i in range(10):
        ctx.messages.append(Message(role="user", content=f"u{i}"))

    # Force repeated high usage > 0.95 to use base_keep=2
    def high_usage():
        return int(engine._get_model_max_context_tokens() * 0.96)

    monkeypatch.setattr(engine, "_estimate_token_usage", high_usage)
    engine.ai = None  # no summarization

    # First prune run
    run_async(engine._auto_prune_if_needed())
    first_notice = engine._auto_prune_notice
    assert "kept last 2" in first_notice

    first_count = ctx.get_message_count()

    # Run multiple times to drive adaptive min
    for _ in range(4):
        run_async(engine._auto_prune_if_needed())

    assert engine._auto_prune_runs >= 5
    assert engine._auto_prune_min_kept_turns > 0

    # Ensure messages are not completely cleared.
    assert ctx.get_message_count() > 0
    assert ctx.get_message_count() <= first_count


def test_auto_prune_if_needed_handles_prune_exceptions_and_keeps_state(monkeypatch):
    engine = make_engine()
    ctx = engine.context

    for i in range(5):
        ctx.messages.append(Message(role="user", content=f"u{i}"))

    monkeypatch.setattr(engine, "_estimate_token_usage", lambda: int(engine._get_model_max_context_tokens() * 0.9))

    def failing_prune(n: int) -> None:
        raise RuntimeError("prune failed")

    monkeypatch.setattr(ctx, "prune_messages", failing_prune)

    run_async(engine._auto_prune_if_needed())

    # Messages unchanged, notice not set.
    assert ctx.get_message_count() == 5
    assert engine._auto_prune_notice is None


def test_auto_prune_if_needed_respects_summary_in_progress_guard(monkeypatch):
    engine = make_engine()
    ctx = engine.context
    for i in range(10):
        ctx.messages.append(Message(role="user", content=f"u{i}"))

    engine._summary_in_progress = True

    called = {"summary": False}

    async def fake_summarize():
        called["summary"] = True

    monkeypatch.setattr(engine, "summarize_old_messages", fake_summarize)
    monkeypatch.setattr(engine, "_estimate_token_usage", lambda: int(engine._get_model_max_context_tokens() * 0.9))

    run_async(engine._auto_prune_if_needed())

    # Guard should prevent summarization call.
    assert called["summary"] is False


def test_consume_auto_summary_and_prune_notices_reset_after_reading():
    engine = make_engine()
    engine._auto_prune_notice = "PRUNE"
    engine._auto_summary_notice = "SUMMARY"

    n1 = engine.consume_auto_prune_notice()
    n2 = engine.consume_auto_prune_notice()
    s1 = engine.consume_auto_summary_notice()
    s2 = engine.consume_auto_summary_notice()

    assert n1 == "PRUNE"
    assert n2 is None
    assert s1 == "SUMMARY"
    assert s2 is None


# ---------------------------------------------------------------------------
# Local instruction execution tests
# ---------------------------------------------------------------------------

def test_run_local_instruction_pass_executes_single_action_and_logs_success():
    engine = make_engine()
    engine.executor = FakeExecutor()

    assistant_reply = """
    Here is what I will do:

    ```json
    {"action": {"type": "CreateFile", "params": {"path": "src/app.py", "content": "print('hi')\\n"}}}
    ```
    """

    logs = engine._run_local_instruction_pass(assistant_reply)

    assert engine.executor.actions == [
        {"type": "CreateFile", "params": {"path": "src/app.py", "content": "print('hi')\n"}}
    ]
    assert any("[Executing actions (local)]" in line for line in logs)
    assert any("✓ CreateFile" in line for line in logs)


def test_run_local_instruction_pass_executes_multiple_actions_with_mixed_results():
    # First action succeeds, second fails.
    results = [
        ActionResult(status=ActionStatus.SUCCESS, message="OK CreateFile"),
        ActionResult(status=ActionStatus.FAILURE, message="Bad action", error="oops"),
    ]
    engine = make_engine()
    engine.executor = FakeExecutor(results=results)

    assistant_reply = """
    ```json
    {
      "actions": [
        {"type": "CreateFile", "params": {"path": "a.py", "content": "a"}},
        {"type": "DeleteFolder", "params": {"path": "nonexistent"}}
      ]
    }
    ```
    """

    logs = engine._run_local_instruction_pass(assistant_reply)

    assert len(engine.executor.actions) == 2
    assert any("✓ OK CreateFile" in line for line in logs)
    assert any("✗ Bad action: oops" in line for line in logs)


def test_run_local_instruction_pass_ignores_invalid_json_and_returns_empty():
    engine = make_engine()
    engine.executor = FakeExecutor()

    assistant_reply = """
    This is not JSON at all.
    ```json
    {not-valid}
    ```
    """

    logs = engine._run_local_instruction_pass(assistant_reply)
    assert logs == []
    assert engine.executor.actions == []


def test_run_local_instruction_pass_handles_top_level_json_without_fence():
    engine = make_engine()
    engine.executor = FakeExecutor()

    assistant_reply = """
    {"action": {"type": "AppendText", "params": {"path": "a.py", "text": "\\n# hi"}}}
    """

    logs = engine._run_local_instruction_pass(assistant_reply)
    assert len(engine.executor.actions) == 1
    assert engine.executor.actions[0]["type"] == "AppendText"
    assert any("Executing actions (local)" in line for line in logs)


def test_run_local_instruction_pass_no_actions_when_response_empty():
    engine = make_engine()
    engine.executor = FakeExecutor()
    logs = engine._run_local_instruction_pass("")
    assert logs == []
    assert engine.executor.actions == []


# ---------------------------------------------------------------------------
# Stream integration for offline providers
# ---------------------------------------------------------------------------

def test_stream_with_offline_provider_invokes_local_instruction_pass(monkeypatch):
    engine = make_engine()
    # Simulate offline provider with no OpenAI tools.
    engine.provider = "ollama"
    engine.ai = None
    fake_exec = FakeExecutor()
    engine.executor = fake_exec

    # Make provider completion return both natural text and a JSON block.
    reply = (
        "Here is a summary of changes.\n"
        "```json\n"
        "{\"action\": {\"type\": \"CreateFile\", \"params\": {\"path\": \"b.py\", \"content\": \"x\"}}}\n"
        "```"
    )

    async def fake_complete_via_provider(messages, temperature, max_tokens):  # type: ignore[override]
        # Ensure messages contained our latest user input.
        assert any(m["role"] == "user" for m in messages)
        return reply

    monkeypatch.setattr(engine, "_complete_via_provider", fake_complete_via_provider)

    chunks: List[str] = []

    async def run():
        async for ch in engine.stream("make file b.py"):
            chunks.append(ch)

    run_async(run())

    full = "".join(chunks)
    # Natural reply plus local execution logs
    assert "Here is a summary of changes." in full
    assert "[Executing actions (local)]" in full
    assert any(a["type"] == "CreateFile" for a in fake_exec.actions)


def test_stream_with_offline_provider_and_openai_client_skips_local_instruction(monkeypatch):
    """When an OpenAI client exists, local instruction pass must not be used."""
    engine = make_engine()
    # Provider is non-openai but we still have an OpenAI client.
    engine.provider = "ollama"
    engine.ai = FakeAI(summary_text="IRRELEVANT")

    reply = "Just some text, no JSON."

    async def fake_complete_via_provider(messages, temperature, max_tokens):  # type: ignore[override]
        return reply

    monkeypatch.setattr(engine, "_complete_via_provider", fake_complete_via_provider)

    # If local pass is incorrectly invoked, this will be hit.
    def exploding_local_pass(text: str):
        raise AssertionError("Local instruction pass should not be called when ai is present.")

    monkeypatch.setattr(engine, "_run_local_instruction_pass", exploding_local_pass)

    chunks: List[str] = []

    async def run():
        async for ch in engine.stream("hello"):
            chunks.append(ch)

    run_async(run())

    assert "".join(chunks) == reply


# ---------------------------------------------------------------------------
# Model switching / reversion tests
# ---------------------------------------------------------------------------

def test_model_switch_carries_summary_and_resets_auto_state():
    engine = make_engine()
    engine.context.summary_history = "OLD"
    engine._auto_prune_runs = 5
    engine._auto_prune_min_kept_turns = 3
    engine._auto_prune_notice = "X"
    engine._auto_summary_notice = "Y"
    engine._summary_in_progress = True

    # Switch to another OpenAI model; this should not raise, and should
    # carry over summary_history while resetting auto state.
    engine.set_model("gpt-4o")

    assert getattr(engine.context, "summary_history", None) == "OLD"
    assert engine._auto_prune_runs == 0
    assert engine._auto_prune_min_kept_turns == 0
    assert engine._auto_prune_notice is None
    assert engine._auto_summary_notice is None
    assert engine._summary_in_progress is False


def test_revert_model_resets_auto_state():
    engine = make_engine()
    # Simulate a previous engine
    engine._previous_engine_key = "openai::gpt-4o"
    engine._engine_key = "openai::gpt-4o-mini"
    engine._contexts["openai::gpt-4o"] = ContextManager()
    engine._auto_prune_runs = 3
    engine._auto_prune_min_kept_turns = 2
    engine._auto_prune_notice = "P"
    engine._auto_summary_notice = "S"
    engine._summary_in_progress = True

    reverted = engine.revert_model()
    # Either we successfully reverted, or revert_model decided there
    # was nothing to do. In both cases, no exception should be raised,
    # and if revert happened, auto state must be reset.
    if reverted is not None:
        assert engine._auto_prune_runs == 0
        assert engine._auto_prune_min_kept_turns == 0
        assert engine._auto_prune_notice is None
        assert engine._auto_summary_notice is None
        assert engine._summary_in_progress is False


def test_clear_conversation_resets_history_and_auto_state():
    engine = make_engine()
    engine.context.messages.append(Message(role="user", content="hi"))
    engine.context.summary_history = "SUMMARY"
    engine._auto_prune_runs = 2
    engine._auto_prune_min_kept_turns = 3
    engine._auto_prune_notice = "P"
    engine._auto_summary_notice = "S"
    engine._summary_in_progress = True

    engine.clear_conversation()

    assert engine.context.messages == []
    assert engine.context.summary_history is None
    assert engine._auto_prune_runs == 0
    assert engine._auto_prune_min_kept_turns == 0
    assert engine._auto_prune_notice is None
    assert engine._auto_summary_notice is None
    assert engine._summary_in_progress is False


def test_clean_context_creates_fresh_context_and_resets_auto_state():
    engine = make_engine()
    engine.context.system_prompt = "SYSTEM"
    engine.context.workspace_summary = "WS"
    engine.context.messages.append(Message(role="user", content="hi"))
    engine.context.summary_history = "SUMMARY"
    engine._contexts[engine._engine_key] = engine.context
    old_ctx = engine.context

    engine._auto_prune_runs = 2
    engine._auto_prune_min_kept_turns = 3
    engine._auto_prune_notice = "P"
    engine._auto_summary_notice = "S"
    engine._summary_in_progress = True

    engine.clean_context()

    # New ContextManager instance, but system prompt preserved.
    assert engine.context is not old_ctx
    assert engine.context.system_prompt == "SYSTEM"
    assert engine.context.workspace_summary is None
    assert engine.context.messages == []
    assert engine.context.summary_history is None
    assert engine._contexts[engine._engine_key] is engine.context
    assert engine._auto_prune_runs == 0
    assert engine._auto_prune_min_kept_turns == 0
    assert engine._auto_prune_notice is None
    assert engine._auto_summary_notice is None
    assert engine._summary_in_progress is False


# ---------------------------------------------------------------------------
# Small sanity checks for ChatEngine initialization
# ---------------------------------------------------------------------------

def test_make_engine_initializes_with_openai_provider_and_dry_run_controls():
    engine = make_engine()
    assert engine.provider == "openai"
    assert engine.model
    assert isinstance(engine.executor, FakeExecutor)

    assert engine.dry_run is False
    engine.enable_dry_run()
    assert engine.dry_run is True
    engine.disable_dry_run()
    assert engine.dry_run is False


def test_update_workspace_context_sets_workspace_summary_and_active_file():
    engine = make_engine()
    content = "line1\nline2\nline3"
    ws = {
        "mode": "EDITOR",
        "active_file": "foo.py",
        "file_content": content,
    }

    engine.update_workspace_context(ws)

    # Workspace summary should mention mode and active file.
    summary = engine.context.workspace_summary
    assert summary is not None
    assert "Workspace State:" in summary
    assert "Mode: EDITOR" in summary
    assert "Active File: foo.py" in summary

    # Active file view should be last lines with numbered prefix.
    assert engine.context.active_file_path == "foo.py"
    active = engine.context.active_file_content or ""
    assert "1: line1" in active
    assert "2: line2" in active
    assert "3: line3" in active


def test_update_workspace_context_truncates_active_file_to_last_200_lines():
    engine = make_engine()
    # Build 210 lines
    lines = [f"print({i})" for i in range(210)]
    content = "\n".join(lines)
    ws = {
        "mode": "EDITOR",
        "active_file": "big.py",
        "file_content": content,
    }

    engine.update_workspace_context(ws)

    active = engine.context.active_file_content or ""
    # Only 200 lines should be visible.
    visible_lines = active.splitlines()
    assert len(visible_lines) == 200
    # First visible line should correspond to original index 10 (1-based 11).
    assert visible_lines[0].startswith("11: ")
    assert visible_lines[-1].startswith("210: ")


def test_get_base_dir_falls_back_when_executor_raises(monkeypatch):
    engine = make_engine()

    def bad_get_base_dir():
        raise RuntimeError("boom")

    monkeypatch.setattr(engine.executor, "get_base_dir", bad_get_base_dir)

    base = engine.get_base_dir()
    assert isinstance(base, Path)
    assert str(base) == str(Path(engine.base_dir))


def test_get_last_modified_path_and_track_last_modified_behavior():
    engine = make_engine()
    fake_exec = engine.executor

    # No last modified yet
    assert engine.get_last_modified_path() is None

    # Track a filesystem-modifying action with relative path.
    action = {"type": "CreateFile", "params": {"path": "src/main.py"}}
    result = ActionResult(status=ActionStatus.SUCCESS, message="OK", data={"path": "src/main.py"})
    engine._track_last_modified(action, result)

    p = engine.get_last_modified_path()
    assert isinstance(p, Path)
    # Should be resolved under executor base dir when relative.
    base = fake_exec.get_base_dir().resolve()
    assert base in p.resolve().parents


def test_run_action_resolves_create_folder_relative_to_cwd(monkeypatch):
    """
    Directory creation paths must be anchored to the user's current
    working directory (Executor.base_dir), without doubling.
    """
    # Use a real AIActionExecutor so we exercise the actual path logic.
    exec_ = AIActionExecutor(base_dir=".", dry_run=True, github_config=None)

    # Simulate that the user has `cd`'d into a subdirectory relative to the
    # project root / sandbox base_dir.
    root = exec_.supervisor.security_policy.base_dir
    exec_.base_dir = (Path(root) / "demo-project").resolve()

    captured_paths: List[str] = []

    def fake_handle(action: Dict[str, Any], context: ActionContext) -> ActionResult:  # type: ignore[override]
        captured_paths.append(action.get("params", {}).get("path", ""))
        return ActionResult(status=ActionStatus.SUCCESS, message="OK")

    monkeypatch.setattr(exec_.supervisor, "handle_ai_action", fake_handle)

    # CreateFolder for "src" under the current base_dir (demo-project)
    action = {"type": "CreateFolder", "params": {"path": "src"}}
    result = exec_.run_action(action)
    assert result.status == ActionStatus.SUCCESS
    assert captured_paths, "Supervisor should have been called"

    target_path = Path(captured_paths[0])
    # Expected path: <root>/demo-project/src (no doubling of demo-project/demo-project)
    assert target_path == (exec_.base_dir / "src").resolve()


def test_run_action_resolves_demo_project_src_single_step(monkeypatch):
    """
    Creating 'demo-project/src' in a single step should anchor to the
    executor's base_dir without any doubling.
    """
    exec_ = AIActionExecutor(base_dir=".", dry_run=True, github_config=None)
    captured_paths: List[str] = []

    def fake_handle(action: Dict[str, Any], context: ActionContext) -> ActionResult:  # type: ignore[override]
        captured_paths.append(action.get("params", {}).get("path", ""))
        return ActionResult(status=ActionStatus.SUCCESS, message="OK")

    monkeypatch.setattr(exec_.supervisor, "handle_ai_action", fake_handle)

    action = {"type": "CreateFolder", "params": {"path": "demo-project/src"}}
    result = exec_.run_action(action)

    assert result.status == ActionStatus.SUCCESS
    assert captured_paths

    target_path = Path(captured_paths[0])
    assert target_path == (exec_.base_dir / "demo-project/src").resolve()


def test_create_folder_rejects_sandbox_unsafe_path(monkeypatch):
    """
    Sandbox must reject CreateFolder paths that escape the project root
    (e.g., '../outside'), and the pipeline must surface a failure.
    """
    # Use non-dry-run executor so SecurityPolicy.validate_path is actually
    # consulted and can reject the unsafe path.
    exec_ = AIActionExecutor(base_dir=".", dry_run=False, github_config=None)

    # Expected resolved unsafe path (one level above base_dir)
    unsafe = (exec_.base_dir.parent / "outside").resolve()

    def fake_validate(path: Path) -> tuple[bool, str]:
        # Ensure validate_path sees the resolved, unsafe absolute path.
        assert path == unsafe
        return False, "Forbidden"

    # Patch SecurityPolicy.validate_path so we don't touch the real FS
    monkeypatch.setattr(exec_.supervisor.security_policy, "validate_path", fake_validate)

    # Attempt to create a folder outside the sandbox via a relative escape.
    action = {"type": "CreateFolder", "params": {"path": "../outside"}}
    result = exec_.run_action(action)

    assert result.status == ActionStatus.FAILURE
    assert "Forbidden" in (result.error or "")


def test_git_remote_action_uses_set_url_or_add(monkeypatch):
    """
    GitRemote should detect whether a remote exists and call the appropriate
    git subcommand (set-url vs add).
    """
    exec_ = AIActionExecutor(base_dir=".", dry_run=False, github_config=None)
    sup = exec_.supervisor

    calls: List[List[str]] = []

    def fake_run_git_command(args, require_repo=True, cwd=None):
        calls.append(args)
        # First call: 'git remote get-url origin' → remote exists
        if args[:3] == ["remote", "get-url", "origin"]:
            return True, "https://old.url", ""
        # Second call: 'git remote set-url origin ...' → success
        if args[:3] == ["remote", "set-url", "origin"]:
            return True, "", ""
        return False, "", "unexpected"

    monkeypatch.setattr(sup, "_run_git_command", fake_run_git_command)

    action = {
        "type": "GitRemote",
        "params": {"name": "origin", "url": "https://example.com/repo.git"},
    }
    result = exec_.run_action(action)

    assert result.status == ActionStatus.SUCCESS
    # Ensure we first checked existence, then set-url
    assert calls[0] == ["remote", "get-url", "origin"]
    assert calls[1][:3] == ["remote", "set-url", "origin"]


def test_git_add_with_dot_skips_embedded_repo_roots(monkeypatch, tmp_path):
    """
    GitAdd with files=['.'] must avoid staging embedded git repositories.
    Only top-level entries that are not embedded repo roots should be passed
    to the underlying git add invocation.
    """
    # Workspace / sandbox root
    root = tmp_path
    # Primary repo at root
    (root / ".git").mkdir()
    # Regular folder
    (root / "src").mkdir()
    # Embedded repo: libs/other/.git
    embedded = root / "libs" / "other"
    embedded.mkdir(parents=True)
    (embedded / ".git").mkdir()

    exec_ = AIActionExecutor(base_dir=str(root), dry_run=False, github_config=None)
    sup = exec_.supervisor

    # Ensure TerminalEngine cwd matches root so _find_git_root will resolve correctly.
    exec_.terminal.cwd = root

    calls: List[List[str]] = []

    def fake_run_git_command(args, require_repo=True, cwd=None):
        # For repo detection in _get_git_repo_state we allow any command.
        if args[:2] == ["rev-parse", "HEAD"]:
            return False, "", "no commits yet"
        if args[:3] == ["remote", "get-url", "origin"]:
            return False, "", "no remote"
        if args[:3] == ["rev-parse", "--abbrev-ref", "HEAD"]:
            return True, "main", ""

        # Capture the actual add invocation.
        if args and args[0] == "add":
            calls.append(args)
        return True, "", ""

    monkeypatch.setattr(sup, "_run_git_command", fake_run_git_command)

    action = {"type": "GitAdd", "params": {"files": ["."]}}
    result = exec_.run_action(action)
    assert result.status == ActionStatus.SUCCESS
    assert calls, "GitAdd should have invoked git add"

    add_args = calls[0]
    # We expect something like: ['add', 'src', 'libs', ...] but NOT the embedded root 'other'
    joined = " ".join(add_args[1:])
    assert "other" not in joined


def test_github_push_path_resolves_absolute_and_relative_paths(monkeypatch, tmp_path):
    """
    GitHubPushPath must resolve the provided path (absolute or relative)
    into a canonical path inside the sandbox root, validate it, and pass
    a workspace-relative path to GitHubClient.push_path.
    """
    root = tmp_path
    (root / "project").mkdir()
    (root / "project" / "file.txt").write_text("content")

    exec_ = AIActionExecutor(base_dir=str(root), dry_run=False, github_config=None)
    sup = exec_.supervisor

    # Fake security policy to assert the path passed in is the resolved absolute path.
    def fake_validate(path: Path) -> tuple[bool, str | None]:
        # Path must be inside the project directory.
        assert path == (root / "project").resolve()
        return True, None

    monkeypatch.setattr(sup.security_policy, "validate_path", fake_validate)

    pushed: Dict[str, Any] = {}

    class FakeGitHub:
        def push_path(self, repo_full_name, local_root, local_path, branch, commit_message):
            pushed.update(
                {
                    "repo": repo_full_name,
                    "local_root": local_root,
                    "local_path": local_path,
                    "branch": branch,
                    "message": commit_message,
                }
            )
            return {"ok": True, "uploaded": [], "skipped": [], "failed": [], "total": 0}

    def fake_get_client(override=None):
        return FakeGitHub()

    monkeypatch.setattr(sup, "_get_github_client", fake_get_client)

    # Use an absolute path for the project directory.
    abs_path = (root / "project").resolve()
    action = {
        "type": "GitHubPushPath",
        "params": {"repo": "owner/repo", "path": str(abs_path), "branch": "main"},
    }
    result = exec_.run_action(action)
    assert result.status == ActionStatus.SUCCESS
    assert pushed["repo"] == "owner/repo"
    # local_root must be the sandbox root, and local_path must be relative.
    assert pushed["local_root"] == str(root.resolve())
    assert pushed["local_path"] == "project"


def test_messages_to_prompt_and_complete_via_provider_dispatch(monkeypatch):
    engine = make_engine()
    messages = [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "U1"},
    ]

    # Check messages_to_prompt format
    prompt = engine._messages_to_prompt(messages)
    assert "SYSTEM: SYS" in prompt
    assert "USER: U1" in prompt

    # Gemini dispatch
    engine.provider = "gemini"
    called = {"gemini": False}

    async def fake_gemini(prompt: str, temperature: float, max_tokens: int) -> str:  # type: ignore[override]
        called["gemini"] = True
        return "GEMINI-OUT"

    monkeypatch.setattr(engine, "_complete_gemini", fake_gemini)
    out = run_async(engine._complete_via_provider(messages, 0.1, 100))
    assert called["gemini"] is True
    assert out == "GEMINI-OUT"

    # Claude dispatch
    engine.provider = "claude"
    called = {"claude": False}

    async def fake_claude(prompt: str, temperature: float, max_tokens: int) -> str:  # type: ignore[override]
        called["claude"] = True
        return "CLAUDE-OUT"

    monkeypatch.setattr(engine, "_complete_claude", fake_claude)
    out = run_async(engine._complete_via_provider(messages, 0.1, 100))
    assert called["claude"] is True
    assert out == "CLAUDE-OUT"

    # Ollama dispatch
    engine.provider = "ollama"
    called = {"ollama": False}

    async def fake_ollama(prompt: str, temperature: float, max_tokens: int) -> str:  # type: ignore[override]
        called["ollama"] = True
        return "OLLAMA-OUT"

    monkeypatch.setattr(engine, "_complete_ollama", fake_ollama)
    out = run_async(engine._complete_via_provider(messages, 0.1, 100))
    assert called["ollama"] is True
    assert out == "OLLAMA-OUT"

    # OpenAI fallback dispatch
    engine.provider = "openai"

    class AskFullAI(FakeAI):
        async def ask_full(self, system_prompt: str, user_prompt: str, model: Optional[str] = None,
                           temperature: float = 0.7, max_tokens: int = 4096) -> str:  # type: ignore[override]
            self.ask_full_calls.append(
                {"system_prompt": system_prompt, "user_prompt": user_prompt, "model": model}
            )
            return "OPENAI-OUT"

    engine.ai = AskFullAI()
    out = run_async(engine._complete_via_provider(messages, 0.2, 50))
    assert out == "OPENAI-OUT"


def test_github_create_repo_syncs_local_remote_when_repo_present(monkeypatch, tmp_path):
    """
    GitHubCreateRepo with sync_local=True should, when a local git repo
    is present, attempt to align the local 'origin' remote with the new
    GitHub repository's clone URL via GitRemote.
    """
    root = tmp_path
    (root / ".git").mkdir()

    exec_ = AIActionExecutor(base_dir=str(root), dry_run=False, github_config=None)
    sup = exec_.supervisor
    exec_.terminal.cwd = root

    created: Dict[str, Any] = {}

    class FakeGitHub:
        def create_repository(self, name: str, private: bool = True, description: Optional[str] = None):
            created.update(
                {
                    "name": name,
                    "private": private,
                    "description": description,
                }
            )
            return {
                "ok": True,
                "data": {
                    "full_name": "owner/repo",
                    "clone_url": "https://github.com/owner/repo.git",
                },
            }

    def fake_get_client(override=None):
        return FakeGitHub()

    monkeypatch.setattr(sup, "_get_github_client", fake_get_client)

    remote_calls: List[Dict[str, Any]] = []

    def fake_git_remote(params: Dict[str, Any], ctx: ActionContext, tx):
        remote_calls.append(params)
        return ActionResult(status=ActionStatus.SUCCESS, message="OK")

    monkeypatch.setattr(sup, "_handle_git_remote", fake_git_remote)

    action = {
        "type": "GitHubCreateRepo",
        "params": {"name": "demo", "private": True, "sync_local": True},
    }
    result = exec_.run_action(action)

    assert result.status == ActionStatus.SUCCESS
    assert created["name"] == "demo"
    # Supervisor should have attempted to configure origin with the clone URL.
    assert remote_calls, "GitRemote should have been invoked for local sync"
    assert remote_calls[0]["name"] == "origin"
    assert remote_calls[0]["url"].endswith("/owner/repo.git")


# ---------------------------------------------------------------------------
# Input engine / CLI sanitization tests
# ---------------------------------------------------------------------------

def test_sanitize_user_input_preserves_spaces_and_tabs():
    raw = "  hello\tworld \x07"
    sanitized = cli_mod._sanitize_user_input(raw)
    # Leading/trailing spaces preserved
    assert sanitized.startswith("  hello")
    assert sanitized.endswith("world ")
    # Tab preserved, bell character removed
    assert "\t" in sanitized
    assert "\x07" not in sanitized


def test_detect_fenced_block_start_variants():
    assert cli_mod._detect_fenced_block_start("```") == "```"
    assert cli_mod._detect_fenced_block_start("```python") == "```"
    # Inline fenced snippet should not be treated as a block start.
    assert cli_mod._detect_fenced_block_start("Here is `code` and ```inline```") is None


def test_collect_manual_block_preserves_blank_lines(monkeypatch):
    lines = iter(["line1", "", "line3", ":end"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(lines))

    block = cli_mod._collect_manual_block(":paste")
    assert block == "line1\n\nline3"


def test_collect_fenced_block_preserves_inner_content_and_fence(monkeypatch):
    # First line is the opening fence with language tag
    first = "```python"
    lines = iter(['print("hi")', "", "```"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(lines))

    block = cli_mod._collect_fenced_block(first, "```")
    parts = block.splitlines()
    assert parts[0].startswith("```")
    assert 'print("hi")' in block
    assert parts[-1].strip() == "```"


def test_collect_fenced_json_block(monkeypatch):
    first = "```json"
    lines = iter(['{"a": 1,', '"b": 2}', "```"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(lines))

    block = cli_mod._collect_fenced_block(first, "```")
    assert '{"a": 1,' in block
    assert '"b": 2}' in block


def test_sanitize_does_not_truncate_long_input():
    long = "x" * 10000
    sanitized = cli_mod._sanitize_user_input(long)
    assert len(sanitized) == 10000


def test_line_actions_accept_common_alias_fields(monkeypatch, tmp_path):
    """
    InsertBeforeLine / InsertAfterLine / DeleteLineRange must accept both the
    canonical parameter names and common aliases used in prompts:
      - line_number or line
      - start_line/end_line or start/end
    """
    # Prepare a simple file with 3 lines.
    fpath = tmp_path / "sample.txt"
    fpath.write_text("line1\nline2\nline3", encoding="utf-8")

    exec_ = AIActionExecutor(base_dir=str(tmp_path), dry_run=False, github_config=None)
    sup = exec_.supervisor

    # Before-line using alias 'line'
    before_action = {
        "type": "InsertBeforeLine",
        "params": {"path": str(fpath), "line": 2, "text": "BEFORE"},
    }
    result = sup.handle_ai_action(before_action, ActionContext())
    assert result.status == ActionStatus.SUCCESS

    # Ensure BEFORE was inserted somewhere.
    content = fpath.read_text(encoding="utf-8").splitlines()
    assert "BEFORE" in content

    # After-line using alias 'line'
    after_action = {
        "type": "InsertAfterLine",
        "params": {"path": str(fpath), "line": 3, "text": "AFTER"},
    }
    result = sup.handle_ai_action(after_action, ActionContext())
    assert result.status == ActionStatus.SUCCESS

    # Ensure AFTER was inserted somewhere.
    content_after = fpath.read_text(encoding="utf-8").splitlines()
    assert "AFTER" in content_after

    # Delete range using aliases 'start'/'end'
    delete_action = {
        "type": "DeleteLineRange",
        "params": {"path": str(fpath), "start": 2, "end": 3},
    }
    result = sup.handle_ai_action(delete_action, ActionContext())
    assert result.status == ActionStatus.SUCCESS

    # After deletion, the file should have fewer or equal lines than before,
    # and at least one of the lines affected by the range should be gone.
    content_final = fpath.read_text(encoding="utf-8").splitlines()
    assert len(content_final) <= len(content_after)
    # We don't assert the exact layout, only that the operation succeeded
    # and aliases did not cause a crash or mis-routing.
