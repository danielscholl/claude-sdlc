---
description: Meta Prompt for creating git branches
argument-hint: [path-to-spec-file]
allowed-tools: Edit, Write, Read, Bash(git:*), Glob, Grep
---

<git-branch-generation>
  <description>
    Based on the Instructions below, take the Variables follow the Run section to generate a concise Git branch name
    following the specified format. Then follow the Report section to report the results of your work.
  </description>

  <variables>
    <variable name="issue_class">$1</variable>
    <variable name="adw_id">$2</variable>
    <variable name="issue">$3</variable>
  </variables>

  <instructions>
    <format>Generate a branch name in the format: &lt;issue_class&gt;-&lt;issue_number&gt;-&lt;adw_id&gt;-&lt;concise_name&gt;</format>

    <concise-name-rules>
      <rule>3-6 words maximum</rule>
      <rule>All lowercase</rule>
      <rule>Words separated by hyphens</rule>
      <rule>Descriptive of the main task/feature</rule>
      <rule>No special characters except hyphens</rule>
    </concise-name-rules>

    <examples>
      <example>feat-123-a1b2c3d4-add-user-auth</example>
      <example>bug-456-e5f6g7h8-fix-login-error</example>
      <example>chore-789-i9j0k1l2-update-dependencies</example>
    </examples>

    <guideline>Extract the issue number, title, and body from the issue JSON</guideline>
  </instructions>

  <run>
    <step order="1">
      <command>git checkout main</command>
      <purpose>switch to the main branch</purpose>
    </step>
    <step order="2">
      <command>git pull</command>
      <purpose>pull the latest changes from the main branch</purpose>
    </step>
    <step order="3">
      <command>git checkout -b &lt;branch_name&gt;</command>
      <purpose>create and switch to the new branch</purpose>
    </step>
  </run>

  <report>
    <output-format>Return ONLY the branch name that was created (no other text)</output-format>
  </report>
</git-branch-generation>