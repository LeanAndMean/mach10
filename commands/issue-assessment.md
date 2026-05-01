---
description: Read a GitHub issue, perform an independent assessment, and present findings
argument-hint: <issue-number>
allowed-tools: Bash, Read, Grep, Glob, Task, AskUserQuestion
model: opus
---

# Issue Assessment

You are performing an independent assessment of a GitHub issue. Your goal is to deeply understand the issue, explore the relevant codebase, and present your findings with a recommended next step.

**User input:** $ARGUMENTS

## Step 1: Parse Input

The user's input contains:
- An **issue number** (required)

Extract the issue number from the input. If the input is ambiguous, ask the user to clarify.

## Step 2: Read the Issue

Read the issue title and body:

```
gh issue view <issue-number>
```

Then read all comments (`--comments` returns only comments and silently drops the title and body, so both calls are required):

```
gh issue view <issue-number> --comments
```

Parse and understand:
- The problem statement
- Any constraints or requirements mentioned
- Prior discussion or decisions in the comments
- Acceptance criteria (if specified)
- Current state of the issue (open, closed, linked PRs, etc.)

## Step 3: Explore the Codebase

Launch 4 exploration agents in parallel using the Task tool (subagent_type: "feature-dev:code-explorer"). Each agent should trace through the code comprehensively and target a different aspect:

- **Relevant code**: Find existing code related to the issue. Trace through their implementation comprehensively, identifying patterns, conventions, and the design decisions that shaped them.
- **Architecture**: Map the relevant architecture layers, abstractions, and data flow, tracing through the code comprehensively to understand how components interact and where boundaries lie.
- **Prior work**: Check for related branches, PRs, or commits that may already address part of the issue. Trace through any partial implementations to assess their completeness and approach.
- **Counter-evidence**: Look for codebase evidence that challenges the issue's premise or proposed approach. Identify existing patterns, design decisions, or prior solutions that suggest a different approach, reveal the issue may be addressing symptoms rather than root causes, or indicate the problem is a special case of something more general.

Each agent should return a list of 5-10 key files. After agents complete, read all identified files to build deep understanding.

## Step 4: Assess

Based on your understanding of the issue and codebase, present your assessment to the user:

1. **Summary**: What the issue is asking for in your own words.
2. **Current state**: What exists today in the codebase that is relevant.
3. **Gaps**: What is missing, broken, or unclear.
4. **Ambiguities**: Any underspecified aspects, contradictions, or open questions in the issue.
5. **Scope**: Your assessment of the size and complexity of the work.
6. **Risks**: Potential pitfalls, edge cases, or architectural concerns.
7. **Critical evaluation**: Evaluate the issue's premise and proposed approach against codebase evidence and established engineering principles. This category challenges whether the issue is asking for the right thing -- distinct from Ambiguities (underspecified aspects of the issue) and Risks (pitfalls assuming the issue is valid). Challenge only when grounded in evidence or principle -- do not speculate. All claims must be backed by specific references: cite files or patterns for codebase-based challenges; cite established engineering principles or widely-known patterns for principle-based challenges.
   - Whether the codebase suggests a different or better approach than what the issue proposes
   - Whether the proposed change creates redundancy, conflicts, or maintenance burden given existing code
   - Whether the issue addresses symptoms rather than the root cause
   - Whether a more elegant design achieves the same goal with less complexity
   - Whether the problem generalizes beyond the reporter's specific case -- a special case of a broader problem worth solving generally

   If codebase exploration did not surface evidence relevant to evaluating the premise, state that no counter-evidence was found rather than manufacturing concerns. Do not make scheduling or prioritization judgments.

## Step 4a: Track Interaction Findings

From this point forward through Step 6, track any substantive findings that emerge from your interaction with the user. These include:

- **Reframed problems**: The user corrects or reframes the issue's core problem
- **Resolved ambiguities**: Answers to open questions surfaced in Step 4
- **Discovered constraints**: New requirements or limitations that weren't in the issue
- **Shifted root causes**: Evidence that the actual problem differs from what the issue describes
- **Action rationale**: Why the user chose a particular action in Step 5, or why they requested modifications in Step 6

This is a persistent instruction, not a one-time snapshot. Continue tracking through Step 5 (action selection) and Step 6 (drafting, modification loops, and approval). Findings are carried forward to Step 6, where they are included in the content posted to GitHub so they persist for future sessions.

Do not manufacture findings. If the interaction is straightforward and produces no substantive findings beyond what is already captured in the assessment, that is fine -- Step 6 will skip the Assessment Notes section entirely.

## Step 5: Recommend Next Step

Based on your assessment, present your findings and then use `AskUserQuestion` to let the user select the next action:

- **Update issue body**: "The issue description is incomplete or outdated"
- **Post a reply comment**: "The issue body is fine but the assessment adds valuable context"
- **Both**: "Update the issue body and post a separate comment"

Include your recommendation in the assessment text before presenting the choices. If the assessment reveals that the issue should be split into smaller work items or is already resolved, mention these as paths the user can express via the built-in "Other" option.

After the user selects an action, draft the appropriate content:

- **Update issue body**: Draft the updated issue body.
- **Post a reply comment**: Draft the comment.
- **Both**: Draft the updated issue body and the comment.
- **Other**: Handle the user's free-text response (e.g., splitting the issue, closing as resolved, or creating new issues as described).

## Step 6: Execute

Present the drafted content to the user, then use `AskUserQuestion` to ask for approval:

- **Approve**: "Execute the recommended action"
- **Modify**: "Edit the drafted content before executing"
- **Cancel**: "Abort without making changes (a brief audit note will be posted)"

If the user selects "Modify", ask what they want to change, apply the changes, and present the updated draft for approval again.

If the user selects "Cancel":

1. Confirm that no changes were made to the issue.
2. Post a lightweight decision comment on the issue to record that an assessment was conducted:

   ```
   gh issue comment <issue-number> --body "..."
   ```

   Comment format:
   - First line: `<!-- mach10-decisions -->`
   - A note that an independent assessment was performed and the user chose not to act
   - Condensed Summary from Step 4 (2-3 sentences)
   - Condensed Gaps from Step 4 (2-3 sentences)
   - Keep the entire comment body under 15 lines

After the user approves:

If Step 4a produced substantive findings, append an `## Assessment Notes` section to the content before posting. Use freeform format -- a narrative paragraph or tight bullet list, whichever fits the findings naturally. If Step 4a produced no substantive findings, omit the section entirely (do not post an empty or placeholder section).

Path-specific behavior for the Assessment Notes section:

- **"Post a reply comment" or "Both"**: Append `## Assessment Notes` to the reply comment draft.
- **"Update issue body" only**: Do not append Assessment Notes to the issue body -- the issue body is a shared artifact that should contain the problem description, not session-specific interaction history. First execute the body edit, then post a small follow-up comment containing only the `## Assessment Notes` section. Do not include a `<!-- mach10-decisions -->` marker on this comment -- it is primary-path content, not an audit stub.

Execute the action:

- **Update issue body**: `gh issue edit <issue-number> --body "..."`
- **Post comment**: `gh issue comment <issue-number> --body "..."`

When referring to numbered items (findings, suggestions, stages) in any `--body` content, use plain words like "finding 3" or "suggestion 3" -- not `#<number>` notation, which GitHub auto-links to issues/PRs.

Confirm the actions taken and provide links.

**CLI output only (do NOT include in any GitHub comment):** Suggest next step: `/clear` then `/mach10:issue-plan <issue-number>` to create an implementation plan.
