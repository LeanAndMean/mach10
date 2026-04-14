---
description: Fix specific issues from a PR review using feature-dev
argument-hint: <pr-number> [--review-comment <id>] [--assessment-comment <id>] [findings] [context]
allowed-tools: Bash, Read, Grep, Glob, Task, TaskCreate, TaskUpdate, Edit, Write, Skill, AskUserQuestion
model: opus
---

# Fix Review Issues

You are fixing specific issues identified in a PR review. This command gathers context from the PR and its review comments, then delegates to the feature-dev workflow for implementation.

**User input:** $ARGUMENTS

## Step 0: Parse input and create task list

The user's input typically contains:
- A **PR number** (required)
- **`--review-comment <id>`** flag with a numeric comment ID (optional)
- **`--assessment-comment <id>`** flag with a numeric comment ID (optional)
- **Finding identifiers to fix** -- space-separated F/S identifiers (e.g., `F1 F2 S3`) or bare numbers as fallback (optional)
- Additional context or constraints (optional)

Example inputs:
- `108` (PR only -- read the PR and determine which review findings to fix)
- `108 F1 F2 S3`
- `108 --review-comment 1234567890 --assessment-comment 1234567891 F1 F2 S3`
- `108 --review-comment 1234567890 F1 S2 focus on error handling`

Extract the PR number. Parse `--review-comment` and `--assessment-comment` flags if present (each followed by a numeric ID). If finding identifiers are provided (F/S prefixed or bare numbers), note them. If the input is ambiguous, ask the user to clarify.

After parsing input, create the progress-tracking task list. Create a task for Step 0 and immediately mark it in progress. Then create tasks for each of the remaining 4 steps one at a time, in step order, waiting for each to complete before creating the next, all starting as pending. Store each returned task ID for later use -- do not assume IDs are sequential.

| Task | Subject | activeForm |
|------|---------|------------|
| Step 0 | Step 0: Parse input and create task list | Parsing input |
| Step 1 | Step 1: Gather PR and review context | Gathering context |
| Step 2 | Step 2: Identify issues to fix | Identifying issues |
| Step 3 | Step 3: Fix review findings via feature-dev | Fixing findings |
| Step 4 | Step 4: Recommend next steps | Recommending next steps |

Mark Step 0 complete.

## Step 1: Gather PR and review context

Mark Step 1 in progress.

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

Save the review comment content for use in Step 3.

Mark Step 1 complete.

## Step 2: Identify issues to fix

Mark Step 2 in progress.

**If finding identifiers were provided in the input:**
- Match identifiers against the F/S labels in the review comment (e.g., `F1` matches `**F1:**`). If bare numbers were given, match by sequential position across Critical and Important sections. If the review comment lacks F/S labels (e.g., older reviews), fall back to matching by ordinal position within each severity section. Extract the full finding descriptions.

**If only a PR number was provided with no specific finding identifiers:**
- Present all review findings to the user, organized by severity.
- Recommend which to fix in this session using batch sizing heuristics:
  - **Simple one-line fixes:** up to ~10 at once
  - **Moderate fixes:** ~6 at a time
  - **Deep or complex fixes:** no more than ~3 at a time
  - Group similar issues together
- Use `AskUserQuestion` with `multiSelect: true` to let the user select which issues to fix. If there are 4 or fewer findings, list each as a separate option. If there are more than 4 findings, group them by severity as options (e.g., "All critical findings (3)", "All important findings (5)"). The built-in "Other" option allows the user to specify individual finding identifiers (e.g., F1 S3) if they prefer a custom selection.

Mark Step 2 complete.

## Step 3: Fix review findings via feature-dev

Mark Step 3 in progress.

Use the Skill tool to invoke `/feature-dev:feature-dev` with the following context:

> Read PR #<pr-number> (title and description only -- do not fetch all comments). The review comment content is provided below. Implement fixes for the identified issues using the 7-phase development plan. IMPORTANT: Create a task for each phase of the 7-phase development plan before starting work. Use `"Phase N: <action>"` as the subject format (e.g., `"Phase 1: Understand the codebase"`). Mark each phase in progress when starting and complete when finishing. Do not skip any phases.
>
> **Findings to fix (from Step 2):** <list the resolved finding identifiers and their one-line descriptions>
>
> Fix only the findings listed above. Do not fix other findings in the review comment.
>
> **Review comment:**
> <paste the full review comment content retrieved in Step 1>

If an assessment comment was also retrieved in Step 1, append it:

> **Assessment comment:**
> <paste the full assessment comment content>

If the user provided additional context or constraints in their input (parsed in Step 0), append it:

> **User context:** <the additional context or constraints from the user's input>

Mark Step 3 complete.

## Step 4: Recommend next steps

Mark Step 4 in progress.

Once fixes are complete, suggest: "Next: `/mach10:push` to commit, push, and document the fixes on the PR."

Mark Step 4 complete.

## Important Notes

- Each fix session should be **fresh** to maximize available context.
- If an issue is out of scope or would require significant refactoring, recommend deferring it to a new GitHub issue rather than fixing it inline. Offer to create the issue with `/mach10:issue-create`.
- After all fix batches are done, the user should `/clear` then re-run `/mach10:pr-review <pr-number>` to verify the fixes.
