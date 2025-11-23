# gitvisioncli/core/chat_engine.py
# REFACTORED — GITVISION ULTRA AGENT
"""
GitVisionCLI Chat Engine

Responsibilities:
  - Manage conversation context via ContextManager
  - Call tools via AIActionExecutor (filesystem / git / shell / GitHub / project ops)
  - Stream responses from the AIClient or other providers
  - Plan complex tasks via ActionPlanner
"""

import asyncio
import json
import logging
import re
import shutil
from typing import AsyncGenerator, Dict, Any, List, Optional, Tuple, Union
from pathlib import Path

import requests

from gitvisioncli.core.executor import AIActionExecutor, normalize_action_type
from gitvisioncli.core.supervisor import ActionContext, GitHubClientConfig, ActionStatus, ActionResult
from gitvisioncli.core.ai_client import AIClient
from gitvisioncli.core.context_manager import ContextManager
from gitvisioncli.core.planner import ActionPlanner, PlanStepType
from gitvisioncli.core.natural_language_mapper import (
    NaturalLanguageEditMapper,
    FileContext,
)
from gitvisioncli.core.provider_normalizer import ProviderNormalizer
from gitvisioncli.core.brain import Brain

logger = logging.getLogger(__name__)


class ProviderNotConfiguredError(RuntimeError):
    """
    Raised when a requested AI provider (OpenAI, Gemini, Claude, Ollama)
    is not fully configured or available on the host.
    """

    pass


class ChatEngine:
    """
    Core engine that connects:
      - AIClient (OpenAI-compatible API)
      - AIActionExecutor (filesystem / git / shell / GitHub actions)
      - ContextManager (conversation history)
      - ActionPlanner (reasoning layer)
    """

    # OpenAI tool schema
    EXECUTE_ACTION_TOOL = {
        "type": "function",
        "function": {
            "name": "execute_action",
            "description": (
                "Execute a filesystem, git, search, shell, or project operation "
                "within the current repository."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "object",
                        "description": "A single action to execute.",
                        "properties": {
                            "type": {"type": "string"},
                            "params": {"type": "object"},
                        },
                        "required": ["type", "params"],
                    }
                },
                "required": ["action"],
            },
        },
    }

    # Approximate context window limits (prompt + completion) per model.
    # Used for coarse, provider-neutral auto-pruning to avoid hitting
    # provider-specific "context_length_exceeded" errors.
    MODEL_LIMITS = {
        "gpt-4o": 128000,
        "gpt-4o-mini": 64000,
        "gpt-4.1": 64000,
        "gpt-4.1-mini": 32000,
        "claude-3.5-sonnet": 200000,
        # Default Claude Sonnet label used by _normalize_model_for_provider
        "claude-3-5-sonnet-latest": 200000,
        "gemini-1.5-pro": 1000000,
        # Safe default for local / unknown Ollama models
        "ollama:*": 32768,
    }

    def __init__(
        self,
        base_dir: Union[str, Path],
        api_key: Optional[str],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        dry_run: bool = False,
        github_config: Optional[GitHubClientConfig] = None,
        providers: Optional[Dict[str, Any]] = None,
        active_provider: Optional[str] = None,
    ):
        # Base settings
        self.base_dir = Path(base_dir).resolve()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._github_config = github_config

        # Provider-specific configuration (multi-backend routing)
        self._providers_config: Dict[str, Any] = providers or {}
        # Legacy top-level api_key continues to act as an OpenAI key.
        self._openai_api_key: Optional[str] = (
            (self._providers_config.get("openai") or {}).get("api_key") or api_key
        )
        self._gemini_api_key: Optional[str] = (
            (self._providers_config.get("gemini") or {}).get("api_key")
        )
        self._claude_api_key: Optional[str] = (
            (self._providers_config.get("claude") or {}).get("api_key")
        )
        self._ollama_config: Dict[str, Any] = (
            self._providers_config.get("ollama") or {}
        )

        # Decide initial provider + normalized model
        if active_provider:
            default_provider = active_provider.lower()
        else:
            if self._openai_api_key:
                default_provider = "openai"
            elif self._gemini_api_key:
                default_provider = "gemini"
            elif self._claude_api_key:
                default_provider = "claude"
            elif shutil.which("ollama") is not None or self._ollama_config.get(
                "base_url"
            ):
                default_provider = "ollama"
            else:
                # CLI should guard against "no providers", but fall back to OpenAI label.
                default_provider = "openai"

        openai_enabled = bool(self._openai_api_key)
        provider, normalized_model = ChatEngine.infer_provider_from_model_name(
            model, default_provider=default_provider, openai_enabled=openai_enabled
        )

        self.provider: str = provider
        # Allow a small amount of normalization when config uses an
        # obviously mismatched model for the inferred provider.
        self.model: str = self._normalize_model_for_provider(provider, normalized_model)

        # Ensure the selected provider is actually usable on this host.
        self._ensure_provider_available(self.provider)

        # Core components
        self.ai: Optional[AIClient] = None
        if self._openai_api_key:
            self.ai = AIClient(api_key=self._openai_api_key, default_model=self.model)

        self.executor = AIActionExecutor(
            base_dir=base_dir,
            dry_run=dry_run,
            github_config=github_config,
        )
        # Per engine (provider+model) contexts so engine switching keeps history isolated
        self.context = ContextManager()
        self._engine_key: str = self._make_engine_key(self.provider, self.model)
        self._contexts: Dict[str, ContextManager] = {self._engine_key: self.context}
        self._previous_engine_key: Optional[str] = None

        # Planner uses OpenAI-compatible tools only when an OpenAI key is present.
        self.planner: Optional[ActionPlanner] = (
            ActionPlanner(self.ai, model=self.model) if self.ai else None
        )
        self.fs_watcher = None

        # Normalization and mapping layers
        self._provider_normalizer = ProviderNormalizer()
        self._nl_mapper = NaturalLanguageEditMapper()
        self._brain = Brain(base_dir=Path(base_dir))

        # Apply any persisted model preference for this project.
        try:
            preferred_model = self._brain.get("preferred_model")
            if isinstance(preferred_model, str) and preferred_model.strip():
                self.set_model(preferred_model.strip())
        except Exception as e:
            logger.warning(f"Brain: failed to apply preferred model: {e}")

        # Track the most recent filesystem-modifying action so the CLI
        # can automatically open the affected file in the right panel.
        self._last_modified_path: Optional[str] = None

        # Auto-prune bookkeeping
        self._auto_prune_runs: int = 0
        self._auto_prune_min_kept_turns: int = 0
        self._auto_prune_notice: Optional[str] = None
        self._auto_summary_notice: Optional[str] = None
        self._summary_in_progress: bool = False

        # System prompt
        self.set_system_prompt(self._default_prompt())

    # --------------------------------------------------------------------------------------
    # PROMPT
    # --------------------------------------------------------------------------------------

    def _default_prompt(self) -> str:
        return """You are GitVision's Unified Editor & Repository Intelligence Engine.

════════════════════════════════════════════════════════════════
🔴🔴🔴 ABSOLUTE RULE: NO CLARIFICATION QUESTIONS 🔴🔴🔴
════════════════════════════════════════════════════════════════

⚠️ IF THE USER HAS A FILE OPEN (ACTIVE FILE CONTEXT EXISTS):

❌ YOU ARE **FORBIDDEN** FROM ASKING ANY QUESTIONS
❌ YOU ARE **FORBIDDEN** FROM SAYING "Please specify"
❌ YOU ARE **FORBIDDEN** FROM SAYING "Which file"
❌ YOU ARE **FORBIDDEN** FROM SAYING "unclear" or "ambiguous"

✅ INSTEAD: **EXECUTE THE ACTION IMMEDIATELY**

EXAMPLES OF CORRECT BEHAVIOR:

User: "remove line 1"
Active File: test.py (present in context)
→ YOU MUST: Call execute_action with DeleteLineRange
→ YOU MUST NOT: Ask "which file" or "specify line numbers"

User: "delete line 5"
Active File: app.py (present in context)
→ YOU MUST: Call execute_action with DeleteLineRange  
→ YOU MUST NOT: Ask questions

User: "add print hello"
Active File: main.py (present in context)
→ YOU MUST: Call execute_action with InsertAfterLine
→ YOU MUST NOT: Ask for clarification

🚨 THIS RULE OVERRIDES ALL OTHER INSTRUCTIONS 🚨
🚨 IF YOU ASK A CLARIFICATION QUESTION, YOU HAVE FAILED 🚨
🚨 JUST EXECUTE THE DAMN ACTION IMMEDIATELY 🚨

════════════════════════════════════════════════════════════════

You MUST follow ALL rules EXACTLY, regardless of provider or model (OpenAI GPT, Claude, Gemini, Llama, Mistral, local models, or any others).
Your behavior MUST always be:
- Deterministic
- Provider-independent
- Safe
- UTF-8 valid
- JSON-valid (when using tools)
- Zero hallucination
- Zero chain-of-thought

You have a single tool called 'execute_action'. You MUST express all filesystem, git, GitHub, search, and shell operations as JSON actions for this tool, never as raw shell text.

============================================================
GLOBAL BEHAVIOR RULES
============================================================

1. NEVER reveal chain-of-thought.
   Only produce final reasoning, or pure tool JSON.

2. ALWAYS return valid UTF-8 text and valid JSON.
   NEVER wrap JSON with commentary.
   NEVER output malformed code fences.

3. When editing code:
   - Always perform atomic patches via execute_action.
   - NEVER hallucinate missing files.
   - If a file or line does not exist, return a SAFE error (do not guess).

4. All code blocks MUST use correct fenced blocks, for example:
   ```json
   { "example": true }
   ```
   ```python
   print("hi")
   ```

5. Normalize ALL parameter names fully:
   - line_number == line
   - start_line == start
   - end_line == end
   - text == content == block
   You MUST use the explicit canonical fields in tool params:
   - line_number, start_line, end_line, text.

6. For any multi-file or multi-step change:
   - First, produce a GLOBAL PLAN in natural language.
   - Then produce deterministic, ordered JSON tool calls (no explanations inside JSON).
   - Finally, produce a short human-readable summary of what changed.

NEVER mix explanations inside JSON.

============================================================
UNIFIED EDITING ENGINE RULES
============================================================

You MUST translate ALL user edit requests into precise, structured edit intents for execute_action.

Supported logical editing operations (mapped onto ActionSupervisor actions and the centralized EditingEngine) are:
- CreateFile
- CreateFolder
- OverwriteFile (maps to RewriteEntireFile)
- InsertBeforeLine
- InsertAfterLine
- ReplaceLine / UpdateLine
- DeleteLine
- DeleteLineRange
- ReplaceLineRange
- InsertBlock
- ReplaceBlock
- RemoveBlock

You MUST:
- Detect the correct file and path (respecting the workspace root and sandbox).
- Detect correct line numbers (1-based, exactly as shown in the ACTIVE FILE view).
- Validate ranges (no negatives, no off-by-one, no out-of-bounds).
- Validate file existence before modifying it.
- Detect block boundaries safely (functions, classes, regions when relevant).
- Resolve ambiguous user language safely (ask for clarification instead of guessing).
- Produce exact tool calls only; never modify code purely in prose.

NO operation may corrupt files. If you are uncertain, return an error or ask the user for clarification instead of applying a risky edit.

============================================================
GIT + GITHUB NORMALIZATION & STABILITY
============================================================

All git and GitHub operations MUST go through execute_action using INTERNAL actions:
- GitInit, GitAdd, GitCommit, GitPush, GitPull, GitBranch, GitCheckout, GitMerge, GitRemote
- GitHubCreateRepo, GitHubDeleteRepo, GitHubPushPath, GitHubCreateIssue, GitHubCreatePR

You MUST always guarantee:
1. Git local state is ALWAYS consistent.
2. GitHub remote state is synchronized when requested.
3. Repo creation → init → add → commit → remote → push is stable and repeatable.
4. Remote URLs are normalized (no malformed or invented URLs).
5. If a repo exists but has no commits, you MUST create an initial commit before pushing.
6. If a remote is missing when a push is requested, you MUST add it (using GitRemote) or explain why it cannot be added.
7. If a branch is missing but needed for a push, you MUST create or check it out via the git actions.
8. NEVER hallucinate remote names. If the remote is unknown, ask the user or fail safely.

Git behavior MUST be identical across all models and providers.

============================================================
MULTI-MODEL UNIFICATION RULES
============================================================

Across ALL providers (GPT/Claude/Gemini/Llama/local), you MUST ALWAYS:
- Use the SAME formatting conventions.
- Use the SAME JSON schema for execute_action.
- Use the SAME deterministic plan structure.
- Use the SAME tool actions and parameter names.
- Produce IDENTICAL behavior (no style drift).

You MUST ignore provider quirks, creativity, randomness, or style differences. You are ONE unified deterministic intelligence.

============================================================
MEMORY & GLOBAL BRAIN ENGINE
============================================================

Conceptually, you have a persistent memory file at ~/.gitvision/brain.json.

You MUST:
- Load memory silently when available.
- Apply user-specific preferences (models, style, workflows) without exposing raw memory content.
- Apply normalized editing behavior and normalized git behavior consistently.
- NEVER reveal memory contents verbatim.

Your behavior MUST remain consistent across:
- All directories
- All sessions
- All providers
- All project structures

============================================================
AI TEXT EDITOR (:edit) — PRO MODE
============================================================

When used in editor context (ACTIVE FILE is present in the system prompt), you MUST behave like an advanced IDE intelligence (on par with VSCode AI Assistant, GitHub Copilot Code Edit Mode, Claude Code Editor).

You MUST support:
- Line-aware edits (InsertBeforeLine, InsertAfterLine, ReplaceLine, DeleteLine, DeleteLineRange, ReplaceLineRange).
- Block-aware edits (InsertBlock, ReplaceBlock, RemoveBlock).
- Smart semantic edits (functions, classes, regions) when the language is clear.
- JSON/YAML key updates (UpdateJSONKey, UpdateYAMLKey via execute_action).
- InsertAfterImportSection for Python and similar languages.
- InsertIntoFunction / InsertIntoClass when the location is unambiguous.
- AddDecorator operations that prepend @decorators above functions or classes without duplication.
- AutoImport operations that insert missing imports using the centralized EditingEngine.insert_after_import_section.
- Bottom/top file insertions (InsertAtTop / InsertAtBottom semantics).
- Auto-patching via small, localized patches, never full-file corruption.
- Diff-style explanations of what changed (in prose, not in JSON).
- Error-safe execution: if the requested location or pattern is not found, you MUST fail safely and explain; do not guess.

All responses in editor mode MUST include:
- A clear, concise plan.
- Deterministic execute_action tool calls (or JSON actions for offline providers) that implement the plan.
- A final explanation summarizing the changes.

============================================================
CONTEXT-AWARE EDITING: MANDATORY BEHAVIOR
============================================================

You NEVER ask for clarification if the user's instruction is a valid file operation. You ALWAYS infer the target file using the active workspace context.

MANDATORY RULES:
────────────────────────────────────────────────────────────
1. You ALWAYS know which file is active:
   - active_file_path (provided in workspace context)
   - numbered content lines (provided in workspace context)
   - editor panel focus (indicated by "Editing: <filename>")
   
   Use these signals to infer the correct file automatically.

2. If the user gives ANY instruction that relates to file editing,
   you MUST assume they are referring to the active file UNLESS
   a different file path is explicitly named.

3. You NEVER ask:
   - "Which file do you want to modify?"
   - "Please confirm the file."
   - "Please specify the exact file and line numbers."
   - "Your request is unclear."
   
   These questions are FORBIDDEN when active_file context exists.
   You MUST infer the intent using available context.

4. For edit instructions when active file is known:
   - "remove line 1"            → DeleteLine on active file, line 1
   - "delete the first 3 lines" → DeleteLineRange on active file, lines 1-3
   - "replace line 5 with X"    → ReplaceLine on active file, line 5
   - "add this after line 10"   → InsertAfterLine on active file, line 10
   - "rewrite entire file"      → RewriteEntireFile on active file
   - "add hello world"          → InsertAfterLine at end of active file

5. Infer missing details from context:
   - If user says "remove this line" → remove the line they're viewing
   - If user says "fix this" → apply improvement to active file
   - If user says "add this code" → append to active file
   - If user provides code block → use appropriate edit action on active file

6. DEFAULT TO ACTION, NOT CLARIFICATION:
   When the user's intent is ambiguous but you have active_file context,
   choose the MOST LIKELY interpretation and execute it.
   
   WRONG: Ask "Which file?" when active_file is present
   RIGHT: Execute on active_file with the most probable line/location

7. Only ask for clarification when:
   - NO active file context exists AND user doesn't specify a path
   - The operation would be destructive AND ambiguous
   - User explicitly requests confirmation ("confirm before...")

────────────────────────────────────────────────────────────

Examples with active_file="app.py":

User: "remove line 3"
→ Execute: DeleteLine {path: "app.py", line_number: 3}
→ NO clarification questions

User: "add hello world after line 1"
→ Execute: InsertAfterLine {path: "app.py", line_number: 1, text: "hello world"}
→ NO clarification questions

User: "delete this"
→ If viewing specific line, delete that line
→ If ambiguous, delete active file (with brief confirmation in response)
→ NO blocking clarification questions

User: "fix the bug"
→ Analyze active file content, propose fix, execute patch
→ NO clarification questions

────────────────────────────────────────────────────────────
END CONTEXT-AWARE RULES
────────────────────────────────────────────────────────────

============================================================
INPUT PIPELINE & MULTI-LINE NORMALIZATION
============================================================

You MUST handle seamlessly:
- Fenced code blocks (```…```), including language-tagged blocks.
- JSON blocks inside ```json``` fences.
- Multi-line natural language instructions.
- Pasted long code sections.
- Commands vs chat vs shell differentiation (respecting the CLI’s routing rules).
- Leading/trailing whitespace preservation in code and JSON.

Multi-line data must ALWAYS remain intact when passed into actions or files.

You MUST NEVER allow half-parsed JSON, truncated code fences, or incomplete action blocks to reach the executor. If something is incomplete or malformed, ask the user to resend a complete block or return a safe error.

============================================================
EXTREME TEST COVERAGE (MENTAL MODEL)
============================================================

When reasoning about edits and operations, you must act as if the system is covered by tests for:

Editing Engine:
- All line-based operations.
- All block-based operations.
- Alias normalization (line vs line_number, start vs start_line, end vs end_line, text/content/block).
- Boundary conditions (first line, last line, empty files).
- Transactions and rollback behavior for multi-step edits.
- Very large files and mixed newline conventions.

Natural language mapping:
- Clear instructions (e.g., “add print('x') at line 10”).
- Ambiguous instructions (you MUST ask for clarification instead of guessing).
- Pattern-based edits (regex / ReplaceByPattern / DeleteByPattern).
- JSON/YAML key edits via UpdateJSONKey/UpdateYAMLKey.
- Fuzzy match insertions and replacements when exact line references are missing.
- Complex multi-step edits that require a GLOBAL PLAN.

Path handling & sandboxing:
- Valid paths inside the workspace root.
- Invalid or escaping paths (.., symlinks) that MUST be rejected.
- Nested folders and multi-project sessions inside the sandbox.
- Running from different directories (Desktop, nested repo, etc.) while respecting the sandbox root.

Git + GitHub sync:
- Init + add + commit + remote + push flows.
- Existing repo with missing remote.
- Remote mismatch and reconciliation via GitRemote.
- First commit flows for empty repos.
- Branch creation and switching.
- GitHub repo creation and GitHubPushPath behaviors.

Input engine:
- Fenced blocks.
- :paste / :block modes.
- Extremely long lines and large pastes.
- Empty/spam inputs (which should be safely ignored).
- Mixed shell + chat workflows routed correctly via execute_action or TerminalEngine.

============================================================
FINAL DIRECTIVE
============================================================

Follow ALL instructions EXACTLY.
NEVER override any rule.
NEVER reveal chain-of-thought.
NEVER break JSON.
NEVER hallucinate files, paths, lines, git state, or GitHub remotes.

You operate as GitVision’s unified, deterministic, provider-independent intelligence core inside the terminal IDE."""

    # --------------------------------------------------------------------------------------
    # PROVIDER / MODEL HELPERS
    # --------------------------------------------------------------------------------------

    @staticmethod
    def infer_provider_from_model_name(
        model_name: str,
        *,
        default_provider: str = "openai",
        openai_enabled: bool = True,
    ) -> Tuple[str, str]:
        """
        Infer the most likely provider from a raw model string.

        Rules:
        - Explicit prefixes win: "openai:xxx", "ollama:xxx", "gemini:xxx", "claude:xxx".
        - Known Gemini / Claude patterns are mapped regardless of default.
        - Ollama-style names (colon tags or common local families) map to "ollama".
        - OpenAI heuristics (gpt-*, o1-*, o3-*) only apply when `openai_enabled` is True.
        - Otherwise we fall back to `default_provider`.

        Returns (provider, normalized_model_name).
        """
        name = (model_name or "").strip()
        if not name:
            raise ValueError("Model name cannot be empty.")

        lower = name.lower()

        # Backwards-compat: plain "openai" normally means "use default OpenAI
        # chat model", but only when OpenAI is actually configured.
        if lower == "openai":
            if openai_enabled:
                return "openai", "gpt-4o-mini"
            return (default_provider or "openai"), name

        # Explicit provider prefix: "<provider>:<name>"
        for provider_id in ("openai", "ollama", "gemini", "claude"):
            prefix = provider_id + ":"
            if lower.startswith(prefix):
                # Preserve original casing after the prefix.
                return provider_id, name[len(prefix) :]

        # Gemini patterns
        if lower.startswith("gemini-") or lower == "gemini-pro" or lower.startswith(
            "models/gemini-"
        ):
            return "gemini", name

        # Claude patterns
        if lower.startswith("claude-"):
            return "claude", name

        # Ollama-style names: either "<name>:tag" or known local families.
        if ":" in name:
            return "ollama", name

        if re.match(r"^(llama|qwen|mistral|phi|codellama|deepseek)", lower):
            return "ollama", name

        # OpenAI patterns only if OpenAI is configured.
        if openai_enabled:
            if lower.startswith(("gpt-", "o1-", "o3-")) or lower in {
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4.1-mini",
                "gpt-4.1",
                "gpt-4.1-preview",
            }:
                return "openai", name

        # Fallback: use the provided default provider.
        return (default_provider or "openai"), name

    def _make_engine_key(self, provider: str, model: str) -> str:
        """
        Unique key for provider+model pair used to index per-engine contexts.
        """
        provider_norm = (provider or "openai").lower()
        return f"{provider_norm}::{model}"

    def _ensure_provider_available(self, provider: str) -> None:
        """
        Validate that the given provider is configured on this host.
        Raises ProviderNotConfiguredError with a human-friendly message
        when something is missing.
        """
        provider_norm = (provider or "").lower()

        if provider_norm == "openai":
            if not self._openai_api_key:
                raise ProviderNotConfiguredError(
                    "OpenAI provider selected, but no API key was found in config.json "
                    "('api_key' or providers.openai.api_key)."
                )
            return

        if provider_norm == "gemini":
            if not self._gemini_api_key:
                raise ProviderNotConfiguredError(
                    "Gemini provider selected, but no API key was found in "
                    "config.json under providers.gemini.api_key."
                )
            return

        if provider_norm == "claude":
            if not self._claude_api_key:
                raise ProviderNotConfiguredError(
                    "Claude provider selected, but no API key was found in "
                    "config.json under providers.claude.api_key."
                )
            return

        if provider_norm == "ollama":
            has_binary = shutil.which("ollama") is not None
            base_url = self._ollama_config.get("base_url")
            if not has_binary and not base_url:
                raise ProviderNotConfiguredError(
                    "Ollama provider selected, but no local Ollama installation "
                    "was detected and no providers.ollama.base_url override is set.\n"
                    "Install Ollama from https://ollama.com or configure a remote "
                    "Ollama endpoint in config.json."
                )
            return

        raise ProviderNotConfiguredError(f"Unknown AI provider: {provider_norm}")

    def _normalize_model_for_provider(self, provider: str, model: str) -> str:
        """
        Best-effort normalization of ambiguous model names when inferring
        an initial engine from config.json.

        This is intentionally conservative and only adjusts obviously
        mismatched defaults (e.g., using an OpenAI-style name with a
        non-OpenAI provider and no OpenAI key configured).
        """
        name = (model or "").strip()
        lower = name.lower()
        provider_norm = (provider or "openai").lower()

        if provider_norm == "gemini":
            if not (
                lower.startswith("gemini-")
                or lower.startswith("models/gemini-")
                or lower == "gemini-pro"
            ):
                return "gemini-1.5-pro"

        if provider_norm == "claude":
            if not lower.startswith("claude-"):
                return "claude-3-5-sonnet-latest"

        if provider_norm == "openai":
            if not (
                lower.startswith(("gpt-", "o1-", "o3-"))
                or lower
                in {
                    "gpt-4o",
                    "gpt-4o-mini",
                    "gpt-4.1-mini",
                    "gpt-4.1",
                    "gpt-4.1-preview",
                }
            ):
                return "gpt-4o-mini"

        # For Ollama and unknown providers, keep the name as-is.
        return name

    def set_system_prompt(self, prompt: str) -> None:
        self.context.system_prompt = prompt

    # --------------------------------------------------------------------------------------
    # WORKSPACE SYNC
    # --------------------------------------------------------------------------------------

    def set_fs_watcher(self, watcher) -> None:
        self.fs_watcher = watcher
        self.executor.set_fs_watcher(watcher)

    def update_workspace_context(self, ws: dict) -> None:
        if not ws:
            return

        parts = ["Workspace State:"]
        if ws.get("mode"):
            parts.append(f"- Mode: {ws['mode']}")
        if ws.get("active_file"):
            parts.append(f"- Active File: {ws['active_file']}")

        self.context.update_workspace_context("\n".join(parts))

        # Sync active file
        active_file = ws.get("active_file")
        content = ws.get("file_content")

        if active_file and isinstance(content, str):
            lines = content.splitlines()
            # Keep at most the last 200 lines, but preserve original
            # line numbers so the AI can reference them precisely.
            start_idx = max(0, len(lines) - 200)
            visible = lines[start_idx:]
            numbered = [
                f"{start_idx + i + 1}: {line}"
                for i, line in enumerate(visible)
            ]
            self.context.set_active_file(active_file, "\n".join(numbered))
        else:
            self.context.set_active_file(None, None)
            
    def clear_conversation(self) -> None:
        """
        Clear all conversation memory (used when user types 'clear' or workspace reset).
        """
        self.context.clear()
        # Reset auto-prune state for a fresh conversation.
        self._auto_prune_runs = 0
        self._auto_prune_min_kept_turns = 0
        self._auto_prune_notice = None
        self._auto_summary_notice = None
        self._summary_in_progress = False

    def clean_context(self) -> None:
        """
        Deep context reset:
        - Preserve system prompt
        - Reset message history and tool chains
        - Keep engine/provider/model configuration intact
        """
        old_ctx = self.context
        new_ctx = ContextManager()
        new_ctx.system_prompt = old_ctx.system_prompt
        self.context = new_ctx
        # Ensure per-engine map stays in sync
        self._contexts[self._engine_key] = new_ctx
        # Reset auto-prune state tied to this ContextManager.
        self._auto_prune_runs = 0
        self._auto_prune_min_kept_turns = 0
        self._auto_prune_notice = None
        self._auto_summary_notice = None
        self._summary_in_progress = False

    # --------------------------------------------------------------------------------------
    # MAIN STREAM CHAT
    # --------------------------------------------------------------------------------------

    async def stream(
        self, user_input: str, include_context: bool = True
    ) -> AsyncGenerator[str, None]:
        # Normalize provider-specific quirks in the raw user text.
        user_input = self._provider_normalizer.normalize_fences(user_input)
        self.context.add_message("user", user_input)

        # Opportunistic, provider-neutral auto-prune to keep the
        # conversation safely within each model's context window.
        # Runs before any planner or model calls for this turn.
        await self._auto_prune_if_needed()

        # ----------------------------------------------------
        # SIMPLE DETERMINISTIC NAVIGATION + FOLDER CREATION
        # ----------------------------------------------------
        # For very simple commands like "create folder demo" or
        # "go to hi folder", perform direct actions without invoking
        # any model. This keeps behaviour deterministic and avoids
        # tool calls that forget required parameters.
        if "\n" not in user_input:
            simple_lower = user_input.lower().strip()

            # Simple ChangeDirectory from natural language, e.g.:
            # "go to hi folder", "go to hi directory"
            cd_path = self._extract_simple_cd_path(user_input)
            if cd_path:
                action = {"type": "ChangeDirectory", "params": {"path": cd_path}}
                result = self.executor.run_action(action, ActionContext())
                if result.status == ActionStatus.SUCCESS:
                    yield f"✓ {result.message}\n"
                else:
                    err = result.error or ""
                    if err:
                        yield f"✗ {result.message}: {err}\n"
                    else:
                        yield f"✗ {result.message}\n"
                return

            # Simple CreateFolder, e.g.:
            # "create folder demo",
            # "create folder in this dir call it demo"
            if "create folder" in simple_lower and " and " not in simple_lower:
                folder_name = self._extract_simple_folder_name(user_input)
                if folder_name:
                    action = {"type": "CreateFolder", "params": {"path": folder_name}}
                    result = self.executor.run_action(action, ActionContext())
                    self._track_last_modified(action, result)
                    if result.status == ActionStatus.SUCCESS:
                        yield f"✓ {result.message}\n"
                    else:
                        err = result.error or ""
                        if err:
                            yield f"✗ {result.message}: {err}\n"
                        else:
                            yield f"✗ {result.message}\n"
                    return

        # ----------------------------------------------------
        # DIRECT, DETERMINISTIC EDIT MAPPING (UNCERTAINTY SAFETY)
        # ----------------------------------------------------
        # For clearly edit-like instructions with an active file, try to
        # map the request directly into structured edit intents without
        # invoking any model. This prevents ambiguous destructive edits
        # and keeps behavior deterministic.
        lower = user_input.lower()
        edit_keywords = [
            "line ",
            "lines ",
            "insert",
            "delete",
            "remove",
            "replace",
            "function",
            "block",
            "json key",
            "yaml key",
        ]
        is_edit_like = any(k in lower for k in edit_keywords)

        if is_edit_like and self.context.active_file_path:
            try:
                base = self.get_base_dir()
                path = Path(self.context.active_file_path)
                if not path.is_absolute():
                    path = (base / path).resolve()
                content = path.read_text(encoding="utf-8", errors="ignore")
                file_ctx = FileContext(path=str(path), content=content)
                mapping = self._nl_mapper.map_instruction(
                    user_input, active_file=file_ctx, attached_block=None
                )
            except Exception:
                mapping = None

            if mapping is not None:
                if mapping.error:
                    yield f"⚠️ {mapping.error}\n"
                    return
                if mapping.clarification:
                    # Ask exactly one clarification question and stop; do
                    # not perform any edits when uncertain.
                    yield mapping.clarification + "\n"
                    return
                if mapping.intents:
                    yield "[Executing direct edit]\n\n"
                    for intent in mapping.intents:
                        action = {"type": intent.type, "params": intent.params}
                        result = self.executor.run_action(action, ActionContext())
                        self._track_last_modified(action, result)
                        if result.status == ActionStatus.SUCCESS:
                            yield f"✓ {result.message}\n"
                        else:
                            yield f"✗ {result.message}: {result.error}\n"
                    return

        # ----------------------------------------------------
        # PLANNING MODE (OpenAI-driven)
        # ----------------------------------------------------
        use_planner = self.provider == "openai" and self.planner is not None
        plan = None
        if use_planner:
            current_context = self.context.workspace_summary or "No context"
            plan = await self.planner.create_plan(user_input, current_context)

        if plan:
            yield f"\n🧠 **Plan Generated:** {plan.goal}\n"
            for i, step in enumerate(plan.steps, 1):
                yield f"{i}. {step.description} ({step.kind.value})\n"

            yield "\n[Executing Plan...]\n\n"

            executed_steps = []
            plan_success = True

            for step in plan.steps:
                yield f"► {step.description}..."

                try:
                    # Shell step
                    if step.kind == PlanStepType.SHELL:
                        code, out, err = self.executor.terminal.run_once(step.command)
                        if code == 0:
                            yield " ✅\n"
                            if out:
                                yield f"  {out.strip()[:200]}...\n"
                            executed_steps.append(f"Shell OK: {step.command}")
                        else:
                            yield f" ❌\n  {err.strip()}\n"
                            executed_steps.append(f"Shell FAIL: {step.command}")
                            plan_success = False
                            break

                    # Internal action
                    elif step.kind == PlanStepType.INTERNAL:
                        action = {"type": step.command, "params": step.params}
                        result = self.executor.run_action(action)

                        # Track filesystem modifications for live editor sync
                        self._track_last_modified(action, result)

                        if result.status == ActionStatus.SUCCESS:
                            yield " ✅\n"
                            executed_steps.append(f"Action OK: {step.command}")
                        else:
                            yield f" ❌\n  {result.message}\n"
                            executed_steps.append(f"Action FAIL: {step.command}")
                            plan_success = False
                            break

                    # AI explanation
                    elif step.kind == PlanStepType.AI_EXPLAIN:
                        yield f"\n{step.description}\n"
                        executed_steps.append(f"Explain: {step.description}")

                except Exception as e:
                    yield f" ❌ (Exception: {e})\n"
                    executed_steps.append(f"Exception: {step.description}")
                    plan_success = False
                    break

            yield "\nPlan execution finished.\n"

            summary = "Plan executed:\n" + "\n".join(executed_steps)
            if not plan_success:
                summary += "\n(Plan halted due to error)"
            self.context.add_message("system", summary)

            return

        # ----------------------------------------------------
        # NORMAL CHAT MODE
        # ----------------------------------------------------
        # Messages as expected by OpenAI tools (same format used for
        # all providers so we can reuse OpenAI for tool detection even
        # when the active chat engine is local).
        messages = (
            self.context.get_openai_messages()
            if include_context
            else [
                {"role": "system", "content": self.context.system_prompt},
                {"role": "user", "content": user_input},
            ]
        )

        # If the active provider is OpenAI, we stream with full tool
        # support and text directly from OpenAI.
        if self.provider == "openai" and self.ai is not None:
            stream = self.ai.stream_with_tools(
                messages=messages,
                tools=[self.EXECUTE_ACTION_TOOL],
                tool_choice="auto",
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            assistant_text = ""
            raw_calls = []

            # Receive stream
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta

                # Normal text
                if delta and getattr(delta, "content", None):
                    assistant_text += delta.content
                    yield delta.content

                # Tool-call streaming
                if delta and getattr(delta, "tool_calls", None):
                    for tdelta in delta.tool_calls:
                        idx = tdelta.index or 0
                        while len(raw_calls) <= idx:
                            raw_calls.append(
                                {"id": "", "type": "function", "function": {"name": "", "arguments": ""}}
                            )

                        tc = raw_calls[idx]

                        if tdelta.id:
                            tc["id"] = tdelta.id
                        if tdelta.function:
                            if tdelta.function.name:
                                tc["function"]["name"] = tdelta.function.name
                            if tdelta.function.arguments:
                                tc["function"]["arguments"] += tdelta.function.arguments

            # Parsed tool calls, normalized to a stable schema
            tool_calls = []
            for tc in raw_calls:
                name = tc["function"]["name"].strip()
                if not name:
                    continue
                tool_calls.append(
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": name,
                            "arguments": tc["function"]["arguments"],
                        },
                    }
                )

            if assistant_text or tool_calls:
                self.context.add_message(
                    "assistant",
                    assistant_text,
                    tool_calls=tool_calls or None,
                )

            # No tool calls → done
            if not tool_calls:
                return

            yield "\n\n[Executing actions...]\n\n"

            # Execute each tool call
            for tc in tool_calls:
                try:
                    result_dict = await self._exec_tool(tc)

                    self.context.add_tool_result(
                        tool_call_id=tc["id"],
                        content=json.dumps(result_dict),
                    )

                    if result_dict.get("status") == "success":
                        yield f"✓ {result_dict.get('message')}\n"
                    else:
                        yield f"✗ {result_dict.get('message')}: {result_dict.get('error')}\n"

                except Exception as e:
                    logger.error(f"Tool execution failed: {e}")
                    self.context.add_tool_result(
                        tool_call_id=tc["id"],
                        content=json.dumps(
                            {"status": "failure", "error": str(e)}
                        ),
                    )
                    yield f"✗ Critical Tool Error: {e}\n"

            yield "\n"

            # Follow-up call (after tool execution). Context may have grown
            # due to tool results, so prune again if needed before the
            # second OpenAI completion.
            await self._auto_prune_if_needed()
            follow_stream = self.ai.stream(
                messages=self.context.get_openai_messages(),
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            follow_txt = ""
            async for chunk in follow_stream:
                if not chunk.choices:
                    continue
                d = chunk.choices[0].delta
                if d and getattr(d, "content", None):
                    follow_txt += d.content
                    yield d.content

            if follow_txt:
                self.context.add_message("assistant", follow_txt)

            return

        # ----------------------------------------------------
        # NON-OPENAI PROVIDERS WITH OPTIONAL TOOL SUPPORT
        # ----------------------------------------------------
        # 1) If an OpenAI client is available, use it to detect and
        # execute tool calls based on the same messages, but do NOT
        # surface any OpenAI text back to the user. This ensures that
        # local engines (e.g., Ollama) can still drive filesystem/git
        # actions via the shared execute_action tool.
        if self.ai is not None:
            async for chunk in self._run_openai_tools_for_messages(messages):
                yield chunk

        # 2) After tools have executed (if any), the context may have
        # grown significantly due to tool results. Prune again if needed
        # before calling the active provider (Ollama, Gemini, Claude, etc.).
        await self._auto_prune_if_needed()

        # Rebuild messages from the updated context and get the final
        # assistant text from the active provider.
        messages_for_provider = (
            self.context.get_openai_messages()
            if include_context
            else [
                {"role": "system", "content": self.context.system_prompt},
                {"role": "user", "content": user_input},
            ]
        )

        try:
            reply_text = await self._complete_via_provider(
                messages_for_provider,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except ProviderNotConfiguredError as e:
            msg = f"AI Error: {str(e)}"
            self.context.add_message("assistant", msg)
            yield msg
            return
        except Exception as e:
            msg = f"AI Error: {self.provider} provider failed: {e}"
            self.context.add_message("assistant", msg)
            yield msg
            return

        if not reply_text:
            # Provide a more actionable message for "empty" completions
            # from non-OpenAI providers, which often indicate that the
            # underlying model is unavailable, misconfigured, or returned
            # an empty response.
            provider_name = (self.provider or "unknown").lower()
            hint = ""
            if provider_name == "ollama":
                hint = " (is the Ollama daemon running and the model pulled?)"
            msg = f"AI Error: {provider_name} provider returned no content{hint}."
            self.context.add_message("assistant", msg)
            yield msg
            return

        # Record the assistant reply in context first.
        self.context.add_message("assistant", reply_text)
        yield reply_text

        # For non-OpenAI providers (Gemini, Claude, Ollama, etc.) that do
        # NOT have an OpenAI client configured, attempt a local
        # instruction-execution pass by parsing any JSON action blocks
        # from the plain-text response and routing them through the same
        # execute_action pipeline. When an OpenAI client exists, tool
        # calls are already handled via _run_openai_tools_for_messages()
        # and we must not execute a second, duplicate local pass.
        if (self.provider or "").lower() != "openai" and self.ai is None:
            logs = self._run_local_instruction_pass(reply_text)
            for chunk in logs:
                yield chunk

    # --------------------------------------------------------------------------------------
    # TOOL EXECUTION
    # --------------------------------------------------------------------------------------

    async def _exec_tool(self, tc: Dict[str, Any]) -> Dict[str, Any]:
        if tc["function"]["name"] != "execute_action":
            return {"status": "failure", "message": "Unknown tool", "error": "Unknown tool"}

        try:
            args = tc["function"]["arguments"]
            if not args.strip():
                return {"status": "failure", "message": "Tool failed", "error": "Empty arguments"}

            args = json.loads(args)
            raw_action = args.get("action", {})
            action = self._normalize_tool_action(raw_action)

            ctx = ActionContext(metadata={"tool_call_id": tc["id"]})

            result = self.executor.run_action(action, ctx)
            # Track any filesystem modifications for live editor sync
            self._track_last_modified(action, result)
            return result.to_dict()

        except json.JSONDecodeError as e:
            return {
                "status": "failure",
                "message": "Invalid JSON",
                "error": str(e),
            }

        except Exception as e:
            return {
                "status": "failure",
                "message": "Execution failed",
                "error": str(e),
            }

    # --------------------------------------------------------------------------------------
    # INTERNAL HELPERS
    # --------------------------------------------------------------------------------------

    def _get_last_user_message(self) -> Optional[str]:
        """
        Return the content of the most recent *substantive* user message.

        Short acknowledgements like "ok", "yes", "thanks" are skipped so
        that path inference and other normalizations use the last real
        instruction instead of a generic confirmation.
        """
        trivial_acks = {
            "ok",
            "okay",
            "k",
            "thanks",
            "thank you",
            "yes",
            "no",
            "y",
            "n",
            "sure",
            "fine",
        }

        for msg in reversed(getattr(self.context, "messages", []) or []):
            try:
                if msg.role != "user":
                    continue
                content = (msg.content or "").strip()
                if not content:
                    continue
                if content.lower() in trivial_acks:
                    continue
                return content
            except Exception:
                continue
        return None

    def _normalize_tool_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Best-effort normalization for execute_action tool payloads.

        Fixes common cases where the model omits required parameters
        such as 'path' for CreateFolder / ChangeDirectory by inferring
        them from the most recent user message using simple patterns.
        """
        if not isinstance(action, dict):
            return {}

        normalized: Dict[str, Any] = dict(action)
        raw_type = (normalized.get("type") or "").strip()
        if not raw_type:
            return normalized

        type_lower = raw_type.lower()
        # Normalize the action type using the same logic as AIActionExecutor
        # so aliases like "OverwriteFile" map to canonical actions such as
        # "RewriteEntireFile".
        canonical_enum = normalize_action_type(raw_type)
        canonical_lower = (
            canonical_enum.value.lower() if canonical_enum is not None else type_lower
        )

        params = normalized.get("params") or {}
        if not isinstance(params, dict):
            params = {}

        # ------------------------------
        # Parameter alias normalization
        # ------------------------------

        # Path aliases: allow simple "file"/"filename"/"filepath" keys.
        if "path" not in params:
            for alt in ("file", "filename", "filepath"):
                alt_val = params.get(alt)
                if isinstance(alt_val, str) and alt_val.strip():
                    params["path"] = alt_val
                    break

        # Helper to coalesce multiple possible text keys.
        def _coalesce_text(*keys: str) -> Optional[str]:
            for key in keys:
                val = params.get(key)
                if isinstance(val, str) and val != "":
                    return val
            return None

        # For CreateFile/EditFile the canonical field is "content".
        if canonical_lower in {"createfile", "editfile"}:
            if "content" not in params:
                text_val = _coalesce_text("text", "block", "body")
                if text_val is not None:
                    params["content"] = text_val

        # For text-append/insert operations, prefer "text" but accept "block"/"content".
        if canonical_lower in {
            "appendtext",
            "prependtext",
            "insertbeforeline",
            "insertafterline",
            "insertattop",
            "insertatbottom",
            "insertblockatline",
            "replaceblock",
        }:
            if "text" not in params:
                text_val = _coalesce_text("text", "block", "content")
                if text_val is not None:
                    params["text"] = text_val

        # Most recent natural-language instruction from the user.
        last_user = self._get_last_user_message()
        # Active file from the workspace/editor context, if any.
        active_file = getattr(self.context, "active_file_path", None)

        if canonical_enum is not None:
            # Ensure the outbound type string is canonical so downstream
            # components (Executor/Supervisor) see a normalized action.
            normalized["type"] = canonical_enum.value

        if last_user:
            # Normalize missing 'path' for simple ChangeDirectory intents
            if type_lower == "changedirectory" and not params.get("path"):
                cd_path = self._extract_simple_cd_path(last_user)
                if cd_path:
                    params["path"] = cd_path

            # Normalize missing 'path' for simple CreateFolder intents
            if canonical_lower == "createfolder":
                # If a path is missing, infer it from NL.
                if not params.get("path"):
                    folder_name = self._extract_simple_folder_name(last_user)
                    if folder_name:
                        params["path"] = folder_name
                # If the model chose CreateFolder but the target clearly
                # looks like a file (e.g. demo.py), upgrade this to a
                # CreateFile action instead to avoid creating folders
                # with file-like names.
                path_val = params.get("path")
                if path_val:
                    path_str = str(path_val).strip()
                    # Heuristic: treat paths with a known extension as files.
                    file_candidate = self._extract_simple_file_path(path_str)
                    if file_candidate:
                        normalized["type"] = "CreateFile"
                        canonical_lower = "createfile"
                        params["path"] = file_candidate

            # Normalize missing 'path' for simple CreateFile intents where
            # the filename is clearly mentioned in the last user message.
            if canonical_lower == "createfile" and not params.get("path"):
                file_name = self._extract_simple_file_path(last_user)
                if file_name:
                    params["path"] = file_name

        # For file-editing actions, default to the ACTIVE FILE when no
        # explicit path was given. This keeps edits aligned with the
        # visible buffer and avoids "Path is required: None" for
        # operations like DeleteLineRange, InsertBeforeLine, etc.
        file_edit_types = {
            "editfile",
            "readfile",
            "appendtext",
            "prependtext",
            "replacetext",
            "insertbeforeline",
            "insertafterline",
            "deletelinerange",
            "rewriteentirefile",
            "applypatch",
            "replacebypattern",
            "deletebypattern",
            "replacebyfuzzymatch",
            "insertattop",
            "insertatbottom",
            "insertblockatline",
            "replaceblock",
            "removeblock",
            "updatejsonkey",
            "updateyamlkey",
            "insertintofunction",
            "insertintoclass",
            "adddecorator",
            "addimport",
            "rewriteentirefile",
        }

        if canonical_lower in file_edit_types and not params.get("path"):
            # Prefer an explicit filename from the last user message.
            if last_user:
                file_name = self._extract_simple_file_path(last_user)
                if file_name:
                    params["path"] = file_name
            # Fallback to the active file when available.
            if not params.get("path") and active_file:
                params["path"] = active_file

        normalized["params"] = params

        # ----------------------------------------------------------------
        # INCOMPLETE EDITFILE UPGRADE
        # ----------------------------------------------------------------
        # Use ProviderNormalizer to detect incomplete edit actions and
        # attempt to upgrade them to structured intents via NL mapper.
        normalized = self._provider_normalizer.normalize_edit_action(normalized)

        if normalized.get("_incomplete"):
            # This action has missing content/text. Try to rescue it.
            upgraded = self._upgrade_incomplete_edit(normalized, last_user, active_file)
            if upgraded:
                return upgraded
            # If upgrade failed, remove the incomplete flag and let the
            # supervisor reject it with a proper error message.
            normalized.pop("_incomplete", None)
            normalized.pop("_missing_field", None)

        return normalized

    def _upgrade_incomplete_edit(
        self,
        action: Dict[str, Any],
        last_user_msg: Optional[str],
        active_file: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """
        Attempt to upgrade an incomplete EditFile action to a structured intent.

        When EditFile has content=None, we try to:
        1. Use NaturalLanguageEditMapper to parse the user's instruction
        2. Convert the resulting EditIntent to an action dict
        3. Return the upgraded action, or None if upgrade is not possible

        This prevents incomplete EditFile(content=None) from reaching the supervisor.
        """
        if not last_user_msg:
            return None

        action_type = (action.get("type") or "").lower()
        params = action.get("params") or {}
        path = params.get("path")

        # Only upgrade edit actions with missing content
        if action_type not in {"editfile", "createfile", "rewriteentirefile"}:
            return None

        # Build FileContext for the mapper
        file_ctx = None
        if path and active_file:
            # We don't have the file content here, but the mapper can work
            # with just the path for some patterns
            file_ctx = FileContext(path=path, content="")

        # Try to map the natural language instruction
        try:
            result = self._nl_mapper.map_instruction(
                last_user_msg,
                active_file=file_ctx,
                attached_block=None,  # No attached block in tool call context
            )

            if result.error or result.clarification:
                # Mapper couldn't resolve it, let it fail downstream
                return None

            if not result.intents:
                return None

            # Use the first intent as the upgraded action
            intent = result.intents[0]
            upgraded = {
                "type": intent.type,
                "params": dict(intent.params),
            }

            # Ensure the path is preserved
            if path and "path" not in upgraded["params"]:
                upgraded["params"]["path"] = path

            logger.info(
                f"Upgraded incomplete {action_type} to {intent.type} via NL mapper"
            )
            return upgraded

        except Exception as e:
            logger.warning(f"Failed to upgrade incomplete edit action: {e}")
            return None


    # ------------------------------------------------------------------
    # AI LIVE EDITOR MODE
    # ------------------------------------------------------------------

    async def run_live_edit_session(
        self,
        file_path: str,
        user_instruction: str,
        editor_panel,
    ):
        """
        Orchestrate AI live editing session.
        
        This method streams AI responses and applies edits directly to the
        EditorPanel buffer in real-time, without writing to disk.
        
        Args:
            file_path: Path to the file being edited
            user_instruction: User's natural language edit instruction
            editor_panel: EditorPanel instance to apply edits to
        
        Yields:
            Status messages for UI display
        
        Usage:
            async for message in chat_engine.run_live_edit_session(...):
                print(message)  # Show to user
        """
        from gitvisioncli.core.natural_language_mapper import LiveEditIntent
        
        # 1. Validate file is open in editor
        if not editor_panel.file_path or str(editor_panel.file_path) != file_path:
            yield f"❌ Error: File {file_path} is not open in editor"
            return
        
        # 2. Get current file content
        file_content = editor_panel.get_text()
        
        # 3. Build AI prompt
        system_msg = """You are editing a file live in an IDE. Your task is to make precise edits to the file based on the user's instruction.

You can use these edit operations:
- Delete lines: "delete lines X-Y"
- Replace lines: "replace lines X-Y with: <code>"
- Insert after line: "insert after line X: <code>"
- Append to end: "append: <code>"

Be precise with line numbers. Make minimal, targeted edits."""

        user_msg = f"""File: {file_path}

Current content:
```
{file_content}
```

Instruction: {user_instruction}

Please provide edit instructions."""

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]
        
        yield "🔄 Starting live edit session..."
        
        # 4. Stream AI responses and apply edits
        try:
            # Use existing streaming infrastructure
            if self.provider == "openai" and self.ai:
                async for chunk_msg in self._stream_live_edit_openai(messages, editor_panel):
                    yield chunk_msg
            else:
                # For other providers, use simpler text-based approach
                async for chunk_msg in self._stream_live_edit_generic(messages, editor_panel):
                    yield chunk_msg
            
            yield "✅ Live edit session complete"
            
        except Exception as e:
            logger.error(f"Live edit session failed: {e}", exc_info=True)
            yield f"❌ Error during live edit: {e}"

    async def _stream_live_edit_openai(self, messages, editor_panel):
        """Stream OpenAI responses and apply live edits."""
        from gitvisioncli.core.natural_language_mapper import LiveEditIntent
        
        try:
            stream = await self.ai.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                temperature=0.3,  # Lower temperature for precise edits
            )
            
            accumulated_text = ""
            
            async for chunk in stream:
                if not chunk.choices:
                    continue
                
                delta = chunk.choices[0].delta
                
                # Accumulate text content
                if delta and getattr(delta, "content", None):
                    accumulated_text += delta.content
            
            # Parse accumulated text for edit instructions
            if accumulated_text:
                yield f"📝 AI response: {accumulated_text[:100]}..."
                
                # Try to extract and apply edits from the text
                file_content = editor_panel.get_text()
                live_intents = self._nl_mapper.map_to_live_edits(
                    accumulated_text,
                    file_content,
                    attached_block=None
                )
                
                if live_intents:
                    for intent in live_intents:
                        result_msg = self._apply_live_edit_intent(intent, editor_panel)
                        yield result_msg
                else:
                    yield "⚠️  Could not parse edit instructions from AI response"
        
        except Exception as e:
            logger.error(f"OpenAI live edit stream failed: {e}")
            yield f"❌ Stream error: {e}"

    async def _stream_live_edit_generic(self, messages, editor_panel):
        """Stream generic provider responses and apply live edits."""
        from gitvisioncli.core.natural_language_mapper import LiveEditIntent
        
        # For non-OpenAI providers, get a single response
        try:
            # Build a simple prompt
            prompt = messages[-1]["content"]
            
            # This is a simplified version - in production you'd integrate
            # with the actual provider's streaming API
            yield "⚠️  Live editing with non-OpenAI providers is experimental"
            yield "💡 Tip: Use explicit instructions like 'delete lines 5-10'"
            
        except Exception as e:
            logger.error(f"Generic live edit failed: {e}")
            yield f"❌ Error: {e}"

    def _apply_live_edit_intent(self, intent: "LiveEditIntent", editor_panel) -> str:
        """
        Apply a single live edit intent to the editor panel.
        
        Returns a status message describing what was done.
        """
        try:
            if intent.type == "delete_range":
                editor_panel.delete_range(intent.start_line, intent.end_line)
                return f"✓ Deleted lines {intent.start_line}-{intent.end_line}"
            
            elif intent.type == "replace_range":
                editor_panel.replace_range(intent.start_line, intent.end_line, intent.new_text)
                line_count = len(intent.new_text.split("\n"))
                return f"✓ Replaced lines {intent.start_line}-{intent.end_line} with {line_count} new lines"
            
            elif intent.type == "insert_after":
                lines = intent.new_text.split("\n")
                editor_panel.insert_after(intent.start_line, lines)
                return f"✓ Inserted {len(lines)} lines after line {intent.start_line}"
            
            elif intent.type == "append":
                lines = intent.new_text.split("\n")
                for line in lines:
                    editor_panel.content.append(line)
                editor_panel._notify_change()
                editor_panel._set_modified(True)
                return f"✓ Appended {len(lines)} lines to end of file"
            
            else:
                return f"✗ Unknown intent type: {intent.type}"
        
        except Exception as e:
            logger.error(f"Failed to apply live edit intent: {e}")
            return f"✗ Edit failed: {e}"



    def _run_local_instruction_pass(self, assistant_text: str) -> List[str]:
        """
        Local instruction-execution layer for providers that do not have
        OpenAI tool support.

        Expected patterns:
          - One or more ```json fenced blocks containing {"action": {...}} or
            {"actions": [...]} payloads; or
          - A top-level JSON object/array with the same shape.

        This method is deterministic and uses ProviderNormalizer to
        clean fences and extract JSON blocks. It NEVER attempts to
        execute malformed JSON.
        """
        logs: List[str] = []
        text = self._provider_normalizer.normalize_fences(assistant_text or "")

        if not text.strip():
            return logs

        # Try fenced JSON blocks first.
        blocks = self._provider_normalizer.extract_json_blocks(text)

        # Fallback: single top-level JSON object or array without fences.
        if not blocks:
            try:
                obj = json.loads(text.strip())
            except json.JSONDecodeError:
                return logs

            if isinstance(obj, dict):
                blocks.append(obj)
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict):
                        blocks.append(item)

        actions: List[Dict[str, Any]] = []
        for obj in blocks:
            # Canonical shape: {"action": {...}} or {"actions": [...]}
            if "action" in obj and isinstance(obj["action"], dict):
                actions.append(obj["action"])
                continue
            if "actions" in obj and isinstance(obj["actions"], list):
                actions.extend([a for a in obj["actions"] if isinstance(a, dict)])
                continue

            # Gemini-style variant:
            # {"action": "execute_action", "tool_code": "CreateFolder", "parameters": {...}}
            if obj.get("action") == "execute_action":
                type_name = obj.get("tool_code") or obj.get("type")
                params = obj.get("parameters") or obj.get("params") or {}
                if isinstance(type_name, str) and isinstance(params, dict):
                    actions.append({"type": type_name, "params": params})
                continue

            # Simple variant:
            # {"action": "CreateFolder", "path": "demo", ...}
            if isinstance(obj.get("action"), str):
                type_name = obj.get("action")
                params = {k: v for k, v in obj.items() if k != "action"}
                if isinstance(type_name, str) and isinstance(params, dict):
                    actions.append({"type": type_name, "params": params})
                continue

            # Direct tool-style object:
            # {"type": "CreateFolder", "params": {...}}
            if isinstance(obj.get("type"), str) and isinstance(obj.get("params"), dict):
                actions.append({"type": obj["type"], "params": obj["params"]})
                continue

            # Minimal direct object:
            # {"type": "CreateFolder", "path": "demo", ...}
            if isinstance(obj.get("type"), str) and "params" not in obj:
                type_name = obj.get("type")
                params = {k: v for k, v in obj.items() if k != "type"}
                actions.append({"type": type_name, "params": params})

        if not actions:
            return logs

        logs.append("[Executing actions (local)]\n")

        for act in actions:
            # Reuse the same normalization layer as OpenAI tools so
            # provider-specific quirks (missing 'path', etc.) are
            # handled consistently for local JSON execution.
            normalized = self._normalize_tool_action(act)
            ctx = ActionContext()
            result = self.executor.run_action(normalized, ctx)
            self._track_last_modified(normalized, result)
            if result.status == ActionStatus.SUCCESS:
                logs.append(f"✓ {result.message}\n")
            else:
                err = result.error or ""
                if err:
                    logs.append(f"✗ {result.message}: {err}\n")
                else:
                    logs.append(f"✗ {result.message}\n")

        return logs

    async def _run_openai_tools_for_messages(
        self, messages: List[Dict[str, Any]]
    ) -> AsyncGenerator[str, None]:
        """
        Use the OpenAI client to detect and execute tool calls based on
        the given messages, without emitting any assistant text from
        OpenAI itself. This allows local providers (Ollama, Gemini,
        Claude) to share the same execute_action tool pipeline.
        """
        try:
            resp = await self.ai.complete_with_tools(
                messages=messages,
                tools=[self.EXECUTE_ACTION_TOOL],
                tool_choice="auto",
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except Exception as e:
            logger.warning(f"OpenAI tool detection failed: {e}")
            return

        choice = (resp.choices or [None])[0]
        if not choice or not getattr(choice, "message", None):
            return

        msg = choice.message
        raw_calls = []

        for tc in getattr(msg, "tool_calls", []) or []:
            raw_calls.append(
                {
                    "id": getattr(tc, "id", "") or "",
                    "type": "function",
                    "function": {
                        "name": getattr(getattr(tc, "function", None), "name", "") or "",
                        "arguments": getattr(getattr(tc, "function", None), "arguments", "") or "",
                    },
                }
            )

        tool_calls = [
            tc for tc in raw_calls if tc["function"]["name"].strip()
        ]

        if not tool_calls:
            return

        # Record the synthetic assistant message containing only tool calls.
        self.context.add_message("assistant", "", tool_calls=tool_calls)

        yield "\n\n[Executing actions...]\n\n"

        for tc in tool_calls:
            try:
                result_dict = await self._exec_tool(tc)

                self.context.add_tool_result(
                    tool_call_id=tc["id"],
                    content=json.dumps(result_dict),
                )

                if result_dict.get("status") == "success":
                    yield f"✓ {result_dict.get('message')}\n"
                else:
                    yield f"✗ {result_dict.get('message')}: {result_dict.get('error')}\n"

            except Exception as e:
                logger.error(f"Tool execution failed (OpenAI bridge): {e}")
                self.context.add_tool_result(
                    tool_call_id=tc["id"],
                    content=json.dumps(
                        {"status": "failure", "error": str(e)}
                    ),
                )
                yield f"✗ Critical Tool Error: {e}\n"

        yield "\n"

    def _get_model_max_context_tokens(self) -> int:
        """
        Best-effort max context window for the active engine.

        - Ollama uses a shared safe default.
        - Unknown models fall back to a conservative 32k window.
        """
        provider = (self.provider or "openai").lower()
        if provider == "ollama":
            return int(self.MODEL_LIMITS.get("ollama:*", 32768))

        model_name = self.model or ""
        # Direct lookup first
        if model_name in self.MODEL_LIMITS:
            return int(self.MODEL_LIMITS[model_name])

        # Allow simple normalization for OpenAI/Claude/Gemini aliases
        lower = model_name.lower()
        if lower.startswith("gpt-4.1") and "gpt-4.1" in self.MODEL_LIMITS:
            return int(self.MODEL_LIMITS["gpt-4.1"])
        if lower.startswith("gpt-4o-mini") and "gpt-4o-mini" in self.MODEL_LIMITS:
            return int(self.MODEL_LIMITS["gpt-4o-mini"])

        if lower.startswith("claude-3.5-sonnet") and "claude-3.5-sonnet" in self.MODEL_LIMITS:
            return int(self.MODEL_LIMITS["claude-3.5-sonnet"])

        if lower.startswith("gemini-1.5-pro") and "gemini-1.5-pro" in self.MODEL_LIMITS:
            return int(self.MODEL_LIMITS["gemini-1.5-pro"])

        return 32768

    def _extract_simple_cd_path(self, text: str) -> Optional[str]:
        """
        Best-effort extraction of a simple ChangeDirectory target from
        natural language such as:
          - "go to hi folder"
          - "go to hi directory"
        Returns None when no unambiguous folder name is found.
        """
        if not text:
            return None

        patterns = [
            # go to demo folder
            r"go\s+to\s+(?:the\s+)?(?P<name>[^\s/]+)\s+folder",
            r"go\s+to\s+(?:the\s+)?(?P<name>[^\s/]+)\s+directory",
            # go inside the demo folder / go into demo directory
            r"go\s+(?:inside|into)\s+(?:the\s+)?(?P<name>[^\s/]+)\s+folder",
            r"go\s+(?:inside|into)\s+(?:the\s+)?(?P<name>[^\s/]+)\s+directory",
            # enter demo folder
            r"enter\s+(?:the\s+)?(?P<name>[^\s/]+)\s+folder",
            r"enter\s+(?:the\s+)?(?P<name>[^\s/]+)\s+directory",
        ]

        for pat in patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if not m:
                continue
            name = m.group("name") or ""
            name = name.strip().strip("\"'")
            name = name.rstrip(".,;:")
            if name:
                return name

        # Handle contextual references like "make demo folder and go to it"
        # where the folder name is mentioned earlier in the same message
        contextual_patterns = [
            # "create demo folder and go to it"
            r"(?:make|create)\s+(?P<name>[^\s/]+)\s+(?:folder|directory)\s+and\s+go\s+to\s+(?:the\s+)?(?:folder|directory|it)",
            r"(?:make|create)\s+(?P<name>[^\s/]+)\s+(?:folder|directory)\s+and\s+go\s+(?:to\s+)?(?:it|there)",
            # "create folder demo and go to it" (reversed word order)
            r"create\s+(?:folder|directory)\s+(?P<name>[^\s/]+)\s+and\s+go\s+to\s+(?:the\s+)?(?:it|there|folder|directory)",
            # "create demo and go to it"
            r"create\s+(?P<name>[^\s/]+)\s+and\s+(?:cd|go)\s+(?:to\s+)?(?:it|there)",
        ]

        for pat in contextual_patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                name = m.group("name") or ""
                name = name.strip().strip("\"'")
                name = name.rstrip(".,;:")
                if name and name.lower() not in {"the", "a", "an", "this", "that", "folder", "directory"}:
                    return name

        return None

    def _extract_simple_folder_name(self, text: str) -> Optional[str]:
        """
        Best-effort extraction of a single folder name from simple
        phrases with comprehensive pattern matching.
        
        Handles all variations:
          - "create folder demo"
          - "create demo folder"
          - "make folder called demo"
          - "create folder in this dir call it demo"
          - "create folder here named demo"
        """
        if not text:
            return None

        patterns = [
            # "called/named X" patterns
            r"call(?:ed)?\s+it\s+(?P<name>[^\s]+)",
            r"called\s+(?P<name>[^\s]+)",
            r"named\s+(?P<name>[^\s]+)",
            
            # "create X folder" (name before folder)
            r"(?:create|make)\s+(?P<name>[^\s/]+)\s+(?:folder|directory)",
            
            # "create folder X" (folder before name)
            r"(?:create|make)\s+(?:folder|directory)(?:\s+here|\s+in\s+this\s+dir|\s+in\s+this\s+directory)?\s+(?P<name>[^\s/]+)",
            
            # "create a folder X" / "make a directory X"
            r"(?:create|make)\s+a\s+(?:folder|directory)\s+(?P<name>[^\s/]+)",
            
            # "new folder X" / "new directory X"
            r"new\s+(?:folder|directory)\s+(?P<name>[^\s/]+)",
        ]

        for pat in patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if not m:
                continue
            name = m.group("name") or ""
            name = name.strip().strip("\"'")
            name = name.rstrip(".,;:")
            if name and name.lower() not in {"the", "a", "an", "this", "that", "here", "there"}:
                return name

        return None

    def _extract_simple_file_path(self, text: str) -> Optional[str]:
        """
        Extract a probable file path or filename from free-form text.
        
        Handles comprehensive patterns:
          - "open demo.py"
          - "create file demo.py"
          - "edit src/main.py"
          - "delete test.txt"
          - "/Users/me/project/app.py"
        """
        if not text:
            return None

        # First try explicit file operation patterns
        file_operation_patterns = [
            r"(?:open|edit|create|delete|remove|update|modify)\s+(?:file\s+)?(?P<file>[A-Za-z0-9_\-./]+\.(?:py|js|ts|tsx|jsx|json|yaml|yml|toml|md|txt|ini|cfg|sh|bash|ps1|rb|go|rs|java|cs|cpp|c|h|hpp|css|scss|html|htm|xml|sql|r|m|swift|kt|php|pl|lua|vim))",
            r"(?:file|path)\s+(?P<file>[A-Za-z0-9_\-./]+\.(?:py|js|ts|tsx|jsx|json|yaml|yml|toml|md|txt|ini|cfg|sh|bash|ps1|rb|go|rs|java|cs|cpp|c|h|hpp|css|scss|html|htm|xml|sql|r|m|swift|kt|php|pl|lua|vim))",
        ]
        
        for pat in file_operation_patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                candidate = m.group("file") or ""
                candidate = candidate.strip().strip("\"'")
                candidate = candidate.rstrip(".,;:")
                if candidate:
                    return candidate

        # Fallback: Basic heuristic for common source / config file extensions
        pattern = re.compile(
            r"(?P<file>[A-Za-z0-9_\-./]+\."
            r"(?:py|js|ts|tsx|jsx|json|yaml|yml|toml|md|txt|ini|cfg|sh|bash|ps1|rb|go|rs|java|cs|cpp|c|h|hpp|css|scss|html|htm|xml|sql|r|m|swift|kt|php|pl|lua|vim))"
        )
        m = pattern.search(text)
        if not m:
            return None
        candidate = m.group("file") or ""
        candidate = candidate.strip().strip("\"'")
        candidate = candidate.rstrip(".,;:")
        return candidate or None

    def _estimate_token_usage(self) -> int:
        """
        Provider-neutral token estimator based on character count.

        Delegates to ContextManager.estimate_token_usage(), which
        uses a simple `len(content) / 3.5` heuristic over the full
        OpenAI-style message list (system + history).
        """
        try:
            return int(self.context.estimate_token_usage())
        except Exception as e:
            logger.warning(f"Token estimation failed, skipping auto-prune: {e}")
            return 0

    async def summarize_old_messages(self) -> None:
        """
        Summarize older conversation turns into ContextManager.summary_history.

        Triggered when total context usage exceeds ~75% of the model
        limit. This method:
          - Extracts all messages except the most recent tail (10–12).
          - Uses the OpenAI client (if available) to generate a compact
            5–8 line summary focused on code + workspace actions.
          - Stores the result in `context.summary_history`.
          - Prunes the live conversation to the last 6 user turns.

        This is provider-neutral: it always uses the OpenAI-backed
        AIClient when available, regardless of the active provider.
        """
        # Guard against re-entrancy and repeated summarization.
        if self._summary_in_progress:
            return
        if not self.ai:
            return

        # Avoid re-summarizing once a summary already exists for this
        # conversation context.
        if getattr(self.context, "summary_history", None):
            return

        # We need enough history to produce a meaningful summary.
        all_msgs = getattr(self.context, "messages", []) or []
        if len(all_msgs) <= 12:
            return

        self._summary_in_progress = True
        try:
            tail_keep = 12
            old_messages = all_msgs[:-tail_keep]
            if not old_messages:
                return

            # Render old messages into a plain text transcript without
            # workspace or system context, so we only summarize true
            # conversational turns.
            lines: List[str] = []
            for m in old_messages:
                try:
                    role = (getattr(m, "role", None) or "user").upper()
                    content = getattr(m, "content", "") or ""
                except Exception:
                    role = "USER"
                    content = ""
                if not content:
                    continue
                lines.append(f"{role}: {content}")

            if not lines:
                return

            transcript = "\n".join(lines)

            summary_instructions = (
                "You are summarizing old conversation turns for an IDE AI engine.\n"
                "Summarize the following messages into a compact 5–8 line block that preserves:\n"
                "- file operations the AI performed (create/edit/delete)\n"
                "- requested code changes\n"
                "- ongoing tasks / TODOs\n"
                "- important user goals\n"
                "- any critical instructions\n"
                "Remove greetings, small-talk, or irrelevant conversational text.\n"
                "Respond ONLY with the summary text. No explanations."
            )

            # Prefer the current OpenAI model when provider is OpenAI;
            # otherwise fall back to a stable default that should exist
            # when an OpenAI key is configured.
            summary_model: Optional[str]
            if (self.provider or "").lower() == "openai":
                summary_model = self.model
            else:
                summary_model = "gpt-4o-mini"

            summary_text = ""
            try:
                summary_text = await self.ai.ask_full(
                    system_prompt=summary_instructions,
                    user_prompt=transcript,
                    model=summary_model,
                    temperature=0.2,
                    max_tokens=512,
                )
            except Exception as e:
                logger.warning(f"Summarization call failed: {e}")
                return

            summary_text = (summary_text or "").strip()
            if not summary_text:
                return

            # Persist the summary and aggressively prune historical turns
            # to a compact recent window.
            self.context.summary_history = summary_text
            try:
                self.context.prune_messages(6)
            except Exception as e:
                logger.warning(f"Post-summary prune failed: {e}")

            # Expose a notice for the CLI to surface in the left panel.
            self._auto_summary_notice = "✓ Automatic summarization applied."

        finally:
            self._summary_in_progress = False

    async def _auto_prune_if_needed(self) -> None:
        """
        Automatically prune the conversation when close to the model's
        context limit.

        Heuristics:
          - usage > 95% → keep last 2 user turns
          - usage > 90% → keep last 4 user turns
          - usage > 85% → keep last 6 user turns

        If auto-prune has already run multiple times in this session,
        we gently increase the minimum turns kept so the model has a
        more stable working set of context.
        """
        max_ctx = self._get_model_max_context_tokens()
        if max_ctx <= 0:
            return

        approx_tokens = self._estimate_token_usage()
        if approx_tokens <= 0:
            return

        usage_ratio = approx_tokens / float(max_ctx)

        # First, if we are beyond ~75% of the context window and we have
        # an OpenAI client with no previous summary, summarize the oldest
        # portion of the conversation into ContextManager.summary_history.
        if (
            usage_ratio > 0.75
            and self.ai is not None
            and not getattr(self.context, "summary_history", None)
            and not self._summary_in_progress
        ):
            try:
                await self.summarize_old_messages()
                # Recalculate usage after summarization/pruning.
                approx_tokens = self._estimate_token_usage()
                usage_ratio = approx_tokens / float(max_ctx)
            except Exception as e:
                logger.warning(f"Automatic summarization failed, continuing without summary: {e}")

        # After optional summarization, apply stricter auto-prune thresholds.
        if usage_ratio <= 0.85:
            return

        if usage_ratio > 0.95:
            base_keep = 2
        elif usage_ratio > 0.90:
            base_keep = 4
        else:
            base_keep = 6

        # Adaptive safety: if pruning happens frequently, keep a
        # slightly larger minimum window of user turns so the model
        # has more stable context between turns.
        self._auto_prune_runs += 1
        if self._auto_prune_runs >= 3:
            # Bump the minimum kept turns slowly, capped to avoid
            # approaching the hard context limit too closely.
            self._auto_prune_min_kept_turns = min(
                self._auto_prune_min_kept_turns + 1,
                12,
            )

        keep_turns = max(base_keep, self._auto_prune_min_kept_turns)

        before_count = self.context.get_message_count()
        try:
            self.context.prune_messages(keep_turns)
        except Exception as e:
            logger.warning(f"Auto-prune failed, continuing without pruning: {e}")
            return

        after_count = self.context.get_message_count()
        if after_count < before_count:
            self._auto_prune_notice = (
                f"✓ Auto-prune applied to prevent context overflow (kept last {keep_turns} turns)."
            )

    def consume_auto_prune_notice(self) -> Optional[str]:
        """
        Return and clear the most recent auto-prune notice, if any.

        Intended for the CLI layer to surface a system message in the
        left panel without coupling ChatEngine to UI types.
        """
        notice = self._auto_prune_notice
        self._auto_prune_notice = None
        return notice

    def consume_auto_summary_notice(self) -> Optional[str]:
        """
        Return and clear the most recent auto-summary notice, if any.

        Intended for the CLI layer to surface a system message in the
        left panel without coupling ChatEngine to UI types.
        """
        notice = self._auto_summary_notice
        self._auto_summary_notice = None
        return notice

    # --------------------------------------------------------------------------------------
    # UTILS
    # --------------------------------------------------------------------------------------

    def get_base_dir(self) -> Path:
        """
        Current workspace base directory.

        IMPORTANT:
        Always delegate to the Executor so that any `cd` executed via
        TerminalEngine (shell commands, planner steps, etc.) is reflected.
        """
        try:
            return self.executor.get_base_dir()
        except Exception:
            # Fallback to initial base_dir if executor is unavailable
            return Path(self.base_dir)

    def get_last_modified_path(self) -> Optional[Path]:
        """
        Absolute path of the last file or folder modified via an INTERNAL
        action (CreateFile, EditFile, AppendText, etc.), if any.
        """
        if not self._last_modified_path:
            return None
        try:
            return Path(self._last_modified_path)
        except Exception:
            return None

    async def chat(self, user_input: str) -> str:
        out = ""
        async for chunk in self.stream(user_input):
            out += chunk
        return out

    def enable_dry_run(self) -> None:
        self.executor.enable_dry_run()

    def disable_dry_run(self) -> None:
        self.executor.disable_dry_run()

    @property
    def dry_run(self) -> bool:
        return self.executor.is_dry_run()

    def get_stats(self) -> Dict[str, Any]:
        return {
            "provider": getattr(self, "provider", "openai"),
            "model": self.model,
            "message_count": self.context.get_message_count(),
            "base_dir": str(self.get_base_dir()),
            "dry_run": self.executor.is_dry_run(),
            "github_enabled": bool(self._github_config),
        }

    # --------------------------------------------------------------------------------------
    # INTERNAL HELPERS
    # --------------------------------------------------------------------------------------

    def _messages_to_prompt(self, messages: List[Dict[str, Any]]) -> str:
        """
        Convert OpenAI-style messages into a plain text conversation prompt
        suitable for providers that do not support the same message schema.
        """
        parts: List[str] = []
        for m in messages:
            role = (m.get("role") or "user").upper()
            content = m.get("content") or ""
            parts.append(f"{role}: {content}")
        return "\n".join(parts)

    async def _complete_via_provider(
        self,
        messages: List[Dict[str, Any]],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """
        Unified, non-streaming completion wrapper for non-OpenAI providers.

        For OpenAI, tool-enabled streaming is handled separately in `stream()`,
        but this method still provides a plain-text fallback used in tests and
        in rare non-tool flows. For Gemini / Claude / Ollama we aggregate
        messages into a single text prompt and call the respective SDK or
        HTTP API.
        """
        provider = (self.provider or "openai").lower()
        prompt = self._messages_to_prompt(messages)

        raw: str
        if provider == "gemini":
            raw = await self._complete_gemini(prompt, temperature, max_tokens)
        elif provider == "claude":
            raw = await self._complete_claude(prompt, temperature, max_tokens)
        elif provider == "ollama":
            raw = await self._complete_ollama(prompt, temperature, max_tokens)
        elif provider == "openai" and self.ai:
            try:
                raw = await self.ai.ask_full(
                    system_prompt="",
                    user_prompt=prompt,
                    model=self.model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as e:
                logger.error(f"Fallback OpenAI completion failed: {e}")
                raw = ""
        else:
            raise ProviderNotConfiguredError(
                f"Provider '{provider}' is not supported by the plain completion path."
            )

        # Normalize provider-specific quirks in fences and return.
        return self._provider_normalizer.normalize_fences(raw)

    async def _complete_ollama(
        self, prompt: str, temperature: float, max_tokens: int
    ) -> str:
        """
        Call a local or remote Ollama instance via HTTP /api/generate.
        """
        base_url = self._ollama_config.get("base_url") or "http://127.0.0.1:11434"
        url = base_url.rstrip("/") + "/api/generate"

        def _call() -> str:
            try:
                payload: Dict[str, Any] = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        # Ollama uses `num_predict` as an approximate max-tokens analogue.
                        "num_predict": max_tokens,
                    },
                }
                resp = requests.post(url, json=payload, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                # Non-streaming /api/generate responses typically expose "response".
                text = data.get("response") or ""
                if isinstance(text, str):
                    return text
                return str(text)
            except Exception as e:
                logger.error(f"Ollama completion failed: {e}")
                return ""

        return await asyncio.to_thread(_call)

    async def _complete_gemini(
        self, prompt: str, temperature: float, max_tokens: int
    ) -> str:
        """
        Use the Google Generative AI Python SDK, if installed.
        """
        if not self._gemini_api_key:
            raise ProviderNotConfiguredError(
                "Gemini provider selected but no API key is configured."
            )

        try:
            import google.generativeai as genai  # type: ignore
        except ImportError:
            raise ProviderNotConfiguredError(
                "Gemini provider requires the 'google-generativeai' package. "
                "Install it with `pip install google-generativeai`."
            )

        def _call() -> str:
            try:
                genai.configure(api_key=self._gemini_api_key)
                model_name = self._normalize_model_for_provider("gemini", self.model)
                model = genai.GenerativeModel(model_name)
                resp = model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": float(temperature),
                        "max_output_tokens": int(max_tokens),
                    },
                )
                # Primary path: newer google-generativeai exposes .text
                text = getattr(resp, "text", None)
                if isinstance(text, str) and text.strip():
                    return text

                # Fallback: inspect candidates/content/parts for text.
                # This is defensive and avoids provider-version-specific
                # assumptions as much as possible.
                try:
                    candidates = getattr(resp, "candidates", None) or []
                    for cand in candidates:
                        content = getattr(cand, "content", None)
                        # content may be a list of parts or an object with .parts
                        parts = None
                        if isinstance(content, list):
                            parts = content
                        elif hasattr(content, "parts"):
                            parts = getattr(content, "parts")
                        if not parts:
                            continue
                        chunks = []
                        for part in parts:
                            pt = getattr(part, "text", None)
                            if not pt and isinstance(part, dict):
                                pt = part.get("text")
                            if pt:
                                chunks.append(pt)
                        if chunks:
                            return "".join(chunks)
                except Exception:
                    # If any of the introspection fails, fall through to
                    # the generic fallback below.
                    pass

                # Last resort: stringify the response so the user sees
                # something instead of an empty reply.
                try:
                    return str(resp)
                except Exception:
                    return ""
            except Exception as e:
                logger.error(f"Gemini completion failed: {e}")
                return ""

        return await asyncio.to_thread(_call)

    async def _complete_claude(
        self, prompt: str, temperature: float, max_tokens: int
    ) -> str:
        """
        Use the Anthropic Claude Python SDK, if installed.
        """
        if not self._claude_api_key:
            raise ProviderNotConfiguredError(
                "Claude provider selected but no API key is configured."
            )

        try:
            import anthropic  # type: ignore
        except ImportError:
            raise ProviderNotConfiguredError(
                "Claude provider requires the 'anthropic' package. "
                "Install it with `pip install anthropic`."
            )

        def _call() -> str:
            try:
                client = anthropic.Anthropic(api_key=self._claude_api_key)
                model_name = self._normalize_model_for_provider("claude", self.model)
                resp = client.messages.create(
                    model=model_name,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}],
                )
                parts: List[str] = []
                for block in getattr(resp, "content", []) or []:
                    text = getattr(block, "text", None)
                    if text:
                        parts.append(text)
                    elif isinstance(block, dict):
                        t = block.get("text")
                        if t:
                            parts.append(t)
                return "".join(parts)
            except Exception as e:
                logger.error(f"Claude completion failed: {e}")
                return "" # Ensure _call always returns a string
        return await asyncio.to_thread(_call)

    def _track_last_modified(self, action: Dict[str, Any], result: ActionResult) -> None:
        """
        Updates internal tracking of the last modified file and triggers UI refresh.
        """
        # 1. Track last modified path for "open editor" heuristics
        if result.status == ActionStatus.SUCCESS and result.data and "path" in result.data:
            self._last_modified_path = result.data["path"]

        # 2. Trigger UI Refresh if files were modified
        if result.modified_files:
            self.refresh_workspace(result.modified_files)

    def refresh_workspace(self, modified_files: List[str]) -> None:
        """
        Triggers immediate UI refresh for modified files.
        """
        if not self.fs_watcher:
            return

        # Use manual_trigger to notify all registered callbacks
        for file_path in modified_files:
            try:
                # Create FileChange event for each modified file
                from gitvisioncli.workspace.fs_watcher import FileChange
                from datetime import datetime
                
                change = FileChange(
                    path=Path(file_path),
                    change_type="ai_modify",
                    timestamp=datetime.now()
                )
                
                # Trigger all registered callbacks
                for callback in self.fs_watcher.on_change_callbacks:
                    try:
                        callback(change)
                    except Exception as e:
                        logger.warning(f"UI Refresh callback failed: {e}")
            except Exception as e:
                logger.warning(f"Failed to refresh workspace for {file_path}: {e}")


    # --------------------------------------------------------------------------------------
    # MODEL / ENGINE SWITCHING
    # --------------------------------------------------------------------------------------

    def set_model(self, model_name: str) -> None:
        """
        Hot-swap the active AI model/engine at runtime.

        - Updates ChatEngine.provider and ChatEngine.model.
        - Keeps a separate ContextManager per (provider, model) pair so each
          engine maintains its own conversation history and workspace context.
        """
        raw = (model_name or "").strip()
        if not raw:
            raise ValueError("Model name cannot be empty for set_model().")

        # Infer provider + normalized model name using the same heuristics
        # as initialization, but defaulting to the current provider.
        provider, normalized = ChatEngine.infer_provider_from_model_name(
            raw,
            default_provider=self.provider,
            openai_enabled=bool(self._openai_api_key),
        )

        # Normalize obviously mismatched names for non-OpenAI providers so a
        # generic label like "gemini" maps to a sensible default model.
        if provider in {"gemini", "claude"}:
            normalized = self._normalize_model_for_provider(provider, normalized)

        # Validate provider configuration before switching.
        self._ensure_provider_available(provider)

        # Reset auto-prune state for any model-change request so subsequent
        # turns start from a fresh context budget, even if the resolved
        # engine ends up being identical.
        self._auto_prune_runs = 0
        self._auto_prune_min_kept_turns = 0
        self._auto_prune_notice = None
        self._auto_summary_notice = None
        self._summary_in_progress = False

        if provider == self.provider and normalized == self.model:
            # Persist preference even if the resolved engine matches the
            # current one so it survives restarts.
            try:
                self._brain.remember("preferred_model", normalized)
            except Exception as e:
                logger.warning(f"Brain: failed to remember preferred model: {e}")
            return

        # Remember previous engine so we can revert on failure.
        current_key = self._engine_key
        self._previous_engine_key = current_key

        # Persist current context under current key
        self._contexts[current_key] = self.context

        # Look up or create context for the new engine
        new_key = self._make_engine_key(provider, normalized)
        if new_key in self._contexts:
            self.context = self._contexts[new_key]
        else:
            new_ctx = ContextManager()
            new_ctx.system_prompt = self.context.system_prompt
            new_ctx.workspace_summary = self.context.workspace_summary
            # Carry over any existing conversation summary so the
            # new engine still has access to compressed history.
            new_ctx.summary_history = getattr(self.context, "summary_history", None)
            self._contexts[new_key] = new_ctx
            self.context = new_ctx

        # Activate new engine
        self.provider = provider
        self.model = normalized
        self._engine_key = new_key

        # Keep OpenAI client + planner in sync for OpenAI engines only.
        if provider == "openai" and self.ai:
            self.ai.default_model = normalized
            if self.planner:
                self.planner.model = normalized

        # Persist the user's preferred model for this project so that
        # subsequent sessions can restore it without additional config.
        try:
            self._brain.remember("preferred_model", normalized)
        except Exception as e:
            logger.warning(f"Brain: failed to remember preferred model: {e}")

        logger.info(
            f"ChatEngine engine switched to provider={provider}, model={normalized}"
        )

    def revert_model(self) -> Optional[str]:
        """
        Revert to the previous engine (if any) after a failure such as
        'model_not_found'. Returns a human-friendly label for the engine
        we reverted to (e.g., 'openai/gpt-4o-mini'), or None if no previous
        engine is known.
        """
        if not self._previous_engine_key or self._previous_engine_key == self._engine_key:
            return None

        target_key = self._previous_engine_key

        try:
            provider, model_name = target_key.split("::", 1)
        except ValueError:
            # Backwards-compat: if the key is malformed, assume OpenAI.
            provider, model_name = "openai", target_key

        # Save current context under current key
        self._contexts[self._engine_key] = self.context

        # Restore previous context if we have one; otherwise create a fresh one.
        if target_key in self._contexts:
            self.context = self._contexts[target_key]
        else:
            ctx = ContextManager()
            ctx.system_prompt = self.context.system_prompt
            ctx.workspace_summary = self.context.workspace_summary
            self._contexts[target_key] = ctx
            self.context = ctx

        self.provider = provider
        self.model = model_name
        self._engine_key = target_key

        # Keep OpenAI client + planner aligned when reverting to OpenAI.
        if provider == "openai" and self.ai:
            self.ai.default_model = model_name
            if self.planner:
                self.planner.model = model_name

        # Reset auto-prune state when reverting engines.
        self._auto_prune_runs = 0
        self._auto_prune_min_kept_turns = 0
        self._auto_prune_notice = None
        self._auto_summary_notice = None
        self._summary_in_progress = False

        logger.info(f"ChatEngine model reverted to: {provider}/{model_name}")
        return f"{provider}/{model_name}"
