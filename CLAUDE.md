# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

mach10 defines a structured development methodology for agentic coding and provides a Claude Code plugin that implements it. The methodology centers on fresh sessions for each step, GitHub as the inter-session persistence layer, staged implementation, and iterative review-fix cycles. The plugin codifies this into 15 slash commands covering the complete issue-to-merge lifecycle.

## Architecture

This is a pure plugin definition -- no build system, no runtime, no tests. Claude Code reads the command files directly.

```
.claude-plugin/plugin.json   # Plugin manifest (name, version, author)
agents/                       # Specialized agent definitions (markdown with YAML frontmatter)
commands/                     # Slash command definitions (markdown with YAML frontmatter)
```

Each command file is a self-contained workflow specification with:
- **YAML frontmatter**: `description`, `argument-hint`, `allowed-tools`, `model`
- **Markdown body**: Step-by-step instructions Claude Code follows when the command is invoked

## Command Structure

**Issue workflow:** `issue-assessment`, `issue-plan`, `issue-plan-review`, `issue-implement`, `issue-create`
**PR workflow:** `pr-create`, `pr-review`, `pr-review-fix`, `pr-ci-fix`, `pr-review-validate`, `doc-review`, `pr-pre-merge`, `pr-merge`
**Utilities:** `push`, `test-audit`

## Key Design Decisions

- **Thin orchestration**: Commands gather context and delegate to `feature-dev` and `pr-review-toolkit` plugins via the Skill tool rather than reimplementing workflows.
- **Single-concern sessions**: Review and fix are separate commands to preserve context budget for implementation. Each command is designed to run in a fresh CLI session.
- **GitHub as backbone**: Plans, reviews, and progress are posted as issue/PR comments so context persists across sessions.
- **Safe defaults**: No `git add -A`, no staging of secrets, no force-pushes, branch deletion uses `-d` flag.

## GitHub Comment Formatting

When composing content for GitHub comments or issue bodies:
- Do not use bare `#<number>` notation for numbered items (findings, suggestions, stages) -- GitHub auto-links `#<number>` to issues and PRs.
- Use plain words instead: "finding 3", "suggestion 3", "stage 2".
- Reserve `#<number>` exclusively for intentional GitHub issue/PR references (e.g., `Fixes #55`).

## Plugin Dependencies

- `gh` CLI (GitHub authentication required)
- `feature-dev` plugin (used by `issue-plan`, `issue-implement`, `pr-review-fix`, `pr-ci-fix`)
- `pr-review-toolkit` plugin (used by `pr-review`)

## Writing Commands

When adding or modifying commands, follow the existing pattern:
- YAML frontmatter must include `description` and `argument-hint`
- Set `allowed-tools` to the minimum set needed (principle of least privilege)
- Set `model: opus` for commands requiring deep reasoning (reviews, planning, implementation)
- End commands with a "next step" suggestion that includes `/clear` guidance for session boundaries (omit `/clear` when the next command needs session context, e.g., `/mach10:push` after implementation)
- Use `gh` CLI for all GitHub operations (issues, PRs, comments, CI logs)
- Commands that modify code delegate to `/feature-dev:feature-dev` via the Skill tool
- Commands that need codebase exploration or architecture analysis can use the Task tool with `subagent_type` to invoke agents from dependent plugins (e.g., `feature-dev:code-explorer`, `feature-dev:code-architect`)
- Commands that review code delegate to `/pr-review-toolkit:review-pr` via the Skill tool
- **Repo structure sync**: The repository structure diagram is duplicated between `CLAUDE.md` (Architecture section) and `README.md` (Repository structure section). Any change to the structure block must be applied to both locations.
- **Contributing-guide lookup sync**: The lookup pattern (`CONTRIBUTING.md` → `DEVELOPMENT.md` → `.github/CONTRIBUTING.md`, first-match-stop) is duplicated in three command files: `commands/issue-plan.md` (Step 3a), `commands/issue-plan-review.md` (Step 3a), and `commands/pr-pre-merge.md` (contributing guide lookup). `README.md` (the "Customizing with CONTRIBUTING.md" section) also documents this feature. Any change to the lookup logic must be applied to all four locations.
- **Plan marker sync**: The `<!-- mach10-plan -->` HTML marker is used to reliably locate implementation plan comments. The marker is emitted by `commands/issue-plan.md` (Step 7) and `commands/issue-plan-review.md` (revised plan posting). It is consumed by `commands/issue-implement.md` (Step 3), `commands/issue-plan-review.md` (Step 2), and `agents/feature-completeness-checker.md` (Step 1). Any change to the marker convention must be applied to all locations.
- **Issue-reference pattern sync**: The list of issue reference patterns (`Fixes #N`, `Closes #N`, `Resolves #N`, `Part of #N`, `Issue #N`, bare `#N`) is duplicated between `commands/pr-review.md` (Step 3, Skill invocation instruction) and `agents/feature-completeness-checker.md` (Step 1, "Detect the linked issue"). Any change to the pattern list must be applied to both locations.
- **Duplicate-issue detection sync**: The duplicate-detection search command (`gh issue list --search "<keywords>" --state all --limit 5 --json number,title,state,url`) and keyword-extraction approach are duplicated between `commands/issue-create.md` (Step 4) and `commands/pr-review.md` (Step 8). Any change to the search command or keyword strategy must be applied to both locations. Note: result-handling logic intentionally differs -- `issue-create` is interactive (user prompted via `AskUserQuestion`) while `pr-review` is autonomous (batch processing). Only the search mechanics are synchronized.
- **Decision-comment marker sync**: The `<!-- mach10-decisions -->` HTML marker is used to identify follow-up comments that capture user-driven post-creation decisions. The marker is emitted as a standalone comment by `commands/pr-review.md`, `commands/pr-review-validate.md`, and `commands/issue-plan-review.md`. Two commands use inline variants: `commands/issue-plan.md` embeds decision rationale as an inline `## Decision Log` section within the plan comment instead of a standalone marker, and `commands/issue-assessment.md` has two paths -- on the approve path, comment-bearing actions embed interaction findings as an inline `## Assessment Notes` section within the reply comment (no standalone marker), while the body-only action posts Assessment Notes as a separate follow-up comment (also no standalone marker); on the cancel path, it emits a standalone `<!-- mach10-decisions -->` marker comment. Any change to the marker convention, the Decision Log section convention, or the Assessment Notes section convention must be applied to all five locations.
- **Issue auto-assignment sync**: The assignment logic (assignee check via `gh issue view --json assignees`, current user check via `gh api user`, skip-if-already-assigned condition, `AskUserQuestion` option set for other-assignees case, and graceful failure handling) is duplicated between `commands/issue-plan.md` (Step 7, sub-step 3) and `commands/issue-implement.md` (Step 2, "Assign the issue" section). The sub-issue detection and assignment block (two-strategy detection from `pr-create.md`, per-sub-issue three-path assignment, bulk `AskUserQuestion` for conflicting assignees) immediately follows the parent assignment in both locations: `commands/issue-plan.md` (Step 7, sub-step 4) and `commands/issue-implement.md` (Step 2, "Assign sub-issues" section). Any change to the parent or sub-issue assignment logic must be applied to both locations. Note: `issue-implement` includes an additional note that already-assigned is the expected case for subsequent stages.
- **Finding-identifier sync**: The `F<n>`/`S<n>` finding identifier convention (F for Critical/Important findings, S for Suggestions, numbered globally within each prefix) and the `<findings>` handoff parameter are synchronized across: `commands/pr-review.md` (Step 3 Skill instruction, Step 4 comment format, Step 5 subagent prompt, Step 9 handoff), `commands/pr-review-validate.md` (Step 3 classification instruction, Step 6 handoff variants), `commands/pr-review-fix.md` (argument-hint, Step 1 examples/parsing, Step 3 extraction), and `README.md` (command table, phase description, and quick reference). The six "plain words" reminder lines in `pr-review.md` (Steps 4, 6, 8) and `pr-review-validate.md` (Step 5) must also use the updated F/S-permitting wording. Any change to the identifier scheme or parameter name must be applied to all locations.

### User Interaction Patterns

Every user interaction point in a command must explicitly specify its method: `AskUserQuestion` with structured choices, or free-text.

- **Use `AskUserQuestion`** when the set of valid responses is known or can be inferred: draft approvals, yes/no decisions, multi-option selections, branch selection from a discovered list.
- **Use free-text** only when the answer set cannot be enumerated: open-ended questions, follow-up prompts for specific values (e.g., branch names after a structured selection), modification descriptions.

Conventions for `AskUserQuestion` instructions:

- Use context-specific option descriptions tailored to the command (e.g., "Edit the PR title or body" rather than generic "Modify").
- Include an escape-path option (e.g., "Cancel", "Skip", "Reject") when the user should be able to exit or skip the flow. For forced-choice questions where all options are valid continuations (e.g., version bump level), an escape path may be omitted.
- Add follow-up instructions for non-terminal options (e.g., "If the user selects 'Modify', ask what they want to change, apply the changes, and present the updated draft for approval again.").
- Use `multiSelect: true` when choices are not mutually exclusive. If more than 4 items, group into severity-based or category-based options.
- `AskUserQuestion` always includes a built-in "Other" option that lets users provide free-text input. When a question could have more valid responses than the 4-option limit allows, reference the built-in "Other" option in the command instructions to cover the overflow (e.g., "list the 4 most recent and let the built-in 'Other' option cover the rest"). For uncommon-but-valid paths, coach the user in the response text before the question about what they can express via "Other" rather than adding a rarely-used explicit option.

Example instruction text for a draft approval step:

```
Present the draft to the user, then use `AskUserQuestion` to ask for approval:

- **Approve**: "Create the issue as drafted"
- **Modify**: "Edit the issue title, body, labels, or assignees"
- **Cancel**: "Abort without creating an issue"

If the user selects "Modify", ask what they want to change, apply the changes,
and present the updated draft for approval again.
```

## Writing Agents

Agent definitions live in the `agents/` directory as markdown files with YAML frontmatter. When adding or modifying agents, follow the existing pattern:

- YAML frontmatter must include `name`, `description`, `model`, and `color`
- `description` should explain when the agent should be used, with `<example>` blocks showing trigger scenarios
- Set `model: inherit` to use the caller's model, or specify a model explicitly (e.g., `model: opus`)
- `color` provides visual distinction in CLI output (e.g., `magenta`, `cyan`)
- The markdown body defines the agent's system prompt: its role, review process, output format, and tone
- Agents are invoked via the Task tool with `subagent_type` -- they do not have `allowed-tools` or `argument-hint` fields

## Release Process

Every change merged into `main` must follow this process:

1. **Version bump**: Before the PR is merged, bump the plugin version in `.claude-plugin/plugin.json`.
2. **Tagged commit**: After the merge, create a git tag matching the new version (e.g., `v0.2.0`).
3. **GitHub release**: Create a GitHub release for the tag with a description of the change.

## Working in This Repo

- Proactively load any plugin development skills you think might be relevant when modifying or reviewing files in this repo.
