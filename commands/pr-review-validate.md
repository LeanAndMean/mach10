---
description: Independently assess remaining review findings to triage genuine issues from nitpicks
argument-hint: <pr-number> [--review-comment <id>]
allowed-tools: Bash, Read, Grep, Glob, Task, AskUserQuestion
model: opus
---

# Validate Review

You are performing an independent assessment of the most recent PR review findings. The goal is to determine which remaining issues are genuine problems versus nitpicks or false positives, so the PR can proceed to merge with confidence.

**User input:** $ARGUMENTS

## Step 1: Parse Input

The user's input contains:
- A **PR number** (required)
- **`--review-comment <id>`** flag with a numeric comment ID (optional)

Example inputs:
- `108`
- `108 --review-comment 1234567890`

Extract the PR number. Parse the `--review-comment` flag if present (followed by a numeric ID). If the input is ambiguous, ask the user to clarify.

## Step 2: Read Everything

Read the PR title and description:

```
gh pr view <pr-number>
```

### Locate the review comment

**If `--review-comment` was provided:** Fetch the specific comment by ID:

```
gh api repos/:owner/:repo/issues/comments/<review-comment-id>
```

Extract the `body` field from the JSON response. This is the review comment content. Note the comment ID for use in Step 6.

**If `--review-comment` was NOT provided (fallback):** Fetch all comments as JSON:

```
gh pr view <pr-number> --json comments
```

Parse the JSON array and search from the END (most recent first) for the first comment whose body contains the HTML marker `<!-- mach10-review -->`. If no comment contains the marker, fall back to finding the last comment with the structured review format (Critical/Important/Suggestions sections and model attribution). If a review comment is found, extract its numeric ID from the `url` field (the number after `issuecomment-`). Note this ID for use in Step 6.

### Read remaining context

Fetch the full comment history for context on prior discussion, fixes, and implementation notes:

```
gh pr view <pr-number> --comments
```

Understand:
- The PR's purpose and scope
- The full comment history (implementation notes, prior reviews, fix documentation)
- The review comment identified above

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

Present the assessment to the user, then use `AskUserQuestion` to ask for approval:

- **Approve and post**: "Post the assessment as a comment on the PR"
- **Modify before posting**: "Edit the assessment before posting it"
- **Skip posting**: "Do not post a comment to the PR"

If the user selects "Modify before posting", ask what they want to change, apply the changes, and present the updated assessment for approval again. If the user selects "Skip posting", skip to Step 6.

After the user approves, post a reply comment on the PR documenting:

- `<!-- mach10-assessment -->` as the very first line of the comment body (this invisible HTML marker enables reliable identification in future sessions)
- Which findings are being addressed (and in which commit/session)
- Which findings are not being addressed, with clear reasoning for each
- Any new issues created for deferred items

When referring to numbered items (findings, suggestions, stages) in the comment body, use plain words like "finding 3" or "suggestion 3" -- not `#<number>` notation, which GitHub auto-links to issues/PRs.

```
gh pr comment <pr-number> --body "..."
```

This comment serves as an audit trail for the human reviewer, demonstrating that each finding was considered rather than ignored.

After posting, retrieve the URL of the assessment comment:

```
gh pr view <pr-number> --json comments --jq '.comments[-1].url'
```

Extract the numeric comment ID from the URL (the number after `issuecomment-`). Note this ID for use in Step 6.

## Step 6: Recommend Next Steps

**CLI output only (do NOT include in the GitHub comment from Step 5).**

First, if an assessment comment was posted and its ID was captured, display the comment IDs for reference:
- Review comment ID: `<review-comment-id from Step 2>`
- Assessment comment ID: `<assessment-comment-id from Step 5>`

Then, based on the assessment, recommend next step to the user:
- If genuine issues remain and both comment IDs are known: "`/clear` then `/mach10:pr-review-fix <pr-number> --review-comment <review-comment-id> --assessment-comment <assessment-comment-id> <issue-numbers>`"
- If genuine issues remain and only the review comment ID is known: "`/clear` then `/mach10:pr-review-fix <pr-number> --review-comment <review-comment-id> <issue-numbers>`"
- If genuine issues remain but no comment IDs are available: "`/clear` then `/mach10:pr-review-fix <pr-number> <issue-numbers>`"
- If only deferred items: "Create issues with `/mach10:issue-create`, then `/clear` and `/mach10:pr-pre-merge <pr-number>`"
- If clean: "`/clear` then `/mach10:pr-pre-merge <pr-number>`"
