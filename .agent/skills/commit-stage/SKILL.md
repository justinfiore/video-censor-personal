---
name: commit-stage
description: Commits currently staged files, generates commit message, pushes, and creates PR. Use when asked to commit staged changes or commit what's on the stage.
---

# Committing Staged Changes

Commit the currently staged files, push, and create a PR.

## Important

**DO NOT USE `git add -a`**

## Workflow

1. Analyze staged files with `git diff --cached`
2. Generate commit message using the `generate-commit-message` skill workflow
3. Commit using the message in `COMMIT_MESSAGE.txt`
4. Delete `COMMIT_MESSAGE.txt`
5. Push with `git push origin HEAD`

## PR Creation

Use meaningful title and detailed description for the PR.
