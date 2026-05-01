---
description: Create a pull request for the current branch with structured description
argument-hint: [issue-number] [context]
allowed-tools: Bash, Read, Grep, Glob, AskUserQuestion, TaskCreate, TaskUpdate
---

# Create Pull Request

You are creating a pull request for the current branch, with a structured description that includes a summary, test plan, and issue linkage.

**Context (optional):** $ARGUMENTS

## Step 0: Parse input and create task list

The user may provide:
- An **issue number** to link (e.g., `55`)
- An issue number plus **additional context** (e.g., `55 focus on the API changes`)
- **Nothing** — you will infer context from the branch and commits

Extract the issue number if provided. Note any additional context for use when drafting the PR body. If the input is ambiguous (e.g., it's unclear whether a token is an issue number or context), use free-text to ask the user to clarify.

After parsing input, create the progress-tracking task list. Create a task for Step 0 and immediately mark it in progress. Then create tasks for each of the remaining 4 steps one at a time, in step order, all starting as pending. Task list display order matches creation order, so each task must be a separate sequential call -- do not batch multiple task creations in a single message. Store each returned task ID for later use -- do not assume IDs are sequential.

| Task | Subject | activeForm |
|------|---------|------------|
| Step 0 | Step 0: Parse input and create task list | Parsing input |
| Step 1 | Step 1: Gather context | Gathering context |
| Step 2 | Step 2: Draft PR and get approval | Drafting PR |
| Step 3 | Step 3: Create pull request | Creating pull request |
| Step 4 | Step 4: Confirm PR and suggest next steps | Confirming PR |

Mark Step 0 complete.

## Step 1: Gather context

Mark Step 1 in progress.

Determine the current branch:

```
git branch --show-current
```

If the output is empty (detached HEAD state), stop and tell the user to create or checkout a branch first. Leave Step 1 as `in_progress`.

Determine the default branch of the repository:

```
gh repo view --json defaultBranchRef --jq .defaultBranchRef.name
```

If the current branch is the default branch, stop and tell the user to create a feature branch first. Leave Step 1 as `in_progress`.

Read recent commits on this branch vs the default branch:

```
git log <default-branch>..HEAD --oneline
```

Read the diff summary to understand the scope of changes:

```
git diff <default-branch>...HEAD --stat
```

If both the commit log and diff are empty, stop and tell the user there are no changes on this branch relative to the default branch. Suggest checking `git status` for uncommitted work. Leave Step 1 as `in_progress`.

For complex changes, use your Read and Grep tools to examine specific modified files and understand the changes in enough detail to write an accurate summary.

**Issue resolution:**

1. If an issue number was provided in $ARGUMENTS, read it:
   ```
   gh issue view <issue-number>
   ```
   If this fails (issue not found, permission denied, etc.), report the error to the user. Do NOT proceed without the issue when the user explicitly provided an issue number.
   Then read all comments (`--comments` returns only comments and silently drops the title and body, so both calls are required):
   ```
   gh issue view <issue-number> --comments
   ```
   Comment content (implementation plans, decisions, assessment findings, progress notes) should inform the Summary bullets and Test plan when drafting the PR, but should not be copy-pasted verbatim into the PR body.
2. If no issue number was provided, try to infer one from the branch name (e.g., `feature/issue-55-*`, `fix/issue-23-*`, or `55-some-description`). If found, read that issue and its comments using the same two-call approach as above.
3. If no issue can be identified, proceed without one.

**Sub-issue detection:**

If an issue was identified, detect any sub-issues so closing keywords can be included for them in the PR body. Skip this block entirely if no issue was identified.

1. **Strategy A (API):** First resolve the repository identifier, then query the GitHub sub-issues API:
   ```
   REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
   gh api --paginate repos/$REPO/issues/<issue-number>/sub_issues --jq '.[] | {number, state}'
   ```
   - If the API call **succeeds and returns one or more results**, use them as the confirmed sub-issue list (each entry includes both the issue number and its state).
   - If the API call **succeeds but returns no results** (empty array), the issue has no sub-issues. Do NOT fall through to Strategy B -- treat the sub-issue list as empty.
   - If the API call **fails** (e.g., 404, permission error, network timeout), proceed to Strategy B.

2. **Strategy B (body-parse fallback):** This strategy runs only when the API call in Strategy A failed. Scan the issue body for sub-issue references. Match `#<number>` references that appear on GitHub task list lines -- lines beginning with optional whitespace followed by a list marker (`-`, `*`, or `+`) and a checkbox (`[ ]`, `[x]`, or `[X]`). Exclude any `#<number>` preceded by relational keywords: "Related to", "Blocked by", "See also", or "Depends on". Collect the matched issue numbers, excluding the parent issue number itself. Use these as candidate sub-issues. Note: this fallback is less reliable than the API -- flag these as candidates when presenting the draft (see Step 2). After collecting the candidate list, query each sub-issue's state individually: `gh issue view <N> --json state --jq .state`. If the state query fails for a sub-issue, treat it as open.

3. If Strategy A returned an empty result or Strategy B yielded no matches, the sub-issue list is empty.

Mark Step 1 complete.

## Step 2: Draft PR and get approval

Mark Step 2 in progress.

Compose a PR title and body based on the gathered context.

**Title:**
- Short, under 70 characters
- Imperative form (e.g., "Add validation for bulk solvent inputs")

**Body:**

```
## Summary
- <bullet points summarizing the changes>

## Test plan
- [ ] <bulleted checklist of how to verify the changes>

Fixes #<issue-number>

---
Generated with [Claude Code](https://claude.com/claude-code)
```

**Closing keywords inclusion rule:**
- **No issue identified:** Omit all closing keywords.
- **Issue without sub-issues:** Include only `Fixes #<issue-number>`.
- **Issue with sub-issues:** Include `Fixes #<issue-number>` for the parent, followed by one `Fixes #<N>` line for each sub-issue. If any sub-issues are already closed, present a note above the `Fixes` lines listing those sub-issues and their closed state (adding `Fixes` for an already-closed issue is harmless but adds noise). When presenting the draft, tell the user they can remove unwanted closing keywords via the "Modify" option (e.g., for already-closed sub-issues, or if this PR only addresses some of the sub-issues). If the sub-issues were detected via Strategy B (body-parse fallback), note this to the user so they can verify the list is correct.

- When referring to numbered items (findings, suggestions, stages) in the body, use plain words like "finding 3" or "suggestion 3" -- not `#<number>` notation, which GitHub auto-links to issues/PRs. (`Fixes #<issue-number>` is an intentional GitHub reference and should be kept as-is.)
- If the user provided additional context in $ARGUMENTS, incorporate it into the summary or test plan as appropriate.

Present the draft title and body to the user, then use `AskUserQuestion` to ask for approval with these options:

- **Approve**: "Create the PR as drafted"
- **Modify**: "Edit the PR title or body"
- **Cancel**: "Abort without creating a PR"

If the user selects "Modify", ask what they want to change, apply the changes, and present the updated draft for approval again. If the user selects "Cancel", stop and confirm that no PR was created. Leave Step 2 as `in_progress`.

Mark Step 2 complete.

## Step 3: Create pull request

Mark Step 3 in progress.

After user approval, ensure the branch has been pushed to the remote. Check if the branch exists on the remote:

```
git ls-remote --heads origin <branch-name>
```

If the branch does not exist on the remote, push it:

```
git push -u origin <branch-name>
```

If the push fails, report the error and stop. Leave Step 3 as `in_progress`.

Then create the PR using `gh`. Use a HEREDOC for the body to ensure correct formatting:

```
gh pr create --title "<approved-title>" --body "$(cat <<'EOF'
<approved-body>
EOF
)"
```

If `gh pr create` fails:
- **PR already exists for this branch**: Report the existing PR URL using `gh pr view`.
- **Permission or authentication errors**: Suggest checking `gh auth status`.
- **Other errors**: Report the full error to the user.

Do NOT proceed to the confirmation step if PR creation failed. Leave Step 3 as `in_progress`.

Mark Step 3 complete.

## Step 4: Confirm PR and suggest next steps

Mark Step 4 in progress.

Report to the user:
- PR number and URL
- Linked issue (if any)

Mark Step 4 complete.

**CLI output only (do NOT include in the report above):** Suggest next step using the actual PR number: "Next: `/clear` then `/mach10:pr-review <pr-number>`"
