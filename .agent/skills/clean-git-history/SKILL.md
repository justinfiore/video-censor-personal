---
name: clean-git-history
description: Refactors messy commit history into clean, logical commits on a new branch. Use when asked to clean up commits, refactor history, or make a clean branch.
---

# Cleaning Git Commit History

Refactor a messy branch into clean, cohesive commits.

## Workflow

1. Create new branch from current with `-clean` suffix
2. Reorganize commits so each is:
   - Cohesive and performs one logical piece of work
   - Has a clear, descriptive commit message
3. Push new branch with `git push origin HEAD`

## Commit Message Format

Follow the `generate-commit-message` skill format:
- Use conventional prefix (feat, fix, refactor, etc.)
- Clear subject line
- Descriptive body explaining the "why"

## PR Description

Use emojis in the description for readability.
