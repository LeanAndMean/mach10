---
description: Read a GitHub issue and all comments, review the implementation plan, and present findings
argument-hint: <issue-number>
allowed-tools: Bash, Read, Grep, Glob, Task
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

Locate the implementation plan comment. If no plan exists, inform the user and suggest running `/mach10:issue-plan <issue-number>` first.

## Step 3: Explore the Codebase

Launch 2-3 exploration agents in parallel using the Task tool (subagent_type: Explore) to verify the plan's assumptions:

- **Files referenced in the plan**: Confirm they exist, check their current state, and verify the plan's characterization of them is accurate.
- **Architecture and patterns**: Validate that the plan aligns with existing codebase conventions and architecture.
- **Gaps**: Look for code, constraints, or dependencies the plan may have missed.

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

## Step 5: Present Findings

Present your review to the user, organized as:

1. **Plan summary**: Brief restatement of what the plan proposes.
2. **Strengths**: What the plan gets right.
3. **Issues**: Problems found, classified by severity:
   - **Critical**: Will cause the implementation to fail or produce incorrect results.
   - **Important**: Significant gaps or risks that should be addressed before implementation.
   - **Suggestions**: Improvements that would make the plan better but are not blockers.
4. **Questions**: Any clarifying questions that came up during your review.

Ask the user how they want to proceed:
- Update the plan and post a revised version
- Proceed with the plan as-is
- Discuss specific findings in more detail
