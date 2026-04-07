---
description: Read a GitHub issue, analyze the codebase, and create a staged implementation plan
argument-hint: <issue-number>
allowed-tools: Bash, Read, Grep, Glob, Task, AskUserQuestion
model: opus
---

# Issue Plan

You are creating a staged implementation plan for a GitHub issue. Your goal is to deeply understand the issue, explore the relevant codebase, and produce a plan where each stage can be implemented within a single Claude Code CLI session.

**User input:** $ARGUMENTS

## Guardrails

This command is strictly for **planning**. Do NOT:

- Use `EnterPlanMode` or enter plan mode
- Implement any code changes -- no file edits, no file writes
- Attempt to execute the plan within this session

Implementation happens in separate sessions via `/mach10:issue-implement`.

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

### 3a. Read Contributing Guidelines

Before launching exploration agents, look for project contribution guidelines in order of precedence:

```
CONTRIBUTING.md
DEVELOPMENT.md
.github/CONTRIBUTING.md
```

Read only the first file found; skip the rest.

If found, read the file and extract any planning-relevant guidance: expected project layers (e.g., models, migrations, API routes, services, UI, documentation), testing expectations (test frameworks, coverage requirements, test types), and any other requirements that should inform the implementation plan.

Record these as **project planning requirements** -- they will inform both the exploration focus and the plan drafting in Step 6.

If no contributing guide exists, proceed without project-specific requirements.

### 3b. Explore

Launch 2-3 exploration agents in parallel using the Task tool (subagent_type: "feature-dev:code-explorer"). Each agent should trace through the code comprehensively and target a different aspect:

- **Similar features**: Find existing code that solves related problems. Trace through their implementation comprehensively, identifying patterns and conventions the new work should follow.
- **Architecture**: Map the architecture and abstractions for the relevant area, tracing through the code comprehensively to understand the layers, data flow, and design decisions.
- **Integration points**: Identify where new code would connect to existing systems, including extension surfaces, testing infrastructure, and cross-cutting concerns.

If project planning requirements were identified in Step 3a, include them in each agent's context so exploration covers the relevant project layers and testing infrastructure.

Each agent should return a list of 5-10 key files. After agents complete, read all identified files to build deep understanding.

Present a comprehensive summary of findings and patterns discovered.

## Step 4: Clarifying Questions

**CRITICAL**: This is one of the most important steps. DO NOT SKIP.

Review the codebase findings from Step 3 against the issue requirements. Identify all underspecified aspects:

1. Present a clear analysis of the problem based on what you found in the codebase.
2. Identify ambiguities, underspecified scope, unstated constraints, edge cases, integration concerns, and design preferences that will affect the implementation plan.
3. **Present all questions to the user in a clear, organized list.**
4. **Wait for answers before proceeding to architecture design.**

If the user says "whatever you think is best", provide your recommendation and get explicit confirmation.

## Step 5: Architecture Design

Based on the codebase findings and clarified requirements, launch 2-3 architecture agents in parallel using the Task tool (subagent_type: "feature-dev:code-architect"). Assign each agent a different architectural lens:

- **Minimal changes**: Design the implementation with the smallest change surface. Maximize reuse of existing patterns. Minimize new abstractions.
- **Clean architecture**: Design the implementation prioritizing clear separation of concerns, maintainability, and well-defined abstractions.
- **Pragmatic balance**: Design the implementation balancing speed with code quality and extensibility.

Each agent should produce a full implementation blueprint: files to create or modify, component responsibilities, data flow, and a phased build sequence.

After all agents complete, review their approaches and form your own recommendation based on the issue's scope, the codebase's conventions, and the user's clarified requirements.

Present to the user: brief summary of each approach, trade-offs comparison, **your recommendation with reasoning**, concrete implementation differences.

**Ask user which approach they prefer.**

## Step 6: Plan Drafting

Using the architecture selected in Step 5 as the structural foundation, draft a **staged implementation plan** with:
- Clear stages (numbered, with descriptive names)
- What each stage accomplishes
- Which files will be created or modified
- Dependencies between stages
- Testing approach for each stage

### Planning requirements

Before finalizing the plan, verify it satisfies the following:

**Project-layer coverage:** Cross-check the plan against the project layers discovered during codebase exploration and any layers specified in the project planning requirements recorded in Step 3a. Every affected layer should be addressed by at least one stage. If a discovered layer is not affected by this change, it may be omitted -- but if a layer is affected and no stage addresses it, add the missing work to the appropriate stage or create a new one.

**Test coverage planning:** Identify what testing is appropriate for this project and codebase. If the project has an existing test suite or the project planning requirements specify testing expectations, each stage that introduces or modifies behavior must specify: what tests to add or modify, what test types are needed (unit, integration, end-to-end, etc.), and what behaviors or interfaces to cover. If the project has no testable runtime code (e.g., plugin definitions, documentation, configuration), note this in the plan and skip test planning.

**Each stage must be scoped to what can be implemented within a single Claude Code CLI session.** A stage that is too large should be split. Consider:
- The amount of codebase exploration needed
- The number of files to create or modify
- The complexity of the logic involved
- The testing surface area

## Step 7: Post and Branch

Present the plan to the user, then use `AskUserQuestion` to ask for approval with these options:

- **Approve**: "Post the plan and create the feature branch"
- **Request changes**: "Suggest changes to the plan before posting"
- **Cancel**: "Abort without posting the plan or creating a branch"

If the user selects "Request changes", discuss their feedback, revise the plan, and present it for approval again. If the user selects "Cancel", stop and confirm that the plan was not posted and no branch was created.

After the user approves the plan:

1. **Post the plan as a reply comment on the issue** using `gh issue comment <issue-number> --body "..."`. Format the comment so it serves as input to future CLI sessions. Include:
   - `<!-- mach10-plan -->` as the very first line of the comment body (this invisible HTML marker enables reliable identification in future sessions)
   - The full implementation plan
   - The staged breakdown
   - A `## Decision Log` section appended after the staged breakdown. This section captures the reasoning behind key decisions made during planning:
     - **Clarifying Questions (Step 4):** For each question asked and answered, include the question and a synthesized answer. Only include exchanges where the answer changed or constrained the plan. Omit exchanges where the user confirmed a default or said "whatever you think is best."
     - **Architecture Choice (Step 5):** The selected approach, the rationale for choosing it, and the alternatives considered with brief reasons for rejection.
     - **Omission condition:** Skip the Decision Log section entirely if Step 4 produced no questions AND Step 5 had no meaningful differentiation between approaches (e.g., only one viable approach existed).
   - A note that this comment will guide staged implementation

2. **Create a feature branch**:
   - Derive a short slug from the issue title (lowercase, hyphens, 3-5 words max)
   - Branch name format: `feature/issue-<issue-number>-<slug>`
   - Example: `feature/issue-55-fix-analytics-url`
   - Push the branch to remote with `-u` flag

3. **Assign the issue** to the current user:
   - Check existing assignees: `gh issue view <issue-number> --json assignees --jq '[.assignees[].login] | join(",")'`
   - Check current user: `gh api user --jq .login`
   - If the current user is already assigned, skip silently.
   - If there are no assignees, run `gh issue edit <issue-number> --add-assignee @me`.
   - If other assignees exist (not including the current user), warn the user and use `AskUserQuestion` to ask how to proceed:
     - **Add me**: "Add yourself as an additional assignee alongside the existing assignee(s)" -- run `gh issue edit <issue-number> --add-assignee @me`
     - **Skip**: "Leave the current assignee(s) unchanged" -- no-op, continue
     - **Replace**: "Remove existing assignee(s) and assign only yourself" -- run `gh issue edit <issue-number> --remove-assignee <existing-logins> --add-assignee @me`
   - If the assignment command fails (e.g., insufficient permissions), warn the user in CLI output and continue -- assignment failure must not block the workflow.

When referring to numbered items (findings, suggestions, stages) in the comment body, use plain words like "finding 3" or "suggestion 3" -- not `#<number>` notation, which GitHub auto-links to issues/PRs.

Confirm all three actions to the user (plan posted, branch created, issue assigned).

**CLI output only (do NOT include in the GitHub comment):** Let the user know the next steps are `/clear` then optionally `/mach10:issue-plan-review <issue-number>` to review the plan, or `/mach10:issue-implement <issue-number> 1` to begin Stage 1 of the implementation in a fresh session.
