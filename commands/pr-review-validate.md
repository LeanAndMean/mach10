---
description: Independently assess remaining review findings to triage genuine issues from nitpicks
argument-hint: <pr-number>
allowed-tools: Bash, Read, Grep, Glob, Task
model: opus
---

# Validate Review

You are performing an independent assessment of the most recent PR review findings. The goal is to determine which remaining issues are genuine problems versus nitpicks or false positives, so the PR can proceed to merge with confidence.

**User input:** $ARGUMENTS

## Step 1: Parse Input

The user's input contains:
- A **PR number** (required)

Extract the PR number from the input. If the input is ambiguous, ask the user to clarify.

## Step 2: Read Everything

Read the PR title and description:

```
gh pr view <pr-number>
```

Then read all comments (`--comments` returns only comments and silently drops the title and description, so both calls are required):

```
gh pr view <pr-number> --comments
```

Understand:
- The PR's purpose and scope
- The full comment history (implementation notes, prior reviews, fix documentation)
- The most recent review comment

## Step 3: Independent Assessment

For each finding in the most recent review:

1. **Read the actual code** referenced by the finding. Do not rely on the review's description alone.
2. **Verify independently** whether the issue exists.
3. **Classify** each finding as one of:
   - **Genuine issue** — Real problem that should be fixed before merge. Explain why.
   - **Nitpick** — Stylistic preference or minor point that does not affect correctness or maintainability. Explain why it does not matter.
   - **False positive** — The reviewer flagged something that is not actually an issue. Explain why the code is correct.
   - **Deferred** — Real issue but out of scope for this PR. Should be tracked in a new issue.

## Step 4: Present Findings

Present your assessment to the user as a clear table or list:

For each finding:
- Original finding (brief summary)
- Your classification (genuine / nitpick / false positive / deferred)
- Your reasoning (1-2 sentences, referencing specific code)

Summarize: how many genuine, how many nitpicks, how many false positives, how many deferred.

## Step 5: Post Comment

After user approval, post a reply comment on the PR documenting:

- Which findings are being addressed (and in which commit/session)
- Which findings are not being addressed, with clear reasoning for each
- Any new issues created for deferred items

```
gh pr comment <pr-number> --body "..."
```

This comment serves as an audit trail for the human reviewer, demonstrating that each finding was considered rather than ignored.

## Step 6: Recommend Next Steps

**CLI output only (do NOT include in the GitHub comment from Step 5):** Based on the assessment, recommend next step to the user:
- If genuine issues remain: "`/clear` then `/mach10:pr-review-fix <pr-number> <issue-numbers>`"
- If only deferred items: "Create issues with `/mach10:issue-create`, then `/clear` and `/mach10:pr-pre-merge <pr-number>`"
- If clean: "`/clear` then `/mach10:pr-pre-merge <pr-number>`"
