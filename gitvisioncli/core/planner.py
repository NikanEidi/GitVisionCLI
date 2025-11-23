# gitvisioncli/core/planner.py
"""
GitVisionCLI Action Planner
Reasoning engine that converts natural language intents into executable plans.
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from gitvisioncli.core.ai_client import AIClient

logger = logging.getLogger(__name__)

class PlanStepType(Enum):
    SHELL = "shell"           # Run a shell command
    INTERNAL = "internal"     # Run a Supervisor Action (CreateFile, GitCommit, etc.)
    AI_EXPLAIN = "ai-explain" # Just explain something to the user

@dataclass
class PlanStep:
    """A single step in an execution plan."""
    kind: PlanStepType
    command: str
    description: str
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind.value,
            "command": self.command,
            "description": self.description,
            "params": self.params
        }

@dataclass
class Plan:
    """A sequence of steps to achieve a goal."""
    goal: str
    steps: List[PlanStep] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "steps": [s.to_dict() for s in self.steps]
        }

class ActionPlanner:
    """
    The 'Pre-frontal Cortex' of GitVision.
    Decides if a request needs a complex plan or a simple tool call.
    """

    def __init__(self, ai_client: AIClient, model: str = "gpt-4o-mini"):
        self.ai = ai_client
        self.model = model

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        FIX 3.2: Robust JSON extraction using regex to find the main object.
        Handles Markdown code blocks and surrounding conversational text.
        """
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find code block first
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Fallback: find raw JSON object start/end
        try:
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                json_str = text[start:end+1]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
            
        return None

    async def create_plan(self, user_input: str, context_summary: str) -> Optional[Plan]:
        """
        Analyze user input and generate a multi-step plan if complex.
        Returns None if the request is simple enough for direct chat handling.
        """
        
        # FIX 3.1: Improved complexity heuristic
        # Triggers on explicit sequential logic, high-level goals, or
        # multi-file search/refactor requests. Line-based edits like
        # "remove lines 10-20" or "debug from line 30 to 40" are treated
        # as simple requests and handled directly by the ChatEngine
        # without a planning phase.
        triggers = [
            " then ", " after ", " and finally ", " first ", 
            "create a project", "scaffold", "setup", "initialize",
            "search for ", "find all", "replace all", "across files",
            "across the codebase", "in the whole project",
        ]
        
        u_lower = user_input.lower()
        is_complex = any(t in u_lower for t in triggers)

        # Treat explicit line-range edits as simple. These should go
        # straight to execute_action (DeleteLineRange, InsertBeforeLine,
        # InsertAfterLine, ApplyPatch) rather than a multi-step plan.
        line_edit_pattern = re.compile(r"\blines?\s+\d+(\s*-\s*\d+)?")
        if line_edit_pattern.search(u_lower) or "from line" in u_lower:
            is_complex = False
        
        # Also check for multiple distinct commands separated by explicit " and "
        # Only if input is long enough to likely be a compound command
        if " and " in u_lower and len(user_input.split()) > 8:
            is_complex = True

        if not is_complex:
            return None

        logger.info("Planner activated for complex request.")

        system_prompt = (
            "You are the Strategic Planner for GitVisionCLI.\n"
            "Your goal is to break down complex user requests into a sequential list of executable steps.\n"
            "\n"
            "AVAILABLE ACTIONS (INTERNAL):\n"
            "- File operations: CreateFile, EditFile, ReadFile, DeleteFile, CreateFolder, DeleteFolder\n"
            "- Text edits: AppendText, PrependText, ReplaceText, InsertBeforeLine,\n"
            "             InsertAfterLine, DeleteLineRange, RewriteEntireFile\n"
            "- Git operations: GitInit, GitAdd, GitCommit, GitPush, GitPull,\n"
            "                 GitBranch, GitCheckout, GitMerge, GitRemote\n"
            "- GitHub operations: GitHubCreateRepo, GitHubDeleteRepo, GitHubPushPath (only if configured)\n"
            "\n"
            "PARAMETER RULES FOR INTERNAL ACTIONS:\n"
            '- CreateFolder: params = {"path": "relative/or/absolute/folder"}\n'
            '- DeleteFolder: params = {"path": "relative/or/absolute/folder"}\n'
            '- CreateFile:   params = {"path": "path/to/file", "content": "file contents"}\n'
            '- EditFile:     params = {"path": "path/to/file", "content": "new contents"}\n'
            '- ReadFile:     params = {"path": "path/to/file"}\n'
            '- DeleteFile:   params = {"path": "path/to/file"}\n'
            "All INTERNAL steps MUST include the required params; never leave them empty.\n"
            "\n"
            "CANONICAL GIT + GITHUB PIPELINE:\n"
            "- For a NEW repository that should be synced with GitHub you MUST use the following order:\n"
            "  1) CreateFolder / CreateFile steps to build the workspace tree.\n"
            "  2) GitInit (once per workspace, never via shell).\n"
            "  3) GitAdd with {\"files\": [\".\"]} to stage all relevant changes.\n"
            "  4) GitCommit with a clear message.\n"
            "  5) GitHubCreateRepo (private/public as requested) and then GitRemote to point 'origin' at it\n"
            "     (or rely on the Supervisor's automatic remote sync after GitHubCreateRepo).\n"
            "  6) Either GitPush (using the configured remote/branch) OR GitHubPushPath to sync the local\n"
            "     filesystem into the GitHub repository.\n"
            "- NEVER call RunShellCommand with raw 'git ...' or 'gh ...' for standard workflows; always\n"
            "  prefer the dedicated INTERNAL git / GitHub actions listed above.\n"
            "\n"
            "Shell steps are for commands like 'pip install', 'npm test', 'ls -la'.\n"
            "For any filesystem, git, or GitHub change you MUST use an INTERNAL action.\n"
            "\n"
            "OUTPUT FORMAT:\n"
            "You must respond with PURE JSON only. No markdown formatting.\n"
            "Structure:\n"
            "{\n"
            '  "goal": "Summary of the plan",\n'
            '  "steps": [\n'
            '    {\n'
            '      "kind": "shell" | "internal",\n'
            '      "command": "command string or ActionName",\n'
            '      "description": "What this step does",\n'
            '      "params": { ... } // Only for internal actions. MUST be a dictionary.\n'
            '    }\n'
            '  ]\n'
            "}\n"
            "\n"
            "Do NOT invent new internal action names. Only use the ones listed above.\n"
            "\n"
            f"CONTEXT:\n{context_summary}\n"
        )

        try:
            response_text = await self.ai.ask_full(
                system_prompt=system_prompt,
                user_prompt=f"Create a plan for: {user_input}",
                model=self.model,
                temperature=0.2 
            )
            
            # FIX 3.2: Safe JSON extraction
            plan_data = self._extract_json(response_text)
            
            if not plan_data or "steps" not in plan_data:
                logger.warning("Planner failed to generate valid JSON plan.")
                return None
            
            steps = []
            for s in plan_data.get("steps", []):
                kind_str = s.get("kind", "ai-explain").lower()
                
                # FIX 3.3: Safer enum conversion
                try:
                    kind = PlanStepType(kind_str)
                except ValueError:
                    kind = PlanStepType.AI_EXPLAIN
                
                # FIX 3.4: Validate params shape
                params = s.get("params", {})
                if not isinstance(params, dict):
                    params = {}

                # FIX 3.5: Enforce required params for common INTERNAL file actions.
                command_raw = s.get("command", "Unknown")
                if isinstance(command_raw, str):
                    command = command_raw.strip()
                else:
                    command = str(command_raw)

                if kind == PlanStepType.INTERNAL:
                    cmd_lower = command.lower()
                    needs_path = cmd_lower in {
                        "createfile",
                        "editfile",
                        "readfile",
                        "deletefile",
                        "createfolder",
                        "deletefolder",
                    }
                    if needs_path and not params.get("path"):
                        logger.warning(
                            "Planner produced INTERNAL step '%s' without required 'path'; "
                            "dropping plan and falling back to direct tool execution.",
                            command,
                        )
                        # Abort the entire plan so ChatEngine falls back to the
                        # standard execute_action tool path, which enforces params.
                        return None

                description_raw = s.get("description", "Execute step")
                if isinstance(description_raw, str):
                    description = description_raw
                else:
                    description = str(description_raw)

                steps.append(
                    PlanStep(
                        kind=kind,
                        command=command,
                        description=description,
                        params=params,
                    )
                )
                
            if not steps:
                return None

            return Plan(goal=plan_data.get("goal", "Execute task"), steps=steps)

        except Exception as e:
            logger.error(f"Planning failed: {e}")
            return None
