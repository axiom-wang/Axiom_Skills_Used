---
name: bcpm
description: Automate Git branch naming, commit creation, push, and GitLab merge request flow for the current repository changes. Use when Codex needs to turn the current diff into a standards-compliant branch, generate a conventional commit, push to GitLab, and create or reuse a GitLab merge request.
metadata:
  skill_os:
    standardized: true
---

# BCPM

Use this skill when the user wants the current repo changes packaged and sent through the GitLab merge workflow with minimal manual git work.

## Workflow

1. Read repo guidance before acting. If present, inspect `AGENTS.md`, `.guidance/standards/git-branch-commit-standards.md`, `.guidance/process/development-workflow.md`, `.guidance/quality-gates/ci-gates.md`, and `.guidance/standards/testing-standards.md`.

2. **生成变更总结（新增）**：
   - 运行 `git diff --cached` 获取变更内容
   - 使用 LLM 分析 diff，生成中文语义总结
   - 总结应包含：变更目的、主要改动、业务价值、影响范围
   - 用 2-4 段话描述，使用专业但易懂的语言

3. Resolve this skill's root directory first, then prefer the helper wrapper instead of hand-writing git and `glab` commands. Start with `bash /absolute/path/to/bcpm/run.sh --dry-run --json --summary "总结内容"` when the inferred branch name or commit subject might need review.

4. Run `bash /absolute/path/to/bcpm/run.sh --summary "总结内容"` for the full flow. The wrapper resolves `scripts/bcpm.py` from the skill directory. If bcpm needs to branch from `main`, it first stashes current changes with untracked files, runs `git pull`, restores the stash, then stages current changes, runs quality gates, commits, pushes, and creates or reuses the merge request.

5. Report the final branch name, commit subject, quality-gate results, merge request URL, and whether auto-merge was explicitly enabled.

The helper files belong to this skill, not to the target repository. Do not run `python3 scripts/bcpm.py` from the repo root unless that repo actually contains its own `scripts/bcpm.py`.

## Defaults

- `branch-mode=auto` by default. If the current branch matches the target branch, the script first stashes local changes, pulls the target branch, restores the stash, then creates a compliant source branch so the merge request is valid. After the MR is created or updated, bcpm switches back to the original target branch and runs `git pull` again. Otherwise it keeps the current branch.
- `branch-mode=create-on-non-main` is available for the user-specific preference discussed for this repo. In that mode the script creates a child branch only when the current branch is not the target branch. If the current branch equals the target branch, the script stops before MR creation because GitLab cannot open an MR from a branch to itself.
- The target branch defaults to `main`.
- The merge flow creates or updates the MR without enabling auto-merge by default. Pass `--auto-merge` when the user explicitly wants GitLab to merge automatically after pipelines succeed. Squash follows project settings unless `--squash true` or `--squash false` is passed.
- The script does not rename an existing non-compliant branch automatically. It keeps the branch and emits a warning.

## Overrides

Use script flags when the repo diff is too ambiguous for the default heuristics:

- `--branch-type feat|fix|chore|docs|refactor|test|ci|perf|build`
- `--branch-description short-hyphenated-slug`
- `--commit-subject "type: concise subject"`
- `--summary "LLM 生成的中文变更总结"`
- `--target-branch main`
- `--squash auto|true|false`
- `--branch-mode auto|create-on-non-main`
- `--auto-merge`

## Guardrails

- Do not bypass failing `ruff`, `mypy`, `pytest`, or `python -m build` checks inside this skill.
- Do not force-push, reset, or rename branches automatically.
- If the repo is not connected to GitLab or `glab auth status` fails, stop and report the blocker.
- If branch or commit inference looks wrong, rerun with explicit overrides instead of patching git state manually.
- Do not enable auto-merge unless the user explicitly asks for it or the invocation passes `--auto-merge`.

## Usage

TODO: Document the primary workflow for this skill.

## Examples

- TODO: Add one concrete trigger or use case for this skill.
