---
description: Run a comprehensive PR review, post results, then independently assess each finding
argument-hint: <pr-number> [aspects] [context]
allowed-tools: Bash, Read, Grep, Glob, Task, Skill
model: opus
---

# Review PR

You are running a comprehensive review of a pull request, posting the results, then independently assessing each finding to separate genuine issues from nitpicks and false positives.

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

## Step 4: Post Review

After the review completes, post the full review results as a reply comment on the PR:

```
gh pr comment <pr-number> --body "..."
```

The comment must include:
- The complete review findings (Critical, Important, Suggestions, Strengths)
- Model attribution at the bottom (e.g., "Reviewed by Claude Opus 4.6")
- A note that this is an automated review

Format the comment as a well-structured markdown document that can serve as input to a future `/mach10:pr-review-fix` session.

After posting, retrieve the URL of the review comment (use `gh pr view <pr-number> --comments --json comments` to get the URL of the last comment). You will need this URL in Step 7.

## Step 5: Independent Assessment

After posting the review, run an independent assessment of each finding using the Task tool with a `general-purpose` subagent. The subagent prompt should instruct it to:

1. Read the review comment that was just posted (provide the review text directly in the prompt — do not ask the subagent to fetch it from GitHub).
2. For each finding, **read the actual code** referenced and **independently verify** whether the issue exists.
3. Classify each finding as one of:
   - **Genuine issue** — Real problem that should be fixed before merge. Explain why.
   - **Nitpick** — Stylistic preference or minor point that doesn't affect correctness or maintainability. Explain why it doesn't matter.
   - **False positive** — The reviewer flagged something that isn't actually an issue. Explain why the code is correct.
   - **Deferred** — Real issue but out of scope for this PR. Should be tracked separately.
4. Return a structured result: for each finding, the original summary, classification, and 1-2 sentence reasoning referencing specific code.

## Step 6: Present Assessment

Present the subagent's assessment to the user in CLI output:

For each finding:
- Original finding (brief summary)
- Classification (genuine / nitpick / false positive / deferred)
- Reasoning (1-2 sentences, referencing specific code)

Summary counts: how many genuine, how many nitpicks, how many false positives, how many deferred.

Ask the user if they want to adjust any classifications before posting.

## Step 7: Post Assessment

Post the assessment as a reply comment on the PR. The comment must:
- Reference the review comment it is assessing (link to the specific comment URL from Step 4)
- List each finding with its classification and reasoning
- Include model attribution at the bottom

```
gh pr comment <pr-number> --body "..."
```

## Step 8: Handle Deferred Items

If any findings were classified as **deferred**, ask the user if they want to create GitHub issues for them. For each approved deferred item, use `gh issue create` with:
- A title summarizing the issue
- A body referencing the PR and the specific finding
- Any relevant labels

## Step 9: Recommend Next Steps

**CLI output only (do NOT include in any GitHub comment).** Based on the assessment:
- If genuine issues remain: "`/clear` then `/mach10:pr-review-fix <pr-number> <issue-numbers>` (only the genuine issues)"
- If all findings are nitpicks/false positives (with or without deferred items): "`/clear` then `/mach10:pr-pre-merge <pr-number>`"

## Important

Do NOT fix any issues in this session. Fixes must happen in a fresh session via `/mach10:pr-review-fix`.
