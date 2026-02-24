---
description: Read a GitHub issue, analyze the codebase, and create a staged implementation plan
argument-hint: <issue-number>
allowed-tools: Bash, Read, Grep, Glob, Task
model: opus
---

# Issue Plan

You are creating a staged implementation plan for a GitHub issue. Your goal is to deeply understand the issue, explore the relevant codebase, and produce a plan where each stage can be implemented within a single Claude Code CLI session.

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

## Step 3: Explore the Codebase

Launch 2-3 exploration agents in parallel using the Task tool (subagent_type: Explore). Each agent should target a different aspect:

- **Similar features**: Find existing code that solves related problems. Trace through implementation patterns.
- **Architecture**: Map the relevant architecture layers, abstractions, and data flow.
- **Integration points**: Identify where new code would connect to existing systems.

Each agent should return a list of 5-10 key files. After agents complete, read all identified files to build deep understanding.

## Step 4: Analyze and Plan

Based on your understanding of the issue and codebase:

1. Present a clear analysis of the problem.
2. Identify any ambiguities or underspecified aspects.
3. Ask the user clarifying questions before finalizing the plan.
4. Draft a **staged implementation plan** with:
   - Clear stages (numbered, with descriptive names)
   - What each stage accomplishes
   - Which files will be created or modified
   - Dependencies between stages
   - Testing approach for each stage

**Each stage must be scoped to what can be implemented within a single Claude Code CLI session.** A stage that is too large should be split. Consider:
- The amount of codebase exploration needed
- The number of files to create or modify
- The complexity of the logic involved
- The testing surface area

## Step 5: Post and Branch

After the user approves the plan:

1. **Post the plan as a reply comment on the issue** using `gh issue comment <issue-number> --body "..."`. Format the comment so it serves as input to future CLI sessions. Include:
   - The full implementation plan
   - The staged breakdown
   - A note that this comment will guide staged implementation

2. **Create a feature branch**:
   - Derive a short slug from the issue title (lowercase, hyphens, 3-5 words max)
   - Branch name format: `feature/issue-<issue-number>-<slug>`
   - Example: `feature/issue-55-fix-analytics-url`
   - Push the branch to remote with `-u` flag

Confirm both actions to the user.

**CLI output only (do NOT include in the GitHub comment):** Let the user know the next step is `/clear` then `/mach10:issue-implement <issue-number> 1` to begin Stage 1 of the implementation in a fresh session.
