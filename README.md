<div align="center">
  <img src="docs/logo.png" alt="Mach 10 Logo" width="50%">
</div>

# Mach 10

A development methodology for agentic coding -- and a Claude Code plugin that implements it.

## What is Mach 10?

In agentic coding, the AI is not an autocomplete engine -- it is an active collaborator that writes code, reviews it, manages GitHub issues and PRs, runs tests, and documents its work. The human's role shifts from writing code to directing, aligning, and reviewing. You describe requirements, approve architectural decisions, and steer direction. The AI handles the searching, writing, testing, and bookkeeping.

This changes the failure mode. The bottleneck is no longer typing speed or syntax recall -- it is context management. LLM context windows are finite. A deep code review can consume most of the available context, leaving little room for implementation. Multi-session feature development requires persistent memory across sessions. And without a structured workflow, agentic coding produces inconsistent results: missed edge cases, orphaned TODOs, reviews that never converge.

Mach 10 is a methodology that addresses these constraints directly: fresh sessions for each step, GitHub as persistent memory, staged implementation, and iterative review-fix cycles. This repository contains a Claude Code plugin that codifies the methodology into 15 slash commands, but the methodology stands on its own -- you can follow it manually with any agentic coding tool.

Because the methodology builds entirely on standard developer practices -- issues, PRs, comments, feature branches, frequent commits -- there is no vendor lock-in. Every artifact Mach 10 produces is a normal GitHub artifact. If you stop using the plugin, you're left with well-documented issues, structured PRs, and a clean commit history. Nothing is stored in a proprietary format or locked behind a tool-specific layer.

## The methodology

### Your role as the human

You are directing, not spectating. The AI handles the mechanical work -- searching, writing, testing, documenting -- but you own the decisions:

- **Push back on designs.** When the AI presents a plan, you don't have to accept it. Ask *why* it chose a particular approach. Ask it to present alternatives. If the architecture doesn't feel right, say so -- before implementation is the cheapest place to catch mistakes.
- **Don't guess when the AI asks questions.** When it presents clarifying questions with options, ask it to explain the tradeoffs of each option rather than picking one blindly. You have a collaborator that can reason about the implications -- use it.
- **Review plans, not just code.** Plans can be reviewed by AI agents just like code can. Catching a design flaw before implementation saves far more effort than catching it in code review.
- **GitHub is the shared medium.** Plans, assessments, and reviews are posted as GitHub comments. Any future session -- yours or a teammate's -- can read and build on prior work. The persistence layer is GitHub, not your local machine.

### GitHub as shared memory

Each CLI session starts with a fresh context window. Multi-session feature development requires persistent memory. Rather than maintaining bespoke planning documents on disk, the methodology uses GitHub's existing infrastructure -- issues, PRs, and comments -- as the inter-session communication layer:

- **Issues** capture requirements, analysis, and staged implementation plans.
- **PR descriptions** summarize what was built.
- **PR comments** carry reviews, fix documentation, and design discussions.

Everything persists across sessions and is accessible via `gh`. When a new session starts, it reads the relevant issue or PR and has full context without any filesystem state or memory.

### Fresh sessions for every step

LLM context windows are finite. A deep code review can consume most of the available context, leaving little room for implementation. If you try to review and fix in the same session, the fixes suffer from a starved context budget.

The methodology is designed around this constraint:

- **Planning** explores the codebase and persists its plan as a GitHub comment before the context fills up.
- **Review** posts its findings as a PR comment and does not fix anything.
- **Fixing** starts fresh with the full context budget available for implementation.
- **Implementation** runs one stage per session so each stage gets full context depth.

### Staged implementation

Large features are broken into numbered stages during the planning step. Each stage is implemented in its own session. This significantly improves one-shot success rates compared to attempting an entire feature in a single session -- each stage gets full context depth for codebase exploration, architecture design, implementation, and quality review.

### Iterative review-fix cycles

Code review is not a single pass. The methodology uses an iterative cycle:

1. **Review + Assess** -- Run specialized review agents in parallel (code quality, test coverage, error handling, type design, comment accuracy, complexity). Post findings as a PR comment. Then independently assess each finding, classifying it as genuine, nitpick, false positive, or deferred. The assessment is the convergence signal.
2. **Fix** -- In a new session, read the review comment and fix the genuine issues. Batch size depends on complexity: ~10 simple fixes, ~6 moderate, ~3 complex.
3. **Re-review** -- Run the review suite again. Each review includes a fresh assessment.

This continues until the assessment shows no genuine issues remaining.

## The workflow

The methodology in action across a feature's lifecycle. Each step below runs in a **fresh CLI session**. GitHub comments carry context between sessions -- no filesystem state or memory is required. This also means other team members' sessions can pick up where yours left off by reading the same issue or PR.

```
                     ┌───────────┐
                     │  Create   │
                     │   Issue   │
                     └─────┬─────┘
                           │
                         Issue
                           │
                     ┌─────▼─────┐
                     │  Assess   │
                     └─────┬─────┘
                           │
                     ┌─────▼─────┐
                     │   Plan    │
                     └─────┬─────┘
                           │
                     ┌─────▼─────┐
                     │  Review   │
                     │   Plan    │
                     └─────┬─────┘
                           │
            ┌──────────────┴──────────────┐
            │      for each stage:        │
            │                             │
            │   ┌─────────────────────┐   │
            │   │  Implement → Push   │───┤
            │   └─────────────────────┘   │
            └──────────────┬──────────────┘
                           │
                     ┌─────▼─────┐
                     │  Create   │
                     │    PR     │
                     └─────┬─────┘
                           │
            ┌──────────────┴──────────────┐
            │   until no genuine issues:  │
            │                             │
            │   ┌─────────────────────┐   │
            │   │ Review → Fix → Push │───┤
            │   └─────────────────────┘   │
            └──────────────┬──────────────┘
                           │
                     ┌─────▼─────┐
                     │Doc Review │
                     └─────┬─────┘
                           │
                     ┌─────▼─────┐
                     │ Pre-merge │
                     └─────┬─────┘
                           │
                     ┌─────▼─────┐
                     │   Merge   │
                     └───────────┘
```

### Phase 0: Create the issue

**Command:** `/mach10:issue-create`

When no issue exists yet, start here. Claude helps you draft a structured GitHub issue from a description of the problem or feature you have in mind. The command walks you through title, body, and labels, then creates the issue. If you already have an issue, skip directly to Phase 1.

**Your role:** Provide the context -- what needs to be built or fixed and why. Review the drafted issue before it's created to make sure scope and requirements are right.

### Phase 1: Understand the issue

**Command:** `/mach10:issue-assessment <number>`

Claude reads the issue, explores the relevant parts of the codebase, and presents its findings -- scope, risks, ambiguities, and a recommended next step.

**Your role:** Read the assessment critically. Push back if the scope is wrong, if risks are missed, or if important ambiguities aren't surfaced. The assessment is posted as a GitHub comment, so it becomes shared context for every future session on this issue.

### Phase 2: Plan the implementation

**Command:** `/mach10:issue-plan <number>`

Claude explores the codebase, asks clarifying questions about underspecified requirements, then presents multiple architecture approaches (minimal changes, clean architecture, pragmatic balance) for you to choose from before drafting a staged implementation plan. The plan is posted as a GitHub comment, and a feature branch is created. If the project has a `CONTRIBUTING.md` (or `DEVELOPMENT.md` / `.github/CONTRIBUTING.md`), the plan incorporates its guidance on project layers and testing expectations (see [Customizing with CONTRIBUTING.md](#customizing-with-contributingmd) below).

The plan is *staged* because each stage will get its own session with a full context budget. Trying to implement everything at once starves later work of context depth. The plan is *posted to GitHub* so that any future session -- yours or a teammate's -- can read it and pick up the work.

**Your role:** This is the most important moment to invest your attention. The command will present clarifying questions and architecture alternatives automatically -- answer the questions thoughtfully rather than deferring, and evaluate the architecture options carefully before choosing. Before approving the final plan:
- Scrutinize the selected architecture. Ask Claude to explain trade-offs if the choice isn't clear.
- Push back on anything that doesn't feel right. This is the cheapest point to catch bad design decisions -- before any code is written.

### Phase 3: Review the plan

**Command:** `/mach10:issue-plan-review <number>`

A fresh Claude session independently reviews the plan against the codebase. If the project has contributing guidelines, the review checks the plan against their requirements for layer coverage and testing. Plans can be reviewed just like code -- this is a second pair of eyes on the architecture before implementation begins.

**Your role:** Read both the plan and the review. If the review raises valid concerns, direct Claude to revise the plan. You can iterate on plan-review cycles until the design is solid.

### Phase 4: Implement stage by stage

**Commands:** `/mach10:issue-implement <issue> <stage>` then `/mach10:push` (one session per stage)

Each stage is implemented in its own fresh session, then committed and pushed with a progress comment on the issue. One stage per session means full context budget for codebase exploration, implementation, and testing.

**Your role:** Review each stage's output before moving to the next. If something deviates from the plan or introduces problems, raise it now rather than letting it compound.

### Phase 5: Create a PR

**Command:** `/mach10:pr-create [issue]`

Create a PR linking back to the issue with a structured description summarizing what was built.

### Phase 6: Review-fix cycle

**Commands:** `/mach10:pr-review <pr>`, `/mach10:pr-review-fix <pr> [findings]`, `/mach10:pr-ci-fix <pr>`

This is an iterative cycle: review in one session, fix in the next, re-review, repeat. Each review posts its findings as a PR comment, then independently assesses every finding to classify it as genuine, nitpick, false positive, or deferred. The assessment includes a staged implementation plan that groups genuine issues into required stages and nitpicks into optional stages, giving you a ready-made fix list for the next session. The assessment serves as the convergence signal -- when all remaining findings are nitpicks or false positives, the PR is ready to merge.

If CI fails after a fix, use `pr-ci-fix` to diagnose and resolve the failure.

**Your role:** Read the assessment after each review. Direct which genuine issues to fix and which deferred items to track as new issues. The assessment does the triage for you, but you make the final call.

### Phase 7: Merge

**Commands:** `/mach10:doc-review <pr>` (optional), `/mach10:pr-pre-merge <pr>`, `/mach10:pr-merge <pr>`

Once the review-fix cycle converges (the assessment shows no genuine issues remaining), optionally run a deep documentation review with `doc-review`, run the pre-merge checklist (branch freshness, docs, version, CHANGELOG, tests), and merge.

### Quick reference

Once you're familiar with the phases above, this session log serves as a cheat sheet:

```
Session 0:  /mach10:issue-create            (when no issue exists yet)
Session 1:  /mach10:issue-assessment 55
Session 2:  /mach10:issue-plan 55
Session 3:  /mach10:issue-plan-review 55
Session 4:  /mach10:issue-implement 55 1
            /mach10:push
Session 5:  /mach10:issue-implement 55 2
            /mach10:push
Session 6:  /mach10:pr-create 55
Session 7:  /mach10:pr-review 108
Session 8:  /mach10:pr-review-fix 108 F1 F2 F3
            /mach10:push
Session 9:  /mach10:pr-review 108
Session 10: /mach10:pr-ci-fix 108
            /mach10:push
Session 11: /mach10:pr-review 108             (converges when assessment shows no genuine issues)
Session 12: /mach10:doc-review 108            (optional)
Session 13: /mach10:pr-pre-merge 108
Session 14: /mach10:pr-merge 108
```

## The plugin

### Prerequisites and installation

**Requirements:**

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)
- [feature-dev](https://github.com/anthropics/claude-code-plugins) plugin (required by `/issue-plan`, `/issue-implement`, `/pr-review-fix`, `/pr-ci-fix`)
- [pr-review-toolkit](https://github.com/anthropics/claude-code-plugins) plugin (required by `/pr-review`)
- `gh` CLI authenticated with your GitHub account

**From the CLI:**

1. Start Claude Code: `claude`
2. Register the repository as a marketplace: `/plugin marketplace add LeanAndMean/mach10`
3. Install the plugin: `/plugin install mach10@LeanAndMean-mach10`

You can also use the interactive plugin manager (`/plugin`) and browse the **Discover** tab after adding the marketplace.

**Manual:**

```bash
claude --plugin-dir /path/to/mach10
```

### Commands

#### Issue lifecycle

| Command | Description |
|---------|-------------|
| `/mach10:issue-assessment <number>` | Read issue, perform independent assessment, and present findings with recommended next step |
| `/mach10:issue-plan <number>` | Read issue, explore codebase, ask clarifying questions, design architecture with user, create staged implementation plan, post as comment, create feature branch |
| `/mach10:issue-plan-review <number>` | Read issue and all comments, review the implementation plan, and present findings |
| `/mach10:issue-implement <issue> <stage>` | Implement a specific stage of the plan via feature-dev |
| `/mach10:issue-create` | Create a structured GitHub issue from current context |

#### PR lifecycle

| Command | Description |
|---------|-------------|
| `/mach10:pr-create [issue] [context]` | Create a PR for the current branch with structured description |
| `/mach10:pr-review <pr> [aspects]` | Run comprehensive PR review, post results, then independently assess each finding |
| `/mach10:pr-review-fix <pr> [findings]` | Fix specific review findings via feature-dev |
| `/mach10:pr-ci-fix <pr> [context]` | Diagnose and fix failing CI checks via feature-dev |
| `/mach10:pr-review-validate <pr>` | Standalone: independently assess review findings without re-running the review |
| `/mach10:doc-review <pr> [scope]` | Review and update documentation based on PR changes |
| `/mach10:pr-pre-merge <pr>` | Run pre-merge checklist (branch freshness, docs, version, CHANGELOG, tests) |
| `/mach10:pr-merge <pr>` | Merge PR, delete branch, optionally create release |

#### Utilities

| Command | Description |
|---------|-------------|
| `/mach10:push` | Commit, push, and post progress comment on the associated PR/issue |
| `/mach10:test-audit` | Fan out subagents to audit test quality across the repo |

### Design principles

- **Thin orchestration layer**: Commands gather context and delegate to existing plugins (feature-dev, pr-review-toolkit) rather than reimplementing workflows.
- **GitHub as source of truth**: Plans, reviews, and progress are posted as issue/PR comments so future sessions can pick up where previous ones left off.
- **Context-window aware**: Review and fix are separate commands to preserve context budget for implementation. Each review includes an independent assessment of its own findings.

### Repository structure

```
.claude-plugin/plugin.json   # Plugin manifest (name, version, author)
agents/                       # Specialized agent definitions (markdown with YAML frontmatter)
commands/                     # Slash command definitions (markdown with YAML frontmatter)
```

### Customizing with CONTRIBUTING.md

Several commands consult your project's contributing guidelines to tailor their behavior. Place a `CONTRIBUTING.md` at the repository root (or `DEVELOPMENT.md`, or `.github/CONTRIBUTING.md`) and the following commands will incorporate its guidance:

- **`issue-plan`** -- Cross-checks project layers discovered during codebase exploration against any layers specified in the contributing guide (e.g., models, migrations, API routes, services, UI, documentation) to ensure the plan covers all affected layers. Uses testing expectations (frameworks, coverage requirements, test types) to include appropriate test planning in each stage.
- **`issue-plan-review`** -- Checks the plan against the same layer and testing requirements, flagging gaps in coverage.
- **`pr-pre-merge`** -- Reads pre-merge requirements (version bumps, changelog entries, documentation updates, test requirements) from the guide.

Projects without a contributing guide work fine -- the planning commands (`issue-plan`, `issue-plan-review`) proceed using discovery-based defaults from codebase exploration, and `pr-pre-merge` falls back to its built-in checklist. The contributing guide simply lets you codify project-specific expectations so they are applied consistently across sessions and contributors.
