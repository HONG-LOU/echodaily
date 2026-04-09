---
name: git-ship
description: Executes a strict git delivery workflow: inspect diff, stage changes, run pre-commit, fix hook failures, create concise commit message, commit, and push. Use when the user asks to finalize and ship local code changes.
---

# Git Ship Workflow

## Goal
Standardize final delivery steps so code is reviewed, validated, committed, and pushed with minimal mistakes.

## Steps
1. Check current changes:
   - Run `git status --short --branch`
   - Run `git diff` to review unstaged and staged updates
2. Stage all intended files:
   - Run `git add <paths>` (or `git add .` only when scope is clear)
3. Run hooks:
   - Execute `pre-commit run --all-files`
4. If hooks fail:
   - Read errors carefully
   - Apply minimal fixes
   - Re-run `pre-commit run --all-files` until green
5. Create commit message:
   - Keep it concise
   - Prefer one short line
   - Follow repository commit style if required
6. Commit with message
7. Push to tracked remote branch

## Safety Rules
- Never use destructive git commands unless explicitly asked.
- Do not amend old commits unless explicitly requested.
- Do not push force unless explicitly requested.
- Do not include secrets in commits.

## Output Contract
After shipping, report:
- Branch name
- Commit hash and message
- Hook result
- Push result
