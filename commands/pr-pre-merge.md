---
description: Run pre-merge checklist — branch freshness, docs, version, CHANGELOG, tests
argument-hint: <pr-number>
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, AskUserQuestion, TaskCreate, TaskUpdate
---

# Pre-Merge Checklist

You are running the pre-merge checklist for a PR that has passed review. Walk through each checklist item, perform the necessary updates, and commit the results.

**User input:** $ARGUMENTS

## Step 0: Parse input and create task list

The user's input contains:
- A **PR number** (required)

Extract the PR number from the input. If the input is ambiguous, ask the user to clarify.

After parsing input, create the progress-tracking task list. Create a task for Step 0 and immediately mark it in progress. Then create tasks for each of the remaining 7 steps one at a time, in step order, all starting as pending. Task list display order matches creation order, so each task must be a separate sequential call -- do not batch multiple task creations in a single message. Store each returned task ID for later use -- do not assume IDs are sequential.

| Task | Subject | activeForm |
|------|---------|------------|
| Step 0 | Step 0: Parse input and create task list | Parsing input |
| Step 1 | Step 1: Read contributing guidelines | Reading contributing guidelines |
| Step 2 | Step 2: Check out and prepare | Checking out PR branch |
| Step 3 | Step 3: Check branch freshness | Checking branch freshness |
| Step 4 | Step 4: Gather PR context | Gathering PR context |
| Step 5 | Step 5: Run pre-merge checklist | Running pre-merge checklist |
| Step 6 | Step 6: Commit checklist changes | Committing checklist changes |
| Step 7 | Step 7: Present pre-merge report | Presenting report |

Mark Step 0 complete.

## Step 1: Read contributing guidelines

Mark Step 1 in progress.

Look for project contribution guidelines in order of precedence:

```
CONTRIBUTING.md
DEVELOPMENT.md
.github/CONTRIBUTING.md
```

Read only the first file found; skip the rest.

If found, read the file and extract any pre-merge requirements (version bumps, changelog entries, documentation updates, test requirements, etc.).

If no contributing guide exists, use the standard checklist below.

Mark Step 1 complete.

## Step 2: Check out and prepare

Mark Step 2 in progress.

Ensure you are on the PR's branch with latest changes:

```
gh pr checkout <pr-number>
git pull
```

If either command fails (PR not found, authentication error, merge conflicts during pull), report the error to the user and stop -- the checklist cannot proceed without a clean, up-to-date working copy of the PR branch. Leave Step 2 as `in_progress`.

Mark Step 2 complete.

## Step 3: Check branch freshness

Mark Step 3 in progress.

Ensure the feature branch is up to date with the default branch before running the checklist.

Determine the default branch and fetch the latest remote state:

```
gh repo view --json defaultBranchRef --jq .defaultBranchRef.name
git fetch origin
```

If either command fails (authentication error, rate limit, network error), report the error to the user and stop -- the freshness check cannot proceed without knowing the default branch and having up-to-date remote state. Leave Step 3 as `in_progress`.

Count how many commits the branch is behind:

```
git rev-list --count HEAD..origin/<default-branch>
```

If the count is **0**, the branch is current — continue to Step 4.

If the count is **greater than 0**, inform the user that the branch is N commits behind `origin/<default-branch>`, then use `AskUserQuestion` to ask how to proceed:

- **Merge**: "Merge the default branch into this branch now"
- **Skip**: "Leave the branch as-is and continue the checklist"
- **Cancel**: "Stop without running the checklist"

If the user selects **Cancel**, stop the session. Leave Step 3 as `in_progress`.

If the user selects **Skip**, note the skipped status for the report and continue to Step 4.

If the user selects **Merge**, run:

```
git merge origin/<default-branch>
```

**If the merge succeeds cleanly**, push the merge commit (`git push`). If the push fails, report the error to the user and stop — do not continue the checklist with an unpushed merge commit. Advise the user they can retry with `git push`, or undo the merge with `git reset --hard HEAD~1`. Leave Step 3 as `in_progress`. On success, continue to Step 4.

**If the merge has conflicts**, check whether all conflicted files are on the version-file allowlist: `plugin.json`, `package.json`, `pyproject.toml`, `setup.cfg`, `Cargo.toml`, `build.gradle`. Only files on this allowlist are eligible for auto-resolution.

- **All conflicts are trivial (version files only):** For each conflicted file, resolve by taking the default branch's version (`git checkout --theirs <file>` then `git add <file>`), then finalize the merge with `git commit --no-edit`. Push the result (`git push`). If the push fails, report the error and stop — advise the user they can retry with `git push`, or undo the merge with `git reset --hard HEAD~1`. Leave Step 3 as `in_progress`. Record which files were auto-resolved for the report.
- **Any non-trivial conflicts exist:** Abort the merge with `git merge --abort`. Report the list of conflicted files to the user and stop the session — the user must resolve conflicts manually. Leave Step 3 as `in_progress`.

**If the merge fails for any reason other than conflicts** (invalid ref, dirty working tree, internal error), report the full error output to the user and stop. Leave Step 3 as `in_progress`.

Mark Step 3 complete.

## Step 4: Gather PR context

Mark Step 4 in progress.

Build a picture of what the PR changed so the checklist in Step 5 can make informed decisions:

1. **Changed files**: `gh pr diff <pr-number> --name-only` and `git diff origin/<default-branch>...HEAD --stat`
2. **PR description**: `gh pr view <pr-number>`
3. **Commit history**: `git log origin/<default-branch>..HEAD --oneline`

From these, identify what features, APIs, behaviors, or configurations were added, changed, or removed. Produce a brief change summary covering:
- The nature of the changes (new feature, bug fix, refactor, configuration change, etc.)
- Which areas of the project are affected
- Whether there are user-facing behavior changes

This summary provides the foundation for the documentation, version bump, CHANGELOG, and test items in Step 5.

Mark Step 4 complete.

## Step 5: Run pre-merge checklist

Mark Step 5 in progress.

Using the PR context gathered in Step 4, work through each item. For each, report whether action is needed and perform it if so.

### 5a. Documentation

- Are there new features or changed behavior that need documentation updates?
- Check README.md, any docs/ directory, docstrings, and help text.
- Update as needed.

### 5b. Version Bump

- Check if the project uses semantic versioning (look for version in package.json, pyproject.toml, setup.cfg, __version__, etc.)
- If version tracking exists, determine if a bump is warranted:
  - **Patch**: Bug fixes, minor improvements
  - **Minor**: New features, non-breaking changes
  - **Major**: Breaking changes
- If the bump level is not obvious from the changes, use `AskUserQuestion` to ask:
  - **Patch**: "Bug fixes and minor improvements"
  - **Minor**: "New features, non-breaking changes"
  - **Major**: "Breaking changes to existing behavior"

### 5c. CHANGELOG

- Check if the project maintains a CHANGELOG.md or CHANGES.md.
- If so, add an entry for this PR's changes following the existing format.

### 5d. Tests

Run the project's test suite:

```
# Auto-detect test runner
# Python: pytest, unittest
# JavaScript: npm test, jest
# etc.
```

Report results. If tests fail, investigate and report — do NOT silently ignore failures.

Mark Step 5 complete.

## Step 6: Commit checklist changes

Mark Step 6 in progress.

Check whether the checklist produced any uncommitted changes by running `git status --porcelain`. If the output is empty, no changes were made — mark Step 6 complete and proceed to Step 7.

If there are changes, commit and push them:

1. **Stage** only the files modified during this checklist (`git add <file>...`). If staging fails, report the error to the user, leave Step 6 as `in_progress`, and proceed to Step 7.
2. **Commit** with message: "Pre-merge checklist: [brief summary of what was updated]". If the commit fails (pre-commit hook, empty commit, permissions), report the error to the user, leave Step 6 as `in_progress`, and proceed to Step 7.
3. **Push** to remote (`git push`). If the push fails, report the error to the user and advise them to retry manually with `git push`. Leave Step 6 as `in_progress` and proceed to Step 7.

If all three operations succeeded, mark Step 6 complete.

## Step 7: Present pre-merge report

Mark Step 7 in progress.

Present a summary of what was done:
- [ ] Branch freshness: [current with <default-branch> / merged N commits from <default-branch> / auto-resolved conflicts in: <files> / behind <default-branch> (user skipped merge)]
- [ ] Documentation: [updated / no changes needed]
- [ ] Version: [bumped to X.Y.Z / no version tracking / no changes needed]
- [ ] CHANGELOG: [updated / no changelog maintained / no changes needed]
- [ ] Tests: [all passing / N failures noted]

Recommend next step: `/clear` then `/mach10:pr-merge <pr-number>`

Mark Step 7 complete.
