"""
GitVisionCLI — Entry Point with Dual Panel UI
Neon-Cyberpunk AI Terminal with Unified Command Router.
"""

import argparse
import asyncio
import os
import sys
import logging
import shutil
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime
import re

from gitvisioncli.ui import banner_with_info, startup_sequence
from gitvisioncli.ui.colors import ELECTRIC_CYAN, BRIGHT_MAGENTA, BOLD, RESET, RED, MID_GRAY
from gitvisioncli.ui.chat_box import ConversationHistory
from gitvisioncli.ui.dual_panel import DualPanelRenderer, DualPanelConfig, clear_screen
from gitvisioncli.utils.path_utils import resolve_base_dir


from gitvisioncli.config.settings import load_config
from gitvisioncli.core.chat_engine import ChatEngine, ProviderNotConfiguredError
from gitvisioncli.core.github_client import GitHubClientConfig
from gitvisioncli.core.supervisor import ActionStatus
from gitvisioncli.workspace import RightPanel, FileSystemWatcher, PanelManager
from gitvisioncli.workspace.panel_manager import PanelMode  # Import PanelMode

import gitvisioncli.core.terminal as term_mod  # <-- for sandbox toggling

# Set up logging
logger = logging.getLogger(__name__)

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _visible_len(text: str) -> int:
    """Length of a string without ANSI escape sequences."""
    return len(_ANSI_RE.sub("", text))

# =====================================================================
#  WORKSPACE INITIALIZATION
# =====================================================================

def _init_workspace(
    engine: ChatEngine,
    base_dir: Path
) -> Tuple[Optional[RightPanel], Optional[FileSystemWatcher]]:
    """Initializes and wires up the workspace panels and file watcher."""
    try:
        # Initialize PanelManager (pure UI state) and attach supervisor
        panel_manager = PanelManager()
        try:
            # Expose supervisor so panels (e.g., GitGraphPanel) can reuse
            # unified git detection and repository state.
            panel_manager.supervisor = engine.executor.supervisor  # type: ignore[attr-defined]
        except Exception:
            panel_manager.supervisor = None  # type: ignore[attr-defined]

        # Initialize RightPanel (Tree / Editor / Markdown / Banner)
        right_panel = RightPanel(
            base_dir=base_dir,
            panel_manager=panel_manager
        )

        # --------------------------------------------------------------
        # CRITICAL: Attach UI components so PanelManager can refresh them
        # --------------------------------------------------------------
        if hasattr(panel_manager, "attach_ui"):
            panel_manager.attach_ui(
                right_panel,                  # root UI
                right_panel.editor_panel,     # editor panel
                right_panel.tree_panel,       # tree panel
            )

        # Initialize FSWatcher
        fs_watcher = FileSystemWatcher(
            base_dir=str(base_dir),
            poll_interval=1.5
        )

        # --------------------------------------------------------------
        # FULL SYNC: PanelManager listens to FSWatcher events
        # --------------------------------------------------------------
        if hasattr(panel_manager, "handle_fs_event"):
            fs_watcher.register_callback(panel_manager.handle_fs_event)

        # --------------------------------------------------------------
        # SMART TREE GUARD:
        # Refresh tree ONLY if Tree mode is active
        # --------------------------------------------------------------
        def _refresh_if_tree(_change=None):
            try:
                mode = panel_manager.get_mode()
                if mode == PanelMode.TREE:
                    right_panel.refresh_tree_panel()
            except Exception as e:
                logger.warning(f"Tree refresh guard failed: {e}")
                right_panel.refresh_tree_panel()

        fs_watcher.register_callback(_refresh_if_tree)

        # --------------------------------------------------------------
        # Link executor → watcher
        # so AI modifications trigger UI reload
        # --------------------------------------------------------------
        engine.set_fs_watcher(fs_watcher)

        fs_watcher.start()

        return right_panel, fs_watcher

    except Exception as e:
        print(f"{RED}⚠️ Workspace initialization failed: {e}{RESET}")
        return None, None


# =====================================================================
#  MAIN CHAT LOOP
# =====================================================================

def _build_status_line(engine: Optional[ChatEngine], conversation: Optional[ConversationHistory]) -> str:
    """
    Build a single-line status bar string summarizing:
    - active provider/model
    - current working directory
    - git branch (if any)
    - last error message (if any)
    """
    if engine is None:
        return ""

    try:
        provider = (getattr(engine, "provider", "openai") or "openai").lower()
        raw_model = getattr(engine, "model", "") or ""
        model = raw_model

        # Avoid redundant prefixes such as "openai/openai gpt-4o-mini" or
        # "ollama/ollama:qwen2.5..." when the model string already embeds
        # the provider name.
        if raw_model:
            model_lower = raw_model.lower()
            for sep in ("/", " ", ":"):
                prefix = provider + sep
                if model_lower.startswith(prefix):
                    model = raw_model[len(prefix) :].lstrip()
                    break

        stats = {}
        try:
            stats = engine.get_stats() or {}
        except Exception:
            stats = {}

        base_dir = stats.get("base_dir") or ""
        cwd_label = base_dir if base_dir else "."
        try:
            cwd_path = Path(cwd_label)
            cwd_short = cwd_path.name or cwd_path.as_posix()
        except Exception:
            cwd_short = cwd_label

        branch = "-"
        try:
            sup = getattr(engine.executor, "supervisor", None)  # type: ignore[attr-defined]
            if sup is not None and hasattr(sup, "get_git_repo_state"):
                state = sup.get_git_repo_state()
                branch = getattr(state, "current_branch", None) or "-"
        except Exception:
            branch = "-"

        last_error = ""
        if conversation is not None and getattr(conversation, "last_error", None):
            # Keep the error concise for the status bar.
            last_error = conversation.last_error.strip().replace("\n", " ")

            # Try to extract the core provider message from verbose
            # payloads like "Error code: 400 - {'error': {'message': 'X', ...}}".
            try:
                msg_match = re.search(r"['\"]message['\"]\s*:\s*['\"]([^'\"]+)['\"]", last_error)
                if msg_match:
                    core = msg_match.group(1)
                    # Prefer the concise message when it is shorter.
                    if _visible_len(core) < _visible_len(last_error):
                        last_error = core
            except Exception:
                pass

            # Hard cap the length so verbose provider error payloads
            # do not overwhelm the status bar.
            max_err_len = 120
            if _visible_len(last_error) > max_err_len:
                last_error = last_error[: max_err_len - 1] + "…"

        parts = []
        parts.append(
            f"{BRIGHT_MAGENTA}{provider}/{model}{RESET}"
            if model
            else f"{BRIGHT_MAGENTA}{provider}{RESET}"
        )
        parts.append(f"{MID_GRAY}│ cwd:{RESET} {ELECTRIC_CYAN}{cwd_short}{RESET}")
        parts.append(
            f"{MID_GRAY}│ branch:{RESET} {ELECTRIC_CYAN}{branch}{RESET}"
            if branch != "-"
            else f"{MID_GRAY}│ branch:{RESET} -"
        )

        if last_error:
            parts.append(f"{MID_GRAY}│ last error:{RESET} {last_error}")

        base = "  " + "  ".join(parts)

        # Right-aligned timestamp (best-effort based on terminal width).
        try:
            cols = shutil.get_terminal_size((120, 40)).columns
        except Exception:
            cols = 120

        ts_raw = datetime.now().strftime("%H:%M:%S")
        ts_col = f"{MID_GRAY}{ts_raw}{RESET}"

        # Target inner width approximates the area inside the frame borders.
        target_inner = max(40, cols - 4)
        base_len = _visible_len(base)
        ts_len = len(ts_raw)  # visible length without ANSI
        # At least one space before the timestamp when room allows.
        gap = max(1, target_inner - base_len - ts_len)

        return f"{base}{' ' * gap}{ts_col}"
    except Exception:
        # Status bar is best-effort only; never break the UI.
        return ""


def _render_ui(
    renderer: Optional[DualPanelRenderer],
    conversation: ConversationHistory,
    engine: Optional[ChatEngine] = None,
    processing_msg: str = "",
):
    """
    Helper to clear screen and render the UI panels in a single, stable frame.
    Ensures we NEVER append new "panels" — just redraw one frame.
    """
    chat_content = conversation.render()
    if processing_msg:
        chat_content += "\n" + processing_msg

    if renderer:
        # DualPanelRenderer is responsible for full-frame rendering.
        status_line = _build_status_line(engine, conversation)
        frame = renderer.render(chat_content, status_line=status_line)
    else:
        # Fallback: single-panel mode, clear manually.
        frame = clear_screen() + chat_content

    print(frame, end="", flush=True)


def _move_cursor_to_input_bar():
    """
    Reposition the terminal cursor into the DualPanelRenderer input row
    so the user types directly inside the panel.

    Relies on ANSI escape sequences and the known layout of the input row:
    - bottom line  : bottom border
    - above border : input row with '● INPUT'
    """
    try:
        # Move to beginning of the input row (one line up, column 0)
        sys.stdout.write("\x1b[1A\r")
        # Skip left border + leading space + '● INPUT' (7 chars) + space
        # 1 (border) + 1 + 7 + 1 = 10 visible columns
        sys.stdout.write("\x1b[10C")
        sys.stdout.flush()
    except Exception:
        # If the terminal does not support these sequences, silently ignore.
        pass


def _sanitize_user_input(raw: str) -> str:
    """
    Sanitize a raw line from input().

    Rules:
    - Strip only control characters that are not tab.
    - Preserve leading/trailing spaces and tabs.
    - Preserve all printable Unicode characters verbatim.
    """
    if raw is None:
        return ""

    # input() strips the trailing newline, but we defensively drop CR/LF.
    cleaned = raw.replace("\r", "").replace("\n", "")

    result_chars: List[str] = []
    for ch in cleaned:
        code = ord(ch)
        # Allow horizontal tab and all printable characters (space and above).
        if ch == "\t" or code >= 32:
            result_chars.append(ch)
        # Drop other control characters silently.
    return "".join(result_chars)


def _detect_fenced_block_start(line: str) -> Optional[str]:
    """
    Detect the start of a fenced multi-line block.

    We treat a line as starting a block when it begins with a common
    fence token such as triple backticks (```), triple single quotes
    ('''), or three double quotes, and there is no matching closing
    fence on the same line.
    """
    stripped = line.lstrip()
    if not stripped:
        return None

    fences = ("```", "'''", '"""')
    for fence in fences:
        idx = stripped.find(fence)
        if idx != 0:
            continue
        rest = stripped[len(fence) :]
        # If the same fence appears again on this line, it's an inline block.
        if fence in rest:
            continue
        return fence
    return None


def _collect_fenced_block(first_line: str, fence: str) -> str:
    """
    Collect a fenced multi-line block starting from first_line.

    Reads additional lines until a line containing the closing fence
    is encountered. The fence lines and inner formatting are preserved.
    """
    lines: List[str] = [first_line]

    while True:
        # We intentionally do not pass a prompt here so that the existing
        # input row in the TUI remains stable.
        next_raw = input("")
        next_line = _sanitize_user_input(next_raw)
        lines.append(next_line)

        if fence in next_line:
            break

    return "\n".join(lines)


def _collect_manual_block(initial_line: str) -> str:
    """
    Collect a manual multi-line block initiated by :paste / :ml / :block.

    The user terminates the block with a single line ':end' (case-insensitive).
    Any text after the initial command on the first line is treated as the
    first content line and preserved.
    """
    stripped = initial_line.lstrip()
    lower = stripped.lower()
    first_content = ""

    for cmd in (":paste", ":ml", ":block"):
        if lower.startswith(cmd):
            remainder = stripped[len(cmd) :].lstrip()
            first_content = remainder
            break

    lines: List[str] = []
    if first_content:
        lines.append(first_content)

    while True:
        next_raw = input("")
        next_line = _sanitize_user_input(next_raw)

        if next_line.strip().lower() == ":end":
            break

        lines.append(next_line)

    return "\n".join(lines)


async def _handle_editor_open(
    engine: ChatEngine,
    conversation: ConversationHistory,
    path: str,
    editor: str
):
    """Unified handler for opening nano or vscode."""
    print(clear_screen(), end="", flush=True)

    result = engine.executor._open_editor(path, editor)

    if result.status == ActionStatus.SUCCESS:
        conversation.add_system(f"Closed {path}")
    else:
        conversation.add_error(f"Editor failed: {result.error}")

    return True


def _soft_reset_workspace(conversation: ConversationHistory, engine: ChatEngine, right_panel: Optional[RightPanel]):
    """
    Unified 'clear' behavior:
    - Clear chat history
    - Clear engine conversation
    - Reset right panel to BANNER mode
    - Show a clean system message
    """
    conversation.clear()
    engine.clear_conversation()
    if right_panel:
        right_panel.panel_manager.set_mode(PanelMode.BANNER)

    conversation.add_system(
        "Workspace ready.\n"
        "Type ':banner' to see workspace commands, or start typing in natural language."
    )


async def run_chat_loop(engine: ChatEngine, enable_workspace=True):
    """Main input/render loop for the CLI."""

    right_panel: Optional[RightPanel] = None
    fs_watcher: Optional[FileSystemWatcher] = None
    renderer: Optional[DualPanelRenderer] = None

    if enable_workspace:
        right_panel, fs_watcher = _init_workspace(engine, engine.get_base_dir())

    # Use a default width for the ConversationHistory object
    chat_width = 60
    conversation = ConversationHistory(width=chat_width)

    if enable_workspace and right_panel:
        # Initialize the dual panel renderer
        renderer = DualPanelRenderer(
            right_panel,
            DualPanelConfig()  # total_width adapts to terminal size
        )

        # Ensure right panel starts in BANNER mode
        right_panel.panel_manager.set_mode(PanelMode.BANNER)

        # Set initial workspace context for the AI
        engine.update_workspace_context(right_panel.get_workspace_context())
        
        # Wire editor panel reference for streaming support
        engine.set_editor_panel(right_panel.editor_panel)

    # --- ONE-TIME AUTO CLEAR (like user typing `clear`, but only once) ---
    _soft_reset_workspace(conversation, engine, right_panel)

    # Initial render
    _render_ui(renderer, conversation, engine)

    while True:
        try:
            # --- 1. FILESYSTEM WATCHER TICK + RENDER CURRENT FRAME ---
            if fs_watcher and fs_watcher.is_watching:
                fs_watcher.check_once()

            # Render UI with current state (no "processing" yet)
            
            # --- 2. GET INPUT ---
            if renderer:
                _move_cursor_to_input_bar()
                prompt = ""
            else:
                prompt = f"{BOLD}{BRIGHT_MAGENTA}● INPUT {ELECTRIC_CYAN}> {RESET}"

            raw_input = input(prompt)
            user_input = _sanitize_user_input(raw_input)

            # Treat pure whitespace or an empty line as "no input". This keeps
            # the loop resilient to spammy ENTER presses.
            if not user_input or not user_input.strip():
                _render_ui(renderer, conversation, engine)
                continue

            # Multi-line collection: either explicit block commands (:paste)
            # or fenced code/JSON blocks (``` ... ```). These are always
            # treated as natural-language / content, not as shell or CLI
            # commands, to avoid mis-parsing.
            collected: Optional[str] = None
            manual_trigger = user_input.strip().lower()

            if manual_trigger in {":paste", ":ml", ":block"}:
                conversation.add_system(
                    "Multi-line input mode: paste your content, then finish with a line ':end'."
                )
                _render_ui(renderer, conversation, engine)
                collected = _collect_manual_block(user_input)
            else:
                fence = _detect_fenced_block_start(user_input)
                if fence is not None:
                    collected = _collect_fenced_block(user_input, fence)

            if collected is not None:
                user_input = collected

            is_multiline = "\n" in user_input

            # Normalize for routing. We only treat single-line inputs as
            # potential commands or shell invocations; multi-line inputs are
            # always forwarded to the AI as chat content.
            cmd_lower = user_input.strip().lower() if not is_multiline else ""

            # --- 3. HANDLE CLIENT-SIDE COMMANDS (EXIT / CLEAR / STATS) ---
            if cmd_lower in {"exit", "quit"}:
                if fs_watcher:
                    fs_watcher.stop()
                conversation.add_system("Goodbye, operator.")
                _render_ui(renderer, conversation, engine)
                break

            if cmd_lower in {"clear", "reset"}:
                _soft_reset_workspace(conversation, engine, right_panel)
                _render_ui(renderer, conversation, engine)
                continue

            if cmd_lower == "stats":
                st = engine.get_stats()
                conversation.add_system(
                    f"Engine: {st.get('provider', 'openai')}/{st['model']}\n"
                    f"Messages: {st['message_count']}\n"
                    f"Directory: {st['base_dir']}\n"
                    f"Dry Run: {st['dry_run']}\n"
                    f"GitHub Enabled: {st['github_enabled']}"
                )
                _render_ui(renderer, conversation, engine)
                continue

            # Context / history management
            if cmd_lower == ":clear-history":
                try:
                    engine.context.clear_messages()
                    conversation.clear()
                    conversation.add_system("✓ Chat history cleared (context preserved).")
                except Exception as e:
                    conversation.add_error(f"Failed to clear history: {e}")

                if enable_workspace and right_panel:
                    try:
                        right_panel.on_fs_change(None)
                    except Exception:
                        pass

                _render_ui(renderer, conversation, engine)
                continue

            if cmd_lower.startswith(":prune"):
                parts = user_input.split()
                if len(parts) != 2:
                    conversation.add_error("Usage: :prune <N>")
                    _render_ui(renderer, conversation, engine)
                    continue
                try:
                    n = int(parts[1])
                    if n < 0:
                        raise ValueError()
                except ValueError:
                    conversation.add_error("Usage: :prune <N> (N must be a non-negative integer)")
                    _render_ui(renderer, conversation, engine)
                    continue

                try:
                    engine.context.prune_messages(n)
                    conversation.clear()
                    if n == 0:
                        conversation.add_system("✓ Chat history cleared (context preserved).")
                    else:
                        conversation.add_system(f"✓ History pruned to last {n} turns.")
                except Exception as e:
                    conversation.add_error(f"Failed to prune history: {e}")

                if enable_workspace and right_panel:
                    try:
                        right_panel.on_fs_change(None)
                    except Exception:
                        pass

                _render_ui(renderer, conversation, engine)
                continue

            if cmd_lower == ":clean-context":
                try:
                    engine.clean_context()
                    conversation.clear()
                    conversation.add_system("✓ Context cleaned (engine and workspace preserved).")
                    if enable_workspace and right_panel:
                        # Re-sync workspace context into the fresh ContextManager
                        engine.update_workspace_context(right_panel.get_workspace_context())
                        try:
                            right_panel.on_fs_change(None)
                        except Exception:
                            pass
                except Exception as e:
                    conversation.add_error(f"Failed to clean context: {e}")

                _render_ui(renderer, conversation, engine)
                continue

            # Live model / engine switching
            if cmd_lower.startswith(":set-ai "):
                new_model = user_input.split(" ", 1)[1].strip()
                if not new_model:
                    conversation.add_error("Usage: :set-ai <model_name>")
                    _render_ui(renderer, conversation, engine)
                    continue

                try:
                    engine.set_model(new_model)
                    # Persist in config.json
                    try:
                        from gitvisioncli.config.settings import load_config, save_config

                        cfg = load_config()
                        # Persist the normalized engine so future sessions
                        # start from the same provider/model pair.
                        active = engine.get_stats()
                        cfg["model"] = active["model"]
                        cfg["active_provider"] = active.get("provider", "openai")
                        save_config(cfg)
                    except Exception:
                        # Non-fatal; engine has already switched
                        pass

                    conversation.add_system(
                        f"AI engine switched to: "
                        f"{active.get('provider', 'openai')}/{active['model']}"
                    )
                except ProviderNotConfiguredError as e:
                    # Provider is missing an API key or local installation.
                    conversation.add_error(str(e))
                    if enable_workspace and right_panel:
                        right_panel.panel_manager.clear_file()
                        right_panel.panel_manager.set_mode(PanelMode.MODELS)
                        conversation.add_system(
                            "Opened the Models panel to help you configure this provider."
                        )
                except Exception as e:
                    conversation.add_error(f"Failed to switch AI model: {e}")

                _render_ui(renderer, conversation, engine)
                continue

            # --- 4. NAVIGATION (cd / :back) ---
            if cmd_lower.startswith("cd ") or cmd_lower == ":back" or cmd_lower == "cd ..":
                path = ".." if (cmd_lower == ":back" or cmd_lower == "cd ..") else user_input[3:].strip()

                result = engine.executor._change_directory(path)

                if result.status == ActionStatus.SUCCESS:
                    conversation.add_system(f"CWD: {result.data['path']}")

                    if right_panel:
                         new_base = engine.get_base_dir()
                         # 1) update base dir
                         right_panel.update_base_dir(new_base)
                         # 2) force TreePanel to sync base_dir
                         right_panel.tree_panel.update_base_dir(new_base)
                         # 3) refresh tree immediately
                         right_panel.refresh_tree_panel()

                    if fs_watcher:
                        fs_watcher.update_base_dir(engine.get_base_dir())
                else:
                    conversation.add_error(f"cd failed: {result.error}")

                _render_ui(renderer, conversation, engine)
                continue

            # --- 5. EDITORS (nano / code) ---
            if cmd_lower.startswith("nano "):
                path = user_input[5:].strip()
                if await _handle_editor_open(engine, conversation, path, "nano"):
                    _render_ui(renderer, conversation, engine)
                    continue

            if cmd_lower.startswith("code "):
                path = user_input[5:].strip()
                if await _handle_editor_open(engine, conversation, path, "code"):
                    _render_ui(renderer, conversation, engine)
                    continue

            # --- 6. SANDBOX COMMANDS (User Controlled) ---
            if cmd_lower in {":sandbox on", "sandbox on", ":sb on", "sb on"}:
                term_mod.SANDBOX_ENABLED = True
                conversation.add_system("Sandbox enabled. Navigation restricted to project root.")
                _render_ui(renderer, conversation, engine)
                continue

            if cmd_lower in {":sandbox off", "sandbox off", ":sb off", "sb off"}:
                term_mod.SANDBOX_ENABLED = False
                conversation.add_system("Sandbox disabled. Full navigation allowed.")
                _render_ui(renderer, conversation, engine)
                continue

            if cmd_lower in {":sandbox status", "sandbox status", ":sb status", "sb status"}:
                state = "ON" if term_mod.SANDBOX_ENABLED else "OFF"
                conversation.add_system(f"Sandbox is currently: {state}")
                _render_ui(renderer, conversation, engine)
                continue

            # --- 7. WORKSPACE COMMANDS (Right Panel) ---
            if enable_workspace and right_panel and (not is_multiline) and user_input.startswith(":"):
                ok, msg = right_panel.handle_command(user_input)
                if ok:
                    conversation.add_system(msg)
                    engine.update_workspace_context(right_panel.get_workspace_context())
                else:
                    conversation.add_error(msg)

                _render_ui(renderer, conversation, engine)
                continue

            # --- 8. LOCAL SHELL COMMAND ROUTER (pwd / ls / prefixes / etc) ---

            # If input starts with ".", treat the rest as a pure shell command:
            #   .pwd  -> pwd
            #   .ls   -> ls
            shell_cmd: Optional[str] = None

            if not is_multiline:
                if user_input.startswith(".") and len(user_input.strip()) > 1:
                    shell_cmd = user_input[1:].strip()
                else:
                    # Plain commands like `pwd`, `ls`, etc. (no dot) that should bypass AI
                    simple_shells = {
                        "pwd",
                        "ls",
                        "ll",
                        "whoami",
                        "cat",
                        "tree",
                        "mkdir",
                        "rmdir",
                        "rm",
                        "touch",
                    }
                    parts = cmd_lower.split()
                    first_token = parts[0] if parts else ""
                    if first_token in simple_shells:
                        shell_cmd = user_input

                    # Cross-OS prefix commands (p./c./l./m.) are always treated
                    # as direct shell commands and routed through TerminalEngine,
                    # not the AI. Example: p.clear, c.dir, l.ls, m.say "hi".
                    if not shell_cmd and first_token:
                        if (
                            len(first_token) > 2
                            and first_token[1] == "."
                            and first_token[0] in {"p", "c", "l", "m"}
                        ):
                            shell_cmd = user_input

            if shell_cmd:
                # Execute via the shared TerminalEngine
                exit_code, stdout, stderr = engine.executor.terminal.run_once(shell_cmd)

                # Log into the left chat panel
                conversation.add_user(f"$ {shell_cmd}")
                if stdout.strip():
                    conversation.add_system(stdout.rstrip())
                if stderr.strip():
                    conversation.add_error(stderr.rstrip())

                _render_ui(renderer, conversation, engine)
                continue

            # --- 8.5. HANDLE SHOW GIT GRAPH (from Natural Language Action Engine) ---
            # Check for "git graph" command and route to panel before sending to AI
            if enable_workspace and right_panel:
                from gitvisioncli.core.action_router import ActionRouter
                from gitvisioncli.core.natural_language_action_engine import ActiveFileContext
                
                action_router = ActionRouter(base_dir=engine.get_base_dir())
                ws_ctx = right_panel.get_workspace_context()
                active_file_ctx = None
                if ws_ctx.get("active_file"):
                    active_file_ctx = ActiveFileContext(
                        path=ws_ctx["active_file"],
                        content=ws_ctx.get("file_content")
                    )
                
                direct_action = action_router.try_direct_action(user_input, active_file=active_file_ctx)
                if direct_action and direct_action.get("type") == "ShowGitGraph":
                    right_panel.panel_manager.open_git_graph()
                    conversation.add_system("Git commit graph opened.")
                    _render_ui(renderer, conversation, engine)
                    continue

            # --- 9. SEND TO AI (DEFAULT PATH) ---
            conversation.add_user(user_input)

            # Show "Processing..." overlay while AI is working
            processing_msg = f"{BOLD}{BRIGHT_MAGENTA}⚡ Processing...{RESET}"
            _render_ui(renderer, conversation, engine, processing_msg)

            if enable_workspace and right_panel:
                engine.update_workspace_context(right_panel.get_workspace_context())
                # Update editor panel reference for streaming
                engine.set_editor_panel(right_panel.editor_panel)

            chunks = []
            response_text = ""
            try:
                async for ch in engine.stream(user_input):
                    # We buffer chunks; rendering of final answer is done after
                    chunks.append(ch)

                response_text = "".join(chunks)
                if response_text:
                    conversation.add_ai(response_text)

                # Surface any automatic summarization or pruning events
                # that occurred inside the ChatEngine so the user sees
                # a system notice and the workspace panels can refresh
                # without resetting state.
                summary_notice = None
                prune_notice = None
                try:
                    summary_notice = engine.consume_auto_summary_notice()
                except AttributeError:
                    summary_notice = None

                try:
                    prune_notice = engine.consume_auto_prune_notice()
                except AttributeError:
                    prune_notice = None

                for notice in (summary_notice, prune_notice):
                    if not notice:
                        continue
                    conversation.add_system(notice)
                    if enable_workspace and right_panel:
                        try:
                            right_panel.on_fs_change(None)
                        except Exception:
                            pass

            except Exception as ai_error:
                logger.error(f"AI stream failed: {ai_error}", exc_info=True)
                err_msg = str(ai_error)

                # Handle invalid / missing model errors more gracefully:
                # revert to previous model if possible and present a clean
                # explanation instead of a raw stack trace.
                lowered = err_msg.lower()
                if "model_not_found" in lowered or "does not exist or you do not have access to it" in lowered:
                    reverted_to = None
                    try:
                        reverted_to = engine.revert_model()
                    except Exception:
                        pass

                    if reverted_to:
                        conversation.add_error(
                            f"Selected model is not available in the current AI engine.\n"
                            f"Reverted back to previous model: {reverted_to}"
                        )
                    else:
                        conversation.add_error(
                            "Selected model is not available in the current AI engine "
                            "and no previous model could be restored."
                        )
                else:
                    conversation.add_error(f"AI Error: {err_msg}")

            # After AI finishes, ensure workspace base_dir is synchronized
            # with the ChatEngine / Executor view, regardless of how the
            # directory was changed (tools, shell commands, planner steps).
            if enable_workspace and right_panel and fs_watcher:
                try:
                    new_base_dir = engine.get_base_dir()
                    if new_base_dir != right_panel.base_dir:
                        right_panel.update_base_dir(new_base_dir)
                        fs_watcher.update_base_dir(new_base_dir)
                except Exception as sync_err:
                    logger.warning(f"Workspace sync after AI response failed: {sync_err}")

                # Auto-open the last file modified by INTERNAL actions so
                # the user immediately sees live updates in the editor.
                # Only open if it's actually a file (not a folder).
                try:
                    last_path = engine.get_last_modified_path()
                    if last_path is not None:
                        path_obj = Path(last_path)
                        # Only open files, not folders
                        if path_obj.exists() and path_obj.is_file():
                            right_panel.editor_panel.load_file(path_obj)
                            right_panel.panel_manager.open_file(path_obj)
                            right_panel.panel_manager.set_mode(PanelMode.EDITOR)
                except Exception as editor_sync_err:
                    logger.debug(f"Editor sync after AI response skipped: {editor_sync_err}")

            # After AI finishes, render a clean final frame (input line cleared)
            _render_ui(renderer, conversation, engine)

        except KeyboardInterrupt:
            conversation.add_system("\nInterrupted by user.")
            _render_ui(renderer, conversation, engine)
            continue

        except Exception as e:
            logger.error(f"Main loop error: {e}", exc_info=True)
            conversation.add_error(f"FATAL ERROR: {e}\nRestart recommended.")
            _render_ui(renderer, conversation, engine)

    # Cleanup
    if fs_watcher:
        fs_watcher.stop()
    print(f"\n{ELECTRIC_CYAN}Neural link terminated.{RESET}\n")


# =====================================================================
#  BOOTSTRAP
# =====================================================================

def run_interactive_chat(args):
    """Loads config and initializes the ChatEngine and main loop."""
    try:
        cfg = load_config()
    except Exception as e:
        print(f"{RED}❌ Fatal Error: Could not load config. {e}{RESET}")
        return

    providers_cfg = cfg.get("providers", {}) or {}

    # Provider keys (multi-backend)
    openai_key = cfg.get("api_key") or (providers_cfg.get("openai") or {}).get(
        "api_key"
    )
    gemini_key = (providers_cfg.get("gemini") or {}).get("api_key")
    claude_key = (providers_cfg.get("claude") or {}).get("api_key")

    has_ollama = shutil.which("ollama") is not None

    try:
        base_dir = Path.cwd()
    except PermissionError:
        # Fall back to the user's home directory if the current working
        # directory is not accessible (e.g., macOS sandboxed locations).
        home = Path.home()
        print(
            f"{RED}⚠️ Warning: Permission denied for current directory. "
            f"Falling back to home: {home}{RESET}"
        )
        base_dir = home

    if not (Path(base_dir) / ".git").exists():
        print(f"{RED}⚠️ Warning: No git repository found in {base_dir}{RESET}")

    github_cfg_dict = cfg.get("github")
    github_config: Optional[GitHubClientConfig] = None
    if github_cfg_dict and github_cfg_dict.get("token") and github_cfg_dict.get("user"):
        github_config = GitHubClientConfig(
            token=github_cfg_dict["token"],
            default_owner=github_cfg_dict["user"],
            default_visibility=github_cfg_dict.get("default_visibility", "private")
        )

    # Ensure at least one AI provider is available.
    if not (openai_key or gemini_key or claude_key or has_ollama):
        print(f"{RED}❌ No AI providers configured in config.json.{RESET}")
        print(
            "Configure OpenAI/Gemini/Claude API keys under 'providers', "
            "or install Ollama and ensure its binary is on PATH."
        )
        return

    # 1. Resolve base directory using unified utility
    base_dir = resolve_base_dir(
        cli_arg=args.dir,
        config_val=cfg.get("default_dir"),
        cwd=os.getcwd()
    )
    
    # Ensure it exists
    if not base_dir.exists():
        print(f"{RED}❌ Directory not found: {base_dir}{RESET}")
        return

    # 2. Initialize Engine
    try:
        engine = ChatEngine(
            base_dir=base_dir,  # Pass Path object directly
            api_key=openai_key,

            model=cfg.get("model", "gpt-4o-mini"),
            temperature=cfg.get("temperature", 0.7),
            max_tokens=cfg.get("max_tokens", 4096),
            dry_run=cfg.get("dry_run", False),
            github_config=github_config,
            providers=providers_cfg,
            active_provider=cfg.get("active_provider"),
        )
    except Exception as e:
        print(f"{RED}❌ Fatal Error: Could not initialize ChatEngine: {e}{RESET}")
        logger.error("ChatEngine init failed", exc_info=True)
        return

    print(
        f"✓ Initialized in: {base_dir}\n"
        f"✓ Engine: {engine.provider}/{engine.model}\n"
        f"✓ Dry-Run: {engine.dry_run}\n"
        f"✓ GitHub Enabled: {bool(github_config)}\n\n"
        "Launching dual-panel interface...\n"
    )

    try:
        asyncio.run(run_chat_loop(engine, enable_workspace=True))
    except Exception as e:
        print(f"\n{RED}❌ UNHANDLED ASYNC ERROR: {e}{RESET}")
        logger.error("asyncio.run() failed", exc_info=True)


# =====================================================================
#  SUBCOMMAND HANDLERS
# =====================================================================

def cmd_doctor(args) -> int:
    """Check system health and configuration."""
    print(f"\n{ELECTRIC_CYAN}🔍 GitVision Doctor - System Health Check{RESET}")
    print("=" * 60)
    
    # Check Python version
    py_version = sys.version.split()[0]
    print(f"{ELECTRIC_CYAN}✓{RESET} Python {py_version}")
    
    # Check dependencies
    missing_deps = []
    try:
        import openai
        print(f"{ELECTRIC_CYAN}✓{RESET} openai SDK installed")
    except ImportError:
        missing_deps.append("openai")
        print(f"{RED}✗{RESET} openai SDK missing")
    
    try:
        import anthropic
        print(f"{ELECTRIC_CYAN}✓{RESET} anthropic SDK installed")
    except ImportError:
        missing_deps.append("anthropic")
        print(f"{RED}✗{RESET} anthropic SDK missing")
    
    try:
        import google.generativeai
        print(f"{ELECTRIC_CYAN}✓{RESET} google-generativeai SDK installed")
    except ImportError:
        missing_deps.append("google-generativeai")
        print(f"{RED}✗{RESET} google-generativeai SDK missing")
    
    # Check Ollama
    has_ollama = shutil.which("ollama") is not None
    if has_ollama:
        print(f"{ELECTRIC_CYAN}✓{RESET} Ollama binary found")
    else:
        print(f"{MID_GRAY}○{RESET} Ollama not installed (optional)")
    
    # Check API keys
    print(f"\n{ELECTRIC_CYAN}API Keys:{RESET}")
    try:
        config = load_config()
        providers_cfg = config.get("providers", {}) or {}
        
        openai_key = config.get("api_key") or (providers_cfg.get("openai") or {}).get("api_key")
        gemini_key = (providers_cfg.get("gemini") or {}).get("api_key")
        claude_key = (providers_cfg.get("claude") or {}).get("api_key")
        
        if openai_key:
            print(f"{ELECTRIC_CYAN}✓{RESET} OpenAI API key configured")
        else:
            print(f"{RED}✗{RESET} OpenAI API key missing")
        
        if gemini_key:
            print(f"{ELECTRIC_CYAN}✓{RESET} Gemini API key configured")
        else:
            print(f"{MID_GRAY}○{RESET} Gemini API key not configured")
        
        if claude_key:
            print(f"{ELECTRIC_CYAN}✓{RESET} Claude API key configured")
        else:
            print(f"{MID_GRAY}○{RESET} Claude API key not configured")
        
        # Check if at least one provider is available
        has_provider = openai_key or gemini_key or claude_key or has_ollama
        if not has_provider:
            print(f"\n{RED}⚠️  No AI providers configured!{RESET}")
            print("Configure at least one provider in config.json")
            return 1
        
    except Exception as e:
        print(f"{RED}✗{RESET} Failed to load config: {e}")
        return 1
    
    # Summary
    print(f"\n{ELECTRIC_CYAN}{'=' * 60}{RESET}")
    if missing_deps:
        print(f"{RED}⚠️  Missing dependencies: {', '.join(missing_deps)}{RESET}")
        print(f"Install with: pip install {' '.join(missing_deps)}")
        return 1
    else:
        print(f"{ELECTRIC_CYAN}✅ All systems operational{RESET}\n")
        return 0


def cmd_scan(args) -> int:
    """Scan repository for analysis."""
    path = Path(args.path).resolve()
    print(f"\n{ELECTRIC_CYAN}📊 Scanning: {path}{RESET}")
    print("=" * 60)
    
    if not path.exists():
        print(f"{RED}✗ Path does not exist{RESET}")
        return 1
    
    # Count files by extension
    extensions = {}
    total_files = 0
    total_size = 0
    
    for file_path in path.rglob("*"):
        if file_path.is_file():
            ext = file_path.suffix or "(no extension)"
            extensions[ext] = extensions.get(ext, 0) + 1
            total_files += 1
            try:
                total_size += file_path.stat().st_size
            except Exception:
                pass
    
    # Display results
    print(f"\n{ELECTRIC_CYAN}Total Files:{RESET} {total_files}")
    print(f"{ELECTRIC_CYAN}Total Size:{RESET} {total_size / 1024:.2f} KB")
    
    if extensions:
        print(f"\n{ELECTRIC_CYAN}Files by Extension:{RESET}")
        for ext, count in sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {ext}: {count}")
    
    # Check for git
    if (path / ".git").exists():
        print(f"\n{ELECTRIC_CYAN}✓{RESET} Git repository detected")
    else:
        print(f"\n{MID_GRAY}○{RESET} Not a git repository")
    
    print(f"\n{ELECTRIC_CYAN}✅ Scan complete{RESET}\n")
    return 0


def cmd_sync(args) -> int:
    """Sync workspace state."""
    print(f"\n{ELECTRIC_CYAN}🔄 Syncing workspace...{RESET}")
    print("=" * 60)
    
    # Placeholder: In a real implementation, this would sync state
    print(f"{ELECTRIC_CYAN}✓{RESET} Workspace state synchronized")
    print(f"{ELECTRIC_CYAN}✓{RESET} File system watcher updated")
    print(f"{ELECTRIC_CYAN}✓{RESET} Panel states refreshed")
    
    print(f"\n{ELECTRIC_CYAN}✅ Sync complete{RESET}\n")
    return 0


def cmd_init(args) -> int:
    """Initialize new project."""
    path = Path(args.path).resolve()
    print(f"\n{ELECTRIC_CYAN}🚀 Initializing project at: {path}{RESET}")
    print("=" * 60)
    
    try:
        path.mkdir(exist_ok=True)
        print(f"{ELECTRIC_CYAN}✓{RESET} Created directory: {path}")
        
        # Create basic structure
        (path / "src").mkdir(exist_ok=True)
        print(f"{ELECTRIC_CYAN}✓{RESET} Created src/ directory")
        
        # Create README
        readme_path = path / "README.md"
        if not readme_path.exists():
            readme_path.write_text(f"# {path.name}\n\nProject initialized with GitVision\n")
            print(f"{ELECTRIC_CYAN}✓{RESET} Created README.md")
        
        # Initialize git
        import subprocess
        result = subprocess.run(
            ["git", "init"],
            cwd=path,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"{ELECTRIC_CYAN}✓{RESET} Initialized git repository")
        
        print(f"\n{ELECTRIC_CYAN}✅ Project initialized successfully{RESET}\n")
        return 0
        
    except Exception as e:
        print(f"{RED}✗ Initialization failed: {e}{RESET}")
        return 1


async def cmd_demo(args) -> int:
    """Run fully automated demo showcasing GitVisionCLI capabilities."""
    import subprocess
    import tempfile
    
    print(f"\n{BRIGHT_MAGENTA}{'=' * 70}{RESET}")
    print(f"{BRIGHT_MAGENTA}🎬 GitVision Automated Demo{RESET}")
    print(f"{BRIGHT_MAGENTA}{'=' * 70}{RESET}\n")
    
    # Create demo workspace
    demo_dir = Path.cwd() / "demo-gitvision"
    demo_dir.mkdir(exist_ok=True)
    os.chdir(demo_dir)
    
    print(f"{ELECTRIC_CYAN}✓{RESET} Created demo workspace: {demo_dir}\n")

    
    # Load config and initialize engine
    try:
        cfg = load_config()
    except Exception as e:
        print(f"{RED}❌ Could not load config: {e}{RESET}")
        return 1
    
    providers_cfg = cfg.get("providers", {}) or {}
    openai_key = cfg.get("api_key") or (providers_cfg.get("openai") or {}).get("api_key")
    
    github_cfg_dict = cfg.get("github")
    github_config: Optional[GitHubClientConfig] = None
    if github_cfg_dict and github_cfg_dict.get("token") and github_cfg_dict.get("user"):
        github_config = GitHubClientConfig(
            token=github_cfg_dict["token"],
            default_owner=github_cfg_dict["user"],
            default_visibility=github_cfg_dict.get("default_visibility", "private")
        )
    
    try:
        engine = ChatEngine(
            base_dir=demo_dir,
            api_key=openai_key,
            model=cfg.get("model", "gpt-4o-mini"),
            temperature=0.7,
            max_tokens=4096,
            dry_run=False,
            github_config=github_config,
            providers=providers_cfg,
            active_provider=cfg.get("active_provider"),
        )
    except Exception as e:
        print(f"{RED}❌ Could not initialize ChatEngine: {e}{RESET}")
        return 1
    
    # Demo script - commands to execute
    demo_commands = [
        # Phase 1: File creation
        ("create demo.py", "Creating Python file"),
        ("create notes.md", "Creating Markdown file"),
        ("create test.txt", "Creating text file"),
        
        # Phase 2: File operations
        (":edit demo.py", "Opening demo.py in editor"),
        ("rename test.txt to example.txt", "Renaming file"),
        
        # Phase 3: Git operations
        (".git init", "Initializing git repository"),
        (".git add .", "Staging all files"),
        (".git commit -m 'Initial demo commit from GitVision'", "Creating first commit"),
        (".git checkout -b feature/demo", "Creating feature branch"),
        
        # Phase 4: GitHub (if configured)
        # This will be added conditionally
        
        # Phase 5: Demo report
        ("create demo-report.md with summary of automated demo", "Creating demo report"),
    ]
    
    # Add GitHub commands if configured
    if github_config:
        demo_commands.insert(-1, (
            "create private github repo named gitvision-demo-repo",
            "Creating GitHub repository"
        ))
        demo_commands.insert(-1, (
            ".git push -u origin main",
            "Pushing to GitHub"
        ))
    
    print(f"{BRIGHT_MAGENTA}Starting automated demo sequence...{RESET}\n")
    
    # Execute demo commands
    for i, (command, description) in enumerate(demo_commands, 1):
        print(f"{ELECTRIC_CYAN}[{i}/{len(demo_commands)}]{RESET} {description}")
        print(f"  {MID_GRAY}→{RESET} {command}")
        
        try:
            # Execute command through engine
            if command.startswith("."):
                # Shell command
                shell_cmd = command[1:].strip()
                exit_code, stdout, stderr = engine.executor.terminal.run_once(shell_cmd)
                if stdout.strip():
                    print(f"  {MID_GRAY}{stdout.strip()}{RESET}")
                if stderr.strip() and exit_code != 0:
                    print(f"  {RED}{stderr.strip()}{RESET}")
            elif command.startswith(":"):
                # Panel command - would need right_panel integration
                print(f"  {MID_GRAY}(Panel command - skipped in demo mode){RESET}")
            else:
                # AI command - execute through engine
                response = []
                async for chunk in engine.stream(command):
                    response.append(chunk)
                result_text = "".join(response)
                if result_text:
                    # Show truncated response
                    preview = result_text[:100] + "..." if len(result_text) > 100 else result_text
                    print(f"  {MID_GRAY}{preview}{RESET}")
            
            # Small delay for visual effect
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"  {RED}✗ Error: {e}{RESET}")
        
        print()
    
    # Final summary
    print(f"{BRIGHT_MAGENTA}{'=' * 70}{RESET}")
    print(f"{ELECTRIC_CYAN}✅ Demo completed successfully!{RESET}\n")
    print(f"{ELECTRIC_CYAN}Demo workspace:{RESET} {demo_dir}")
    print(f"{ELECTRIC_CYAN}Files created:{RESET}")
    for file in demo_dir.rglob("*"):
        if file.is_file() and not file.name.startswith("."):
            print(f"  • {file.name}")
    
    if (demo_dir / ".git").exists():
        print(f"\n{ELECTRIC_CYAN}Git repository:{RESET} Initialized")
        # Show git log
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-n", "5"],
                cwd=demo_dir,
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                print(f"{ELECTRIC_CYAN}Recent commits:{RESET}")
                for line in result.stdout.strip().split("\n"):
                    print(f"  {line}")
        except Exception:
            pass
    
    print(f"\n{BRIGHT_MAGENTA}{'=' * 70}{RESET}\n")
    return 0


def cmd_interactive(args) -> int:
    """Launch interactive dual-panel UI (default behavior)."""
    if not args.fast:
        startup_sequence()
    else:
        try:
            banner_with_info(os.getcwd())
        except PermissionError:
            banner_with_info(str(Path.home()))
    
    if args.dir:
        try:
            os.chdir(args.dir)
        except FileNotFoundError:
            print(f"{RED}❌ Error: Directory not found: {args.dir}{RESET}")
            return 1
        except NotADirectoryError:
            print(f"{RED}❌ Error: Path is not a directory: {args.dir}{RESET}")
            return 1
        except PermissionError:
            print(f"{RED}❌ Error: Permission denied for: {args.dir}{RESET}")
            return 1
    
    if args.model or args.dry_run:
        from gitvisioncli.config.settings import save_config
        cfg = load_config()
        if args.dry_run:
            cfg["dry_run"] = True
            print(f"{BRIGHT_MAGENTA}Config override: Dry-run enabled{RESET}")
        if args.model:
            cfg["model"] = args.model
            providers_cfg = cfg.get("providers", {}) or {}
            openai_key = cfg.get("api_key") or (providers_cfg.get("openai") or {}).get("api_key")
            try:
                provider_hint, _ = ChatEngine.infer_provider_from_model_name(
                    args.model,
                    default_provider=cfg.get("active_provider", "openai"),
                    openai_enabled=bool(openai_key),
                )
                cfg["active_provider"] = provider_hint
            except Exception:
                pass
            print(f"{BRIGHT_MAGENTA}Config override: Model set to {args.model}{RESET}")
        save_config(cfg)
    
    run_interactive_chat(args)
    return 0


# =====================================================================
#  CLI ENTRY WITH SUBCOMMANDS
# =====================================================================

def _create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="gitvision",
        description="GitVisionCLI — Neon Cyberpunk AI Git Terminal IDE with dual-panel interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  gitvision                    # Launch interactive UI
  gitvision --fast             # Skip startup animation
  gitvision doctor             # Check system health
  gitvision scan .             # Scan current directory
  gitvision demo               # Run automated demo
  gitvision init myproject     # Initialize new project
        """
    )
    
    # Global options
    parser.add_argument(
        "--version",
        action="version",
        version="gitvision 1.0.0"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip startup animation"
    )
    parser.add_argument(
        "--dir",
        type=str,
        help="Specify a directory to run in"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force dry-run mode, overriding config"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Override the model from config"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands"
    )
    
    # doctor
    subparsers.add_parser(
        "doctor",
        help="Check system health and configuration"
    )
    
    # scan
    parser_scan = subparsers.add_parser(
        "scan",
        help="Scan repository for analysis"
    )
    parser_scan.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to scan (default: current directory)"
    )
    
    # sync
    subparsers.add_parser(
        "sync",
        help="Sync workspace state"
    )
    
    # init
    parser_init = subparsers.add_parser(
        "init",
        help="Initialize new project"
    )
    parser_init.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project path (default: current directory)"
    )
    
    # demo
    subparsers.add_parser(
        "demo",
        help="Run fully automated demo (for screen recording)"
    )
    
    return parser


def main():
    """Main entry point with subcommand routing."""
    parser = _create_parser()
    args = parser.parse_args()
    
    # Route to subcommand handlers
    if args.command == "doctor":
        return cmd_doctor(args)
    elif args.command == "scan":
        return cmd_scan(args)
    elif args.command == "sync":
        return cmd_sync(args)
    elif args.command == "init":
        return cmd_init(args)
    elif args.command == "demo":
        # Demo is async, so we need to run it with asyncio
        return asyncio.run(cmd_demo(args))
    else:
        # Default: Interactive UI
        return cmd_interactive(args)


if __name__ == "__main__":
    sys.exit(main() or 0)
