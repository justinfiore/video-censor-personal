---
description: Refactor the commit history to make a clean branch
auto_execution_mode: 3
---

The code is working as it is. However, the branch is a bit messy in terms of commit messages, clean coherent logical commits, etc.

I want you to create a new branch from the current branch (just add the `-clean` suffix).

Then create a cleaner commit history where each commit is cohesive and performs a small logical part of the overall branch.
Each commit message should be clear and descriptive.
Then create a new PR using `git-create-pr` with a good title `-t` and description `-d` (feel free to use emojis in the description).

Make sure each commit has the JIRA ticket as the start of the commit message title (if you can extract that from the branch name).

Make sure to push the new branch to the remote with `git push origin HEAD`

**NOTE**: before running `git-create-pr`, make sure that you have run `source ~/.windsurfrc` first.
Also, if you can't find `git-create-pr` look for it at `~/bin/git-create-pr`
