---
description: Merge a PR, delete the feature branch, and optionally create a release
argument-hint: <pr-number>
allowed-tools: Bash
---

# Merge and Release

You are merging a PR that has passed review and the pre-merge checklist, then optionally creating a release.

**PR number:** $ARGUMENTS

## Step 1: Verify Readiness

Confirm the PR is ready to merge:

```
gh pr view $ARGUMENTS --json state,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup
```

If there are blocking issues (failed checks, merge conflicts, etc.), report them to the user and stop. Do NOT force-merge.

## Step 2: Merge

Merge the PR using the repository's default merge strategy, and delete the remote feature branch in the same command:

```
gh pr merge $ARGUMENTS --delete-branch
```

Then update local main:

```
git checkout main && git pull
```

Clean up the local feature branch if it still exists. Get the branch name from the PR:

```
gh pr view $ARGUMENTS --json headRefName --jq .headRefName
```

Then delete the local branch:

```
git branch -d <branch-name-from-above>
```

## Step 3: Ask About Release

Ask the user if they want to create a release for this merge.

If yes, proceed to Step 4. If no, skip to Step 5.

## Step 4: Create Release (If Requested)

Read recent releases for style consistency:

```
gh release list --limit 5
```

If there are existing releases, read the most recent one for format reference:

```
gh release view <latest-tag>
```

Draft a release:
- **Tag**: Follow existing tagging convention (e.g., `v1.2.3`, `1.2.3`). If a version bump was done in pre-merge, use that version.
- **Title**: Follow existing title convention. If none, use the PR title.
- **Notes**: Summarize changes from this PR. Match the style of previous release notes.

Present the draft to the user for approval, then create:

```
gh release create <tag> --title "..." --notes "..."
```

## Step 5: Confirm

Report to the user:
- PR merged (with merge commit hash)
- Feature branch deleted
- Release created (if applicable, with link)
- Current state of main branch
