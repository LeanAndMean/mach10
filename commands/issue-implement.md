---
description: Implement a specific stage of an issue's implementation plan using feature-dev
argument-hint: <issue-number> <stage(s)> [context]
allowed-tools: Bash, Read, Grep, Glob, Task, Edit, Write, Skill, AskUserQuestion
model: opus
---

# Implement Stage

You are implementing a specific stage of a staged implementation plan. This command gathers context from a GitHub issue, then delegates to the feature-dev workflow.

**User input:** $ARGUMENTS

## Step 1: Parse Input

The user's input typically contains:
- An **issue number** (required)
- A **stage number or range** (required)
- Additional context or constraints (optional)

Example inputs:
- `55 1`
- `55 2 but only the frontend parts`
- `55 stages 3-4`

Extract the issue number and stage(s). If the input is ambiguous, ask the user to clarify.

## Step 2: Ensure Feature Branch

Before gathering context or delegating work, ensure you are on an appropriate feature branch. Implementation must never happen directly on the default branch.

Determine the current branch and the default branch:

```
git branch --show-current
gh repo view --json defaultBranchRef --jq .defaultBranchRef.name
```

### If on the default branch

1. Check for uncommitted changes with `git status --porcelain`. If the working tree is dirty, stop and tell the user to commit or stash their changes before proceeding.

2. Search for convention-named branches that match the issue number. Run `git branch -a` and normalize each result by trimming leading whitespace and stripping the `remotes/origin/` prefix if present. Then filter for branches that start with `feature/issue-<number>-` or `fix/issue-<number>-`, or that equal `feature/issue-<number>` or `fix/issue-<number>` exactly. Use strict matching so that `issue-4-` does not match `issue-42-`.

3. **Exactly one match found:** Check it out with `git checkout <branch>` and `git pull --ff-only`. If the pull fails because local and remote have diverged, stop and tell the user to resolve the divergence before continuing.

4. **Multiple matches found:** Present the list to the user, then use `AskUserQuestion` to let them choose. Use the branch names as option labels (if more than 4 branches match, list the 4 most recently updated and let the built-in "Other" option cover the rest).

5. **No match found:** Use `AskUserQuestion` to ask the user how to proceed:

   - **Create a new branch**: "Derive a branch name from the issue title"
   - **Use an existing branch**: "Specify an existing branch to check out"

   If the user selects "Create a new branch":
     - Read the issue title: `gh issue view <issue-number> --json title --jq .title`
     - Derive a slug: lowercase, replace spaces and special characters with hyphens, truncate to 3-5 words
     - Create the branch: `git checkout -b feature/issue-<number>-<slug>`
     - Push with upstream tracking: `git push -u origin <branch-name>`
   If the user selects "Use an existing branch", ask them for the branch name (free-text, since the target is open-ended). Verify the branch exists in `git branch -a` output, check it out with `git checkout <branch>`, and `git pull --ff-only`. If the pull fails because local and remote have diverged, stop and tell the user to resolve the divergence before continuing.

### If not on the default branch

1. Check whether the current branch name appears related to the issue. Use strict delimited matching: the branch name should contain `issue-<number>-` or end with `issue-<number>` as a distinct segment (e.g., `feature/issue-4-branch-safety` matches issue 4, but `feature/issue-42-thing` does not). Also match `feature/issue-<number>-` and `fix/issue-<number>-` prefixed patterns.

2. If the branch appears related to the issue, proceed silently.

3. If the branch does not appear related, warn the user and use `AskUserQuestion` to ask how to proceed:

   - **Continue on this branch**: "Proceed with implementation on the current branch"
   - **Switch branch**: "Check out a different branch first"

   If the user selects "Switch branch", ask them for the branch name (free-text, since the target is open-ended). Verify the branch exists in `git branch -a` output, check it out with `git checkout <branch>`, and `git pull --ff-only`. If the pull fails because local and remote have diverged, stop and tell the user to resolve the divergence before continuing.

### Before proceeding

After the branch is confirmed (whether by checkout, silent match, or user confirmation), check for uncommitted changes with `git status --porcelain`. If the working tree is dirty, stop and tell the user to commit or stash their changes before proceeding.

### Assign the issue

After the branch is confirmed and the working tree is clean, assign the current user to the issue:

1. Check existing assignees: `gh issue view <issue-number> --json assignees --jq '[.assignees[].login] | join(",")'`
2. Check current user: `gh api user --jq .login`
3. If the current user is already assigned, skip silently. This is the expected case when returning for subsequent stages after `issue-plan` already assigned the user.
4. If there are no assignees, run `gh issue edit <issue-number> --add-assignee @me`.
5. If other assignees exist (not including the current user), warn the user and use `AskUserQuestion` to ask how to proceed:
   - **Add me**: "Add yourself as an additional assignee alongside the existing assignee(s)" -- run `gh issue edit <issue-number> --add-assignee @me`
   - **Skip**: "Leave the current assignee(s) unchanged" -- no-op, continue
   - **Replace**: "Remove existing assignee(s) and assign only yourself" -- run `gh issue edit <issue-number> --remove-assignee <existing-logins> --add-assignee @me`
6. If the assignment command fails (e.g., insufficient permissions), warn the user in CLI output and continue -- assignment failure must not block the workflow.

### Assign sub-issues

After the parent issue assignment, assign sub-issues to the current user:

1. Detect sub-issues using the two-strategy approach:

   - **Strategy A (API):** First resolve the repository identifier, then query the GitHub sub-issues API:
     ```
     REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
     gh api repos/$REPO/issues/<issue-number>/sub_issues --jq '.[].number'
     ```
     - If the API call **succeeds and returns one or more numbers**, use them as the confirmed sub-issue list.
     - If the API call **succeeds but returns no results** (empty array), the issue has no sub-issues. Do NOT fall through to Strategy B -- treat the sub-issue list as empty.
     - If the API call **fails** (e.g., 404, permission error, network timeout), proceed to Strategy B.

   - **Strategy B (body-parse fallback):** This strategy runs only when Strategy A **failed**. Scan the issue body for sub-issue references. Match `#<number>` references that appear on GitHub task list lines -- lines beginning with optional whitespace followed by a list marker (`-`, `*`, or `+`) and a checkbox (`[ ]`, `[x]`, or `[X]`). Exclude any `#<number>` preceded by relational keywords: "Related to", "Blocked by", "See also", or "Depends on". Collect the matched issue numbers, excluding the parent issue number itself.

2. If sub-issues are found, get the current user login via `gh api user --jq .login` (reuse the value from the parent assignment step if already retrieved). For each sub-issue, check assignees via `gh issue view <sub-issue> --json assignees --jq '[.assignees[].login] | join(",")'`. Three paths:
   - Current user already assigned: skip silently. This is the expected case when returning for subsequent stages after `issue-plan` already assigned sub-issues.
   - No assignees: auto-assign with `gh issue edit <sub-issue> --add-assignee @me`
   - Other assignees exist: collect into a "conflicting" list

3. If the conflicting list is non-empty, use `AskUserQuestion` to ask the user how to proceed with a single bulk decision:
   - **Add me**: "Add yourself as an additional assignee on all conflicting sub-issues" -- run `gh issue edit <sub-issue> --add-assignee @me` for each
   - **Skip**: "Leave the current assignee(s) unchanged on all sub-issues" -- no-op
   - **Replace**: "Remove existing assignee(s) and assign only yourself on all sub-issues" -- run `gh issue edit <sub-issue> --remove-assignee <existing-logins> --add-assignee @me` for each

4. Assignment failures are non-blocking (warn and continue).

## Step 3: Gather Context

Read the issue title and body:

```
gh issue view <issue-number>
```

Then read all comments to find the implementation plan (`--comments` returns only comments and silently drops the title and body, so both calls are required):

```
gh issue view <issue-number> --comments
```

Locate the implementation plan comment by searching all issue comments for the `<!-- mach10-plan -->` HTML marker. If multiple comments contain the marker, use the last one (the most recent revision). If no comment contains the marker, fall back to identifying the most recent substantive comment that contains a staged implementation plan. Identify the requested stage(s).

## Step 4: Delegate to Feature Dev

Use the Skill tool to invoke `/feature-dev:feature-dev` with the following context:

> Read issue #<issue-number> (both the issue body and all comments). Locate the staged implementation plan in the comments, then implement the requested stage(s) using the 7-phase development plan. Use the issue body for context on the problem statement, requirements, and acceptance criteria. IMPORTANT: After reading the development plan phases, add each phase as a task to your todo list so you do not skip any phases.

If the stage reveals issues with the original plan, note them and suggest plan adjustments rather than silently deviating.

After implementation is complete, suggest: "Next: `/mach10:push` to commit, push, and document progress."

Each stage should be implemented in a **fresh CLI session** to maximize available context.
