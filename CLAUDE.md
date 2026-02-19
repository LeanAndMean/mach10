# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

mach10 defines a structured development methodology for agentic coding and provides a Claude Code plugin that implements it. The methodology centers on fresh sessions for each step, GitHub as the inter-session persistence layer, staged implementation, and iterative review-fix cycles. The plugin codifies this into 15 slash commands covering the complete issue-to-merge lifecycle.

## Architecture

This is a pure plugin definition -- no build system, no runtime, no tests. Claude Code reads the command files directly.

```
.claude-plugin/plugin.json   # Plugin manifest (name, version, author)
commands/                     # 15 slash command definitions (markdown with YAML frontmatter)
```

Each command file is a self-contained workflow specification with:
- **YAML frontmatter**: `description`, `argument-hint`, `allowed-tools`, `model`
- **Markdown body**: Step-by-step instructions Claude Code follows when the command is invoked

## Command Structure

**Issue workflow:** `issue-assessment`, `issue-plan`, `issue-review-plan`, `issue-implement`, `issue-create`
**PR workflow:** `pr-create`, `pr-review`, `pr-review-fix`, `pr-ci-fix`, `pr-review-validate`, `doc-review`, `pr-pre-merge`, `pr-merge`
**Utilities:** `push`, `test-audit`

## Key Design Decisions

- **Thin orchestration**: Commands gather context and delegate to `feature-dev` and `pr-review-toolkit` plugins via the Skill tool rather than reimplementing workflows.
- **Single-concern sessions**: Review and fix are separate commands to preserve context budget for implementation. Each command is designed to run in a fresh CLI session.
- **GitHub as backbone**: Plans, reviews, and progress are posted as issue/PR comments so context persists across sessions.
- **Safe defaults**: No `git add -A`, no staging of secrets, no force-pushes, branch deletion uses `-d` flag.

## Plugin Dependencies

- `gh` CLI (GitHub authentication required)
- `feature-dev` plugin (used by `issue-implement`, `pr-review-fix`, `pr-ci-fix`)
- `pr-review-toolkit` plugin (used by `pr-review`)

## Writing Commands

When adding or modifying commands, follow the existing pattern:
- YAML frontmatter must include `description` and `argument-hint`
- Set `allowed-tools` to the minimum set needed (principle of least privilege)
- Set `model: opus` for commands requiring deep reasoning (reviews, planning, implementation)
- End commands with a "next step" suggestion that includes `/clear` guidance for session boundaries
- Use `gh` CLI for all GitHub operations (issues, PRs, comments, CI logs)
- Commands that modify code delegate to `/feature-dev:feature-dev` via the Skill tool
- Commands that review code delegate to `/pr-review-toolkit:review-pr` via the Skill tool

## Working in This Repo

- Proactively load any plugin development skills you think might be relevant when modifying or reviewing files in this repo.
