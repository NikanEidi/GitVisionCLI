# gitvisioncli/features/project_generator.py
"""
Project Generator — GitVisionCLI
Creates full professional project structures from a high-level AI plan.
Supports Python, JavaScript, CLI tools, APIs, and custom layouts.

STABILIZED: This class is now a feature that uses the AIActionExecutor
to safely perform all file operations, ensuring it respects the sandbox
and updates the UI.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List

# Import the executor and supervisor types for correct operation
from gitvisioncli.core.executor import AIActionExecutor
from gitvisioncli.core.supervisor import ActionType, ActionResult, ActionContext

logger = logging.getLogger(__name__)

class ProjectGenerator:
    """
    Core engine for generating entire project structures.
    Uses the AIActionExecutor to run a batch of file/folder creation actions.
    """

    def __init__(self, executor: AIActionExecutor):
        self.executor = executor
        self.base_dir = executor.get_base_dir() # Get the synced base_dir

    # ------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------
    def generate_project(self, params: Dict[str, Any]) -> ActionResult:
        """
        params expected:
        {
          "name": "visiontool",
          "type": "python" / "js" / "api" / "cli"
          "with_git": true/false
          "structure": { "path": "content", ... }
        }
        """
        name = params.get("name")
        project_type = params.get("type", "python")
        structure = params.get("structure", {})
        with_git = params.get("with_git", True)

        if not name:
            return ActionResult(status="failure", message="Missing project name.")

        # All paths will be relative to this new root
        project_root_rel = name
        
        actions = []

        # 1. Create the root folder
        actions.append({
            "type": ActionType.CREATE_FOLDER.value,
            "params": {"path": project_root_rel}
        })

        # --------------------------------------------------
        # 2. Create AI-defined files
        # --------------------------------------------------
        for rel_path, content in structure.items():
            full_rel_path = f"{project_root_rel}/{rel_path}"
            actions.append({
                "type": ActionType.CREATE_FILE.value,
                "params": {"path": full_rel_path, "content": content}
            })

        # --------------------------------------------------
        # 3. Ensure minimum structure exists
        # --------------------------------------------------
        actions.extend(
            self._ensure_minimum_actions(project_root_rel, name, project_type, structure)
        )

        # --------------------------------------------------
        # 4. Optional git init
        # --------------------------------------------------
        if with_git:
            # We must run GitInit *after* the folder is created.
            # This is tricky in a single batch.
            # For stability, we will run file/folder creation as one batch,
            # then run GitInit as a separate action.
            
            # TODO: Enhance this to run GitInit *inside* the new folder.
            # This requires changing the executor's base_dir, which this
            # feature shouldn't do. For now, we skip GitInit to avoid
            # initializing the *parent* directory.
            
            # A better AI prompt would be to:
            # 1. Call this ProjectGenerator
            # 2. Call `cd <new_project_name>`
            # 3. Call `GitInit`
            
            logger.warning("Skipping GitInit. AI must 'cd' into project and run 'GitInit' separately.")
            pass

        # --------------------------------------------------
        # 5. Execute as a single batch
        # --------------------------------------------------
        batch_action = {
            "type": ActionType.BATCH_OPERATION.value,
            "params": {"actions": actions}
        }
        
        logger.info(f"Running batch project generation for '{name}' with {len(actions)} actions.")
        result = self.executor.run_action(batch_action)
        
        # Add our own summary message
        if result.status == "success":
            result.message = f"Project '{name}' generated successfully."
            result.data["root"] = str(self.base_dir / project_root_rel)
        
        return result

    # ------------------------------------------------------------
    # PRIVATE HELPERS
    # ------------------------------------------------------------
    
    def _ensure_minimum_actions(
        self,
        root_rel: str,
        name: str,
        project_type: str,
        ai_structure: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate action dicts for minimum required files if not in AI plan."""
        actions = []

        # Helper to check if file was already in the AI's plan
        def file_not_planned(rel_path: str) -> bool:
            # Check for both 'src/main.py' and '/src/main.py'
            return rel_path not in ai_structure and rel_path.lstrip("/") not in ai_structure

        # ---------------------------
        # README.md
        # ---------------------------
        if file_not_planned("README.md"):
            readme = f"# {name}\n\nGenerated by GitVisionCLI.\n"
            actions.append({
                "type": ActionType.CREATE_FILE.value,
                "params": {"path": f"{root_rel}/README.md", "content": readme}
            })

        # ---------------------------
        # .gitignore
        # ---------------------------
        if file_not_planned(".gitignore"):
            gitignore = self._gitignore_template(project_type)
            actions.append({
                "type": ActionType.CREATE_FILE.value,
                "params": {"path": f"{root_rel}/.gitignore", "content": gitignore}
            })

        # ---------------------------
        # Python project defaults
        # ---------------------------
        if project_type == "python":
            src_folder_rel = f"{root_rel}/src/{name}"
            
            # Create src/name folder (supervisor handles nested creation)
            actions.append({
                "type": ActionType.CREATE_FOLDER.value,
                "params": {"path": src_folder_rel}
            })

            # __init__.py
            init_path = f"src/{name}/__init__.py"
            if file_not_planned(init_path):
                actions.append({
                    "type": ActionType.CREATE_FILE.value,
                    "params": {"path": f"{root_rel}/{init_path}", "content": "# Package init\n"}
                })

            # main.py
            main_path = f"src/{name}/main.py"
            if file_not_planned(main_path):
                main_content = (
                    f"def main():\n"
                    f"    print('Hello from {name}!')\n\n"
                    f"if __name__ == '__main__':\n"
                    f"    main()\n"
                )
                actions.append({
                    "type": ActionType.CREATE_FILE.value,
                    "params": {"path": f"{root_rel}/{main_path}", "content": main_content}
                })

            # pyproject.toml
            if file_not_planned("pyproject.toml"):
                actions.append({
                    "type": ActionType.CREATE_FILE.value,
                    "params": {"path": f"{root_rel}/pyproject.toml", "content": self._pyproject_template(name)}
                })

        # ---------------------------
        # JavaScript defaults
        # ---------------------------
        if project_type == "js":
            if file_not_planned("package.json"):
                actions.append({
                    "type": ActionType.CREATE_FILE.value,
                    "params": {"path": f"{root_rel}/package.json", "content": self._package_json_template(name)}
                })

            if file_not_planned("index.js"):
                actions.append({
                    "type": ActionType.CREATE_FILE.value,
                    "params": {"path": f"{root_rel}/index.js", "content": "console.log('Hello from JS project!');\n"}
                })

        return actions

    # ------------------------------------------------------------
    # TEMPLATE CONTENT
    # ------------------------------------------------------------
    def _gitignore_template(self, project_type: str) -> str:
        common = (
            "*.log\n"
            ".DS_Store\n"
            ".gitvision_backup/\n"
        )
        if project_type == "python":
            return (
                "__pycache__/\n"
                "*.pyc\n"
                ".venv/\n"
                "venv/\n"
                "dist/\n"
                "build/\n"
                ".pytest_cache/\n"
            ) + common
        if project_type == "js":
            return (
                "node_modules/\n"
                "dist/\n"
                ".npm/\n"
            ) + common
        return common

    def _pyproject_template(self, name: str) -> str:
        return (
            "[project]\n"
            f"name = \"{name}\"\n"
            "version = \"0.1.0\"\n"
            "description = \"Generated by GitVisionCLI\"\n"
            "requires-python = \">=3.10\"\n\n"
            "[build-system]\n"
            "requires = [\"setuptools\"]\n"
            "build-backend = \"setuptools.build_meta\"\n"
        )

    def _package_json_template(self, name: str) -> str:
        return (
            "{\n"
            f"  \"name\": \"{name}\",\n"
            "  \"version\": \"1.0.0\",\n"
            "  \"main\": \"index.js\",\n"
            "  \"license\": \"MIT\"\n"
            "}\n"
        )