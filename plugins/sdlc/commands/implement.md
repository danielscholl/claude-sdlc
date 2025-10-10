---
description: Meta Prompt for implementing detailed plans.
argument-hint: [path-to-spec-file]
allowed-tools: Edit, Write, Read, Bash(git*), Glob, Grep
---

<plan-implementation>
  <description>
    Follow the Instructions to implement the Plan then Report the completed work.
  </description>

  <instructions>
    <guideline>Read the plan, ultrathink about the plan and implement the plan.</guideline>
  </instructions>

  <plan>
    <content>$ARGUMENTS</content>
  </plan>

  <report>
    <requirement>Summarize the work you've just done in a concise bullet point list.</requirement>
    <requirement>
      <command>git diff --stat</command>
      <purpose>Report the files and total lines changed</purpose>
    </requirement>
  </report>
</plan-implementation>
