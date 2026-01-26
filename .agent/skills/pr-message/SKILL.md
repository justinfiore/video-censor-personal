---
name: pr-message
description: Generates a Pull Request title and description from branch changes. Use when asked to create, write, or generate a PR message or description.
---

# PR Message

Generates a Pull Request title and description.

## Workflow

1. Delete `PR_DETAILS.md` if it exists.
2. Analyze all changes and commit messages on this branch compared to `master`.
3. Write a PR title and description to `PR_DETAILS.md`.

## Format

```
{prefix}: {subject}

{body}
```

## Subject

The first line should be the "subject" of the PR—a one-line summary.

- Written in Present Tense
- Written as Commands
- Example: "perf: Adds Pooled `RestTemplates` for the 3 different foobar Instances"

## Body

- Can be informal
- Describe the "why" of the change
- Messages to your team (present and future)
- Use Markdown where appropriate
- Feel free to use emojis
- Include links to relevant material (Confluence, Stack Overflow, documentation)

## Prefix Options

- **feat**: Introduce a new feature
- **fix**: Fix a bug or issue
- **tweak**: Make minor adjustments or improvements
- **style**: Update code style or formatting
- **refactor**: Restructure code without changing functionality
- **perf**: Improve performance or efficiency
- **test**: Add or update tests
- **docs**: Update documentation
- **chore**: Perform maintenance tasks or updates
- **ci**: Change CI/CD configuration
- **build**: Modify build system or dependencies
- **revert**: Revert a previous commit
- **hotfix**: Apply an urgent bug fix
- **init**: Initialize a new project or feature
- **merge**: Merge branches
- **wip**: Mark work in progress
- **release**: Prepare for a release

## Requirements

PR Bodies **MUST** tell us:
- What the change does
- Why it is necessary

PR Messages **MAY** tell us:
- Alternatives considered
- Potential consequences of the change
