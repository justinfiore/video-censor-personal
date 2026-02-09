---
name: commit-all
description: Commits all current changes (new and modified files), generates commit message, pushes, and creates PR. Use when asked to commit everything or commit all changes.
---

# Committing All Changes

Stage all changes, commit with a generated message, push, and create a PR.

## Important

**DO NOT USE `git add -a`**

## Workflow

1. Add newly-created files individually with `git add <file>`
2. Add modified files with `git add -u`
3. Generate commit message using the `generate-commit-message` skill workflow
4. Commit using the message in `COMMIT_MESSAGE.txt`
5. Delete `COMMIT_MESSAGE.txt`
6. Push with `git push origin HEAD`

## PR Creation

Use meaningful title and detailed description for the PR.
