---
description: Fix specific issues from a PR review using feature-dev
argument-hint: <pr-number> [issue-numbers] [context]
allowed-tools: Bash, Read, Grep, Glob, Task, Edit, Write, Skill
model: opus
---

# Fix Review Issues

You are fixing specific issues identified in a PR review. This command gathers context from the PR and its review comments, then delegates to the feature-dev workflow for implementation.

**User input:** $ARGUMENTS

## Step 1: Parse Input

The user's input typically contains:
- A **PR number** (required)
- **Issue numbers to fix** from the review (optional)
- Additional context or constraints (optional)

Example inputs:
- `108` (PR only -- read the PR and determine which review findings to fix)
- `108 1,2,3`
- `108 1,2,3 focus on error handling`

Extract the PR number. If issue numbers are provided, note them. If the input is ambiguous, ask the user to clarify.

## Step 2: Gather Context

Read the PR description and all comments to find the review:

```
gh pr view <pr-number>             # title + description
gh pr view <pr-number> --comments  # comments only
```

Locate the most recent review comment (look for the structured review format with Critical/Important/Suggestions sections and model attribution).

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
- Ask the user which issues to tackle in this session.

## Step 4: Delegate to Feature Dev

Use the Skill tool to invoke `/feature-dev:feature-dev` with the following context:

> Read PR #<pr-number> and all comments. Locate the most recent review comment, then implement fixes for the identified issues using the 7-phase development plan. IMPORTANT: After reading the development plan phases, add each phase as a task to your todo list so you do not skip any phases.

## Step 5: After Fixes

Once fixes are complete, the user will typically run `/mach10:push` to commit, push, and document the fixes on the PR.

## Important Notes

- Each fix session should be **fresh** to maximize available context.
- If an issue is out of scope or would require significant refactoring, recommend deferring it to a new GitHub issue rather than fixing it inline. Offer to create the issue with `/mach10:issue-create`.
- After all fix batches are done, the user should `/clear` then re-run `/mach10:pr-review <pr-number>` to verify the fixes.
