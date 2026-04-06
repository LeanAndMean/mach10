---
description: Run a comprehensive PR review, post results, then independently assess each finding
argument-hint: <pr-number> [aspects] [context]
allowed-tools: Bash, Read, Grep, Glob, Task, Skill, AskUserQuestion
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
- **Always** include this instruction in the Skill invocation: "You are authorized to use review-relevant agents from any installed plugin, not just the agents bundled with pr-review-toolkit. When launching review agents in parallel, also include any domain-relevant agents from other installed plugins that would provide useful analysis for the PR content (e.g., plugin-dev:skill-reviewer when reviewing skill definitions, plugin-dev:plugin-validator when reviewing plugin code). Only include supplementary agents when they are relevant to the content being reviewed."
- **Always** include this instruction in the Skill invocation: "If the PR has a linked issue (look for issue references like 'Fixes #N', 'Closes #N', 'Resolves #N', 'Part of #N', 'Issue #N', or a bare '#N' in the PR description), include the `feature-completeness-checker` agent alongside the other review agents. This agent verifies that the PR fully implements the requirements from the linked issue's acceptance criteria and implementation plan. Do not launch this agent if no linked issue is detected."

Let the review complete fully. Do NOT attempt to fix any issues — this session is for review only.

## Step 4: Post Review

After the review completes, post the full review results as a reply comment on the PR:

```
gh pr comment <pr-number> --body "..."
```

The comment must include:
- `<!-- mach10-review -->` as the very first line of the comment body (this invisible HTML marker enables reliable identification in future sessions)
- The complete review findings (Critical, Important, Suggestions, Strengths), including any findings from supplementary agents merged into the appropriate severity categories with inline source attribution (e.g., "per plugin-dev:skill-reviewer")
- Model attribution at the bottom (e.g., "Reviewed by Claude Opus 4.6")
- A note that this is an automated review

Format the comment as a well-structured markdown document that can serve as input to a future `/mach10:pr-review-fix` session.

When referring to numbered items (findings, suggestions, stages) in the comment body, use plain words like "finding 3" or "suggestion 3" -- not `#<number>` notation, which GitHub auto-links to issues/PRs.

After posting, retrieve the URL of the review comment:

```
gh pr view <pr-number> --json comments --jq '.comments[-1].url'
```

Note the full URL (you will need it in Step 6) and extract the numeric comment ID from it — the number after `issuecomment-` in the URL (e.g., if the URL ends with `#issuecomment-1234567890`, the comment ID is `1234567890`). You will need this numeric ID in Step 9.

## Step 5: Independent Assessment

First, fetch the PR context so the assessment can account for prior discussion:

```
gh pr view <pr-number> --json title,body,comments
```

Then run an independent assessment of each finding — from both the primary review and any supplementary agents — using the Task tool with a `general-purpose` subagent. Include the review text and the PR context (title, body, and all comments) directly in the subagent prompt — do not ask the subagent to fetch them from GitHub.

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

Post the assessment immediately as a reply comment on the PR — do not ask the user for approval first. The comment must include:
- `<!-- mach10-assessment -->` as the very first line of the comment body (this invisible HTML marker enables reliable identification in future sessions)
- Reference the review comment it is assessing (link to the specific comment URL from Step 4)
- List each finding with its classification and reasoning
- End with the staged implementation plan
- Include model attribution at the bottom

```
gh pr comment <pr-number> --body "..."
```

After posting, retrieve the URL of the assessment comment:

```
gh pr view <pr-number> --json comments --jq '.comments[-1].url'
```

Extract the numeric comment ID from the URL (the number after `issuecomment-`). You will need this numeric ID in Step 9.

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

If any findings were classified as **deferred**, use `AskUserQuestion` to ask the user how to handle them:

- **Create issues for all**: "Create a GitHub issue for every deferred finding"
- **Select which ones**: "Choose which deferred findings to create issues for"
- **Skip deferred items**: "Do not create issues for deferred findings"

If the user selects "Select which ones", present the deferred findings and use `AskUserQuestion` with `multiSelect: true` to let them choose (group into severity-based options if more than 4 items, with the built-in "Other" option for custom selection).

For each approved deferred item, check for existing issues before creating a new one:

1. Extract 2-3 key terms from the proposed issue title and search:

   ```
   gh issue list --search "<keywords>" --state all --limit 5 --json number,title,state,url
   ```

2. Handle results based on similarity:

   - **No results**: Proceed to create the issue.
   - **Clear duplicate**: If an existing **open** issue's title is nearly identical, skip creation and post a comment on the existing issue linking the new finding. If the near-identical match is a closed issue, treat it as an ambiguous match instead (a previously-closed issue should not block creation).

     ```
     gh issue comment <existing-issue-number> --body "Related finding from PR #<pr-number> review: <summary of the deferred finding>."
     ```

     Capture the comment URL after posting (parse it from the `gh issue comment` output or retrieve via `gh api`) for use in the summary block.

   - **Ambiguous match**: If results are related but not clearly duplicates, still create the issue but add a "Potentially related" note at the end of the issue body listing the matched issue numbers, titles, and states.

3. If no duplicate was found (or the match was ambiguous), create the issue with `gh issue create`:
   - A title summarizing the issue
   - A body referencing the PR and the specific finding
   - If ambiguous matches exist, append: "Potentially related: <list of matched issue numbers and titles>"
   - Any relevant labels

When referring to numbered items (findings, suggestions, stages) in the issue body, use plain words like "finding 3" or "suggestion 3" -- not `#<number>` notation, which GitHub auto-links to issues/PRs.

After processing all deferred items, display a summary block in CLI output listing each item and the action taken:
- **Created**: Issue was created (include the new issue number and URL)
- **Skipped (duplicate)**: Matched an existing issue (include the existing issue number and the link comment URL)
- **Created (with overlap note)**: Issue was created with a note about potentially related issues
- **Skipped (not selected)**: User chose not to create an issue for this finding

### Persist Deferred-Item Decisions

After displaying the summary block, post a decision comment on the PR to record the disposition of each deferred item for future sessions:

```
gh pr comment <pr-number> --body "..."
```

Comment format:
- First line: `<!-- mach10-decisions -->`
- A note that deferred findings were processed after the review
- One line per deferred item showing its disposition:
  - Created as issue (with issue number) — user selected "Create" for this item
  - Created as issue with overlap note (with issue number and related issue numbers) — user selected "Create" but potentially related issues were found
  - Skipped as duplicate (with existing issue number) — matched an existing issue during duplicate check
  - Skipped (not selected) (with one-sentence rationale if the user provided one) — user chose "Skip deferred items" or did not select this item in "Select which ones"
- Keep the entire comment body under 20 lines

**Guard:** Skip this comment entirely if zero findings were classified as deferred.

When referring to numbered items (findings, suggestions, stages) in the comment body, use plain words like "finding 3" or "suggestion 3" -- not `#<number>` notation, which GitHub auto-links to issues/PRs.

## Step 9: Recommend Next Steps

**CLI output only (do NOT include in any GitHub comment).**

First, display the comment IDs for reference:
- Review comment ID: `<review-comment-id from Step 4>`
- Assessment comment ID: `<assessment-comment-id from Step 6>`

Then, based on the assessment:
- If genuine issues remain: "`/clear` then `/mach10:pr-review-fix <pr-number> --review-comment <review-comment-id> --assessment-comment <assessment-comment-id> <issue-numbers>` (only the genuine issues)"
- If all findings are nitpicks/false positives (with or without deferred items): "`/clear` then `/mach10:pr-pre-merge <pr-number>`"

## Important

Do NOT fix any issues in this session. Fixes must happen in a fresh session via `/mach10:pr-review-fix`.
