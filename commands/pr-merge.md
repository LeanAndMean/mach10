---
description: Merge a PR, delete the feature branch, and optionally create a release
argument-hint: <pr-number> [context]
allowed-tools: Bash, AskUserQuestion
---

# Merge and Release

You are merging a PR that has passed review and the pre-merge checklist, then optionally creating a release.

**User input:** $ARGUMENTS

## Step 1: Parse Input

The user's input contains:
- A **PR number** (required)
- Additional **context** or constraints (optional)

Extract the PR number from the input. If the input is ambiguous, ask the user to clarify. If context was provided, note it for use in later steps (e.g., release notes guidance, version tag preference).

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

If the user provided context about release creation, honor it as guidance for this step:

- **Skip directives** (e.g., "skip release", "no release this time"): Skip the `AskUserQuestion` below entirely and proceed directly to Step 6. Report in CLI output: "Skipping release per user request." The user has already declined; re-asking is friction without safety benefit. No release will be created; this is the safe path.
- **Release-creating directives** (e.g., "tag as v2.0.0", "highlight the auth changes"): Still ask the question below, but frame it to acknowledge the user wants to create a release and present "Create release" as the recommended choice in the question text. Stash the specific details (tag, highlights, notes style) for the Step 5 draft. The yes/no gate is preserved because a release is a substantive action -- Claude should not draft and create one without an explicit confirmation, even if the user named a tag.
- **No release-relevant context**: Ask the question below as a neutral yes/no.

Step 5's draft-approval gate is the content-review gate for the release itself -- it always runs when a release is being created, regardless of context.

If no skip directive was given, use `AskUserQuestion` to ask whether to create a release:

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

If the user provided context, use it to inform the release draft (e.g., specific tag, highlighted changes, notes style).

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
