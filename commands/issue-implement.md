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

4. **Multiple matches found:** Present the list to the user and ask them to choose which branch to use.

5. **No match found:** Ask the user: "No feature branch found for issue #N. Create a new one, or specify an existing branch name?" Then:
   - **Create a new branch:**
     - Read the issue title: `gh issue view <issue-number> --json title --jq .title`
     - Derive a slug: lowercase, replace spaces and special characters with hyphens, truncate to 3-5 words
     - Create the branch: `git checkout -b feature/issue-<number>-<slug>`
     - Push with upstream tracking: `git push -u origin <branch-name>`
   - **Use an existing branch:** Verify the branch exists in `git branch -a` output, check it out with `git checkout <branch>`, and `git pull --ff-only`. If the pull fails because local and remote have diverged, stop and tell the user to resolve the divergence before continuing.

### If not on the default branch

1. Check whether the current branch name appears related to the issue. Use strict delimited matching: the branch name should contain `issue-<number>-` or end with `issue-<number>` as a distinct segment (e.g., `feature/issue-4-branch-safety` matches issue 4, but `feature/issue-42-thing` does not). Also match `feature/issue-<number>-` and `fix/issue-<number>-` prefixed patterns.

2. If the branch appears related to the issue, proceed silently.

3. If the branch does not appear related, warn the user: "You're on `<branch>` which doesn't appear to be related to issue #N. Continue on this branch?" Let them confirm or switch.

### Before proceeding

After the branch is confirmed (whether by checkout, silent match, or user confirmation), check for uncommitted changes with `git status --porcelain`. If the working tree is dirty, stop and tell the user to commit or stash their changes before proceeding.

## Step 3: Gather Context

Read the issue and all comments to find the implementation plan:

```
gh issue view <issue-number> --comments
```

Locate the implementation plan comment (typically the most recent substantive comment). Identify the requested stage(s).

## Step 4: Delegate to Feature Dev

Use the Skill tool to invoke `/feature-dev:feature-dev` with the following context:

> Read issue #<issue-number> and all comments. Locate the staged implementation plan in the comments, then implement the requested stage(s) using the 7-phase development plan. IMPORTANT: After reading the development plan phases, add each phase as a task to your todo list so you do not skip any phases.

If the stage reveals issues with the original plan, note them and suggest plan adjustments rather than silently deviating.

After implementation is complete, suggest: "Next: `/clear` then `/mach10:push` to commit, push, and document progress."

Each stage should be implemented in a **fresh CLI session** to maximize available context.
