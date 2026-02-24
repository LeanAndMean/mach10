---
description: Create a pull request for the current branch with structured description
argument-hint: [issue-number] [context]
allowed-tools: Bash, Read, Grep, Glob, AskUserQuestion
---

# Create Pull Request

You are creating a pull request for the current branch, with a structured description that includes a summary, test plan, and issue linkage.

**Context (optional):** $ARGUMENTS

## Step 1: Parse Input

The user may provide:
- An **issue number** to link (e.g., `55`)
- An issue number plus **additional context** (e.g., `55 focus on the API changes`)
- **Nothing** — you will infer context from the branch and commits

Extract the issue number if provided. Note any additional context for use when drafting the PR body. If the input is ambiguous (e.g., it's unclear whether a token is an issue number or context), ask the user to clarify.

## Step 2: Gather Context

Determine the current branch:

```
git branch --show-current
```

If the output is empty (detached HEAD state), stop and tell the user to create or checkout a branch first.

Determine the default branch of the repository:

```
gh repo view --json defaultBranchRef --jq .defaultBranchRef.name
```

If the current branch is the default branch, stop and tell the user to create a feature branch first.

Read recent commits on this branch vs the default branch:

```
git log <default-branch>..HEAD --oneline
```

Read the diff summary to understand the scope of changes:

```
git diff <default-branch>...HEAD --stat
```

If both the commit log and diff are empty, stop and tell the user there are no changes on this branch relative to the default branch. Suggest checking `git status` for uncommitted work.

For complex changes, use your Read and Grep tools to examine specific modified files and understand the changes in enough detail to write an accurate summary.

**Issue resolution:**

1. If an issue number was provided in $ARGUMENTS, read it:
   ```
   gh issue view <issue-number>
   ```
   If this fails (issue not found, permission denied, etc.), report the error to the user. Do NOT proceed without the issue when the user explicitly provided an issue number.
2. If no issue number was provided, try to infer one from the branch name (e.g., `feature/issue-55-*`, `fix/issue-23-*`, or `55-some-description`). If found, read that issue.
3. If no issue can be identified, proceed without one.

## Step 3: Draft PR

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

- Include `Fixes #<issue-number>` only if an issue was identified.
- When referring to numbered items (findings, suggestions, stages) in the body, use plain words like "finding 3" or "suggestion 3" -- not `#<number>` notation, which GitHub auto-links to issues/PRs. (`Fixes #<issue-number>` is an intentional GitHub reference and should be kept as-is.)
- If the user provided additional context in $ARGUMENTS, incorporate it into the summary or test plan as appropriate.

Present the draft title and body to the user, then use `AskUserQuestion` to ask for approval with these options:

- **Approve**: "Create the PR as drafted"
- **Modify**: "Edit the PR title or body"
- **Cancel**: "Abort without creating a PR"

If the user selects "Modify", ask what they want to change, apply the changes, and present the updated draft for approval again. If the user selects "Cancel", stop and confirm that no PR was created.

## Step 4: Create PR

After user approval, ensure the branch has been pushed to the remote. Check if the branch exists on the remote:

```
git ls-remote --heads origin <branch-name>
```

If the branch does not exist on the remote, push it:

```
git push -u origin <branch-name>
```

If the push fails, report the error and stop.

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

Do NOT proceed to the confirmation step if PR creation failed.

## Step 5: Confirm

Report to the user:
- PR number and URL
- Linked issue (if any)
- Suggest next step using the actual PR number: "Next: `/clear` then `/mach10:pr-review <pr-number>`"
