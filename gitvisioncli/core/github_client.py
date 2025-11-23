# gitvisioncli/core/github_client.py
"""
Fully deterministic, synchronous GitHub REST v3 client for GitVisionCLI.

This client is designed to be used by the ActionSupervisor. It handles
real API calls, implements rate limiting, retries, and maps all
API errors to structured dictionary responses rather than raising
exceptions (except for critical connection failures).
"""

import os
import base64
import requests
import logging
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass

# Use standard logging
logger = logging.getLogger(__name__)

# ============================================================
# Exceptions
# ============================================================

class GitHubClientError(Exception):
    """Base exception for client-side errors (e.g., config, connection)."""
    pass

# Supervisor expects this exact name
GitHubError = GitHubClientError

# ============================================================
# Configuration
# ============================================================

@dataclass
class GitHubClientConfig:
    """Configuration data class for the GitHub Client."""
    token: str
    default_owner: str
    default_visibility: str = "private"

    def __post_init__(self):
        if not self.token:
            raise GitHubClientError("GitHub token (token) is missing in config.")
        if not self.default_owner:
            raise GitHubClientError("GitHub default owner (user) is missing in config.")

# ============================================================
# GitHub Client
# ============================================================

class GitHubClient:
    """
    A synchronous, deterministic client for the GitHub v3 REST API.
    
    All public methods return a structured dictionary:
    Success: {"ok": True, "data": ...}
    Failure: {"ok": False, "error": "...", "details": {...}}
    
    Raises GitHubError ONLY for critical network/connection issues.
    """
    
    BASE_URL = "https://api.github.com"
    API_VERSION = "2022-11-28"
    
    # Retry logic for server-side errors
    MAX_RETRIES = 3
    RETRY_STATUS_CODES = {502, 503, 504}
    BACKOFF_FACTOR = 0.5  # Initial backoff (0.5s, 1s, 2s)

    # Sandbox files to ignore during push
    SANDBOX_IGNORE = {
        ".git",
        ".DS_Store",
        "__pycache__",
        ".pytest_cache",
        ".venv"
    }

    def __init__(self, config: Union[Dict[str, Any], GitHubClientConfig]):
        """
        Initializes the client with either a raw dictionary
        or a GitHubClientConfig object.
        """
        if isinstance(config, dict):
            # Handle dict from config.json (which uses 'user' for owner)
            self.config = GitHubClientConfig(
                token=config.get("token"),
                default_owner=config.get("user"),
                default_visibility=config.get("default_visibility", "private")
            )
        elif isinstance(config, GitHubClientConfig):
            self.config = config
        else:
            raise TypeError("config must be a dict or GitHubClientConfig instance")

        # Use a session for connection pooling and persistent headers
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.config.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": self.API_VERSION,
        })

    # ============================================================
    # Core Request & Error Handling
    # ============================================================

    def _req(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Internal request wrapper with retry, rate limit, and error mapping.
        
        This method is the core of the client. It translates all API
        responses (good or bad) into the structured `{"ok": ...}` format.
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = self.session.request(method, url, timeout=15, **kwargs)

                # --- Rate Limit Handling ---
                if response.status_code == 403 and \
                   response.headers.get("X-RateLimit-Remaining") == "0":
                    
                    if attempt == self.MAX_RETRIES:
                        logger.error("Rate limited and out of retries.")
                        return self._handle_api_error(response, endpoint)
                    
                    reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                    sleep_duration = max(0, reset_time - int(time.time())) + 1 # Add 1s buffer
                    
                    logger.warning(
                        "Rate limited by GitHub. Sleeping for %d seconds.", 
                        sleep_duration
                    )
                    time.sleep(sleep_duration)
                    continue # Retry the request

                # --- Retryable Server Error Handling ---
                if response.status_code in self.RETRY_STATUS_CODES and \
                   attempt < self.MAX_RETRIES:
                    
                    sleep_time = self.BACKOFF_FACTOR * (2 ** attempt)
                    logger.warning(
                        "GitHub API returned %d. Retrying in %.1fs...",
                        response.status_code, sleep_time
                    )
                    time.sleep(sleep_time)
                    continue # Retry the request

                # --- Handle Final HTTP Errors (non-retryable or out of retries) ---
                if not response.ok:
                    return self._handle_api_error(response, endpoint)

                # --- Success ---
                if response.status_code == 204: # No Content
                    return {"ok": True, "data": None}
                
                return {"ok": True, "data": response.json()}

            except requests.exceptions.RequestException as e:
                # Critical network/connection error
                logger.error("GitHub network request failed: %s", e)
                # This is the ONLY place a GitHubError should be raised
                raise GitHubError(f"Network error communicating with GitHub: {e}") from e
        
        # Should be unreachable, but as a fallback
        return {"ok": False, "error": "Exhausted all retries.", "details": {}}

    def _handle_api_error(self, response: requests.Response, endpoint: str) -> Dict[str, Any]:
        """Formats a failed requests.Response into the standard error dict."""
        try:
            content = response.json()
        except requests.exceptions.JSONDecodeError:
            content = {"message": response.text or "Unknown error"}

        message = content.get("message", "Unknown API error")
        errors = content.get("errors", [])
        doc_url = content.get("documentation_url", "")

        logger.error(
            "GitHub API error on %s: %s (Status: %d) | Errors: %s",
            endpoint, message, response.status_code, errors
        )
        
        return {
            "ok": False,
            "error": message,
            "details": {
                "status": response.status_code,
                "endpoint": endpoint,
                "errors": errors,
                "documentation_url": doc_url
            }
        }

    # ============================================================
    # Internal Helpers
    # ============================================================

    def _get_owner_repo(self, name_or_fullname: str) -> Tuple[str, str]:
        """Splits 'owner/repo' or defaults to the configured owner."""
        if "/" in name_or_fullname:
            owner, repo = name_or_fullname.split("/", 1)
            return owner, repo
        return self.config.default_owner, name_or_fullname

    def _safe_relpath(self, file_path: Path, root: Path) -> str:
        """Calculates a POSIX-style relative path."""
        return file_path.relative_to(root).as_posix()

    def _sanitize_content(self, content_bytes: bytes) -> bytes:
        """Removes CRLF, replacing with LF as per Git's preference."""
        return content_bytes.replace(b"\r\n", b"\n")

    def _compute_git_sha(self, content_bytes: bytes) -> str:
        """
        Computes the Git blob SHA-1 hash for byte content.
        Git prefixes the content with `blob <size>\0` before hashing.
        """
        header = f"blob {len(content_bytes)}\0".encode("utf-8")
        data = header + content_bytes
        return hashlib.sha1(data).hexdigest()

    def _collect_local_files(self, local_root: Path, target_path: Path) -> List[Path]:
        """
        Recursively finds all files from a target, filtering ignored files.
        """
        files_to_process: List[Path] = []
        if target_path.is_file():
            files_to_process = [target_path]
        elif target_path.is_dir():
            files_to_process = [f for f in target_path.rglob("*") if f.is_file()]

        # Discover embedded git repositories so we can avoid pushing their
        # contents into the parent repository.
        embedded_roots: List[Path] = []
        if target_path.is_dir():
            try:
                for git_dir in target_path.rglob(".git"):
                    if git_dir.is_dir():
                        embedded_roots.append(git_dir.parent.resolve())
            except Exception as e:
                logger.warning("Failed to scan for embedded git repos during push: %s", e)

        filtered_files: List[Path] = []
        for f in files_to_process:
            try:
                rel = f.relative_to(local_root)
            except ValueError:
                # Outside of the declared root; skip defensively.
                logger.warning("Skipping file outside local_root during push: %s", f)
                continue

            rel_parts = rel.parts

            # Skip anything under embedded git repositories.
            full_path = f.resolve()
            if any(root in full_path.parents or root == full_path for root in embedded_roots):
                logger.info("Skipping file inside embedded git repo: %s", f)
                continue

            # Skip sandbox / tooling artefacts.
            if any(part in self.SANDBOX_IGNORE for part in rel_parts):
                logger.info("Ignoring sandboxed file: %s", f.name)
                continue

            filtered_files.append(f)

        return filtered_files

    # ============================================================
    # Public API: Repository Operations
    # ============================================================

    def create_repository(self, name: str, private: bool = True, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Creates a new repository.
        Handles 422 "name already exists" error gracefully.
        """
        logger.info("Creating repo: %s", name)
        payload = {
            "name": name,
            "private": private,
            "description": description or "",
            "auto_init": True, # Ensure repo is not empty
        }
        
        response = self._req("POST", "/user/repos", json=payload)

        # Specific 422 handling for existing repo
        if not response["ok"] and response.get("details", {}).get("status") == 422:
            api_errors = response.get("details", {}).get("errors", [])
            if any(err.get("field") == "name" and "already exists" in err.get("message", "") for err in api_errors):
                logger.warning("Repository exists, skipping: %s", name)
                return {"ok": False, "error": "Repository exists", "repo": name}

        return response

    def delete_repo(self, repo_full_name: str) -> Dict[str, Any]:
        """
        Deletes a repository. This is a destructive action.
        """
        owner, repo = self._get_owner_repo(repo_full_name)
        logger.warning("Deleting repo: %s/%s", owner, repo)
        
        # A 204 No Content is expected on success
        return self._req("DELETE", f"/repos/{owner}/{repo}")

    def repo_exists(self, name_or_fullname: str) -> Dict[str, Any]:
        """
        Checks if a repository exists and is accessible.
        Returns {"ok": True, "data": True/False} on success.
        """
        owner, repo = self._get_owner_repo(name_or_fullname)
        
        response = self._req("GET", f"/repos/{owner}/{repo}")

        if response["ok"]:
            return {"ok": True, "data": True}
        
        # A 404 is a successful "doesn't exist" check
        if response.get("details", {}).get("status") == 404:
            return {"ok": True, "data": False}

        # Any other error (e.g., 403, 500) is a failed check
        return response

    def ensure_repo(self, name: str) -> Dict[str, Any]:
        """
        Ensures a repository exists. If not, creates it.
        Uses default visibility from config.
        """
        logger.info("Ensuring repo exists: %s", name)
        exists_res = self.repo_exists(name)
        
        if not exists_res["ok"]:
            return exists_res # Pass through the API error
        
        if exists_res["data"]:
            logger.info("Repo %s already exists.", name)
            # Get full repo data to be consistent with create_repository response
            owner, repo = self._get_owner_repo(name)
            return self._req("GET", f"/repos/{owner}/{repo}")

        # Repo doesn't exist, create it
        visibility = self.config.default_visibility == "private"
        return self.create_repository(name, private=visibility, description="Managed by GitVisionCLI")

    # ============================================================
    # Public API: File Operations
    # ============================================================

    def get_file_sha(self, repo_full_name: str, path_in_repo: str, branch: Optional[str] = None) -> Dict[str, Any]:
        """
        Gets the SHA of a single file.
        Returns {"ok": True, "data": "sha_string"} on success.
        Returns {"ok": True, "data": None} if file not found (404).
        """
        owner, repo = self._get_owner_repo(repo_full_name)
        endpoint = f"/repos/{owner}/{repo}/contents/{path_in_repo}"
        params = {"ref": branch} if branch else {}
        
        response = self._req("GET", endpoint, params=params)

        if response["ok"]:
            # Handle both single file and directory listings (though should be file)
            data = response["data"]
            if isinstance(data, dict) and data.get("type") == "file":
                return {"ok": True, "data": data.get("sha")}
            elif isinstance(data, list):
                return {"ok": False, "error": "Path is a directory, not a file."}
            else:
                return {"ok": False, "error": "Unexpected content type from API."}

        # A 404 is a successful "no SHA" lookup
        if response.get("details", {}).get("status") == 404:
            logger.info("File not found (no SHA): %s", path_in_repo)
            return {"ok": True, "data": None}
        
        return response # Pass through other errors

    def _create_or_update_file(
        self,
        repo_full_name: str,
        path_in_repo: str,
        content_bytes: bytes,
        commit_message: str,
        branch: str
    ) -> Dict[str, Any]:
        """
        Internal helper to create or update a single file.
        Implements SHA detection to skip identical files.
        """
        owner, repo = self._get_owner_repo(repo_full_name)
        endpoint = f"/repos/{owner}/{repo}/contents/{path_in_repo}"

        # 1. Get remote SHA
        sha_res = self.get_file_sha(repo_full_name, path_in_repo, branch)
        if not sha_res["ok"]:
            return sha_res # Propagate API error
        remote_sha = sha_res["data"]

        # 2. Sanitize and compute local SHA
        content_bytes = self._sanitize_content(content_bytes)
        local_sha = self._compute_git_sha(content_bytes)
        
        # 3. Skip if SHAs match (Rule 8)
        if remote_sha == local_sha:
            logger.info("Skipping identical file: %s", path_in_repo)
            return {"ok": True, "data": None, "status": "skipped"}

        # 4. Prepare payload for upload
        payload = {
            "message": commit_message,
            "content": base64.b64encode(content_bytes).decode("utf-8"),
            "branch": branch,
        }
        
        if remote_sha:
            payload["sha"] = remote_sha # Must provide SHA for updates
            status_str = "updated"
        else:
            status_str = "created"
        
        logger.info("Pushing %s file: %s", status_str, path_in_repo)
        
        response = self._req("PUT", endpoint, json=payload)
        
        # Add our custom status to the successful response
        if response["ok"]:
            response["status"] = status_str
            
        return response

    def push_path(
        self,
        repo_full_name: str,
        local_root: str,
        local_path: str,
        branch: str = "main",
        commit_message: str = "Sync from GitVisionCLI"
    ) -> Dict[str, Any]:
        """
        Pushes a local file or directory (recursively) to the repository.
        Skips files defined in SANDBOX_IGNORE.
        Skips files where content SHA matches remote SHA.
        """
        root = Path(local_root).resolve()
        target = (root / local_path).resolve()

        if not target.exists():
            return {"ok": False, "error": f"Local path not found: {target}"}

        try:
            files_to_push = self._collect_local_files(root, target)
        except Exception as e:
            return {"ok": False, "error": f"Failed to collect files: {e}"}

        uploaded, skipped, failed = [], [], []

        for file_path in files_to_push:
            rel_path = self._safe_relpath(file_path, root)
            try:
                content_bytes = file_path.read_bytes()
                
                result = self._create_or_update_file(
                    repo_full_name,
                    rel_path,
                    content_bytes,
                    f"{commit_message} ({rel_path})", # File-specific commit msg
                    branch
                )

                if result["ok"]:
                    if result.get("status") == "skipped":
                        skipped.append(rel_path)
                    else:
                        uploaded.append(rel_path)
                else:
                    failed.append({"path": rel_path, "error": result["error"]})

            except (IOError, OSError) as e:
                logger.error("Failed to read local file %s: %s", rel_path, e)
                failed.append({"path": rel_path, "error": f"File read error: {e}"})
            except Exception as e:
                # Catch-all for unexpected errors during loop
                logger.error("Unexpected error pushing %s: %s", rel_path, e)
                failed.append({"path": rel_path, "error": f"Unexpected error: {e}"})

        return {
            "ok": True,
            "uploaded": uploaded,
            "skipped": skipped,
            "failed": failed,
            "total": len(files_to_push)
        }

    # ============================================================
    # Public API: Issues & PRs
    # ============================================================

    def create_issue(
        self,
        repo_full_name: str,
        title: str,
        body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a new issue in the specified repository.
        """
        owner, repo = self._get_owner_repo(repo_full_name)
        logger.info("Creating issue in %s/%s: %s", owner, repo, title)
        
        payload = {
            "title": title,
            "body": body or "",
        }
        
        return self._req("POST", f"/repos/{owner}/{repo}/issues", json=payload)

    def create_pull_request(
        self,
        repo_full_name: str,
        title: str,
        head: str,
        base: str,
        body: Optional[str] = None,
        draft: bool = False
    ) -> Dict[str, Any]:
        """
        Creates a new pull request.
        
        :param head: The name of the branch where your changes are implemented.
        :param base: The name of the branch you want the changes pulled into.
        """
        owner, repo = self._get_owner_repo(repo_full_name)
        logger.info(
            "Creating PR in %s/%s: '%s' (%s -> %s)",
            owner, repo, title, head, base
        )
        
        payload = {
            "title": title,
            "head": head,
            "base": base,
            "body": body or "",
            "draft": draft
        }
        
        return self._req("POST", f"/repos/{owner}/{repo}/pulls", json=payload)
