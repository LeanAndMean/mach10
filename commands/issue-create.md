---
description: Create a structured GitHub issue from current context or description
argument-hint: [context]
allowed-tools: Bash, Read, Grep, Glob, AskUserQuestion
---

# Create Issue

You are creating a structured GitHub issue. This may be invoked at any point in the workflow — to capture deferred review findings, document refactoring needs, or track new feature ideas.

**Context (optional):** $ARGUMENTS

## Step 1: Gather Context

If context was provided ($ARGUMENTS), parse it for two kinds of input and act on each:

- **Descriptive content** (problem statement, feature description, observed behavior, motivation): Use as the starting point for drafting the issue body in Step 2.
- **Meta-directives about the issue itself** (e.g., "use the bug template", "tag as priority-high", "create as a sub-issue of 137", "assign me", "make this a tracking issue", "create as draft"): Note these for the appropriate downstream step. Template choice influences Step 2's template selection. Labels, assignees, parent issue, and draft state are applied via `gh issue create` / `gh issue edit` flags in Step 5. Honor meta-directives explicitly -- do not fold them into the issue body as descriptive text.

If no context was provided, ask the user what the issue is about.

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
- **Proposed Behavior**: What should happen -- describe desired outcomes rather than implementation steps. If the issue's subject is a command definition, agent definition, or workflow specification, naming the specific file and section as the target of a behavioral change is appropriate here; move to Technical Notes only when describing the mechanism of the change (algorithm, control flow, data structure choices).
- **Acceptance Criteria**: Bullet list of verifiable end-state conditions that define "done", independent of implementation approach. Exception: when the artifact being changed is itself a specification (command definitions, config schemas, workflow files, documentation), implementation-specific criteria are appropriate because the spec IS the implementation.
- **Context** (optional): Links to related PRs, issues, or discussions
- **Technical Notes** (optional): Implementation hints, relevant files, architectural considerations

### Drafting notes

**PII and sensitive content**: During drafting, paraphrase rather than include verbatim: API tokens (patterns like `ghp_`, `sk-`, `Bearer eyJ`), passwords, private keys, personal email addresses, and internal hostnames/IPs. When paraphrasing, preserve the semantic role of the content (e.g., "the reporter's email" instead of the literal address, "an API token" instead of the literal value). Do not use placeholder artifacts like `[REDACTED]` -- the draft should read naturally. Track what was paraphrased for a brief summary in Step 3.

Safe-list of routine content that must NOT be paraphrased or flagged: file paths, GitHub usernames, branch names, config key names, public URLs, API response fragments, GitHub comment IDs (`issuecomment-N` form), HTML comment markers (`<!-- ... -->`), jq filter expressions, shell command invocations, and YAML frontmatter key-value pairs.

When the input ($ARGUMENTS or user response) is structured output from another mach10 command (identifiable by F/S identifiers, `<!-- mach10-* -->` markers, or step-reference formatting), treat all content as specification-artifact material and do not apply PII paraphrasing.

**Proposed Behavior boundary**: Outcome vs. implementation decision test -- if a sentence describes a specific implementation mechanism (algorithm, data structure, control flow decision, code pattern), it belongs in Technical Notes. Naming a specific file or section as the target of a behavioral change is Proposed Behavior, not implementation detail. This distinction matters especially in plugin/specification repos where command files and their sections are the behavioral surface.

**Acceptance Criteria constraint**: Observable end-state framing. Each criterion should be confirmable regardless of implementation path. Exception for specification artifacts (command definitions, config schemas, workflow files, documentation) where the spec is the deliverable -- in those cases, implementation-specific criteria are appropriate because they describe the desired state of the specification itself.

## Step 3: Review

If any content was paraphrased during drafting, include a single-sentence note before the draft (e.g., "Note: 1 sensitive item was paraphrased in the draft below"). If no content was paraphrased, skip the note.

Present the drafted issue to the user, then use `AskUserQuestion` to ask for approval with these options:

- **Approve**: "Create the issue as drafted"
- **Modify**: "Edit the issue title, body, labels, or assignees"
- **Cancel**: "Abort without creating an issue"

If the user selects "Modify", ask what they want to change, apply the changes, and present the updated draft for approval again. If the user wants to restore paraphrased content to its original form, honor the request -- the user has final authority over what appears in the issue.

## Step 4: Check for Duplicates

After the user approves the draft, check for existing issues that may already cover the same topic before creating.

Extract 2-3 key terms from the approved issue title and search:

```
gh issue list --search "<keywords>" --state all --limit 5 --json number,title,state,url
```

Handle results based on similarity:

- **No results**: Proceed silently to Step 5.
- **Clear duplicate**: If an existing **open** issue's title is nearly identical, present the match to the user (showing issue number, title, state, and URL) and use `AskUserQuestion` to ask how to proceed:

  - **Link to existing**: "Post a comment on the existing issue and skip creation"
  - **Create anyway**: "Create the new issue despite the potential duplicate"
  - **Skip**: "Do not create an issue"

  If the user selects "Link to existing", post a comment on the existing issue referencing the new context, then skip creation. Report the existing issue number, URL, and the comment URL to the user.

  ```
  gh issue comment <existing-issue-number> --body "Related context: <summary of the new finding or context that prompted this issue>."
  ```

  Capture the comment URL after posting (parse it from the `gh issue comment` output or retrieve via `gh api`).

  If the user selects "Create anyway", proceed to Step 5. If the user selects "Skip", proceed directly to Step 6 and report that issue creation was skipped.

  If the near-identical match is a **closed** issue, treat it as an ambiguous match instead -- a previously-closed issue should not block creation.

- **Ambiguous matches**: If results are related but not clearly duplicates, present the matches to the user (showing issue number, title, state, and URL for each). Flag closed issues prominently (e.g., "This issue was previously closed"). Then use `AskUserQuestion` to ask how to proceed:

  - **Proceed**: "Create the new issue anyway"
  - **Link**: "Add this finding as a comment on one of the listed issues"
  - **Skip**: "Do not create an issue"

  If the user selects "Link" and multiple matches were shown, ask which existing issue to link to (free-text, since the user may want to specify by number). Post a comment on the chosen issue referencing the new context, then skip creation. Report the existing issue number, URL, and the comment URL to the user.

  ```
  gh issue comment <chosen-issue-number> --body "Related context: <summary of the new finding or context that prompted this issue>."
  ```

  Capture the comment URL after posting (parse it from the `gh issue comment` output or retrieve via `gh api`).

  If the user selects "Skip", proceed directly to Step 6 and report that issue creation was skipped.

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
