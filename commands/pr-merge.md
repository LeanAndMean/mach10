---
description: Merge a PR, delete the feature branch, and optionally create a release
argument-hint: <pr-number>
allowed-tools: Bash, AskUserQuestion
---

# Merge and Release

You are merging a PR that has passed review and the pre-merge checklist, then optionally creating a release.

**User input:** $ARGUMENTS

## Step 1: Parse Input

The user's input contains:
- A **PR number** (required)

Extract the PR number from the input. If the input is ambiguous, ask the user to clarify.

## Step 2: Verify Readiness

Confirm the PR is ready to merge:

```
gh pr view <pr-number> --json state,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup
```

If there are blocking issues, report them to the user and stop. Do NOT force-merge.

- **Failed CI checks**: Suggest `/clear` then `/mach10:pr-ci-fix <pr-number>` to diagnose and fix the failures.
- **Merge conflicts**: Suggest resolving conflicts manually or rebasing the branch.
- **Missing review approval**: Suggest requesting a review.
- **Branch behind main**: When `mergeStateStatus` is `BEHIND`, suggest `/clear` then `/mach10:pr-pre-merge <pr-number>` to update the branch before merging.

## Step 3: Merge

Merge the PR using the repository's default merge strategy, and delete the remote feature branch in the same command:

```
gh pr merge <pr-number> --delete-branch
```

Then update local main:

```
git checkout main && git pull
```

Clean up the local feature branch if it still exists. Get the branch name from the PR:

```
gh pr view <pr-number> --json headRefName --jq .headRefName
```

Then delete the local branch:

```
git branch -d <branch-name-from-above>
```

## Step 4: Ask About Release

Use `AskUserQuestion` to ask whether to create a release:

- **Create release**: "Create a release for this merge"
- **Skip release**: "Skip release creation"

If the user selects "Create release", proceed to Step 5. If "Skip release", skip to Step 6.

## Step 5: Create Release (If Requested)

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

Present the draft to the user, then use `AskUserQuestion` to ask for approval with these options:

- **Approve**: "Create the release as drafted"
- **Modify**: "Edit the release tag, title, or notes"
- **Skip release**: "Skip release creation after all"

If the user selects "Modify", ask what they want to change, apply the changes, and present the updated draft for approval again. If the user selects "Skip release", skip to Step 6.

After approval, create the release:

```
gh release create <tag> --title "..." --notes "..."
```

## Step 6: Confirm

Report to the user:
- PR merged (with merge commit hash)
- Feature branch deleted
- Release created (if applicable, with link)
- Current state of main branch
