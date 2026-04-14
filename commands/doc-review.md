---
description: Review and update documentation based on PR changes
argument-hint: <pr-number> [scope]
allowed-tools: Bash, Read, Grep, Glob, Task, TaskCreate, TaskUpdate, Edit, Write, AskUserQuestion
model: opus
---

# Documentation Review

You are performing a thorough review of documentation against the changes in a pull request. The goal is to identify stale, missing, or incorrect documentation, present findings for user approval, apply accepted changes, and verify the result.

**User input:** $ARGUMENTS

## Step 0: Parse input and create task list

The user's input typically contains:
- A **PR number** (required)
- A **scope** to narrow the review (optional)

Example inputs:
- `108`
- `108 focus on API docs`
- `108 only README`

Extract the PR number. If a scope is provided, note it for filtering in Step 3 onward. If the input is ambiguous, ask the user to clarify.

After parsing input, create the progress-tracking task list. Create a task for Step 0 and immediately mark it in progress. Then create tasks for each of the remaining 8 steps one at a time, in step order, waiting for each to complete before creating the next, all starting as pending. Store each returned task ID for later use -- do not assume IDs are sequential.

| Task | Subject | activeForm |
|------|---------|------------|
| Step 0 | Step 0: Parse input and create task list | Parsing input |
| Step 1 | Step 1: Check out PR branch | Checking out PR branch |
| Step 2 | Step 2: Gather PR context | Gathering PR context |
| Step 3 | Step 3: Discover documentation | Discovering documentation |
| Step 4 | Step 4: Fan out review agents | Reviewing documentation |
| Step 5 | Step 5: Present findings and get user decisions | Processing findings with user |
| Step 6 | Step 6: Apply documentation changes | Applying changes |
| Step 7 | Step 7: Verify changes | Verifying changes |
| Step 8 | Step 8: Commit and report | Committing and reporting |

Mark Step 0 complete.

## Step 1: Check out PR branch

Mark Step 1 in progress.

Ensure you are on the PR's branch with the latest changes:

```
gh pr checkout <pr-number>
git pull
```

If either command fails (PR not found, authentication error, merge conflicts during pull), report the error to the user and stop -- the review cannot proceed without a clean, up-to-date working copy of the PR branch. Leave Step 1 as `in_progress`.

Mark Step 1 complete.

## Step 2: Gather PR context

Mark Step 2 in progress.

Build a picture of what changed in the PR:

1. **Changed files**: `gh pr diff <pr-number> --name-only` and `git diff main...HEAD --stat`
2. **PR context** -- read the title and description:
   ```
   gh pr view <pr-number>
   ```
   Then read all comments (`--comments` returns only comments and silently drops the title and body, so both calls are required):
   ```
   gh pr view <pr-number> --comments
   ```

From these, identify what features, APIs, behaviors, or configurations were added, changed, or removed. This summary is critical context for the review agents in Step 4.

Mark Step 2 complete.

## Step 3: Discover documentation

Mark Step 3 in progress.

Launch 2-3 exploration agents in parallel using the Task tool (subagent_type: Explore). Each agent should target a different documentation surface:

- **Repo-level docs**: README, CONTRIBUTING, CHANGELOG, docs/ directory, top-level .md files
- **Code-level docs**: Docstrings, JSDoc, inline comments in changed files and their immediate neighbors
- **Config and integration docs**: OpenAPI specs, CLI help text, config file comments, man pages

After agents return, compile results into a deduplicated list. Categorize each doc file into logical groups (e.g., "User-facing docs", "API reference", "Developer guides", "Inline code docs").

If a scope was provided, filter to only categories and files matching that scope.

Present the discovered documentation as a summary table (category, file path, brief description) before proceeding.

Mark Step 3 complete.

## Step 4: Fan out review agents

Mark Step 4 in progress.

For each documentation category, launch a subagent using the Task tool (subagent_type: general-purpose) to review that category's files. Batch small categories together to keep the total agent count between 3 and 6.

Each agent receives:
- Its assigned doc files (read them in full)
- A summary of what the PR changed (from Step 2)
- The PR description

Each agent evaluates:
- **Stale content**: Text that describes old behavior the PR has changed
- **Missing coverage**: New features, flags, endpoints, or behaviors introduced by the PR that have no documentation
- **Incorrect references**: Wrong function names, outdated code examples, broken links to renamed files
- **Outdated examples**: Code samples or usage examples that no longer work after the PR's changes
- **Obsolete docs**: Documentation for features or APIs that the PR removed entirely

Each agent returns structured findings as a list:
- File path
- Location (line number or section heading)
- Finding type (stale / missing / incorrect / outdated-example / obsolete)
- Severity: **important** (docs are factually wrong or misleading) or **suggestion** (improvement, not blocking)
- What's wrong
- Suggested change

Launch agents in parallel where possible.

Mark Step 4 complete.

## Step 5: Present findings and get user decisions

Mark Step 5 in progress.

After all agents complete, combine findings into a single report:

1. **Summary statistics**: Files reviewed, total findings by type and severity
2. **Important findings**: Listed first, with full detail
3. **Suggestions**: Listed second

Present the report to the user. Maintain objectivity -- these are suggestions from automated reviewers that may be wrong. Frame findings as "the reviewer identified..." rather than definitive statements.

Process findings one at a time. For each finding, use `AskUserQuestion` to ask the user how to handle it:

- **Accept**: "Apply the suggested change as-is"
- **Modify**: "Apply with adjustments"
- **Reject**: "Skip this finding"

If the user selects "Modify", ask what they want to change (free-text), then apply the adjusted version.

Mark Step 5 complete.

## Step 6: Apply documentation changes

Mark Step 6 in progress.

Apply all accepted and modified changes:

- Use Edit for existing files
- Use Write only if a new documentation file is needed
- Do NOT delete entire files without explicit user confirmation
- Do NOT commit yet -- verification comes first

Mark Step 6 complete.

## Step 7: Verify changes

Mark Step 7 in progress.

Launch 1-2 verification agents using the Task tool (subagent_type: general-purpose) on the modified files only. Each agent checks:

- **Internal consistency**: Do updated sections contradict other sections in the same file?
- **Accuracy**: Do changes accurately reflect what the PR actually does?
- **Formatting**: Are headings, lists, code blocks, and links well-formed?
- **Cross-references**: Are links to other files or sections still valid?

Present any verification issues to the user. Apply approved corrections.

Mark Step 7 complete.

## Step 8: Commit and report

Mark Step 8 in progress.

Stage modified documentation files by name (do NOT use `git add -A`). Commit and push:

```
git add <file1> <file2> ...
git commit -m "Update documentation based on PR #<pr-number> review"
git push
```

Post a summary comment on the PR:

```
gh pr comment <pr-number> --body "..."
```

The comment should include:
- Files reviewed and what was updated
- Findings that were rejected (for the record)
- Attribution: "Documentation reviewed by Claude Opus 4.6"

When referring to numbered items (findings, suggestions, stages) in the comment body, use plain words like "finding 3" or "suggestion 3" -- not `#<number>` notation, which GitHub auto-links to issues/PRs.

Mark Step 8 complete.

**CLI output only (do NOT include in the GitHub comment above):** Recommend next step to the user:
- If this was run before code review: "Next: `/clear` then `/mach10:pr-review <pr-number>`"
- If this was run after code review: "Next: `/clear` then `/mach10:pr-pre-merge <pr-number>`"
