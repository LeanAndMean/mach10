---
description: Read a GitHub issue and all comments, review the implementation plan, and present findings
argument-hint: <issue-number>
allowed-tools: Bash, Read, Grep, Glob, Task, AskUserQuestion
model: opus
---

# Issue Plan Review

You are reviewing the implementation plan for a GitHub issue. Your goal is to read the issue and all comments, independently assess the plan, and present your findings.

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

Understand:
- The original problem statement and requirements
- The implementation plan (typically posted as a comment)
- Any discussion, decisions, or clarifications in the comment thread

Locate the implementation plan comment by searching all issue comments for the `<!-- mach10-plan -->` HTML marker. If multiple comments contain the marker, use the last one (the most recent revision). If no comment contains the marker, fall back to identifying the most recent substantive comment that contains a staged implementation plan. If no plan exists at all, inform the user and suggest running `/mach10:issue-plan <issue-number>` first.

## Step 3: Explore the Codebase

### 3a. Read Contributing Guidelines

Before launching exploration agents, look for project contribution guidelines in order of precedence:

```
CONTRIBUTING.md
DEVELOPMENT.md
.github/CONTRIBUTING.md
```

Read only the first file found; skip the rest.

If found, read the file and extract any planning-relevant guidance: expected project layers (e.g., models, migrations, API routes, services, UI, documentation), testing expectations (test frameworks, coverage requirements, test types), and any other requirements that a complete plan should satisfy.

Record these as **project review criteria** -- they will serve as benchmarks when assessing the plan in Step 4.

If no contributing guide exists, proceed without project-specific requirements.

### 3b. Explore

Launch 2-3 exploration agents in parallel using the Task tool (subagent_type: "feature-dev:code-explorer"). Each agent should trace through the code comprehensively and target a different aspect of plan verification:

- **Files referenced in the plan**: Trace through each file referenced in the plan comprehensively, confirming they exist, checking their current state, and verifying the plan's characterization of their structure, responsibilities, and integration points is accurate.
- **Architecture and patterns**: Trace through the relevant architecture comprehensively, validating that the plan aligns with existing codebase conventions, abstractions, data flow, and design decisions.
- **Gaps**: Trace through code adjacent to the plan's scope comprehensively, looking for constraints, dependencies, cross-cutting concerns, or affected areas the plan may have missed.

If project review criteria were recorded in Step 3a, include them in each agent's context so exploration can verify whether the plan covers the relevant project layers and testing infrastructure.

Each agent should return a list of key files and observations. After agents complete, read all identified files.

## Step 4: Review the Plan

For each stage in the plan, assess:

1. **Correctness**: Does the stage accurately describe what needs to happen? Are the files and changes correct?
2. **Completeness**: Are there missing steps, files, or edge cases?
3. **Scope**: Is the stage appropriately sized for a single CLI session, or should it be split/merged?
4. **Dependencies**: Are inter-stage dependencies correctly identified? Is the ordering logical?
5. **Testing**: Is the testing approach adequate for each stage?
6. **Risks**: Are there architectural risks, performance concerns, or subtle pitfalls the plan overlooks?

Also assess the plan holistically:
- Does it address all requirements and acceptance criteria from the issue?
- Does it follow existing codebase patterns and conventions?
- Are there alternative approaches worth considering?
- **Project-layer coverage**: Does the plan address all project layers discovered during codebase exploration or specified in the project review criteria recorded in Step 3a? Flag any affected layer that no stage covers.
- **Test coverage planning**: If the project has an existing test suite or the project review criteria specify testing expectations, does each stage that introduces or modifies behavior include adequate test planning (what to test, test types, behaviors to cover)? If the project has no testable runtime code, verify the plan notes this rather than omitting test planning silently.

## Step 5: Present Findings

Present your review to the user, organized as:

1. **Plan summary**: Brief restatement of what the plan proposes.
2. **Strengths**: What the plan gets right.
3. **Issues**: Problems found, classified by severity:
   - **Critical**: Will cause the implementation to fail or produce incorrect results.
   - **Important**: Significant gaps or risks that should be addressed before implementation.
   - **Suggestions**: Improvements that would make the plan better but are not blockers.
4. **Questions**: Any clarifying questions that came up during your review.

Use `AskUserQuestion` to ask the user how they want to proceed:

- **Update the plan**: "Post a revised plan addressing the findings"
- **Proceed as-is**: "Continue with the current plan despite findings"
- **Discuss findings**: "Explore specific findings in more detail before deciding"
- **Cancel**: "Stop here without updating or proceeding"

If the user selects "Update the plan", draft a revised plan incorporating the findings, and present it for review before posting. When posting the revised plan as a comment, include `<!-- mach10-plan -->` as the very first line of the comment body (this invisible HTML marker enables reliable identification in future sessions). If the user selects "Discuss findings", walk through the specific findings they want to explore, then ask again how to proceed.

If the user selects "Proceed as-is" and at least one Critical or Important finding exists, post a decision comment on the issue to record the user's choice:

```
gh issue comment <issue-number> --body "..."
```

Comment format:
- First line: `<!-- mach10-decisions -->`
- A note that a plan review was conducted and the user chose to proceed without changes
- Each Critical and Important finding on its own line (one sentence each)
- Keep the entire comment body under 15 lines

When referring to numbered items (findings, suggestions, stages) in the comment body, use plain words like "finding 3" or "suggestion 3" -- not `#<number>` notation, which GitHub auto-links to issues/PRs.

If the user selects "Proceed as-is" and all findings are Suggestions only, do NOT post a decision comment -- proceeding past suggestions is the expected path.

If the user selects "Cancel":

1. Confirm that no changes were made to the plan.
2. Post a lightweight decision comment on the issue:

   ```
   gh issue comment <issue-number> --body "..."
   ```

   Comment format:
   - First line: `<!-- mach10-decisions -->`
   - A note that a plan review was conducted and the session ended without updating or proceeding
   - Finding counts by severity (e.g., "2 Critical, 1 Important, 3 Suggestions")
   - Keep the entire comment body to 5 lines or fewer

   When referring to numbered items (findings, suggestions, stages) in the comment body, use plain words like "finding 3" or "suggestion 3" -- not `#<number>` notation, which GitHub auto-links to issues/PRs.

**CLI output only (do NOT include in any GitHub comment):** Suggest next step: `/clear` then `/mach10:issue-plan-review <issue-number>` to re-run the review, or `/mach10:issue-implement <issue-number> 1` to proceed with the existing plan.

After the user's choice is executed (unless cancelled), suggest as **CLI output only (do NOT include in any GitHub comment):** `/clear` then `/mach10:issue-implement <issue-number> 1` to begin implementation.
