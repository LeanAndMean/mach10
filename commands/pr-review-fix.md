---
description: Fix specific issues from a PR review using feature-dev
argument-hint: <pr-number> [--review-comment <id>] [--assessment-comment <id>] [issue-numbers] [context]
allowed-tools: Bash, Read, Grep, Glob, Task, Edit, Write, Skill, AskUserQuestion
model: opus
---

# Fix Review Issues

You are fixing specific issues identified in a PR review. This command gathers context from the PR and its review comments, then delegates to the feature-dev workflow for implementation.

**User input:** $ARGUMENTS

## Step 1: Parse Input

The user's input typically contains:
- A **PR number** (required)
- **`--review-comment <id>`** flag with a numeric comment ID (optional)
- **`--assessment-comment <id>`** flag with a numeric comment ID (optional)
- **Issue numbers to fix** from the review (optional)
- Additional context or constraints (optional)

Example inputs:
- `108` (PR only -- read the PR and determine which review findings to fix)
- `108 1,2,3`
- `108 --review-comment 1234567890 --assessment-comment 1234567891 1,2,3`
- `108 --review-comment 1234567890 1,2,3 focus on error handling`

Extract the PR number. Parse `--review-comment` and `--assessment-comment` flags if present (each followed by a numeric ID). If issue numbers are provided, note them. If the input is ambiguous, ask the user to clarify.

## Step 2: Gather Context

Read the PR title and description:

```
gh pr view <pr-number>
```

### Locate the review comment

**If `--review-comment` was provided:** Fetch the specific comment by ID:

```
gh api repos/:owner/:repo/issues/comments/<review-comment-id>
```

Extract the `body` field from the JSON response. This is the review comment content.

**If `--review-comment` was NOT provided (fallback):** Fetch all comments as JSON and find the review heuristically:

```
gh pr view <pr-number> --json comments
```

Parse the JSON array and search from the END (most recent first) for the first comment whose body contains the HTML marker `<!-- mach10-review -->`. If no comment contains the marker, fall back to finding the last comment with the structured review format (Critical/Important/Suggestions sections and model attribution).

### Locate the assessment comment (optional)

**If `--assessment-comment` was provided:** Fetch it by ID:

```
gh api repos/:owner/:repo/issues/comments/<assessment-comment-id>
```

**If not provided:** This is optional context. Do not attempt to locate the assessment heuristically — proceed without it.

Save the review comment content for use in Step 4.

## Step 3: Identify Issues to Fix

**If issue numbers were provided in the input:**
- Extract those specific issues from the review comment.

**If only a PR number was provided with no specific issue numbers:**
- Present all review findings to the user, organized by severity.
- Recommend which to fix in this session using batch sizing heuristics:
  - **Simple one-line fixes:** up to ~10 at once
  - **Moderate fixes:** ~6 at a time
  - **Deep or complex fixes:** no more than ~3 at a time
  - Group similar issues together
- Use `AskUserQuestion` with `multiSelect: true` to let the user select which issues to fix. If there are 4 or fewer findings, list each as a separate option. If there are more than 4 findings, group them by severity as options (e.g., "All critical findings (3)", "All important findings (5)"). The built-in "Other" option allows the user to specify individual issue numbers if they prefer a custom selection.

## Step 4: Delegate to Feature Dev

Use the Skill tool to invoke `/feature-dev:feature-dev` with the following context:

> Read PR #<pr-number> (title and description only -- do not fetch all comments). The review comment content is provided below. Implement fixes for the identified issues using the 7-phase development plan. IMPORTANT: After reading the development plan phases, add each phase as a task to your todo list so you do not skip any phases.
>
> **Review comment:**
> <paste the full review comment content retrieved in Step 2>

If an assessment comment was also retrieved in Step 2, append it:

> **Assessment comment:**
> <paste the full assessment comment content>

## Step 5: After Fixes

Once fixes are complete, the user will typically run `/mach10:push` to commit, push, and document the fixes on the PR.

## Important Notes

- Each fix session should be **fresh** to maximize available context.
- If an issue is out of scope or would require significant refactoring, recommend deferring it to a new GitHub issue rather than fixing it inline. Offer to create the issue with `/mach10:issue-create`.
- After all fix batches are done, the user should `/clear` then re-run `/mach10:pr-review <pr-number>` to verify the fixes.
