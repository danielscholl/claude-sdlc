---
description: Meta Prompt for locating plans
argument-hint: [path-to-spec-file]
allowed-tools: Read, Glob, Grep
---

<locate-plan-file>
  <description>
    Based on the Previous Step Output below, follow the Instructions to find the path to the plan file that was just created.
  </description>

  <instructions>
    <guideline>The previous step created a plan file. Find the exact file path.</guideline>

    <approaches>
      <approach>Check git status for new untracked files</approach>
      <approach>Use `git diff --stat origin/main...HEAD specs/` to see new files in specs directory compared to origin/main</approach>
      <approach>Use `git diff --name-only origin/main...HEAD specs/` to list only the file names</approach>
      <approach>Look for recently created .md files in the specs directory</approach>
      <approach>Parse the previous output which should mention where the plan was saved</approach>
    </approaches>

    <output-rules>
      <rule>Return ONLY the file path (e.g., "specs/example-plan.md") or "0" if not found</rule>
      <rule>Do not include any explanation, just the path or "0" if not found</rule>
    </output-rules>
  </instructions>

  <previous-step-output>
    <content>$ARGUMENTS</content>
  </previous-step-output>
</locate-plan-file>