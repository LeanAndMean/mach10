---
description: Run pre-merge checklist — branch freshness, docs, version, CHANGELOG, tests
argument-hint: <pr-number>
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, AskUserQuestion
---

# Pre-Merge Checklist

You are running the pre-merge checklist for a PR that has passed review. Walk through each checklist item, perform the necessary updates, and commit the results.

**User input:** $ARGUMENTS

## Step 1: Parse Input

The user's input contains:
- A **PR number** (required)

Extract the PR number from the input. If the input is ambiguous, ask the user to clarify.

## Step 2: Read Contributing Guidelines

Look for project contribution guidelines in order of precedence:

```
CONTRIBUTING.md
DEVELOPMENT.md
.github/CONTRIBUTING.md
```

Read only the first file found; skip the rest.

If found, read the file and extract any pre-merge requirements (version bumps, changelog entries, documentation updates, test requirements, etc.).

If no contributing guide exists, use the standard checklist below.

## Step 3: Checkout and Prepare

Ensure you are on the PR's branch with latest changes:

```
gh pr checkout <pr-number>
git pull
```

## Step 4: Branch Freshness Check

Ensure the feature branch is up to date with the default branch before running the checklist.

Determine the default branch and fetch the latest remote state:

```
gh repo view --json defaultBranchRef --jq .defaultBranchRef.name
git fetch origin
```

Count how many commits the branch is behind:

```
git rev-list --count HEAD..origin/<default-branch>
```

If the count is **0**, the branch is current — continue to Step 5.

If the count is **greater than 0**, inform the user that the branch is N commits behind `origin/<default-branch>`, then use `AskUserQuestion` to ask how to proceed:

- **Merge**: "Merge the default branch into this branch now"
- **Skip**: "Leave the branch as-is and continue the checklist"
- **Cancel**: "Stop without running the checklist"

If the user selects **Cancel**, stop the session.

If the user selects **Skip**, note the skipped status for the report and continue to Step 5.

If the user selects **Merge**, run:

```
git merge origin/<default-branch>
```

**If the merge succeeds cleanly**, push the merge commit (`git push`). If the push fails, report the error to the user and stop — do not continue the checklist with an unpushed merge commit. On success, continue to Step 5.

**If the merge has conflicts**, check whether all conflicted files are version files — files whose conflicts are limited to version fields (e.g., `plugin.json`, `package.json`, `pyproject.toml`, `setup.cfg`). Use your judgement for other files that appear to contain only trivial version-field conflicts.

- **All conflicts are trivial (version files only):** For each conflicted file, resolve by taking the default branch's version (`git checkout --theirs <file>` then `git add <file>`), then finalize the merge with `git commit --no-edit`. Push the result (`git push`). If the push fails, report the error and stop. Record which files were auto-resolved for the report.
- **Any non-trivial conflicts exist:** Abort the merge with `git merge --abort`. Report the list of conflicted files to the user and stop the session — the user must resolve conflicts manually.

## Step 5: Run Checklist

Work through each item. For each, report whether action is needed and perform it if so.

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

## Step 6: Commit

If any changes were made during the checklist, commit them:

- Stage only the files modified during this checklist
- Commit message: "Pre-merge checklist: [brief summary of what was updated]"

Push to remote.

## Step 7: Report

Present a summary of what was done:
- [ ] Branch freshness: [current with main / merged N commits from main / auto-resolved conflicts in: <files> / behind main (user skipped merge)]
- [ ] Documentation: [updated / no changes needed]
- [ ] Version: [bumped to X.Y.Z / no version tracking / no changes needed]
- [ ] CHANGELOG: [updated / no changelog maintained / no changes needed]
- [ ] Tests: [all passing / N failures noted]

Recommend next step: `/clear` then `/mach10:pr-merge <pr-number>`
