---
description: Create a structured GitHub issue from current context or description
argument-hint: [optional-description]
allowed-tools: Bash, Read, Grep, Glob, AskUserQuestion
---

# Create Issue

You are creating a structured GitHub issue. This may be invoked at any point in the workflow — to capture deferred review findings, document refactoring needs, or track new feature ideas.

**Initial context (optional):** $ARGUMENTS

## Step 1: Gather Context

If a description was provided ($ARGUMENTS), use it as the starting point.

If no description was provided, ask the user what the issue is about.

Check if the repository has issue templates:

```
ls .github/ISSUE_TEMPLATE/ 2>/dev/null
```

If templates exist, read them and select the most appropriate one. If no templates, use the standard format below.

## Step 2: Draft the Issue

Draft a structured issue with these sections:

### Title
- Clear, concise, actionable (under 80 characters)
- Use imperative form (e.g., "Add validation for bulk solvent inputs")

### Body
- **Summary**: 2-3 sentences describing the problem or feature
- **Current Behavior** (for bugs/improvements): What happens now
- **Proposed Behavior**: What should happen
- **Acceptance Criteria**: Bullet list of verifiable conditions that define "done"
- **Context** (optional): Links to related PRs, issues, or discussions
- **Technical Notes** (optional): Implementation hints, relevant files, architectural considerations

## Step 3: Review

Present the drafted issue to the user, then use `AskUserQuestion` to ask for approval with these options:

- **Approve**: "Create the issue as drafted"
- **Modify**: "Edit the issue title, body, labels, or assignees"
- **Cancel**: "Abort without creating an issue"

If the user selects "Modify", ask what they want to change, apply the changes, and present the updated draft for approval again.

## Step 4: Check for Duplicates

After the user approves the draft, check for existing issues that may already cover the same topic before creating.

Extract 2-3 key terms from the approved issue title and search:

```
gh issue list --search "<keywords>" --state all --limit 5 --json number,title,state,url
```

Handle results based on similarity:

- **No results**: Proceed silently to Step 5.
- **Clear duplicate**: If an existing open issue's title is nearly identical, act autonomously -- post a comment on the existing issue referencing the new context and skip creation. Report what was done to the user.

  ```
  gh issue comment <existing-issue-number> --body "Related context: <summary of the new finding or context that prompted this issue>."
  ```

- **Ambiguous matches**: If results are related but not clearly duplicates, present the matches to the user (showing issue number, title, state, and URL for each). Flag closed issues prominently (e.g., "This issue was previously closed"). Then use `AskUserQuestion` to ask how to proceed:

  - **Proceed**: "Create the new issue anyway"
  - **Link**: "Add this finding as a comment on one of the listed issues"
  - **Skip**: "Do not create an issue for this finding"

  If the user selects "Link" and multiple matches were shown, ask which existing issue to link to (free-text, since the user may want to specify by number). Post a comment on the chosen issue referencing the new context, then skip creation:

  ```
  gh issue comment <chosen-issue-number> --body "Related context: <summary of the new finding or context that prompted this issue>."
  ```

## Step 5: Create

After approval and duplicate check, create the issue:

```
gh issue create --title "..." --body "..."
```

When referring to numbered items (findings, suggestions, stages) in the issue body, use plain words like "finding 3" or "suggestion 3" -- not `#<number>` notation, which GitHub auto-links to issues/PRs.

Add labels if the user specified them or if the repo has standard labels:

```
gh issue edit <number> --add-label "..."
```

## Step 6: Confirm

Report to the user:
- Issue number and URL
- Suggest next action if relevant (e.g., "Next: `/clear` then `/mach10:issue-plan <number>`")
