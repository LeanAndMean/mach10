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

## Step 4: Create

After approval, create the issue:

```
gh issue create --title "..." --body "..."
```

When referring to numbered items (findings, suggestions, stages) in the issue body, use plain words like "finding 3" or "suggestion 3" -- not `#<number>` notation, which GitHub auto-links to issues/PRs.

Add labels if the user specified them or if the repo has standard labels:

```
gh issue edit <number> --add-label "..."
```

## Step 5: Confirm

Report to the user:
- Issue number and URL
- Suggest next action if relevant (e.g., "Next: `/clear` then `/mach10:issue-plan <number>`")
