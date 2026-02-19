---
description: Diagnose and fix failing CI checks on a pull request
argument-hint: <pr-number> [context]
allowed-tools: Bash, Read, Grep, Glob, Task, Edit, Write, Skill
model: opus
---

# Fix CI Failures

You are diagnosing and fixing failing CI checks on a pull request. This command fetches CI failure details from GitHub, then delegates to the feature-dev workflow for root cause analysis and implementation of fixes.

**User input:** $ARGUMENTS

## Step 1: Parse Input

The user's input typically contains:
- A **PR number** (required)
- Additional context about which checks to focus on (optional)

Example inputs:
- `108`
- `108 only the linting failure`
- `108 ignore the coverage check, focus on the unit test failures`

Extract the PR number. If the user provided context about which checks to focus on, note it for Step 3. If the input is ambiguous, ask the user to clarify.

## Step 2: Checkout PR Branch

Ensure you are on the correct branch:

```
gh pr checkout <pr-number>
git pull
```

## Step 3: Gather CI Failure Details

This is the key step -- fetch CI check status and failure logs.

**List all checks:**

```
gh pr checks <pr-number>
```

If all checks are passing, report this to the user and stop. Suggest re-running `/mach10:pr-review <pr-number>` or `/mach10:pr-pre-merge <pr-number>` as the next step instead.

**For each failed check**, get the run ID and fetch the failed logs:

```
gh run view <run-id> --log-failed
```

If the user provided context about which checks to focus on, filter to only the relevant failed checks. Otherwise, gather logs for all failed checks.

If the logs are very large, extract the most relevant sections:
- Test names and assertion failures
- Stack traces
- Error messages and exit codes
- The last ~100 lines of each failed step

**Get PR context** so the fix session understands what the PR is about:

```
gh pr view <pr-number>
```

## Step 4: Delegate to Feature Dev

Use the Skill tool to invoke `/feature-dev:feature-dev` with the following context:

> This PR (#<pr-number>) has failing CI checks. Here are the failure details:
>
> <include the CI failure logs and error messages gathered in Step 3>
>
> Perform a root cause analysis of these CI failures, then implement fixes using the 7-phase development plan. IMPORTANT: After reading the development plan phases, add each phase as a task to your todo list so you do not skip any phases.

## Step 5: After Fixes

Once fixes are complete, suggest the following workflow:

1. Run `/mach10:push` to commit and push the fixes.
2. `/clear`, then monitor CI on the PR. If CI fails again, re-run `/mach10:pr-ci-fix <pr-number>`.
3. Once CI passes, `/clear` then `/mach10:pr-pre-merge <pr-number>`.

## Important Notes

- Each CI fix session should be **fresh** to maximize available context.
- If a CI failure is caused by a flaky test or infrastructure issue (not a code problem), report this to the user rather than attempting a code fix.
- If fixing the CI failure would require significant changes unrelated to the PR's purpose, recommend creating a separate issue with `/mach10:issue-create`.
