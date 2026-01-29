---
name: pr-template-filler
description: Fill GitHub pull request template fields (What/Why/How/Checks) by summarizing pushed changes from git or a GitHub PR.
---

# PR Template Filler

Use this skill when the user wants a prefilled PR body from `.github/pull_request_template.md` based on the actual changes.

## Workflow (short)

1. Identify the PR context (GitHub PR or local branch) and the base branch.
2. Collect change evidence (files, diffstat, commits, tests run).
3. Draft the PR template with concise bullets aligned to evidence.
4. Mark checks only when confirmed; otherwise leave unchecked and note gaps.

## Step 1: Locate the template

Open `.github/pull_request_template.md` and mirror its sections and formatting.

## Step 2: Collect change evidence

Prefer GitHub PR data when available; otherwise use local git.

### Option A: GitHub PR (preferred for pushed changes)

If `gh` is available and a PR number is known, collect summary and files:

- `gh pr view <PR> --json title,body,baseRefName,headRefName,files,commits`
- `gh pr diff <PR> --stat`

### Option B: Local branch vs base

Determine base (default `origin/main`) and compare:

- `git merge-base HEAD <base>`
- `git log --oneline <base>..HEAD`
- `git diff --stat <base>..HEAD`
- `git diff --name-only <base>..HEAD`

You can use `dev/collect_pr_context.sh` to gather a quick bundle.

## Step 3: Fill the template

Use evidence to produce 1–3 bullets per section:

- **What**: concrete changes (features, fixes, refactors) mapped to files/areas.
- **Why**: motivation, linked issues, user impact, or risk reduced.
- **How**: approach, key design choices, tests run.
- **Checks**: mark only what was actually run; if unknown, leave unchecked and add a short note under **How** or **Checks**.

Keep language neutral and review-ready; avoid speculation.

## Step 4: Confirm

Ask the user to verify correctness and fill missing fields (tests, docs, issue links).

## Output format

Return the filled template as a markdown block, preserving the original checklist.

## If information is missing

State what is missing and ask for the specific data (PR number, base branch, tests run).
