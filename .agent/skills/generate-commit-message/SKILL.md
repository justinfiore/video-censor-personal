---
name: generate-commit-message
description: Generates structured commit messages with conventional prefix, and detailed body. Use when asked to create or write a commit message.
---

# Generating Commit Message

Generate a commit message and write it to `COMMIT_MESSAGE.txt`.

## Workflow

1. Delete `COMMIT_MESSAGE.txt` if it exists
2. Analyze staged changes with `git diff --cached`
3. Write commit message to `COMMIT_MESSAGE.txt`

## Message Format

```
{prefix}: {subject}

{body}
```

## Subject Line

- Present tense, command form
- Example: `perf: Add pooled RestTemplates for foobar instances`

## Prefixes

| Prefix | Use for |
|--------|---------|
| feat | New feature |
| fix | Bug fix |
| tweak | Minor adjustments |
| style | Formatting changes |
| refactor | Code restructuring |
| perf | Performance improvements |
| test | Test additions/updates |
| docs | Documentation |
| chore | Maintenance |
| ci | CI/CD changes |
| build | Build/dependencies |
| revert | Reverting commits |
| hotfix | Urgent fixes |
| init | New project/feature |
| merge | Branch merges |
| wip | Work in progress |
| release | Release prep |

## Body

- Describe the "why" of the change
- Use Markdown formatting
- Include relevant links (Confluence, Stack Overflow, documentation)
- Emojis welcome for readability

## Requirements

Commit messages MUST explain:
- What the change does
- Why it is necessary

MAY include:
- Alternatives considered
- Potential consequences
