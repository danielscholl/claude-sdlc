---
description: Meta Prompt for creating pull requests
argument-hint: [path-to-spec-file]
allowed-tools: Read, Bash(git:*), Glob, Grep
---

<pull-request-creation>
  <description>
    Based on the Instructions below, take the Variables follow the Run section to create a pull request.
    Then follow the Report section to report the results of your work.
  </description>

  <variables>
    <variable name="branch_name">$1</variable>
    <variable name="issue">$2</variable>
    <variable name="plan_file">$3</variable>
    <variable name="adw_id">$4</variable>
  </variables>

  <instructions>
    <title-format>Generate a pull request title in the format: &lt;issue_type&gt;: #&lt;issue_number&gt; - &lt;issue_title&gt;</title-format>

    <pr-body-requirements>
      <requirement>A summary section with the issue context</requirement>
      <requirement>Link to the implementation plan file</requirement>
      <requirement>Reference to the issue (Closes #&lt;issue_number&gt;)</requirement>
      <requirement>ADW tracking ID</requirement>
      <requirement>A checklist of what was done</requirement>
      <requirement>A summary of key changes made</requirement>
    </pr-body-requirements>

    <guideline>Extract issue number, type, and title from the issue JSON</guideline>

    <title-examples>
      <example>feat: #123 - Add user authentication</example>
      <example>bug: #456 - Fix login validation error</example>
      <example>chore: #789 - Update dependencies</example>
    </title-examples>
  </instructions>

  <run>
    <step order="1">
      <command>git diff origin/main...HEAD --stat</command>
      <purpose>see a summary of changed files</purpose>
    </step>
    <step order="2">
      <command>git log origin/main..HEAD --oneline</command>
      <purpose>see the commits that will be included</purpose>
    </step>
    <step order="3">
      <command>git diff origin/main...HEAD --name-only</command>
      <purpose>get a list of changed files</purpose>
    </step>
    <step order="4">
      <command>git push -u origin &lt;branch_name&gt;</command>
      <purpose>push the branch</purpose>
    </step>
    <step order="5">
      <command>gh pr create --title "&lt;pr_title&gt;" --body "&lt;pr_body&gt;" --base main</command>
      <purpose>create the PR</purpose>
      <prerequisite>Set GH_TOKEN environment variable from GITHUB_PAT if available</prerequisite>
    </step>
    <step order="6">
      <action>Capture the PR URL from the output</action>
    </step>
  </run>

  <report>
    <output-format>Return ONLY the PR URL that was created (no other text)</output-format>
  </report>
</pull-request-creation>
