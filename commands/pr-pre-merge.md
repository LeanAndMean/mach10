---
description: Run pre-merge checklist — docs, version, CHANGELOG, tests
argument-hint: <pr-number>
allowed-tools: Bash, Read, Grep, Glob, Edit, Write
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

If found, read the file and extract any pre-merge requirements (version bumps, changelog entries, documentation updates, test requirements, etc.).

If no contributing guide exists, use the standard checklist below.

## Step 3: Checkout and Prepare

Ensure you are on the PR's branch with latest changes:

```
gh pr checkout <pr-number>
git pull
```

## Step 4: Run Checklist

Work through each item. For each, report whether action is needed and perform it if so.

### 4a. Documentation

- Are there new features or changed behavior that need documentation updates?
- Check README.md, any docs/ directory, docstrings, and help text.
- Update as needed.

### 4b. Version Bump

- Check if the project uses semantic versioning (look for version in package.json, pyproject.toml, setup.cfg, __version__, etc.)
- If version tracking exists, determine if a bump is warranted:
  - **Patch**: Bug fixes, minor improvements
  - **Minor**: New features, non-breaking changes
  - **Major**: Breaking changes
- Ask the user for the version bump level if not obvious.

### 4c. CHANGELOG

- Check if the project maintains a CHANGELOG.md or CHANGES.md.
- If so, add an entry for this PR's changes following the existing format.

### 4d. Tests

Run the project's test suite:

```
# Auto-detect test runner
# Python: pytest, unittest
# JavaScript: npm test, jest
# etc.
```

Report results. If tests fail, investigate and report — do NOT silently ignore failures.

## Step 5: Commit

If any changes were made during the checklist, commit them:

- Stage only the files modified during this checklist
- Commit message: "Pre-merge checklist: [brief summary of what was updated]"

Push to remote.

## Step 6: Report

Present a summary of what was done:
- [ ] Documentation: [updated / no changes needed]
- [ ] Version: [bumped to X.Y.Z / no version tracking / no changes needed]
- [ ] CHANGELOG: [updated / no changelog maintained / no changes needed]
- [ ] Tests: [all passing / N failures noted]

Recommend next step: `/clear` then `/mach10:pr-merge <pr-number>`
