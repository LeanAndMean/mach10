---
description: Independently assess remaining review findings to triage genuine issues from nitpicks
argument-hint: <pr-number>
allowed-tools: Bash, Read, Grep, Glob, Task
model: opus
---

# Validate Review

You are performing an independent assessment of the most recent PR review findings. The goal is to determine which remaining issues are genuine problems versus nitpicks or false positives, so the PR can proceed to merge with confidence.

**PR number:** $ARGUMENTS

## Step 1: Read Everything

Read the PR and all associated comments:

```
gh pr view $ARGUMENTS --comments
```

Understand:
- The PR's purpose and scope
- The full comment history (implementation notes, prior reviews, fix documentation)
- The most recent review comment

## Step 2: Independent Assessment

For each finding in the most recent review:

1. **Read the actual code** referenced by the finding. Do not rely on the review's description alone.
2. **Verify independently** whether the issue exists.
3. **Classify** each finding as one of:
   - **Genuine issue** — Real problem that should be fixed before merge. Explain why.
   - **Nitpick** — Stylistic preference or minor point that does not affect correctness or maintainability. Explain why it does not matter.
   - **False positive** — The reviewer flagged something that is not actually an issue. Explain why the code is correct.
   - **Deferred** — Real issue but out of scope for this PR. Should be tracked in a new issue.

## Step 3: Present Findings

Present your assessment to the user as a clear table or list:

For each finding:
- Original finding (brief summary)
- Your classification (genuine / nitpick / false positive / deferred)
- Your reasoning (1-2 sentences, referencing specific code)

Summarize: how many genuine, how many nitpicks, how many false positives, how many deferred.

## Step 4: Post Comment

After user approval, post a reply comment on the PR documenting:

- Which findings are being addressed (and in which commit/session)
- Which findings are not being addressed, with clear reasoning for each
- Any new issues created for deferred items

```
gh pr comment $ARGUMENTS --body "..."
```

This comment serves as an audit trail for the human reviewer, demonstrating that each finding was considered rather than ignored.

## Step 5: Recommend Next Steps

Based on the assessment:
- If genuine issues remain: "Run `/mach10:pr-review-fix $ARGUMENTS <issue-numbers>` in a new session"
- If only deferred items: "Create issues with `/mach10:issue-create`, then proceed to `/mach10:pr-pre-merge $ARGUMENTS`"
- If clean: "Proceed to `/mach10:pr-pre-merge $ARGUMENTS`"
