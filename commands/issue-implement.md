---
description: Implement a specific stage of an issue's implementation plan using feature-dev
argument-hint: <issue-number> <stage(s)> [context]
allowed-tools: Bash, Read, Grep, Glob, Task, Edit, Write, Skill
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

## Step 2: Gather Context

Read the issue and all comments to find the implementation plan:

```
gh issue view <issue-number> --comments
```

Locate the implementation plan comment (typically the most recent substantive comment). Identify the requested stage(s).

## Step 3: Delegate to Feature Dev

Use the Skill tool to invoke `/feature-dev:feature-dev` with the following context:

> Read issue #<issue-number> and all comments. Locate the staged implementation plan in the comments, then implement the requested stage(s) using the 7-phase development plan. IMPORTANT: After reading the development plan phases, add each phase as a task to your todo list so you do not skip any phases.

## Important Notes

- Each stage should be implemented in a **fresh CLI session** to maximize available context.
- After implementation is complete, the user will typically run `/mach10:push` to commit, push, and document progress.
- If the stage reveals issues with the original plan, note them and suggest plan adjustments rather than silently deviating.
