import asyncio
import base64
import json
import logging
import re
from typing import Any

import httpx
from celery import Task

from app.config import settings

logger = logging.getLogger(__name__)

# ── Constants for deep scan ───────────────────────────────────────────────────
GITHUB_API = "https://api.github.com"

_EXCLUDED_DIRS = {
    "node_modules", ".git", "dist", "build", "vendor", "__pycache__",
    ".next", ".nuxt", "coverage", ".cache", "target", "out",
}

_EXCLUDED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf", ".zip",
    ".exe", ".lock", ".bin", ".jar", ".class", ".pyc", ".pyo", ".so",
    ".dll", ".woff", ".woff2", ".ttf", ".eot", ".mp3", ".mp4", ".mov",
    ".min.js", ".min.css",
}

_CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".rb", ".php",
    ".cs", ".cpp", ".c", ".h", ".rs", ".swift", ".kt", ".scala",
    ".r", ".jl", ".lua", ".pl", ".sh", ".bash", ".zsh",
}

_TEST_PATH_PATTERNS = re.compile(
    r"(test|tests|spec|__tests__|__mocks__|fixtures)[/\\]|"
    r"\.(test|spec)\.(js|ts|jsx|tsx|py|rb|go|java|cs)$",
    re.IGNORECASE,
)

_CONFIG_EXTENSIONS = {
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".env",
    ".gitignore", ".dockerignore", ".editorconfig",
}

DEEP_SCAN_LLM_PROMPT = """\
You are CodeIntel, an expert software architect and security engineer. Analyze the following repository source files and return a structured JSON assessment.

## Repository: {owner}/{repo}

## Source Files Analyzed ({file_count} files)

{file_contents}

## Your Task
Evaluate this codebase across 6 dimensions and return ONLY valid JSON — no markdown, no fences, no explanation.

Score each dimension 0-100 (100 = excellent):
1. **architecture_score**: Structure, modularity, separation of concerns, design patterns
2. **security_score**: Vulnerabilities (OWASP Top 10), hardcoded secrets, injection risks, auth/authz issues
3. **duplication_score**: DRY adherence, code reuse, repeated logic patterns
4. **documentation_score**: Comments, docstrings, README quality indicators, self-documenting code
5. **test_coverage_score**: Presence, quality, and coverage indicators of test files

Compute overall_score as: (architecture*25 + security*25 + duplication*15 + documentation*20 + test_coverage*15) / 100

Return ONLY this JSON:
{{
  "overall_score": <0-100>,
  "architecture_score": <0-100>,
  "security_score": <0-100>,
  "duplication_score": <0-100>,
  "documentation_score": <0-100>,
  "test_coverage_score": <0-100>,
  "critical_findings": ["<must-fix issue>", ...],
  "warnings": ["<should-fix issue>", ...],
  "positive_observations": ["<strength>", ...],
  "architecture_feedback": "<detailed paragraph>",
  "security_feedback": "<detailed paragraph>",
  "duplication_feedback": "<detailed paragraph>",
  "documentation_feedback": "<detailed paragraph>",
  "test_coverage_feedback": "<detailed paragraph>",
  "recommended_actions": ["<action 1>", "<action 2>", "<action 3>"]
}}"""


def _gh_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if settings.github_token:
        headers["Authorization"] = f"token {settings.github_token}"
    return headers


def _is_excluded_path(path: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    for part in parts:
        if part in _EXCLUDED_DIRS:
            return True
    return False


def _is_code_file(path: str) -> bool:
    lower = path.lower()
    for ext in _EXCLUDED_EXTENSIONS:
        if lower.endswith(ext):
            return False
    for ext in _CODE_EXTENSIONS:
        if lower.endswith(ext):
            return True
    return False


def _score_file(path: str) -> int:
    """Higher score = higher priority. Test and config files score lower."""
    if _TEST_PATH_PATTERNS.search(path):
        return 0
    lower = path.lower()
    for ext in _CONFIG_EXTENSIONS:
        if lower.endswith(ext):
            return 1
    # Source directories get priority
    for src_dir in ("src/", "app/", "lib/", "pkg/", "core/", "main"):
        if src_dir in path.lower():
            return 10
    return 5


async def _fetch_repo_file_tree(owner: str, repo: str, branch: str) -> list[dict[str, Any]]:
    """Fetch the full recursive file tree for a repository branch."""
    headers = _gh_headers()
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
            headers=headers,
        )
        if resp.status_code == 404:
            # Try 'master' as fallback
            resp = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/master?recursive=1",
                headers=headers,
            )
        resp.raise_for_status()
        data = resp.json()
        return [item for item in data.get("tree", []) if item.get("type") == "blob"]


async def _fetch_file_content(owner: str, repo: str, path: str) -> str | None:
    """Fetch decoded content of a single file from GitHub."""
    headers = _gh_headers()
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}",
                headers=headers,
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            if data.get("encoding") != "base64" or not data.get("content"):
                return None
            content = base64.b64decode(data["content"].replace("\n", "")).decode(
                "utf-8", errors="replace"
            )
            # Truncate very large files
            if len(content) > 8000:
                content = content[:8000] + "\n... [truncated]"
            return content
    except Exception as exc:
        logger.debug("Could not fetch %s/%s/%s: %s", owner, repo, path, exc)
        return None


def _run_deep_scan_llm_sync(owner: str, repo: str, file_contents: dict[str, Any]) -> dict[str, Any]:
    """Synchronous Anthropic call for deep scan (runs in executor)."""
    import anthropic as _anthropic
    client = _anthropic.Anthropic(api_key=settings.anthropic_api_key)

    sections = []
    for path, content in file_contents.items():
        sections.append(f"### {path}\n```\n{content}\n```")

    prompt = DEEP_SCAN_LLM_PROMPT.format(
        owner=owner,
        repo=repo,
        file_count=len(file_contents),
        file_contents="\n\n".join(sections),
    )

    for attempt in range(1, 4):
        try:
            response = client.messages.create(
                model=settings.anthropic_model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            return json.loads(raw)
        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning("Deep scan LLM attempt %d failed: %s", attempt, exc)
        except Exception as exc:
            logger.error("Deep scan LLM attempt %d error: %s", attempt, exc)
            if attempt == 3:
                raise
    raise RuntimeError("Deep scan LLM failed after 3 attempts")


async def _run_deep_scan_llm(owner: str, repo: str, file_contents: dict[str, Any]) -> dict[str, Any]:
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run_deep_scan_llm_sync, owner, repo, file_contents)


def make_celery():
    from celery import Celery

    app = Celery(
        "codeintel",
        broker=settings.redis_url,
        backend=settings.redis_url,
    )
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_time_limit=120,
        task_soft_time_limit=100,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
    )
    return app


celery_app = make_celery()


@celery_app.task(
    bind=True,
    name="tasks.process_pr_review",
    max_retries=2,
    default_retry_delay=30,
    time_limit=120,
    soft_time_limit=100,
)
def process_pr_review(
    self: Task,
    repo_full_name: str,
    pr_number: int,
    head_sha: str,
    action: str,
    installation_id: int = 0,
) -> dict:
    """
    Celery task: run the full AI review pipeline for a PR.
    Executes async code by running it in a new event loop.
    """
    logger.info(
        "Task process_pr_review started: %s#%d (sha=%s, action=%s)",
        repo_full_name,
        pr_number,
        head_sha[:8],
        action,
    )

    async def _run():
        from app.database import AsyncSessionLocal
        from app.services.review_service import run_pr_review

        async with AsyncSessionLocal() as session:
            review = await run_pr_review(
                session=session,
                repo_full_name=repo_full_name,
                pr_number=pr_number,
                head_sha=head_sha,
                installation_id=installation_id,
            )
            return {
                "review_id": review.id,
                "repo_full_name": repo_full_name,
                "pr_number": pr_number,
                "score_overall": review.score_overall,
            }

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_run())
        finally:
            loop.close()

        logger.info(
            "Task process_pr_review completed: %s#%d → score=%.1f",
            repo_full_name,
            pr_number,
            result["score_overall"],
        )
        return result

    except Exception as exc:
        logger.error(
            "Task process_pr_review failed for %s#%d: %s",
            repo_full_name,
            pr_number,
            exc,
            exc_info=True,
        )
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error(
                "Max retries exceeded for %s#%d — giving up", repo_full_name, pr_number
            )
            return {
                "error": str(exc),
                "repo_full_name": repo_full_name,
                "pr_number": pr_number,
            }


# ── Deep Scan Task ─────────────────────────────────────────────────────────────

@celery_app.task(
    bind=True,
    name="tasks.deep_scan_repository",
    max_retries=1,
    default_retry_delay=60,
    time_limit=180,
    soft_time_limit=160,
)
def deep_scan_repository(self: Task, owner: str, repo: str, repo_id: int) -> dict:
    """
    Celery task: perform a full AI-powered deep scan of a repository's codebase.
    Fetches up to 30 source files, sends them to the LLM for analysis, and
    stores structured results in the deep_scan_results table.
    Time limit: 180 seconds.
    """
    logger.info("Deep scan started: %s/%s (repo_id=%d)", owner, repo, repo_id)

    async def _run() -> dict:
        from app.database import AsyncSessionLocal
        from app.models import DeepScanResult, Repository
        from sqlalchemy import select

        # ── 1. Get default branch ──────────────────────────────────────────────
        headers = _gh_headers()
        async with httpx.AsyncClient(timeout=15.0) as client:
            repo_resp = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}", headers=headers
            )
            repo_resp.raise_for_status()
            default_branch = repo_resp.json().get("default_branch", "main")

        # ── 2. Fetch file tree ─────────────────────────────────────────────────
        tree = await _fetch_repo_file_tree(owner, repo, default_branch)

        # ── 3. Filter to code files ────────────────────────────────────────────
        candidates = [
            item for item in tree
            if not _is_excluded_path(item["path"]) and _is_code_file(item["path"])
        ]

        # ── 4. Sort by priority (main source files first) ─────────────────────
        candidates.sort(key=lambda x: _score_file(x["path"]), reverse=True)
        selected = candidates[:30]

        # ── 5. Fetch file contents ─────────────────────────────────────────────
        file_contents: dict[str, str] = {}
        for item in selected:
            content = await _fetch_file_content(owner, repo, item["path"])
            if content:
                file_contents[item["path"]] = content

        if not file_contents:
            raise RuntimeError(f"No readable source files found in {owner}/{repo}")

        # ── 6. Call LLM ────────────────────────────────────────────────────────
        llm_result = await _run_deep_scan_llm(owner, repo, file_contents)

        def _clamp(v: Any) -> float:
            try:
                return max(0.0, min(100.0, float(v)))
            except (TypeError, ValueError):
                return 0.0

        # ── 7. Save to DB ──────────────────────────────────────────────────────
        async with AsyncSessionLocal() as session:
            scan = DeepScanResult(
                repo_id=repo_id,
                owner=owner,
                repo_name=repo,
                overall_score=_clamp(llm_result.get("overall_score", 0)),
                architecture_score=_clamp(llm_result.get("architecture_score", 0)),
                security_score=_clamp(llm_result.get("security_score", 0)),
                duplication_score=_clamp(llm_result.get("duplication_score", 0)),
                documentation_score=_clamp(llm_result.get("documentation_score", 0)),
                test_coverage_score=_clamp(llm_result.get("test_coverage_score", 0)),
                critical_findings=llm_result.get("critical_findings", []),
                warnings=llm_result.get("warnings", []),
                positive_observations=llm_result.get("positive_observations", []),
                recommended_actions=llm_result.get("recommended_actions", []),
                architecture_feedback=llm_result.get("architecture_feedback", ""),
                security_feedback=llm_result.get("security_feedback", ""),
                duplication_feedback=llm_result.get("duplication_feedback", ""),
                documentation_feedback=llm_result.get("documentation_feedback", ""),
                test_coverage_feedback=llm_result.get("test_coverage_feedback", ""),
                files_analyzed=len(file_contents),
            )
            session.add(scan)
            await session.flush()
            scan_id = scan.id
            await session.commit()

        logger.info(
            "Deep scan completed: %s/%s → overall=%.1f (files=%d, scan_id=%d)",
            owner,
            repo,
            scan.overall_score,
            len(file_contents),
            scan_id,
        )
        return {
            "scan_id": scan_id,
            "owner": owner,
            "repo": repo,
            "overall_score": scan.overall_score,
            "files_analyzed": len(file_contents),
        }

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_run())
        finally:
            loop.close()
        return result

    except Exception as exc:
        logger.error(
            "Deep scan failed for %s/%s: %s", owner, repo, exc, exc_info=True
        )
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for deep scan %s/%s — giving up", owner, repo)
            return {"error": str(exc), "owner": owner, "repo": repo}


import traceback as _tb_module
from celery.signals import task_failure as _celery_task_failure


@_celery_task_failure.connect
def on_task_failure(sender=None, task_id=None, exception=None,
                    args=None, kwargs=None, traceback=None, einfo=None, **rest):
    """Write failed Celery tasks to task_failures table after max retries exhausted."""
    task_name = getattr(sender, "name", str(sender))
    error_msg = str(exception) if exception else "Unknown error"
    tb_text = "".join(_tb_module.format_tb(traceback)) if traceback else None

    task_args_data: dict = {}
    if args:
        task_args_data["args"] = list(args)
    if kwargs:
        task_args_data["kwargs"] = kwargs

    async def _write():
        from app.database import AsyncSessionLocal
        from app.models import TaskFailure

        async with AsyncSessionLocal() as session:
            failure = TaskFailure(
                task_name=task_name,
                task_args=task_args_data,
                error_message=error_msg,
                traceback_text=tb_text,
            )
            session.add(failure)
            await session.commit()

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_write())
        finally:
            loop.close()
        logger.info("TaskFailure recorded for task: %s", task_name)
    except Exception as exc:
        logger.error("Failed to record TaskFailure: %s", exc)
