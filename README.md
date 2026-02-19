# Mach 10

A Claude Code plugin that codifies a structured agentic development workflow into single-invocation commands.

## What it does

mach10 wraps the repeated multi-step patterns of a GitHub-issue-driven development lifecycle into 14 slash commands. Each command handles context gathering, delegation, and documentation automatically.

## Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)
- [feature-dev](https://github.com/anthropics/claude-code-plugins) plugin (required by `/issue-implement`, `/pr-review-fix`)
- [pr-review-toolkit](https://github.com/anthropics/claude-code-plugins) plugin (required by `/pr-review`)
- `gh` CLI authenticated with your GitHub account

## Installation

### From the CLI menu

1. Start Claude Code: `claude`
2. Type `/plugins`
3. Select **Add plugin...**
4. Choose **From GitHub URL**
5. Enter: `https://github.com/merckgroup/mach10`

### Manual

```bash
claude --plugin-dir /path/to/mach10
```

## Commands

### Workflow (in typical order)

| Command | Description |
|---------|-------------|
| `/mach10:issue-assessment <number>` | Read issue, perform independent assessment, and present findings with recommended next step |
| `/mach10:issue-plan <number>` | Read issue, explore codebase, create staged implementation plan, post as comment, create feature branch |
| `/mach10:issue-review-plan <number>` | Read issue and all comments, review the implementation plan, and present findings |
| `/mach10:issue-implement <issue> <stage>` | Implement a specific stage of the plan via feature-dev |
| `/mach10:push` | Commit, push, and post progress comment on the associated PR/issue |
| `/mach10:pr-create [issue] [context]` | Create a PR for the current branch with structured description |
| `/mach10:pr-review <pr> [aspects]` | Run comprehensive PR review and post results as comment |
| `/mach10:pr-review-fix <pr> [issues]` | Fix specific review findings via feature-dev |
| `/mach10:pr-ci-fix <pr> [context]` | Diagnose and fix failing CI checks via feature-dev |
| `/mach10:pr-review-validate <pr>` | Independently assess remaining findings (genuine vs. nitpick vs. false positive) |
| `/mach10:pr-pre-merge <pr>` | Run pre-merge checklist (docs, version, CHANGELOG, tests) |
| `/mach10:pr-merge <pr>` | Merge PR, delete branch, optionally create release |

### Utilities

| Command | Description |
|---------|-------------|
| `/mach10:issue-create` | Create a structured GitHub issue from current context |
| `/mach10:test-audit` | Fan out subagents to audit test quality across the repo |

## Workflow

```
  GitHub Issue #55                        main
  +-----------------+                       |
  | Problem         |    issue-plan         |
  | description     |---+                   |
  +-----------------+   |                   |
                        v                   |
         Plan posted    o--- feature/issue-55-fix-analytics
         as comment     |
                        |   issue-implement 55 1
                        |   push
                        o   Stage 1
                        |
                        |   issue-implement 55 2
                        |   push
                        o   Stage 2
                        |
                        |   issue-implement 55 N
                        |   push
                        o   Stage N
                        |
            PR #108 <---+   (create PR)
                        |
               +--------+--------+
               |  Review cycle   |
               |                 |
               |   pr-review 108 |
               |   pr-review-fix |
               |   push          |
               |        :        |  repeat until
               |   pr-review 108 |  clean
               |   pr-review-fix |
               |   push          |
               |                 |
               |   [CI fails?]   |
               |   pr-ci-fix 108 |
               |   push          |
               +--------+--------+
                        |
                        |   pr-review-validate 108
                        o   Triage remaining findings
                        |
                        |   pr-pre-merge 108
                        o   Docs, version, CHANGELOG, tests
                        |
                        |   pr-merge 108
          main <--------+   Merge + delete branch + release
            |
            v
```

Each box is a **fresh CLI session**. GitHub comments carry context
between sessions so no filesystem state or memory is required.

### Typical session log

```
Session 1:  /mach10:issue-plan 55
Session 2:  /mach10:issue-implement 55 1    then  /mach10:push
Session 3:  /mach10:issue-implement 55 2    then  /mach10:push
Session 4:  /mach10:pr-review 108
Session 5:  /mach10:pr-review-fix 108 1,2,3  then  /mach10:push
Session 6:  /mach10:pr-review 108
Session 7:  /mach10:pr-ci-fix 108              then  /mach10:push
Session 8:  /mach10:pr-review-validate 108
Session 9:  /mach10:pr-pre-merge 108
Session 10: /mach10:pr-merge 108
```

## The methodology behind mach10

mach10 encodes a specific agentic development methodology. Understanding the philosophy behind it helps you get the most out of the plugin.

### The core idea

In agentic coding, the AI is not an autocomplete engine — it is an active collaborator that writes code, reviews it, manages GitHub issues and PRs, runs tests, and documents its work. The human's role shifts from writing code to **directing, aligning, and reviewing**. You describe requirements, approve architectural decisions, and steer direction. The AI does the typing, searching, testing, and bookkeeping.

### Why GitHub is the backbone

Each Claude Code CLI session starts with a fresh context window. Multi-session feature development requires persistent memory. Rather than maintaining bespoke planning documents on disk, this workflow uses **GitHub's existing infrastructure** — Issues, PRs, and comments — as the inter-session communication layer:

- **Issues** capture requirements, analysis, and staged implementation plans.
- **PR descriptions** summarize what was built.
- **PR comments** carry reviews, fix documentation, and design discussions.

All of it persists across sessions and is accessible via `gh`. When a new session starts, it reads the relevant issue or PR and has full context without any filesystem state or memory.

### Why fresh sessions for every step

LLM context windows are finite. A deep code review can consume most of the available context, leaving little room for implementation. If you try to review and fix in the same session, the fixes suffer from a starved context budget.

mach10 is designed around this constraint:

- **issue-plan** explores the codebase and persists its plan as a GitHub comment before the context fills up.
- **pr-review** posts its findings as a PR comment and explicitly does not fix anything.
- **pr-review-fix** starts fresh with the full context budget available for implementation.
- **issue-implement** runs one stage per session so each stage gets full context depth.

### Staged implementation

Large features are broken into numbered stages during the analysis step. Each stage is implemented in its own session via `/mach10:issue-implement`. This significantly improves one-shot success rates compared to attempting an entire feature in a single session — each stage gets full context depth for codebase exploration, architecture design, implementation, and quality review.

### The review-fix cycle

Code review is not a single pass. mach10 uses an iterative cycle:

1. **Review** — Run 6 specialized agents in parallel (code quality, test coverage, error handling, type design, comment accuracy, complexity). Post findings as a PR comment.
2. **Fix** — In a new session, read the review comment and fix a batch of issues. Batch size depends on complexity: ~10 simple fixes, ~6 moderate, ~3 complex.
3. **Re-review** — Run the review suite again. If issues remain, repeat.
4. **Validate** — When the review converges to mostly nitpicks, independently assess each remaining finding. Classify as genuine, nitpick, false positive, or deferred. Post an audit comment documenting why certain items are not being addressed.

This continues until the PR is clean enough for human review, with confidence that it won't waste a colleague's time with unresolved issues.

### Context-window-aware batch sizing

Not all review findings are equal. A typo fix takes one line; a design flaw may require rearchitecting a module. The pr-review-fix command recommends batch sizes:

- **Simple one-line fixes**: up to ~10 at once
- **Moderate fixes**: ~6 at a time
- **Deep or complex fixes**: no more than ~3 at a time

Similar issues are grouped together. Out-of-scope problems are deferred to new GitHub issues rather than addressed inline.

### Safe by default

The methodology prioritizes safety:

- No `git add -A` or `git add .` — files are staged by name.
- No staging of secrets files (.env, credentials, etc.).
- No force-pushes, no force-merges.
- Merge uses the repository's default strategy.
- Branch deletion uses the safe `-d` flag (refuses to delete unmerged branches).
- Claude never pushes to remote unless explicitly told to.

## Design principles

- **Thin orchestration layer**: Commands gather context and delegate to existing plugins (feature-dev, pr-review-toolkit) rather than reimplementing workflows.
- **GitHub as source of truth**: Plans, reviews, and progress are posted as issue/PR comments so future sessions can pick up where previous ones left off.
- **Context-window aware**: Review and fix are deliberately separate commands because reviews consume most of the context budget.
- **Safe by default**: No force-pushes, no `git add -A`, no staging of secrets files, no force-merges.
