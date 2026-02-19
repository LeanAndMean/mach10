---
description: Run a comprehensive PR review and post results as a comment
argument-hint: <pr-number> [aspects] [context]
allowed-tools: Bash, Read, Grep, Glob, Task, Skill
model: opus
---

# Review PR

You are running a comprehensive review of a pull request, then posting the results as a reply comment on the PR.

**User input:** $ARGUMENTS

## Step 1: Parse Input

The user's input typically contains:
- A **PR number** (required)
- **Review aspects** to focus on (optional)
- Additional context or constraints (optional)

Example inputs:
- `108`
- `108 error handling and test coverage`
- `108 focus on the new API endpoints`

Extract the PR number. If specific review aspects are mentioned, note them for Step 3. If the input is ambiguous, ask the user to clarify.

## Step 2: Prepare

Ensure you are on the correct branch:

```
gh pr checkout <pr-number>
git pull
```

## Step 3: Run Review

Use the Skill tool to invoke `/pr-review-toolkit:review-pr` with the appropriate context:

- If specific aspects were requested, pass them: "Review PR #<pr-number>. Focus on: <aspects>"
- If no aspects specified, run a full review: "Review PR #<pr-number>"

Let the review complete fully. Do NOT attempt to fix any issues — this session is for review only.

## Step 4: Post Results

After the review completes, post the full review results as a reply comment on the PR:

```
gh pr comment <pr-number> --body "..."
```

The comment must include:
- The complete review findings (Critical, Important, Suggestions, Strengths)
- Model attribution at the bottom (e.g., "Reviewed by Claude Opus 4.6")
- A note that this is an automated review

Format the comment as a well-structured markdown document that can serve as input to a future `/mach10:pr-review-fix` session.

## Step 5: Summarize

Report to the user:
- How many critical/important/suggestion issues were found
- Link to the posted comment
- Recommended next step:
  - If critical issues found: "Next: `/mach10:pr-review-fix <pr-number> <issue-numbers>` (in a new session)"
  - If only minor issues: "Next: `/mach10:pr-review-validate <pr-number>` to triage remaining findings"
  - If clean: "Next: `/mach10:pr-pre-merge <pr-number>`"

## Important

Do NOT fix any issues in this session. The review often consumes most of the context window. Fixes must happen in a fresh session to ensure adequate context budget for implementation.
