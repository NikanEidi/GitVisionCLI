# gitvisioncli/features/code_review.py
"""
Code Review Plugin

Modular plugin for code review functionality.
Refactored to use plugin architecture.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import json

from gitvisioncli.plugins.base_plugin import BasePlugin, PluginMetadata


class CodeReviewPlugin(BasePlugin):
    """
    GitVision – Code Review Plugin
    
    Performs:
      - Full static analysis
      - Multi-language detection (30+)
      - JSON-structured review output
    
    Refactored to use modular plugin architecture.
    """

    def __init__(self):
        """Initialize code review plugin."""
        metadata = PluginMetadata(
            name="code_review",
            version="1.0.0",
            description="Advanced code review with multi-language support",
            author="GitVisionCLI"
        )
        super().__init__(metadata)
        self.chat = None
    
    def initialize(self, context: Dict[str, Any]) -> None:
        """Initialize plugin with chat engine."""
        self.chat = context.get("chat_engine")
        if not self.chat:
            raise ValueError("CodeReviewPlugin requires chat_engine in context")
    
    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        self.chat = None
    
    def can_handle(self, command: str, context: Dict[str, Any]) -> bool:
        """Check if plugin can handle code review command."""
        return command.lower() in ("review", "code_review", "analyze_code")
    
    def handle_command(self, command: str, params: Dict[str, Any], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle code review command."""
        if not self.can_handle(command, context):
            return None
        
        file_path = params.get("file_path")
        if file_path:
            # Async method - would need async handling in real implementation
            return {"action": "review_file", "file_path": file_path}
        
        code_text = params.get("code_text")
        if code_text:
            return {"action": "review_text", "code_text": code_text}
        
        return None
    
    def get_commands(self) -> List[str]:
        """Get commands this plugin handles."""
        return ["review", "code_review", "analyze_code"]


# Legacy compatibility - keep original class name
class CodeReviewer:
    """
    Legacy CodeReviewer class for backward compatibility.
    Wraps CodeReviewPlugin.
    """
    
    def __init__(self, chat_engine):
        """Initialize legacy code reviewer."""
        self.chat = chat_engine

    async def review_file(self, file_path: str) -> Dict[str, Any]:
        """Reviews a file from the local filesystem."""
        path = Path(file_path)
        if not path.exists():
            return {"error": f"File not found: {file_path}"}

        code = path.read_text(encoding="utf-8", errors="ignore")
        return await self._review(code, filename=path.name)

    async def review_text(self, code_text: str) -> Dict[str, Any]:
        """Reviews a raw string of code."""
        return await self._review(code_text, filename=None)

    async def _review(self, code: str, filename: Optional[str]) -> Dict[str, Any]:
        """Internal review logic."""
        lang = self._detect_language(filename, code)
        prompt = self._build_prompt(code, lang, filename)
        # Call the ChatEngine's non-streaming method
        ai_response = await self.chat.ask_full(prompt)
        # CRITICAL FIX: Strip ANSI codes from AI response before parsing
        ai_response = self._strip_ansi(ai_response)
        return self._parse_response(ai_response)
    
    def _strip_ansi(self, text: str) -> str:
        """Strip ANSI escape codes from text."""
        import re
        # Comprehensive ANSI escape code pattern
        ansi_re = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\033\[[0-9;]*[a-zA-Z]")
        # Pattern for corrupted ANSI sequences (missing ESC prefix)
        corrupted_ansi_re = re.compile(r"\[[0-9;]+m|[0-9;]+m")
        
        # First remove full ANSI sequences
        text = ansi_re.sub("", text)
        # Then remove any corrupted/partial ANSI sequences
        text = corrupted_ansi_re.sub("", text)
        return text

    def _detect_language(self, filename: Optional[str], code: str) -> str:
        """Heuristic-based language detection."""
        ext_map = {
            ".py": "python", ".js": "javascript", ".jsx": "jsx",
            ".ts": "typescript", ".tsx": "tsx", ".html": "html",
            ".css": "css", ".scss": "scss", ".vue": "vue", ".svelte": "svelte",
            ".go": "go", ".rs": "rust", ".java": "java", ".kt": "kotlin",
            ".rb": "ruby", ".php": "php", ".c": "c", ".h": "c-header",
            ".cpp": "cpp", ".cc": "cpp", ".hpp": "cpp-header",
            ".cs": "csharp", ".json": "json", ".md": "markdown",
            ".yml": "yaml", ".yaml": "yaml", ".sh": "bash", ".bat": "batch",
            ".sql": "sql", ".r": "r", ".tf": "terraform", ".ini": "ini",
            ".cfg": "config", ".toml": "toml"
        }

        if filename:
            fname = filename.lower()
            if fname == "dockerfile":
                return "dockerfile"

            for ext, lang in ext_map.items():
                if fname.endswith(ext):
                    return lang

        # Fallback to content sniffing
        code_lower = code.lower()

        if "def " in code or "import " in code:
            return "python"
        if "function " in code or "console.log" in code_lower:
            return "javascript"
        if "class " in code and "public static void main" in code_lower:
            return "java"
        if "#include <" in code:
            return "cpp"
        if "fn main()" in code:
            return "rust"
        if "resource " in code_lower:
            return "terraform"
        if "select " in code_lower or "insert into" in code_lower:
            return "sql"

        return "unknown"

    def _build_prompt(self, code: str, lang: str, filename: Optional[str]):
        """Builds the specialized JSON-only prompt for the AI."""
        file_info = f"File: {filename}" if filename else "Direct input"

        return f"""
You are GitVision — an advanced AI code-review system.

Perform a complete analysis of the code:
- detect bugs, security vulnerabilities, anti-patterns
- detect unused imports/variables
- detect complexity issues
- detect performance issues
- detect readability and structure issues
- detect framework issues (if applicable)
- detect unsafe patterns (shell, regex, SQL injection, etc.)
- generate severity counters
- generate clear refactor suggestions

⚠️ RESPONSE MUST BE PURE JSON.  
⚠️ DO NOT include explanations outside the JSON.

Use EXACTLY this format:

{{
  "summary": "short overview",
  "issues": [
    {{
      "type": "bug | warning | style | improvement | security",
      "line": number or null,
      "description": "...",
      "suggestion": "..."
    }}
  ],
  "overall_quality": "excellent | good | needs improvement | poor",
  "severity_count": {{
    "critical": number,
    "warnings": number,
    "info": number
  }},
  "refactor_suggestions": [
    "suggestion 1",
    "suggestion 2"
  ]
}}

Code context:
- Language: {lang}
- {file_info}

Review this code:

```code
{code}
```
"""
def _parse_response(self, text: str) -> Dict[str, Any]:
    """Safely parses the AI's JSON response."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "error": "JSON parsing failed",
            "raw_response": text
        }