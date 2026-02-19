---
description: Read a GitHub issue, perform an independent assessment, and present findings
argument-hint: <issue-number>
allowed-tools: Bash, Read, Grep, Glob, Task
model: opus
---

# Issue Assessment

You are performing an independent assessment of a GitHub issue. Your goal is to deeply understand the issue, explore the relevant codebase, and present your findings with a recommended next step.

**Issue number:** $ARGUMENTS

## Step 1: Read the Issue

Read the full issue and all comments:

```
gh issue view $ARGUMENTS --comments
```

Parse and understand:
- The problem statement
- Any constraints or requirements mentioned
- Prior discussion or decisions in the comments
- Acceptance criteria (if specified)
- Current state of the issue (open, closed, linked PRs, etc.)

## Step 2: Explore the Codebase

Launch 2-3 exploration agents in parallel using the Task tool (subagent_type: Explore). Each agent should target a different aspect:

- **Relevant code**: Find existing code related to the issue. Trace through implementation patterns.
- **Architecture**: Map the relevant architecture layers, abstractions, and data flow.
- **Prior work**: Check for related branches, PRs, or commits that may already address part of the issue.

Each agent should return a list of 5-10 key files. After agents complete, read all identified files to build deep understanding.

## Step 3: Assess

Based on your understanding of the issue and codebase, present your assessment to the user:

1. **Summary**: What the issue is asking for in your own words.
2. **Current state**: What exists today in the codebase that is relevant.
3. **Gaps**: What is missing, broken, or unclear.
4. **Ambiguities**: Any underspecified aspects, contradictions, or open questions in the issue.
5. **Scope**: Your assessment of the size and complexity of the work.
6. **Risks**: Potential pitfalls, edge cases, or architectural concerns.

## Step 4: Recommend Next Step

Based on your assessment, decide which of the following actions to recommend. Choose based on context — there is no single right answer.

### Option 1: Update the issue body
Recommend this when the issue description is incomplete, outdated, or missing key information that your assessment uncovered. Draft the updated issue body for user approval.

### Option 2: Post a reply comment on the issue
Recommend this when the issue body is fine but your assessment adds valuable context, clarifications, or questions that should be captured for future sessions. Draft the comment for user approval.

### Option 3: Both update the issue body and post a comment
Recommend this when the issue body needs corrections or additions AND there are separate findings (e.g., architectural observations, open questions) worth capturing in a comment.

### Option 4: Create a new issue (rare)
Recommend this when your assessment reveals that the work described in the issue is already done (e.g., in an existing feature branch) or that the issue should be split into multiple distinct issues. Explain why and draft the new issue for user approval.

## Step 5: Execute

After the user approves your recommendation:

- **Update issue body**: `gh issue edit $ARGUMENTS --body "..."`
- **Post comment**: `gh issue comment $ARGUMENTS --body "..."`
- **Create new issue**: `gh issue create --title "..." --body "..."`

Confirm the actions taken and provide links.
