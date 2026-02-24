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
- **Always** include this instruction in the Skill invocation: "IMPORTANT: Do NOT use `run_in_background: true` when launching review agents. For parallel execution, launch multiple foreground Task calls in a single message instead."

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

When referring to numbered items (findings, suggestions, stages) in the comment body, use plain words like "finding 3" or "suggestion 3" -- not `#<number>` notation, which GitHub auto-links to issues/PRs.

After posting, retrieve the URL of the review comment (use `gh pr view <pr-number> --json comments` to get the URL of the last comment). You will need this URL in Step 6.

## Step 5: Independent Assessment

First, fetch the PR context so the assessment can account for prior discussion:

```
gh pr view <pr-number> --json title,body,comments
```

Then run an independent assessment of each finding using the Task tool with a `general-purpose` subagent. Include the review text and the PR context (title, body, and all comments) directly in the subagent prompt — do not ask the subagent to fetch them from GitHub.

The subagent prompt should instruct it to:

1. Review the PR title, body, and all existing comments. Note any findings that have already been discussed, resolved, or deferred in the PR conversation.
2. For each review finding, **read the actual code** referenced and **independently verify** whether the issue exists.
3. Classify each finding as one of:
   - **Genuine issue** — Real problem that should be fixed before merge. Explain why.
   - **Nitpick** — Stylistic preference or minor point that doesn't affect correctness or maintainability. Explain why it doesn't matter.
   - **False positive** — The reviewer flagged something that isn't actually an issue. Explain why the code is correct.
   - **Deferred** — Real issue but out of scope for this PR. Should be tracked separately.
   - If a finding was already fixed in a subsequent commit or resolved in discussion, classify it as **False positive** with a note that it has been addressed. If explicitly deferred in discussion, classify it as **Deferred** and reference the relevant comment.
4. After classifying all findings, produce a **staged implementation plan** covering everything worth fixing:
   - Number each stage with a descriptive name.
   - Required stages for genuine issues (must fix before merge).
   - Optional stages for nitpicks (nice-to-have improvements).
   - Each stage should list the specific findings it addresses and which files are affected.
5. Return all classifications (each with the original finding summary and 1-2 sentence reasoning referencing specific code), followed by the staged implementation plan produced in instruction (4) above.

## Step 6: Post Assessment

Post the assessment immediately as a reply comment on the PR — do not ask the user for approval first. The comment must:
- Reference the review comment it is assessing (link to the specific comment URL from Step 4)
- List each finding with its classification and reasoning
- End with the staged implementation plan
- Include model attribution at the bottom

```
gh pr comment <pr-number> --body "..."
```

When referring to numbered items (findings, suggestions, stages) in the comment body, use plain words like "finding 3" or "suggestion 3" -- not `#<number>` notation, which GitHub auto-links to issues/PRs.

## Step 7: Present CLI Summary

After posting, present the assessment to the user in CLI output:

For each finding:
- Original finding (brief summary)
- Classification (genuine / nitpick / false positive / deferred)
- Reasoning (1-2 sentences, referencing specific code)

Summary counts: how many genuine, how many nitpicks, how many false positives, how many deferred.

After the per-finding list and summary counts, display the staged implementation plan so the user can identify which issues to address next without switching to GitHub.

## Step 8: Handle Deferred Items

If any findings were classified as **deferred**, ask the user if they want to create GitHub issues for them. For each approved deferred item, use `gh issue create` with:
- A title summarizing the issue
- A body referencing the PR and the specific finding
- Any relevant labels

When referring to numbered items (findings, suggestions, stages) in the issue body, use plain words like "finding 3" or "suggestion 3" -- not `#<number>` notation, which GitHub auto-links to issues/PRs.

## Step 9: Recommend Next Steps

**CLI output only (do NOT include in any GitHub comment).** Based on the assessment:
- If genuine issues remain: "`/clear` then `/mach10:pr-review-fix <pr-number> <issue-numbers>` (only the genuine issues)"
- If all findings are nitpicks/false positives (with or without deferred items): "`/clear` then `/mach10:pr-pre-merge <pr-number>`"

## Important

Do NOT fix any issues in this session. Fixes must happen in a fresh session via `/mach10:pr-review-fix`.
