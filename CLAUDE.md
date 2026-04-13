# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

mach10 defines a structured development methodology for agentic coding and provides a Claude Code plugin that implements it. The methodology centers on fresh sessions for each step, GitHub as the inter-session persistence layer, staged implementation, and iterative review-fix cycles. The plugin codifies this into 14 slash commands covering the complete issue-to-merge lifecycle.

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
**PR workflow:** `pr-create`, `pr-review`, `pr-review-fix`, `pr-ci-fix`, `doc-review`, `pr-pre-merge`, `pr-merge`
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
- **Issue-reference pattern sync**: The list of issue reference patterns (`Fixes #N`, `Closes #N`, `Resolves #N`, `Part of #N`, `Issue #N`, bare `#N`) is duplicated between `commands/pr-review.md` (Step 2, Skill invocation instruction) and `agents/feature-completeness-checker.md` (Step 1, "Detect the linked issue"). Any change to the pattern list must be applied to both locations.
- **Duplicate-issue detection sync**: The duplicate-detection search command (`gh issue list --search "<keywords>" --state all --limit 5 --json number,title,state,url`) and keyword-extraction approach are duplicated between `commands/issue-create.md` (Step 4) and `commands/pr-review.md` (Step 7). Any change to the search command or keyword strategy must be applied to both locations. Note: result-handling logic intentionally differs -- `issue-create` is interactive (user prompted via `AskUserQuestion`) while `pr-review` is autonomous (batch processing). Only the search mechanics are synchronized.
- **Decision-comment marker sync**: The `<!-- mach10-decisions -->` HTML marker is used to identify follow-up comments that capture user-driven post-creation decisions. The marker is emitted as a standalone comment by `commands/issue-plan-review.md`. `commands/pr-review.md` conditionally emits the marker (only in Options 1 and 3 of Step 7, and only when at least one deferred item remained after processing; Options 2 and 4 skip it). Two commands use inline variants: `commands/issue-plan.md` embeds decision rationale as an inline `## Decision Log` section within the plan comment instead of a standalone marker, and `commands/issue-assessment.md` has two paths -- on the approve path, comment-bearing actions embed interaction findings as an inline `## Assessment Notes` section within the reply comment (no standalone marker), while the body-only action posts Assessment Notes as a separate follow-up comment (also no standalone marker); on the cancel path, it emits a standalone `<!-- mach10-decisions -->` marker comment. Any change to the marker convention, the Decision Log section convention, or the Assessment Notes section convention must be applied to all four locations.
- **Issue auto-assignment sync**: The assignment logic (assignee check via `gh issue view --json assignees`, current user check via `gh api user`, skip-if-already-assigned condition, `AskUserQuestion` option set for other-assignees case, and graceful failure handling) is duplicated between `commands/issue-plan.md` (Step 7, sub-step 3) and `commands/issue-implement.md` (Step 2, "Assign the issue" section). The sub-issue detection and assignment block (two-strategy detection, per-sub-issue three-path assignment, bulk `AskUserQuestion` for conflicting assignees) immediately follows the parent assignment in both locations: `commands/issue-plan.md` (Step 7, sub-step 4) and `commands/issue-implement.md` (Step 2, "Assign sub-issues" section). The two-strategy sub-issue detection logic (Strategy A: API, Strategy B: body-parse fallback) is also present in `commands/pr-create.md` (Step 2, "Sub-issue detection" block). Any change to the parent or sub-issue assignment logic must be applied to both `issue-plan.md` and `issue-implement.md`; any change to the two-strategy detection logic must also be applied to `pr-create.md`. Note: `issue-implement` includes an additional note that already-assigned is the expected case for subsequent stages. Note: `pr-create.md` Strategy A uses a different jq filter (`{number, state}` instead of `.number`) to retrieve sub-issue state for closed-issue detection; this divergence is intentional and should not be propagated to the assignment commands. Note: `pr-create.md` Strategy B includes an additional candidate-flagging note specific to draft presentation and an additional per-sub-issue state query; these divergences are intentional and should not be propagated to the assignment commands.
- **Finding-identifier sync**: The `F<n>`/`S<n>` finding identifier convention (F for Critical/Important findings, S for Suggestions, numbered globally within each prefix) and the `<findings>` handoff parameter are synchronized across: `commands/pr-review.md` (Step 2 Skill instruction, Step 3 comment format, Step 4 subagent prompt, Step 8 handoff), `commands/pr-review-fix.md` (argument-hint, Step 1 examples/parsing, Step 3 extraction), and `README.md` (command table, phase description, and quick reference). The five "plain words" reminder lines in `pr-review.md` (Steps 3, 5, 7) must also use the updated F/S-permitting wording. Any change to the identifier scheme or parameter name must be applied to all locations.
- **`--comments` two-call sync**: The parenthetical explaining why two `gh` CLI calls are needed (`--comments` returns only comments and silently drops the title and body, so both calls are required) is duplicated across six command files: `commands/pr-create.md` (Step 2), `commands/issue-plan.md` (Step 2), `commands/issue-implement.md` (Step 3), `commands/issue-assessment.md` (Step 2), `commands/issue-plan-review.md` (Step 2), and `commands/doc-review.md` (Step 2). Any change to the parenthetical wording must be applied to all six locations. Note: `doc-review.md` targets PRs (`gh pr view`) while the other five target issues (`gh issue view`); only the parenthetical wording is synchronized.
- **Task-tracking instruction sync**: The instruction `IMPORTANT: After reading the development plan phases, add each phase as a task to your todo list so you do not skip any phases.` is included in the Skill invocation context block in commands that delegate to `/feature-dev:feature-dev`: `commands/issue-implement.md` (Step 4), `commands/pr-review-fix.md` (Step 4), and `commands/pr-ci-fix.md` (Step 4). Any change to the instruction wording must be applied to all three locations. Note: `pr-review` has adopted native `TaskCreate`/`TaskUpdate` tracking (not via Skill invocation instruction). The remaining per-command task tracking PRs (see #81) will rewrite the Skill invocation instruction in the three feature-dev-delegating commands to use explicit `TaskCreate`/`TaskUpdate` tool references; this sync bullet should be updated at that time to reflect the new wording.

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

### Task Tracking

Commands should use `TaskCreate` and `TaskUpdate` to establish visible progress checkpoints. When a command adopts task tracking, include `TaskCreate` and `TaskUpdate` in its `allowed-tools` frontmatter (these are separate from the `Task` tool used for subagent invocation).

- **Step 0 bootstrap**: The first step of every tracked command is Step 0, which parses input and creates the full task list. Step 0's own task is created first and immediately marked `in_progress`. The remaining tasks are then created (all `pending`). After all tasks exist, Step 0 is marked `completed`. If input parsing fails, no tasks are created. Preparatory work that can fail (e.g., checkout) should be a separate step after Step 0 so its failure is visible in the task list.
- **1-to-1 step mapping**: Every command step gets its own task. Do not collapse multiple steps into compound tasks, even if some steps are brief. The task list serves three purposes: it shows the user the full sequence of work (including when input is needed), it builds confidence by making every check visible, and it keeps Claude on track by providing explicit checkpoints that prevent step-skipping in long algorithms.
- **Subject line**: Use `"Step N: <action>"` format in imperative form (e.g., `"Step 3: Post review comment"`). Set `activeForm` for spinner text in present continuous without the step prefix (e.g., `"Posting review comment"`).
- **State transitions**: `in_progress` immediately before starting; `completed` after finishing, before starting the next step. On error, leave `in_progress` -- don't artificially complete.
- **Skill and subagent delegations**: The step that performs the delegation has its own task like any other step. Don't track the delegated skill's or subagent's internal phases from the command level.
- **Delegation phase tracking**: When a step delegates to a skill that follows a multi-phase plan (e.g., `/feature-dev:feature-dev` with its 7-phase development plan), include an instruction in the Skill invocation telling it to create a task for each phase. Phase tasks use a `"Phase N: <action>"` subject convention to distinguish them from the command's `"Step N:"` tasks in the shared flat list. This prevents Claude from skipping phases during long executions. For skills without a defined phase structure (e.g., fan-out/fan-in patterns like `/pr-review-toolkit:review-pr`), phase tracking is optional.
- **Shared context**: Skill-tool calls share the same task list. Don't assume task IDs are sequential -- store the ID returned by `TaskCreate` for later updates.

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
