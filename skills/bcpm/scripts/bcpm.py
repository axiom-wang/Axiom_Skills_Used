#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ALLOWED_TYPES = ["feat", "fix", "chore", "docs", "refactor", "test", "ci", "perf", "build"]
DOC_EXTENSIONS = {".md", ".rst", ".txt"}
DOC_PATH_PARTS = {"docs", ".guidance", "guidance", "adr"}
TEST_PATH_PARTS = {"tests", "test", "spec"}
CI_PATH_PARTS = {".github", ".gitlab", "workflows", "ci"}
BUILD_FILES = {
    "pyproject.toml",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "poetry.lock",
    "requirements.txt",
    "requirements-dev.txt",
    "setup.py",
    "setup.cfg",
    "Makefile",
}
STOPWORDS = {
    "a",
    "an",
    "api",
    "app",
    "apps",
    "build",
    "cli",
    "cmd",
    "config",
    "configs",
    "conftest",
    "core",
    "data",
    "deepflow",
    "deepflowcore",
    "dist",
    "doc",
    "docs",
    "example",
    "examples",
    "feature",
    "file",
    "files",
    "git",
    "github",
    "gitignore",
    "gitlab",
    "guidance",
    "helper",
    "helpers",
    "impl",
    "index",
    "integration",
    "lib",
    "main",
    "merge",
    "message",
    "messages",
    "md",
    "model",
    "models",
    "module",
    "modules",
    "mr",
    "package",
    "path",
    "paths",
    "plan",
    "progress",
    "project",
    "py",
    "pyproject",
    "readme",
    "repo",
    "request",
    "route",
    "routes",
    "schema",
    "schemas",
    "script",
    "scripts",
    "service",
    "services",
    "src",
    "test",
    "tests",
    "toml",
    "tmp",
    "tool",
    "tools",
    "unit",
    "update",
    "utils",
    "workflow",
    "workflows",
    "yaml",
    "yml",
}
VERB_BY_TYPE = {
    "feat": "add",
    "fix": "fix",
    "chore": "update",
    "docs": "update",
    "refactor": "refactor",
    "test": "add",
    "ci": "update",
    "perf": "improve",
    "build": "update",
}


class CommandError(RuntimeError):
    def __init__(self, command, returncode, stdout, stderr):
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        joined = " ".join(shlex.quote(part) for part in command)
        super().__init__(f"Command failed ({returncode}): {joined}")


def run(command, cwd=None, check=True):
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        env=os.environ.copy(),
    )
    if check and result.returncode != 0:
        raise CommandError(command, result.returncode, result.stdout, result.stderr)
    return result


def run_with_output_files(command, cwd=None):
    with tempfile.TemporaryDirectory(prefix="bcpm-gate-") as tmpdir:
        stdout_path = Path(tmpdir) / "stdout.log"
        stderr_path = Path(tmpdir) / "stderr.log"

        with stdout_path.open("w", encoding="utf-8") as stdout_file, stderr_path.open(
            "w", encoding="utf-8"
        ) as stderr_file:
            result = subprocess.run(
                command,
                cwd=cwd,
                text=True,
                stdout=stdout_file,
                stderr=stderr_file,
                env=os.environ.copy(),
            )

        result.stdout = stdout_path.read_text(encoding="utf-8")
        result.stderr = stderr_path.read_text(encoding="utf-8")
        return result


def command_exists(name):
    return any(
        (Path(path) / name).exists()
        for path in os.environ.get("PATH", "").split(os.pathsep)
    )


def load_package_json(repo_root):
    package_json_path = repo_root / "package.json"
    if not package_json_path.exists():
        return None
    try:
        return json.loads(package_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def quality_gate_commands(repo_root):
    package_json = load_package_json(repo_root)
    scripts = package_json.get("scripts", {}) if isinstance(package_json, dict) else {}
    pnpm_commands = []

    for script_name in ["typecheck", "smoke", "build"]:
        if isinstance(scripts, dict) and script_name in scripts:
            pnpm_commands.append(["pnpm", script_name])

    if pnpm_commands:
        return pnpm_commands

    return [
        ["ruff", "check", "."],
        ["mypy", "."],
        ["pytest"],
        ["python3", "-m", "build"],
    ]


def required_gate_binaries(repo_root):
    return sorted({command[0] for command in quality_gate_commands(repo_root)})


def failure_detail(exc):
    if isinstance(exc, CommandError):
        return exc.stderr.strip() or exc.stdout.strip() or str(exc)
    return str(exc).strip()


def git_repo_root():
    return Path(run(["git", "rev-parse", "--show-toplevel"]).stdout.strip())


def current_branch(repo_root):
    branch = run(["git", "branch", "--show-current"], cwd=repo_root).stdout.strip()
    if not branch:
        raise RuntimeError("Detached HEAD is not supported by bcpm.")
    return branch


def git_remote_url(repo_root, remote):
    return run(["git", "remote", "get-url", remote], cwd=repo_root).stdout.strip()


def check_glab_auth(repo_root):
    result = run(["glab", "auth", "status"], cwd=repo_root, check=False)
    if result.returncode != 0:
        raise RuntimeError("glab auth status failed. Log in with glab before using bcpm.")
    return result.stdout + result.stderr


def git_status_lines(repo_root):
    output = run(["git", "status", "--short"], cwd=repo_root).stdout
    return [line.rstrip("\n") for line in output.splitlines() if line.strip()]


def parse_changed_paths(status_lines):
    paths = []
    for line in status_lines:
        payload = line[3:] if len(line) > 3 else line
        if " -> " in payload:
            payload = payload.split(" -> ", 1)[1]
        paths.append(payload.strip())
    return paths


def is_docs_path(path):
    p = Path(path)
    parts = set(p.parts)
    if p.name in {"README.md", "AGENTS.md", "CLAUDE.md"}:
        return True
    if p.suffix.lower() in DOC_EXTENSIONS:
        return True
    return bool(parts & DOC_PATH_PARTS)


def is_test_path(path):
    p = Path(path)
    parts = set(p.parts)
    stem = p.stem.lower()
    return bool(parts & TEST_PATH_PARTS) or stem.startswith("test_") or stem.endswith("_test")


def is_ci_path(path):
    p = Path(path)
    parts = set(p.parts)
    return bool(parts & CI_PATH_PARTS)


def is_build_path(path):
    p = Path(path)
    if p.name in BUILD_FILES:
        return True
    return any(part in {"build", "dist"} for part in p.parts)


def infer_type(paths):
    if not paths:
        return "chore"
    if all(is_docs_path(path) for path in paths):
        return "docs"
    if all(is_test_path(path) for path in paths):
        return "test"
    if all(is_ci_path(path) for path in paths):
        return "ci"
    if all(is_build_path(path) for path in paths):
        return "build"
    lower_paths = " ".join(path.lower() for path in paths)
    if any(token in lower_paths for token in ["fix", "bug", "error", "regression", "hotfix"]):
        return "fix"
    code_paths = [path for path in paths if not is_docs_path(path) and not is_test_path(path)]
    if code_paths:
        return "feat"
    return "chore"


def tokenize_paths(paths):
    tokens = []
    for path in paths:
        cleaned = path.replace(" -> ", "/")
        parts = re.split(r"[^a-zA-Z0-9]+", cleaned)
        for raw in parts:
            token = raw.lower().strip()
            if len(token) < 2:
                continue
            if token.isdigit():
                continue
            if token in STOPWORDS:
                continue
            if token.endswith("s") and len(token) > 4 and token[:-1] not in STOPWORDS:
                token = token[:-1]
            tokens.append(token)
    return tokens


def infer_slug(paths, change_type, override=None):
    if override:
        return slugify(override)
    tokens = tokenize_paths(paths)
    if not tokens:
        fallback = {
            "docs": "docs-update",
            "test": "test-update",
            "ci": "ci-update",
            "build": "build-update",
        }.get(change_type, "repo-update")
        return fallback
    counts = Counter(tokens)
    ordered = sorted(counts, key=lambda token: (-counts[token], tokens.index(token), token))
    selected = []
    for token in ordered:
        if token not in selected:
            selected.append(token)
        if len(selected) == 3:
            break
    slug = "-".join(selected)
    return slugify(slug) or "repo-update"


def slugify(value):
    lowered = value.strip().lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-{2,}", "-", lowered)
    lowered = lowered.strip("-")
    return lowered[:40].rstrip("-")


def subject_phrase(slug):
    return slug.replace("-", " ")


def infer_commit_subject(change_type, slug, override=None):
    if override:
        return override.strip()
    verb = VERB_BY_TYPE.get(change_type, "update")
    phrase = subject_phrase(slug)
    return f"{change_type}: {verb} {phrase}".strip()


def branch_name(change_type, slug):
    date_part = dt.datetime.now().strftime("%Y%m%d")
    return f"{change_type}/{date_part}-{slug}"


def branch_exists(repo_root, remote, name):
    local = run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{name}"],
        cwd=repo_root,
        check=False,
    )
    if local.returncode == 0:
        return True
    remote_check = run(["git", "ls-remote", "--heads", remote, name], cwd=repo_root, check=False)
    return bool(remote_check.stdout.strip())


def make_unique_branch_name(repo_root, remote, base_name):
    candidate = base_name
    index = 2
    while branch_exists(repo_root, remote, candidate):
        suffix = f"-{index}"
        room = max(1, 40 - len(suffix))
        prefix, rest = candidate.split("/", 1)
        if "-" in rest:
            date_part, slug = rest.split("-", 1)
        else:
            date_part, slug = rest, "update"
        slug = slug[:room].rstrip("-")
        candidate = f"{prefix}/{date_part}-{slug}{suffix}"
        index += 1
    return candidate


def is_compliant_branch(name):
    pattern = r"^(feat|fix|chore|docs|refactor|test|ci|perf|build)/[0-9]{8}-[a-z0-9]+(-[a-z0-9]+)*$"
    return bool(re.match(pattern, name))


def verify_same_source_target(source_branch, target_branch, branch_mode):
    if source_branch == target_branch:
        raise RuntimeError(
            "The source branch matches the target branch, so GitLab cannot create an MR. "
            f"Current branch mode is '{branch_mode}'. "
            "Use --branch-mode auto or change --target-branch."
        )


def stash_changes(repo_root, label):
    before = run(["git", "rev-parse", "-q", "--verify", "refs/stash"], cwd=repo_root, check=False)
    before_ref = before.stdout.strip()
    run(["git", "stash", "push", "-u", "-m", label], cwd=repo_root)
    after = run(["git", "rev-parse", "-q", "--verify", "refs/stash"], cwd=repo_root, check=False)
    after_ref = after.stdout.strip()
    if not after_ref or after_ref == before_ref:
        raise RuntimeError("git stash push -u did not create a stash entry.")
    return "stash@{0}"


def restore_stash(repo_root, stash_ref):
    result = run(["git", "stash", "pop", stash_ref], cwd=repo_root, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git stash pop failed."
        raise RuntimeError(
            f"Failed to restore stashed changes from {stash_ref}. "
            "Resolve the working tree manually; the stash entry was kept. "
            f"Git output: {detail}"
        )


def pull_current_branch(repo_root):
    run(["git", "pull"], cwd=repo_root)


def sync_target_branch_before_branching(repo_root, target_branch):
    label = f"bcpm-pre-branch-sync-{target_branch}-{dt.datetime.now().strftime('%Y%m%d%H%M%S')}"
    stash_ref = stash_changes(repo_root, label)
    try:
        pull_current_branch(repo_root)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"Failed to run git pull on '{target_branch}' before creating a new branch. "
            f"Your changes remain saved in {stash_ref}. {failure_detail(exc)}"
        ) from exc
    try:
        restore_stash(repo_root, stash_ref)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"Pulled '{target_branch}', but restoring stashed changes failed. "
            f"Resolve the working tree on '{target_branch}' before retrying. "
            f"The stash entry {stash_ref} was kept. {failure_detail(exc)}"
        ) from exc
    return stash_ref


def quality_gates(repo_root):
    commands = quality_gate_commands(repo_root)
    results = []
    for command in commands:
        result = run_with_output_files(command, cwd=repo_root)
        entry = {
            "command": " ".join(command),
            "ok": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
        results.append(entry)
        if result.returncode != 0:
            raise RuntimeError(format_gate_failure(results))
    return results


def format_gate_failure(results):
    lines = ["Quality gates failed:"]
    for result in results:
        status = "passed" if result["ok"] else "failed"
        lines.append(f"- {result['command']}: {status}")
        if not result["ok"]:
            snippet = first_output_line(result)
            if snippet:
                lines.append(f"  {snippet}")
    return "\n".join(lines)


def first_output_line(result):
    merged = "\n".join(
        part for part in [result.get("stdout", ""), result.get("stderr", "")] if part
    )
    for line in merged.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:200]
    return ""


def get_diff_stats(repo_root):
    """获取 git diff 统计信息"""
    result = run(["git", "diff", "--cached", "--stat"], cwd=repo_root)
    return result.stdout.strip()


def categorize_paths(paths):
    """将文件路径按类型分类"""
    categories = {
        "code": [],
        "test": [],
        "docs": [],
        "config": [],
        "ci": [],
    }
    for path in paths:
        if is_test_path(path):
            categories["test"].append(path)
        elif is_docs_path(path):
            categories["docs"].append(path)
        elif is_ci_path(path):
            categories["ci"].append(path)
        elif is_build_path(path):
            categories["config"].append(path)
        else:
            categories["code"].append(path)
    return {k: v for k, v in categories.items() if v}


def changed_summary(paths, slug):
    preview = paths[:5]
    suffix = "" if len(paths) <= 5 else f" (+{len(paths) - 5} more)"
    listed = ", ".join(preview)
    if listed:
        return f"Apply current changes for {subject_phrase(slug)} across {listed}{suffix}."
    return f"Apply current changes for {subject_phrase(slug)}."


def build_mr_description(repo_root, paths, slug, change_type, gate_results, warnings, custom_summary=None):
    lines = ["## 📋 变更概述", ""]

    # 使用外部传入的 summary，如果没有则使用默认描述
    if custom_summary:
        lines.append(custom_summary)
    else:
        # 降级方案：基础中文描述
        type_desc = {
            "feat": "新增功能", "fix": "修复问题", "chore": "日常维护",
            "docs": "文档更新", "refactor": "代码重构", "test": "测试相关",
            "ci": "CI/CD配置", "perf": "性能优化", "build": "构建配置",
        }.get(change_type, "代码变更")
        categories = categorize_paths(paths)
        parts = [f"本次提交为 **{type_desc}**，主要涉及 {subject_phrase(slug)}。"]
        parts.append(f"共修改 {len(paths)} 个文件")
        if categories.get("code"):
            parts.append(f"，包括 {len(categories['code'])} 个业务代码文件")
        if categories.get("test"):
            parts.append(f"、{len(categories['test'])} 个测试文件")
        lines.append("".join(parts) + "。")

    lines.extend(["", "## 📊 代码统计"])

    # 添加变更统计
    diff_stats = get_diff_stats(repo_root)
    if diff_stats:
        lines.append("```")
        lines.append(diff_stats)
        lines.append("```")
        lines.append("")

    # 添加文件分类
    categories = categorize_paths(paths)
    lines.append("### 变更文件列表")
    category_names = {
        "code": "业务代码", "test": "测试文件", "docs": "文档",
        "config": "配置文件", "ci": "CI/CD",
    }
    for category, files in categories.items():
        icon = {"code": "💻", "test": "🧪", "docs": "📝", "config": "⚙️", "ci": "🔧"}.get(category, "📄")
        cn_name = category_names.get(category, category)
        lines.append(f"**{icon} {cn_name}** ({len(files)} 个文件)")
        for file in files[:5]:
            lines.append(f"- `{file}`")
        if len(files) > 5:
            lines.append(f"- ... 还有 {len(files) - 5} 个文件")
        lines.append("")

    # 风险评估
    lines.extend(["## ⚠️ 风险评估"])
    if warnings:
        for warning in warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- ✅ bcpm 未检测到额外风险")
    lines.append("")

    # 测试结果
    lines.extend(["## ✅ 质量检查"])
    all_passed = all(result["ok"] for result in gate_results)
    if all_passed:
        lines.append("所有质量门禁检查通过 ✨")
        lines.append("")
    for result in gate_results:
        status_icon = "✅" if result["ok"] else "❌"
        status_text = "通过" if result["ok"] else "失败"
        lines.append(f"{status_icon} `{result['command']}` - {status_text}")
        if not result["ok"]:
            error_line = first_output_line(result)
            if error_line:
                lines.append(f"  ```")
                lines.append(f"  {error_line}")
                lines.append(f"  ```")

    lines.append("")
    lines.append("---")
    lines.append("*由 bcpm 自动生成*")

    return "\n".join(lines)


def squash_before_merge_flag(squash):
    if squash == "auto":
        return []
    return [f"--squash-before-merge={squash}"]


def create_or_update_mr(repo_root, branch, target_branch, title, description, squash, auto_merge):
    existing = run(
        [
            "glab",
            "mr",
            "list",
            "--source-branch",
            branch,
            "--target-branch",
            target_branch,
            "--output",
            "json",
        ],
        cwd=repo_root,
    )
    items = json.loads(existing.stdout or "[]")
    if items:
        iid = str(items[0]["iid"])
        update_command = [
            "glab",
            "mr",
            "update",
            iid,
            "--title",
            title,
            "--description",
            description,
            "--target-branch",
            target_branch,
            "-y",
        ]
        update_command.extend(squash_before_merge_flag(squash))
        run(
            update_command,
            cwd=repo_root,
        )
    else:
        create_command = [
            "glab",
            "mr",
            "create",
            "--source-branch",
            branch,
            "--target-branch",
            target_branch,
            "--title",
            title,
            "--description",
            description,
            "--yes",
        ]
        create_command.extend(squash_before_merge_flag(squash))
        run(
            create_command,
            cwd=repo_root,
        )
        iid = None
    view = run(["glab", "mr", "view", branch, "--output", "json"], cwd=repo_root)
    payload = json.loads(view.stdout or "{}")
    iid = str(payload.get("iid") or iid)
    if auto_merge:
        merge_command = ["glab", "mr", "merge", iid, "--auto-merge", "--remove-source-branch", "-y"]
        run(merge_command, cwd=repo_root)
    payload["iid"] = iid
    return payload


def print_output(payload, as_json):
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    print(f"Repo: {payload['repo_root']}")
    print(f"Current branch: {payload['current_branch']}")
    print(f"Source branch: {payload['source_branch']}")
    if payload.get("created_branch"):
        print(f"Created branch: {payload['created_branch']}")
    print(f"Change type: {payload['change_type']}")
    print(f"Branch slug: {payload['branch_slug']}")
    print(f"Commit subject: {payload['commit_subject']}")
    if payload.get("planned_actions"):
        for action in payload["planned_actions"]:
            print(f"Planned action: {action}")
    if payload.get("pre_branch_sync_performed"):
        print("Pre-branch sync: stash/pull/restore completed")
    if payload.get("pre_branch_stash_ref"):
        print(f"Pre-branch stash ref: {payload['pre_branch_stash_ref']}")
    for warning in payload.get("warnings", []):
        print(f"Warning: {warning}")
    if payload.get("dry_run"):
        print("Dry run: no git or GitLab mutations were executed.")
    if payload.get("gate_results"):
        for result in payload["gate_results"]:
            status = "passed" if result["ok"] else "failed"
            print(f"Gate {result['command']}: {status}")
    if payload.get("mr_url"):
        print(f"Merge request: {payload['mr_url']}")
    if payload.get("auto_merge_enabled"):
        print("Auto-merge: enabled")
    if payload.get("returned_to_branch"):
        print(f"Returned to branch: {payload['returned_to_branch']}")
    if payload.get("post_return_pull_performed"):
        print("Post-return pull: completed")
    if payload.get("final_branch"):
        print(f"Final branch: {payload['final_branch']}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Branch, commit, push, and open a GitLab MR."
    )
    parser.add_argument("--branch-type", choices=ALLOWED_TYPES)
    parser.add_argument("--branch-description")
    parser.add_argument("--commit-subject")
    parser.add_argument("--summary", help="LLM 生成的变更总结（中文）")
    parser.add_argument("--target-branch", default="main")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--squash", choices=["auto", "true", "false"], default="auto")
    parser.add_argument("--branch-mode", choices=["auto", "create-on-non-main"], default="auto")
    parser.add_argument(
        "--auto-merge",
        action="store_true",
        help="Enable GitLab auto-merge after creating or updating the merge request.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()

    if not command_exists("git"):
        raise RuntimeError("git is not available in PATH.")
    if not command_exists("glab"):
        raise RuntimeError("glab is not available in PATH.")

    repo_root = git_repo_root()
    missing_gate_binaries = [
        binary for binary in required_gate_binaries(repo_root) if not command_exists(binary)
    ]
    if missing_gate_binaries:
        raise RuntimeError(
            "Required quality gate commands are not available in PATH: "
            + ", ".join(missing_gate_binaries)
        )
    remote_url = git_remote_url(repo_root, args.remote)
    if "gitlab" not in remote_url.lower():
        raise RuntimeError(f"Remote '{args.remote}' is not a GitLab remote: {remote_url}")
    auth_status = check_glab_auth(repo_root)
    status_lines = git_status_lines(repo_root)
    if not status_lines:
        raise RuntimeError("Working tree is clean. There is nothing for bcpm to commit.")

    branch_now = current_branch(repo_root)
    paths = parse_changed_paths(status_lines)
    inferred_type = args.branch_type or infer_type(paths)
    slug = infer_slug(paths, inferred_type, args.branch_description)
    subject = infer_commit_subject(inferred_type, slug, args.commit_subject)
    warnings = []
    created_branch = None
    source_branch = branch_now

    if args.branch_mode == "auto":
        if branch_now == args.target_branch:
            source_branch = make_unique_branch_name(
                repo_root,
                args.remote,
                branch_name(inferred_type, slug),
            )
        else:
            source_branch = branch_now
    elif args.branch_mode == "create-on-non-main":
        if branch_now != args.target_branch:
            source_branch = make_unique_branch_name(
                repo_root,
                args.remote,
                branch_name(inferred_type, slug),
            )
        else:
            source_branch = branch_now

    if (
        source_branch == branch_now
        and not is_compliant_branch(branch_now)
        and branch_now != args.target_branch
    ):
        warnings.append(
            f"Current branch '{branch_now}' does not match the repo naming convention; "
            "bcpm kept it unchanged."
        )

    created_from_target_branch = branch_now == args.target_branch and source_branch != branch_now

    result = {
        "repo_root": str(repo_root),
        "remote": args.remote,
        "remote_url": remote_url,
        "glab_auth": auth_status.strip(),
        "current_branch": branch_now,
        "source_branch": source_branch,
        "created_branch": None,
        "target_branch": args.target_branch,
        "change_type": inferred_type,
        "branch_slug": slug,
        "commit_subject": subject,
        "changed_paths": paths,
        "warnings": warnings,
        "dry_run": args.dry_run,
        "gate_results": [],
        "mr_url": None,
        "mr_iid": None,
        "auto_merge_enabled": False,
        "branch_mode": args.branch_mode,
        "created_from_target_branch": created_from_target_branch,
        "pre_branch_sync_performed": False,
        "pre_branch_stash_ref": None,
        "pre_branch_pull_performed": False,
        "pre_branch_stash_restored": False,
        "returned_to_branch": None,
        "post_return_pull_performed": False,
        "final_branch": None,
        "planned_actions": [],
    }

    if args.dry_run:
        if source_branch == branch_now and source_branch == args.target_branch:
            warnings.append(
                "Dry-run note: source branch matches target branch. "
                "Actual execution would stop before MR creation in this mode."
            )
        elif source_branch != branch_now:
            result["created_branch"] = source_branch
        if created_from_target_branch:
            result["planned_actions"].extend(
                [
                    "git stash push -u",
                    "git pull",
                    "git stash pop",
                ]
            )
        if source_branch != branch_now:
            result["planned_actions"].append(f"git switch -c {source_branch}")
        result["planned_actions"].extend(
            [
                "git add -A",
                *[" ".join(command) for command in quality_gate_commands(repo_root)],
                f"git commit -m {shlex.quote(subject)}",
                f"git push -u {args.remote} {source_branch}",
                f"glab mr create/update {source_branch} -> {args.target_branch}",
            ]
        )
        if created_from_target_branch:
            result["planned_actions"].extend(
                [
                    f"git switch {branch_now}",
                    "git pull",
                ]
            )
        result["final_branch"] = branch_now if created_from_target_branch else source_branch
        print_output(result, args.json)
        return

    verify_same_source_target(source_branch, args.target_branch, args.branch_mode)

    if created_from_target_branch:
        stash_ref = sync_target_branch_before_branching(repo_root, branch_now)
        result["pre_branch_sync_performed"] = True
        result["pre_branch_stash_ref"] = stash_ref
        result["pre_branch_pull_performed"] = True
        result["pre_branch_stash_restored"] = True

    if source_branch != branch_now:
        run(["git", "switch", "-c", source_branch], cwd=repo_root)
        created_branch = source_branch
        result["created_branch"] = created_branch

    run(["git", "add", "-A"], cwd=repo_root)
    cached_diff = run(["git", "diff", "--cached", "--quiet"], cwd=repo_root, check=False)
    if cached_diff.returncode == 0:
        raise RuntimeError("No staged changes found after git add -A.")

    gate_results = quality_gates(repo_root)
    result["gate_results"] = gate_results

    run(["git", "commit", "-m", subject], cwd=repo_root)
    run(["git", "push", "-u", args.remote, source_branch], cwd=repo_root)

    description = build_mr_description(repo_root, paths, slug, inferred_type, gate_results, warnings, args.summary)
    mr_payload = create_or_update_mr(
        repo_root=repo_root,
        branch=source_branch,
        target_branch=args.target_branch,
        title=subject,
        description=description,
        squash=args.squash,
        auto_merge=args.auto_merge,
    )
    result["mr_url"] = mr_payload.get("web_url") or mr_payload.get("references", {}).get("full")
    result["mr_iid"] = mr_payload.get("iid")
    result["auto_merge_enabled"] = args.auto_merge
    if created_from_target_branch:
        try:
            run(["git", "switch", branch_now], cwd=repo_root)
            result["returned_to_branch"] = branch_now
            pull_current_branch(repo_root)
            result["post_return_pull_performed"] = True
            result["final_branch"] = branch_now
        except Exception as exc:  # noqa: BLE001
            mr_ref = result["mr_url"] or (f"!{result['mr_iid']}" if result["mr_iid"] else "The merge request")
            raise RuntimeError(
                f"{mr_ref} was created or updated, but returning to '{branch_now}' and running git pull failed. "
                f"{failure_detail(exc)}"
            ) from exc
    else:
        result["final_branch"] = source_branch
    print_output(result, args.json)


if __name__ == "__main__":
    try:
        main()
    except CommandError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        print(detail, file=sys.stderr)
        sys.exit(exc.returncode or 1)
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        sys.exit(1)
