---
description: Generate a commit message
auto_execution_mode: 3
---


Write a English commit message to the file `COMMIT_MESSAGE.txt` (delete it first if it exists).

Only analyze the changes on the git stage `git diff --cached`

Use the following format for consistent and descriptive commit messages:

```
{prefix}: {subject}

{body}
```

Definitions of the parts

**Subject**

The first line should be the “subject” of the commit. 
It should give us a summary in one line.
- Written in Present Tense
- Written as Commands
- e.g., "perf: Adds Pooled `RestTemplates` for the 3 different foobar Instances"

This is what the commit is DOING to the code in the present
Use Markdown as appropriate.

**Body**

- Can be informal
- Describe the "why" of the change.
- Messages to your team (present and future)
- Use Markdown where appropriate
- Feel free to use emojis and so forth to make it more readable.
- Include links to any relevant material:
  - Confluence pages
  - Stack Overflow links where you found the solution to all the world’s ills
  - Links to documentation

**prefix**:
- feat: Introduce a new feature.
- fix: Fix a bug or issue.
- tweak: Make minor adjustments or improvements.
- style: Update code style or formatting.
- refactor: Restructure code without changing functionality.
- perf: Improve performance or efficiency.
- test: Add or update tests.
- docs: Update documentation.
- chore: Perform maintenance tasks or updates.
- ci: Change CI/CD configuration.
- build: Modify build system or dependencies.
- revert: Revert a previous commit.
- hotfix: Apply an urgent bug fix.
- init: Initialize a new project or feature.
- merge: Merge branches.
- wip: Mark work in progress.
- release: Prepare for a release.

**Additional Guidance**:

Commit Messages **MUST** tell us:
- What the change does
- Why it is necessary

Commit Messages **MAY** tell us:
- Alternatives considered
- Potential consequences of the change

