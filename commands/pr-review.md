---
description: Run a comprehensive PR review, post results, then independently assess each finding
argument-hint: <pr-number> [aspects] [context]
allowed-tools: Bash, Read, Grep, Glob, Task, TaskCreate, TaskUpdate, Skill, AskUserQuestion
model: opus
---

# Review PR

You are running a comprehensive review of a pull request, posting the results, then independently assessing each finding to separate genuine issues from nitpicks and false positives.

**User input:** $ARGUMENTS

## Step 0: Parse input and create task list

The user's input typically contains:
- A **PR number** (required)
- **Review aspects** to focus on (optional)
- Additional context or constraints (optional)

Example inputs:
- `108`
- `108 error handling and test coverage`
- `108 focus on the new API endpoints`

Extract the PR number. If specific review aspects are mentioned, note them for Step 2. If the input is ambiguous, ask the user to clarify.

After parsing input, create the progress-tracking task list. Create a task for Step 0 and immediately mark it in progress. Then create tasks for each of the remaining 8 steps one at a time, in step order, all starting as pending. Store each returned task ID for later use -- do not assume IDs are sequential.

| Task | Subject | activeForm |
|------|---------|------------|
| Step 0 | Step 0: Parse input and create task list | Parsing input |
| Step 1 | Step 1: Check out PR branch | Checking out PR branch |
| Step 2 | Step 2: Run PR review | Running PR review |
| Step 3 | Step 3: Post review comment | Posting review comment |
| Step 4 | Step 4: Run independent assessment | Running independent assessment |
| Step 5 | Step 5: Post assessment comment | Posting assessment |
| Step 6 | Step 6: Present CLI summary | Presenting summary |
| Step 7 | Step 7: Handle deferred items | Handling deferred items |
| Step 8 | Step 8: Recommend next steps | Recommending next steps |

Mark Step 0 complete.

## Step 1: Check out PR branch

Mark Step 1 in progress.

Ensure you are on the correct branch:

```
gh pr checkout <pr-number>
git pull
```

Mark Step 1 complete.

## Step 2: Run PR review

Mark Step 2 in progress.

Use the Skill tool to invoke `/pr-review-toolkit:review-pr` with the appropriate context:

- If specific aspects were requested, pass them: "Review PR #<pr-number>. Focus on: <aspects>"
- If no aspects specified, run a full review: "Review PR #<pr-number>"
- **Always** include this instruction in the Skill invocation: "IMPORTANT: Do NOT use `run_in_background: true` when launching review agents. For parallel execution, launch multiple foreground Task calls in a single message instead."
- **Always** include this instruction in the Skill invocation: "You are authorized to use review-relevant agents from any installed plugin, not just the agents bundled with pr-review-toolkit. When launching review agents in parallel, also include any domain-relevant agents from other installed plugins that would provide useful analysis for the PR content (e.g., plugin-dev:skill-reviewer when reviewing skill definitions, plugin-dev:plugin-validator when reviewing plugin code). Only include supplementary agents when they are relevant to the content being reviewed."
- **Always** include this instruction in the Skill invocation: "If the PR has a linked issue (look for issue references like 'Fixes #N', 'Closes #N', 'Resolves #N', 'Part of #N', 'Issue #N', or a bare '#N' in the PR description), include the `feature-completeness-checker` agent alongside the other review agents. This agent verifies that the PR fully implements the requirements from the linked issue's acceptance criteria and implementation plan. Do not launch this agent if no linked issue is detected."
- **Always** include this instruction in the Skill invocation: "Label each Critical and Important finding with a sequential F-prefixed identifier (F1, F2, F3, ...) numbered continuously across both sections. Label each Suggestion with a sequential S-prefixed identifier (S1, S2, S3, ...) using a separate counter. Use bold prefixes in the output (e.g., `**F1:** Missing null check`, `**S1:** Consider extracting helper`)."

Let the review complete fully. Do NOT attempt to fix any issues — this session is for review only.

Mark Step 2 complete.

## Step 3: Post review comment

Mark Step 3 in progress.

After the review completes, post the full review results as a reply comment on the PR:

```
gh pr comment <pr-number> --body "..."
```

The comment must include:
- `<!-- mach10-review -->` as the very first line of the comment body (this invisible HTML marker enables reliable identification in future sessions)
- The complete review findings (Critical, Important, Suggestions, Strengths), including any findings from supplementary agents merged into the appropriate severity categories with inline source attribution (e.g., "per plugin-dev:skill-reviewer")
- F/S identifiers on every finding -- Critical and Important findings use `F<n>` numbered sequentially across both sections, Suggestions use `S<n>` with a separate counter (e.g., `**F1:** ...`, `**F2:** ...`, `**S1:** ...`)
- Model attribution at the bottom (e.g., "Reviewed by Claude Opus 4.6")
- A note that this is an automated review

Format the comment as a well-structured markdown document that can serve as input to a future `/mach10:pr-review-fix` session.

Use F/S identifiers (e.g., F1, S2) or plain words (e.g., finding 1, suggestion 2) when referring to findings. Do not use bare `#<number>` notation, which GitHub auto-links to issues/PRs.

After posting, retrieve the URL of the review comment:

```
gh pr view <pr-number> --json comments --jq '.comments[-1].url'
```

Note the full URL (you will need it in Step 5) and extract the numeric comment ID from it — the number after `issuecomment-` in the URL (e.g., if the URL ends with `#issuecomment-1234567890`, the comment ID is `1234567890`). You will need this numeric ID in Step 8.

Mark Step 3 complete.

## Step 4: Run independent assessment

Mark Step 4 in progress.

First, fetch the PR context so the assessment can account for prior discussion:

```
gh pr view <pr-number> --json title,body,comments
```

Then run an independent assessment of each finding — from both the primary review and any supplementary agents — using the Task tool with a `general-purpose` subagent. Include the review text and the PR context (title, body, and all comments) directly in the subagent prompt — do not ask the subagent to fetch them from GitHub.

The subagent prompt should instruct it to:

1. Review the PR title, body, and all existing comments. Note any findings that have already been discussed, resolved, or deferred in the PR conversation.
2. For each review finding, **read the actual code** referenced and **independently verify** whether the issue exists.
3. Classify each finding using its F/S identifier from the review comment (e.g., "F1 -- Genuine", "S2 -- Nitpick"). Classify as one of:
   - **Genuine issue** — Real problem that should be fixed before merge. Explain why.
   - **Nitpick** — Stylistic preference or minor point that doesn't affect correctness or maintainability. Explain why it doesn't matter.
   - **False positive** — The reviewer flagged something that isn't actually an issue. Explain why the code is correct.
   - **Deferred** — Real issue but out of scope for this PR. Should be tracked separately.
   - If a finding was already fixed in a subsequent commit or resolved in discussion, classify it as **False positive** with a note that it has been addressed. If explicitly deferred in discussion, classify it as **Deferred** and reference the relevant comment.
4. After classifying all findings, produce a **staged implementation plan** covering everything worth fixing. Reference findings by their F/S identifiers (e.g., "stage 1 addresses F1 and F3"):
   - Number each stage with a descriptive name.
   - Required stages for genuine issues (must fix before merge).
   - Optional stages for nitpicks (nice-to-have improvements).
   - Each stage should list the specific findings it addresses and which files are affected.
5. Return all classifications (each with the original finding summary and 1-2 sentence reasoning referencing specific code), followed by the staged implementation plan produced in instruction (4) above.

Mark Step 4 complete.

## Step 5: Post assessment comment

Mark Step 5 in progress.

Post the assessment immediately as a reply comment on the PR — do not ask the user for approval first. The comment must include:
- `<!-- mach10-assessment -->` as the very first line of the comment body (this invisible HTML marker enables reliable identification in future sessions)
- Reference the review comment it is assessing (link to the specific comment URL from Step 3)
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

Extract the numeric comment ID from the URL (the number after `issuecomment-`). You will need this numeric ID in Step 8.

Use F/S identifiers (e.g., F1, S2) or plain words (e.g., finding 1, suggestion 2) when referring to findings. Do not use bare `#<number>` notation, which GitHub auto-links to issues/PRs.

Mark Step 5 complete.

## Step 6: Present CLI summary

Mark Step 6 in progress.

After posting, present the assessment to the user in CLI output:

For each finding:
- Original finding (brief summary)
- Classification (genuine / nitpick / false positive / deferred)
- Reasoning (1-2 sentences, referencing specific code)

Summary counts: how many genuine, how many nitpicks, how many false positives, how many deferred.

After the per-finding list and summary counts, display the staged implementation plan so the user can identify which issues to address next without switching to GitHub.

Mark Step 6 complete.

## Step 7: Handle deferred items

Mark Step 7 in progress.

If no findings were classified as deferred, mark Step 7 complete and proceed directly to Step 8.

If any findings were classified as **deferred**, use `AskUserQuestion` to ask the user how to handle them:

- **Create issues for all**: "Create a GitHub issue for every deferred finding"
- **Reclassify all as genuine**: "Mark all deferred items as genuine so they can be fixed in this PR"
- **Decide per finding**: "Choose what to do with each deferred finding individually"
- **Skip deferred items**: "Do not create issues or reclassify any deferred findings"

### Option 1: Create issues for all

For each deferred item, check for existing issues before creating a new one:

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

After processing, display a summary block in CLI output listing each item and the action taken:
- **Created**: Issue was created (include the new issue number and URL)
- **Skipped (duplicate)**: Matched an existing issue (include the existing issue number and the link comment URL)
- **Created (with overlap note)**: Issue was created with a note about potentially related issues

Then proceed to **Persist Deferred-Item Decisions** below.

### Option 2: Reclassify all as genuine

Update the assessment comment to change the classification of every deferred item from "Deferred" to "Genuine". Also update the staged implementation plan within the assessment comment to incorporate the reclassified items.

1. Retrieve the current assessment comment body:

   ```
   gh api repos/:owner/:repo/issues/comments/<assessment-comment-id> --jq .body
   ```

2. In the comment body, for each deferred item, change its classification from "Deferred" to "Genuine".

3. Update the staged implementation plan to include the reclassified items — add them to the appropriate existing stage if they fit, or create a new stage for them.

4. Write the updated body back:

   ```
   gh api repos/:owner/:repo/issues/comments/<assessment-comment-id> --method PATCH --raw-field body="<updated-body>"
   ```

After the update, display a CLI summary block listing each reclassified item by its F/S identifier:
- **Reclassified as genuine**: Item was marked as genuine and will be included in the fix handoff

Use F/S identifiers (e.g., F1, S2) or plain words (e.g., finding 1, suggestion 2) when referring to findings. Do not use bare `#<number>` notation, which GitHub auto-links to issues/PRs.

All reclassified items join the genuine findings list for the Step 8 handoff. Skip the decision comment — no deferred items remain to record.

### Option 3: Decide per finding

Present each deferred finding one at a time (in F/S identifier order) via `AskUserQuestion` with three options:

- **Create issue**: "Create a GitHub issue for this finding"
- **Mark as genuine**: "Reclassify as genuine to fix in this PR"
- **Skip**: "Do nothing with this finding"

After all items are processed:

1. **Reclassified items**: If any items were marked as genuine, follow the assessment-comment update procedure described in Option 2 (retrieve, update classifications from "Deferred" to "Genuine", update the staged implementation plan, and PATCH) — apply all reclassified items in a single PATCH call.

   Use F/S identifiers (e.g., F1, S2) or plain words (e.g., finding 1, suggestion 2) when referring to findings. Do not use bare `#<number>` notation, which GitHub auto-links to issues/PRs.

2. **Issue creation**: For items marked "Create issue", run the duplicate-detection and issue-creation flow described in Option 1.

3. **Summary block**: Display a CLI summary listing each deferred item and the action taken:
   - **Reclassified as genuine**: Item was marked as genuine and will be included in the fix handoff
   - **Created**: Issue was created (include the new issue number and URL)
   - **Skipped (duplicate)**: Matched an existing issue (include the existing issue number and the link comment URL)
   - **Created (with overlap note)**: Issue was created with a note about potentially related issues
   - **Skipped**: User chose to skip this finding

4. If any items remained deferred (created as issue, skipped as duplicate, or skipped), proceed to **Persist Deferred-Item Decisions** below. If all items were reclassified as genuine, skip the decision comment.

### Option 4: Skip deferred items

No issues created, no reclassification. Skip the decision comment entirely.

### Persist Deferred-Item Decisions

After displaying the summary block (Options 1 and 3 only, and only when at least one item remained deferred), post a decision comment on the PR to record the disposition of each deferred item for future sessions:

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
  - Skipped (not selected) (with one-sentence rationale if the user provided one) — user chose to skip this item
  - Reclassified as genuine — item was reclassified and will be addressed in the fix handoff (Option 3 only)
- Keep the entire comment body under 20 lines

Use F/S identifiers (e.g., F1, S2) or plain words (e.g., finding 1, suggestion 2) when referring to findings. Do not use bare `#<number>` notation, which GitHub auto-links to issues/PRs.

If any operation in Step 7 fails or is interrupted, proceed to Step 8 anyway to ensure the user receives the next-step recommendation.

Mark Step 7 complete.

## Step 8: Recommend next steps

Mark Step 8 in progress.

**CLI output only (do NOT include in any GitHub comment).**

First, display the comment IDs for reference:
- Review comment ID: `<review-comment-id from Step 3>`
- Assessment comment ID: `<assessment-comment-id from Step 5>`

Then, based on the assessment (including any items reclassified as genuine in Step 7):
- If genuine issues remain (including reclassified items): "`/clear` then `/mach10:pr-review-fix <pr-number> --review-comment <review-comment-id> --assessment-comment <assessment-comment-id> <findings>` (e.g., F1 F3 S2 -- all genuine issues, interleaved in F/S identifier order)"
- If all findings are nitpicks/false positives (with or without deferred items): "`/clear` then `/mach10:pr-pre-merge <pr-number>`"

Mark Step 8 complete.

## Important

Do NOT fix any issues in this session. Fixes must happen in a fresh session via `/mach10:pr-review-fix`.
