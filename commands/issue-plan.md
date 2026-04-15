---
description: Read a GitHub issue, analyze the codebase, and create a staged implementation plan
argument-hint: <issue-number>
allowed-tools: Bash, Read, Grep, Glob, Task, TaskCreate, TaskUpdate, AskUserQuestion
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

## Step 0: Parse input and create task list

The user's input contains:
- An **issue number** (required)

Extract the issue number from the input. If the input is ambiguous, ask the user to clarify.

After parsing input, create the progress-tracking task list. Create a task for Step 0 and immediately mark it in progress. Then create tasks for each of the remaining 6 steps one at a time, in step order, all starting as pending. Task list display order matches creation order, so each task must be a separate sequential call -- do not batch multiple task creations in a single message. Store each returned task ID for later use -- do not assume IDs are sequential.

| Task | Subject | activeForm |
|------|---------|------------|
| Step 0 | Step 0: Parse input and create task list | Parsing input |
| Step 1 | Step 1: Read the issue | Reading the issue |
| Step 2 | Step 2: Explore the codebase | Exploring the codebase |
| Step 3 | Step 3: Ask clarifying questions | Asking clarifying questions |
| Step 4 | Step 4: Design architecture | Designing architecture |
| Step 5 | Step 5: Draft the plan | Drafting the plan |
| Step 6 | Step 6: Post plan and create branch | Posting plan and creating branch |

Mark Step 0 complete.

## Step 1: Read the issue

Mark Step 1 in progress.

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

Mark Step 1 complete.

## Step 2: Explore the codebase

Mark Step 2 in progress.

### 2a. Read Contributing Guidelines

Before launching exploration agents, look for project contribution guidelines in order of precedence:

```
CONTRIBUTING.md
DEVELOPMENT.md
.github/CONTRIBUTING.md
```

Read only the first file found; skip the rest.

If found, read the file and extract any planning-relevant guidance: expected project layers (e.g., models, migrations, API routes, services, UI, documentation), testing expectations (test frameworks, coverage requirements, test types), and any other requirements that should inform the implementation plan.

Record these as **project planning requirements** -- they will inform both the exploration focus and the plan drafting in Step 5.

If no contributing guide exists, proceed without project-specific requirements.

### 2b. Explore

Launch 2-3 exploration agents in parallel using the Task tool (subagent_type: "feature-dev:code-explorer"). Each agent should trace through the code comprehensively and target a different aspect:

- **Similar features**: Find existing code that solves related problems. Trace through their implementation comprehensively, identifying patterns and conventions the new work should follow.
- **Architecture**: Map the architecture and abstractions for the relevant area, tracing through the code comprehensively to understand the layers, data flow, and design decisions.
- **Integration points**: Identify where new code would connect to existing systems, including extension surfaces, testing infrastructure, and cross-cutting concerns.

If project planning requirements were identified in Step 2a, include them in each agent's context so exploration covers the relevant project layers and testing infrastructure.

Each agent should return a list of 5-10 key files. After agents complete, read all identified files to build deep understanding.

Present a comprehensive summary of findings and patterns discovered.

Mark Step 2 complete.

## Step 3: Ask clarifying questions

Mark Step 3 in progress.

**CRITICAL**: This is one of the most important steps. DO NOT SKIP.

Review the codebase findings from Step 2 against the issue requirements. Identify all underspecified aspects:

1. Present a clear analysis of the problem based on what you found in the codebase.
2. Identify ambiguities, underspecified scope, unstated constraints, edge cases, integration concerns, and design preferences that will affect the implementation plan.
3. **Present all questions to the user in a clear, organized list.**
4. **Wait for answers before proceeding to architecture design.**

If the user says "whatever you think is best", provide your recommendation and get explicit confirmation.

Mark Step 3 complete.

## Step 4: Design architecture

Mark Step 4 in progress.

Based on the codebase findings and clarified requirements, launch 2-3 architecture agents in parallel using the Task tool (subagent_type: "feature-dev:code-architect"). Assign each agent a different architectural lens:

- **Minimal changes**: Design the implementation with the smallest change surface. Maximize reuse of existing patterns. Minimize new abstractions.
- **Clean architecture**: Design the implementation prioritizing clear separation of concerns, maintainability, and well-defined abstractions.
- **Pragmatic balance**: Design the implementation balancing speed with code quality and extensibility.

Each agent should produce a full implementation blueprint: files to create or modify, component responsibilities, data flow, and a phased build sequence.

After all agents complete, review their approaches and form your own recommendation based on the issue's scope, the codebase's conventions, and the user's clarified requirements.

Present to the user: brief summary of each approach, trade-offs comparison, **your recommendation with reasoning**, concrete implementation differences.

**Ask user which approach they prefer.**

Mark Step 4 complete.

## Step 5: Draft the plan

Mark Step 5 in progress.

Using the architecture selected in Step 4 as the structural foundation, draft a **staged implementation plan** with:
- Clear stages (numbered, with descriptive names)
- What each stage accomplishes
- Which files will be created or modified
- Dependencies between stages
- Testing approach for each stage

### Planning requirements

Before finalizing the plan, verify it satisfies the following:

**Project-layer coverage:** Cross-check the plan against the project layers discovered during codebase exploration and any layers specified in the project planning requirements recorded in Step 2a. Every affected layer should be addressed by at least one stage. If a discovered layer is not affected by this change, it may be omitted -- but if a layer is affected and no stage addresses it, add the missing work to the appropriate stage or create a new one.

**Test coverage planning:** Identify what testing is appropriate for this project and codebase. If the project has an existing test suite or the project planning requirements specify testing expectations, each stage that introduces or modifies behavior must specify: what tests to add or modify, what test types are needed (unit, integration, end-to-end, etc.), and what behaviors or interfaces to cover. If the project has no testable runtime code (e.g., plugin definitions, documentation, configuration), note this in the plan and skip test planning.

**Each stage must be scoped to what can be implemented within a single Claude Code CLI session.** A stage that is too large should be split. Consider:
- The amount of codebase exploration needed
- The number of files to create or modify
- The complexity of the logic involved
- The testing surface area

Mark Step 5 complete.

## Step 6: Post plan and create branch

Mark Step 6 in progress.

Present the plan to the user, then use `AskUserQuestion` to ask for approval with these options:

- **Approve**: "Post the plan and create the feature branch"
- **Request changes**: "Suggest changes to the plan before posting"
- **Cancel**: "Abort without posting the plan or creating a branch"

If the user selects "Request changes", discuss their feedback, revise the plan, and present it for approval again. If the user selects "Cancel", stop and confirm that the plan was not posted and no branch was created. Leave Step 6 as `in_progress`.

After the user approves the plan:

1. **Post the plan as a reply comment on the issue** using `gh issue comment <issue-number> --body "..."`. Format the comment so it serves as input to future CLI sessions. Include:
   - `<!-- mach10-plan -->` as the very first line of the comment body (this invisible HTML marker enables reliable identification in future sessions)
   - The full implementation plan
   - The staged breakdown
   - A `## Decision Log` section appended after the staged breakdown. This section captures the reasoning behind key decisions made during planning:
     - **Clarifying Questions (Step 3):** For each question asked and answered, include the question and a synthesized answer. Only include exchanges where the answer changed or constrained the plan. Omit exchanges where the user confirmed a default or said "whatever you think is best."
     - **Architecture Choice (Step 4):** The selected approach, the rationale for choosing it, and the alternatives considered with brief reasons for rejection.
     - **Omission condition:** Skip the Decision Log section entirely if Step 3 produced no questions AND Step 4 had no meaningful differentiation between approaches (e.g., only one viable approach existed).
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

4. **Assign sub-issues** to the current user:

   Detect sub-issues using the two-strategy approach:

   - **Strategy A (API):** First resolve the repository identifier, then query the GitHub sub-issues API:
     ```
     REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
     gh api --paginate repos/$REPO/issues/<issue-number>/sub_issues --jq '.[].number'
     ```
     - If the API call **succeeds and returns one or more numbers**, use them as the confirmed sub-issue list.
     - If the API call **succeeds but returns no results** (empty array), the issue has no sub-issues. Do NOT fall through to Strategy B -- treat the sub-issue list as empty.
     - If the API call **fails** (e.g., 404, permission error, network timeout), proceed to Strategy B.

   - **Strategy B (body-parse fallback):** This strategy runs only when Strategy A **failed**. Scan the issue body for sub-issue references. Match `#<number>` references that appear on GitHub task list lines -- lines beginning with optional whitespace followed by a list marker (`-`, `*`, or `+`) and a checkbox (`[ ]`, `[x]`, or `[X]`). Exclude any `#<number>` preceded by relational keywords: "Related to", "Blocked by", "See also", or "Depends on". Collect the matched issue numbers, excluding the parent issue number itself.

   If sub-issues are found, get the current user login via `gh api user --jq .login` (reuse the value from sub-step 3 if already retrieved). For each sub-issue, check assignees via `gh issue view <sub-issue> --json assignees --jq '[.assignees[].login] | join(",")'`. Three paths:
   - Current user already assigned: skip silently
   - No assignees: auto-assign with `gh issue edit <sub-issue> --add-assignee @me`
   - Other assignees exist: collect into a "conflicting" list

   If the conflicting list is non-empty, use `AskUserQuestion` to ask the user how to proceed with a single bulk decision:
   - **Add me**: "Add yourself as an additional assignee on all conflicting sub-issues" -- run `gh issue edit <sub-issue> --add-assignee @me` for each
   - **Skip**: "Leave the current assignee(s) unchanged on all sub-issues" -- no-op
   - **Replace**: "Remove existing assignee(s) and assign only yourself on all sub-issues" -- run `gh issue edit <sub-issue> --remove-assignee <existing-logins> --add-assignee @me` for each

   Assignment failures are non-blocking (warn and continue).

When referring to numbered items (findings, suggestions, stages) in the comment body, use plain words like "finding 3" or "suggestion 3" -- not `#<number>` notation, which GitHub auto-links to issues/PRs.

Confirm all actions to the user (plan posted, branch created, issue assigned, and sub-issues assigned if applicable).

Mark Step 6 complete.

**CLI output only (do NOT include in the GitHub comment):** Let the user know the next step is `/clear` then `/mach10:issue-plan-review <issue-number>` to review the plan. After review, use `/mach10:issue-implement <issue-number> 1` to begin Stage 1 of the implementation in a fresh session.
