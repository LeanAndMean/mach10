---
description: Read a GitHub issue and all comments, review the implementation plan, and present findings
argument-hint: <issue-number>
allowed-tools: Bash, Read, Grep, Glob, Task, AskUserQuestion
model: opus
---

# Issue Review Plan

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

Launch 2-3 exploration agents in parallel using the Task tool (subagent_type: Explore) to verify the plan's assumptions:

- **Files referenced in the plan**: Confirm they exist, check their current state, and verify the plan's characterization of them is accurate.
- **Architecture and patterns**: Validate that the plan aligns with existing codebase conventions and architecture.
- **Gaps**: Look for code, constraints, or dependencies the plan may have missed.

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

If the user selects "Update the plan", draft a revised plan incorporating the findings, and present it for review before posting. When posting the revised plan as a comment, include `<!-- mach10-plan -->` as the very first line of the comment body (this invisible HTML marker enables reliable identification in future sessions). If the user selects "Discuss findings", walk through the specific findings they want to explore, then ask again how to proceed. If the user selects "Cancel", stop and confirm that no changes were made.

After the user's choice is executed (unless cancelled), suggest as **CLI output only (do NOT include in any GitHub comment):** `/clear` then `/mach10:issue-implement <issue-number> 1` to begin implementation.
