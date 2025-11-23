"""
Model Manager Panel — AI engine and model overview for the right panel.

Shows:
- Currently configured AI engine (provider + model)
- Presence of API keys (OpenAI / Gemini / Claude) without exposing secrets
- Available OpenAI models (via API, when configured)
- Installed Ollama models (via local CLI, when available)
"""

import shutil
import subprocess
from typing import List, Dict, Any, Optional

from gitvisioncli.ui.colors import (
    RESET,
    BOLD,
    DIM,
    NEON_PURPLE,
    BRIGHT_MAGENTA,
    ELECTRIC_CYAN,
    MID_GRAY,
    DARK_GRAY,
    GLITCH_GREEN,
    GLITCH_RED,
)
from gitvisioncli.config.settings import load_config
from gitvisioncli.core.chat_engine import ChatEngine


class ModelManagerPanel:
    def __init__(self, width: int = 80):
        self.width = width
        # Lazy caches so we don't re-query APIs on every frame.
        self._openai_models: List[str] = []
        self._openai_models_error: Optional[str] = None
        self._ollama_models: List[str] = []
        self._ollama_models_error: Optional[str] = None

    def _strip_ansi(self, text: str) -> str:
        import re

        ansi_pattern = re.compile(r"\x1b\[[0-9;]*m")
        return ansi_pattern.sub("", text)

    def _fit_line(self, text: str, width: int) -> str:
        length = len(text)
        if length == width:
            return text
        if length < width:
            return text + (" " * (width - length))
        if width <= 1:
            return text[:1]
        return text[: width - 1] + "…"

    def _center_line(self, text: str) -> str:
        raw_len = len(self._strip_ansi(text))
        if raw_len >= self.width:
            return text
        pad = (self.width - raw_len) // 2
        return (" " * pad) + text

    def _load_config_safe(self) -> dict:
        try:
            return load_config()
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # PROVIDER / MODEL DISCOVERY
    # ------------------------------------------------------------------

    def _load_openai_models(self, cfg: Dict[str, Any]) -> None:
        """
        Populate self._openai_models with IDs returned by the OpenAI API.
        Safe to call multiple times; it will only query once per session.
        """
        if self._openai_models or self._openai_models_error:
            return

        providers = cfg.get("providers", {}) or {}
        api_key = cfg.get("api_key") or (providers.get("openai") or {}).get("api_key")
        if not api_key:
            self._openai_models_error = "No OpenAI API key configured."
            return

        try:
            from openai import OpenAI  # type: ignore
        except Exception:
            self._openai_models_error = (
                "OpenAI Python SDK not available. Install 'openai>=1.40.0'."
            )
            return

        try:
            client = OpenAI(api_key=api_key)
            resp = client.models.list()
            discovered: List[str] = []
            for m in getattr(resp, "data", []) or []:
                mid = getattr(m, "id", None)
                if mid is None and isinstance(m, dict):
                    mid = m.get("id")
                if not isinstance(mid, str):
                    continue
                # Prefer chat/completions-capable models.
                if mid.startswith(("gpt-", "o1-", "o3-")):
                    discovered.append(mid)
            self._openai_models = sorted(set(discovered))
        except Exception as e:
            self._openai_models_error = str(e)

    def _load_ollama_models(self) -> None:
        """
        Populate self._ollama_models using `ollama list`, when available.
        """
        if self._ollama_models or self._ollama_models_error:
            return

        ollama_bin = shutil.which("ollama")
        if not ollama_bin:
            self._ollama_models_error = "Ollama CLI not found on PATH."
            return

        try:
            proc = subprocess.run(
                [ollama_bin, "list"],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            models: List[str] = []
            lines = proc.stdout.splitlines()
            # Skip header row if present.
            for line in lines[1:] if lines and "MODEL" in lines[0] else lines:
                parts = line.split()
                if parts:
                    models.append(parts[0])
            self._ollama_models = models
        except Exception as e:
            self._ollama_models_error = str(e)

    def _ollama_section(self) -> List[str]:
        lines: List[str] = []
        header = f"{BOLD}{ELECTRIC_CYAN}╔═══ Ollama (Local Models) ═══╗{RESET}"
        lines.append(self._center_line(header))
        lines.append("")

        ollama_bin = shutil.which("ollama")
        if ollama_bin:
            ok = f"{GLITCH_GREEN}●{RESET}"
            lines.append(
                f"  {ok} Ollama detected at: {DIM}{MID_GRAY}{ollama_bin}{RESET}"
            )
            self._load_ollama_models()
            if self._ollama_models:
                sample = ", ".join(self._ollama_models[:5])
                extra = ""
                if len(self._ollama_models) > 5:
                    extra = f" {DIM}{MID_GRAY}(+{len(self._ollama_models) - 5} more){RESET}"
                lines.append(
                    f"  {DIM}{MID_GRAY}Installed models:{RESET} "
                    f"{BOLD}{BRIGHT_MAGENTA}{sample}{RESET}{extra}"
                )
            elif self._ollama_models_error:
                lines.append(
                    f"  {GLITCH_RED}○{RESET} {DIM}{MID_GRAY}{self._ollama_models_error}{RESET}"
                )
            lines.append(
                f"  {DIM}{MID_GRAY}Use{RESET} {BOLD}{BRIGHT_MAGENTA}ollama models{RESET} "
                f"{DIM}{MID_GRAY}to list installed models.{RESET}"
            )
            lines.append(
                f"  {DIM}{MID_GRAY}Install recommended models with:{RESET} "
                f"{BOLD}{BRIGHT_MAGENTA}ollama pull qwen2.5-coder:14b{RESET}"
            )
        else:
            warn = f"{GLITCH_RED}○{RESET}"
            lines.append(
                f"  {warn} Ollama not found on PATH. Install from {DIM}{MID_GRAY}https://ollama.com{RESET}"
            )
            lines.append(
                f"  {DIM}{MID_GRAY}After installation, restart GitVisionCLI and use cross-OS shells{RESET}"
            )
            lines.append(
                f"  {DIM}{MID_GRAY}to run:{RESET} {BOLD}{BRIGHT_MAGENTA}ollama pull qwen2.5-coder:14b{RESET}"
            )
        return lines

    def _providers_section(self, cfg: dict) -> List[str]:
        lines: List[str] = []
        header = f"{BOLD}{ELECTRIC_CYAN}╔═══ API Providers (Config) ═══╗{RESET}"
        lines.append(self._center_line(header))
        lines.append("")

        providers = cfg.get("providers", {})

        def status_line(name: str, key: bool) -> str:
            bullet = f"{GLITCH_GREEN}●{RESET}" if key else f"{GLITCH_RED}○{RESET}"
            state = "key configured" if key else "missing key"
            return (
                f"  {bullet} {BOLD}{BRIGHT_MAGENTA}{name:<8}{RESET}"
                f" {DIM}{MID_GRAY}{state} (stored in config.json){RESET}"
            )

        openai_present = bool(cfg.get("api_key") or providers.get("openai", {}).get("api_key"))
        gemini_present = bool(providers.get("gemini", {}).get("api_key"))
        claude_present = bool(providers.get("claude", {}).get("api_key"))

        lines.append(status_line("OpenAI", openai_present))
        lines.append(status_line("Gemini", gemini_present))
        lines.append(status_line("Claude", claude_present))

        lines.append("")
        lines.append(
            f"{DIM}{DARK_GRAY}Use the model manager (:models) to add, replace, or remove keys without{RESET}"
        )
        lines.append(
            f"{DIM}{DARK_GRAY}breaking other configuration values in config.json.{RESET}"
        )
        return lines

    def _openai_models_section(self, cfg: dict) -> List[str]:
        lines: List[str] = []
        header = f"{BOLD}{ELECTRIC_CYAN}╔═══ OpenAI Models (Live) ═══╗{RESET}"
        lines.append(self._center_line(header))
        lines.append("")

        self._load_openai_models(cfg)

        if self._openai_models_error:
            lines.append(
                f"  {GLITCH_RED}○{RESET} {DIM}{MID_GRAY}{self._openai_models_error}{RESET}"
            )
        elif self._openai_models:
            sample = self._openai_models[:8]
            for mid in sample:
                lines.append(
                    f"  {GLITCH_GREEN}●{RESET} {BOLD}{BRIGHT_MAGENTA}{mid}{RESET}"
                )
            if len(self._openai_models) > len(sample):
                remaining = len(self._openai_models) - len(sample)
                lines.append(
                    f"  {DIM}{MID_GRAY}... and {remaining} more. "
                    f"Use the OpenAI dashboard or CLI for the full list.{RESET}"
                )
        else:
            lines.append(
                f"  {GLITCH_RED}○{RESET} {DIM}{MID_GRAY}No models discovered. "
                f"Check your OpenAI key and network connectivity.{RESET}"
            )

        return lines

    def _current_model_section(self, cfg: dict) -> List[str]:
        lines: List[str] = []
        header = f"{BOLD}{ELECTRIC_CYAN}╔═══ Current AI Engine ═══╗{RESET}"
        lines.append(self._center_line(header))
        lines.append("")
        current_model_raw = cfg.get("model") or "gpt-4o-mini"
        provider_hint = (cfg.get("active_provider") or "openai").lower()
        providers = cfg.get("providers", {}) or {}
        openai_key = cfg.get("api_key") or (providers.get("openai") or {}).get("api_key")

        # Use the same inference logic as ChatEngine so the Model Manager
        # reflects the actual provider/model pair instead of blindly
        # trusting possibly stale config values.
        try:
            provider_norm, model_norm = ChatEngine.infer_provider_from_model_name(
                current_model_raw,
                default_provider=provider_hint,
                openai_enabled=bool(openai_key),
            )
        except Exception:
            provider_norm = provider_hint
            model_norm = current_model_raw

        # Ultra-vibrant active engine display with glow effect
        engine_icon = f"{BOLD}{ELECTRIC_CYAN}⚡{RESET}"
        line = (
            f"  {engine_icon} {BOLD}{BRIGHT_MAGENTA}Active:{RESET} "
            f"{BOLD}{ELECTRIC_CYAN}{provider_norm}{RESET}{BOLD}{BRIGHT_MAGENTA}/{RESET}{BOLD}{NEON_PURPLE}{model_norm}{RESET}"
        )
        lines.append(line)

        lines.append(
            f"  {DIM}{MID_GRAY}Switch engines instantly with:{RESET} "
            f"{BOLD}{BRIGHT_MAGENTA}:set-ai <name>{RESET}"
        )
        lines.append(
            f"  {DIM}{MID_GRAY}Examples:{RESET} "
            f"{BOLD}{BRIGHT_MAGENTA}:set-ai qwen2.5-coder:14b{RESET}, "
            f"{BOLD}{BRIGHT_MAGENTA}:set-ai llama3.1{RESET}, "
            f"{BOLD}{BRIGHT_MAGENTA}:set-ai gemini-pro{RESET}"
        )
        return lines

    def render_content_lines(self) -> List[str]:
        cfg = self._load_config_safe()
        lines: List[str] = []

        # Ultra-vibrant title with gradient effect
        title = f"{BOLD}{ELECTRIC_CYAN}╔═══{RESET}{BOLD}{NEON_PURPLE} AI ENGINE / MODEL MANAGER {RESET}{BOLD}{ELECTRIC_CYAN}═══╗{RESET}"
        lines.append(self._center_line(title))
        separator = f"{BOLD}{BRIGHT_MAGENTA}{'═' * min(self.width - 4, 50)}{RESET}"
        sep_pad = max(0, (self.width - len(self._strip_ansi(separator))) // 2)
        lines.append(" " * sep_pad + separator)
        lines.append("")

        # Current model
        lines += self._current_model_section(cfg)
        lines.append("")

        # OpenAI model catalogue (if configured)
        lines += self._openai_models_section(cfg)
        lines.append("")

        # Ollama
        lines += self._ollama_section()
        lines.append("")

        # Providers / API keys
        lines += self._providers_section(cfg)
        lines.append("")

        footer = (
            f"{DIM}{DARK_GRAY}All engines share the same workspace but keep their own chat history."
            f"{RESET}"
        )
        lines.append(footer)

        return lines
