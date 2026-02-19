---
description: Commit, push, and post a progress comment on the associated PR or issue
argument-hint: [optional-commit-message]
allowed-tools: Bash, Read, Grep, Glob
---

# Push

You are finalizing a batch of work: committing changes, pushing to remote, and documenting progress on the associated PR or issue.

## Step 1: Determine What to Commit

Run `git status` and `git diff --staged` to understand the current state.

**Staging logic:**
- If you have context from this session about which files you modified, stage those specific files. Do NOT use `git add -A` or `git add .` — add files by name.
- If files are already staged and the staging looks correct based on session context, proceed with those.
- If it is unclear what should be staged (e.g., this is a fresh session with no prior context), review all untracked and unstaged files, present your findings to the user, and ask for guidance on what to stage.
- Never stage files that likely contain secrets (.env, credentials.json, etc.).

## Step 2: Commit

Review recent commit messages for style consistency:

```
git log --oneline -10
```

Generate a commit message that:
- Follows the repository's existing commit message style
- Summarizes the nature of the changes (new feature, bug fix, refactor, etc.)
- Focuses on the "why" rather than the "what"
- Uses the user's override message if one was provided: $ARGUMENTS

Create the commit. Use a HEREDOC for the message to ensure proper formatting:

```
git commit -m "$(cat <<'EOF'
Commit message here.

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Step 3: Push

Push to the remote tracking branch:

```
git push
```

If no upstream is set, push with `-u` flag to the current branch name.

## Step 4: Post Progress Comment

Determine the associated PR or issue:

1. **Try PR first:** Run `gh pr view --json number,url` on the current branch. If a PR exists, comment on it.
2. **Fall back to issue:** If no PR, check the branch name for an issue number pattern (e.g., `feature/issue-55-*` or `fix/issue-23-*`). If found, comment on that issue.
3. **If neither found:** Skip commenting and inform the user.

Post a reply comment documenting what was done:
- Brief summary of changes in this batch
- Commit hash(es) included
- Any notable decisions or deviations from the plan

## Step 5: Confirm

Report to the user in CLI output (do NOT include next-step suggestions in the GitHub comment from Step 4):
- What was committed (files and message)
- Where it was pushed
- Where the progress comment was posted (with link)
- Suggest next steps, always prefixed with `/clear` (e.g., "Next: `/clear` then `/mach10:issue-implement $ISSUE next-stage`" or "Next: `/clear` then `/mach10:pr-review $PR`")
