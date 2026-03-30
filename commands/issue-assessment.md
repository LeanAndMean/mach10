---
description: Read a GitHub issue, perform an independent assessment, and present findings
argument-hint: <issue-number>
allowed-tools: Bash, Read, Grep, Glob, Task, AskUserQuestion
model: opus
---

# Issue Assessment

You are performing an independent assessment of a GitHub issue. Your goal is to deeply understand the issue, explore the relevant codebase, and present your findings with a recommended next step.

**User input:** $ARGUMENTS

## Step 1: Parse Input

The user's input contains:
- An **issue number** (required)

Extract the issue number from the input. If the input is ambiguous, ask the user to clarify.

## Step 2: Read the Issue

Read the issue title and body:

```
gh issue view <issue-number>
```

Then read all comments (`--comments` returns only comments and silently drops the title and body, so both calls are required):

```
gh issue view <issue-number> --comments
```

Parse and understand:
- The problem statement
- Any constraints or requirements mentioned
- Prior discussion or decisions in the comments
- Acceptance criteria (if specified)
- Current state of the issue (open, closed, linked PRs, etc.)

## Step 3: Explore the Codebase

Launch 2-3 exploration agents in parallel using the Task tool (subagent_type: "feature-dev:code-explorer"). Each agent should trace through the code comprehensively and target a different aspect:

- **Relevant code**: Find existing code related to the issue. Trace through their implementation comprehensively, identifying patterns, conventions, and the design decisions that shaped them.
- **Architecture**: Map the relevant architecture layers, abstractions, and data flow, tracing through the code comprehensively to understand how components interact and where boundaries lie.
- **Prior work**: Check for related branches, PRs, or commits that may already address part of the issue. Trace through any partial implementations to assess their completeness and approach.

Each agent should return a list of 5-10 key files. After agents complete, read all identified files to build deep understanding.

## Step 4: Assess

Based on your understanding of the issue and codebase, present your assessment to the user:

1. **Summary**: What the issue is asking for in your own words.
2. **Current state**: What exists today in the codebase that is relevant.
3. **Gaps**: What is missing, broken, or unclear.
4. **Ambiguities**: Any underspecified aspects, contradictions, or open questions in the issue.
5. **Scope**: Your assessment of the size and complexity of the work.
6. **Risks**: Potential pitfalls, edge cases, or architectural concerns.

## Step 5: Recommend Next Step

Based on your assessment, present your findings and then use `AskUserQuestion` to let the user select the next action:

- **Update issue body**: "The issue description is incomplete or outdated"
- **Post a reply comment**: "The issue body is fine but the assessment adds valuable context"
- **Both**: "Update the issue body and post a separate comment"

Include your recommendation in the assessment text before presenting the choices. If the assessment reveals that the issue should be split into smaller work items or is already resolved, mention these as paths the user can express via the built-in "Other" option.

After the user selects an action, draft the appropriate content:

- **Update issue body**: Draft the updated issue body.
- **Post a reply comment**: Draft the comment.
- **Both**: Draft the updated issue body and the comment.
- **Other**: Handle the user's free-text response (e.g., splitting the issue, closing as resolved, or creating new issues as described).

## Step 6: Execute

Present the drafted content to the user, then use `AskUserQuestion` to ask for approval:

- **Approve**: "Execute the recommended action"
- **Modify**: "Edit the drafted content before executing"
- **Cancel**: "Abort without making changes"

If the user selects "Modify", ask what they want to change, apply the changes, and present the updated draft for approval again. If the user selects "Cancel", stop and confirm that no changes were made.

After the user approves:

- **Update issue body**: `gh issue edit <issue-number> --body "..."`
- **Post comment**: `gh issue comment <issue-number> --body "..."`

When referring to numbered items (findings, suggestions, stages) in any `--body` content, use plain words like "finding 3" or "suggestion 3" -- not `#<number>` notation, which GitHub auto-links to issues/PRs.

Confirm the actions taken and provide links.

**CLI output only (do NOT include in any GitHub comment):** Suggest next step: `/clear` then `/mach10:issue-plan <issue-number>` to create an implementation plan.
