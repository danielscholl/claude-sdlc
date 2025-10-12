---
description: Meta Prompt for making commits
argument-hint: [path-to-spec-file]
allowed-tools: Edit, Write, Read, Bash(git:*), Glob, Grep
---

<git-commit-creation>
  <description>
    Based on the Instructions below, take the Variables and follow the Run section to create a git commit
    with a properly formatted message. Then follow the Report section to report the results of your work.
  </description>

  <variables>
    <variable name="agent_name">$1</variable>
    <variable name="issue_class">$2</variable>
    <variable name="issue">$3</variable>
  </variables>

  <instructions>
    <format>Generate a commit message in the format: &lt;agent_name&gt;: &lt;issue_class&gt;: &lt;commit_message&gt;</format>

    <commit-message-rules>
      <rule>Use present tense (e.g., "add", "fix", "update", not "added", "fixed", "updated")</rule>
      <rule>Maximum 50 characters for the main message</rule>
      <rule>Be descriptive of the actual changes made</rule>
      <rule>No period at the end</rule>
      <rule>Extract context from the issue JSON to make the message relevant</rule>
    </commit-message-rules>

    <examples>
      <example>sdlc_planner: feat: add user authentication module</example>
      <example>sdlc_implementor: bug: fix login validation error</example>
      <example>sdlc_planner: chore: update dependencies to latest versions</example>
    </examples>

    <guideline>Analyze the git diff to understand what changes were made and create an accurate commit message</guideline>
  </instructions>

  <run>
    <step order="1">
      <command>git diff HEAD</command>
      <purpose>understand what changes have been made</purpose>
    </step>
    <step order="2">
      <command>git add -A</command>
      <purpose>stage all changes</purpose>
    </step>
    <step order="3">
      <command>git commit -m "&lt;generated_commit_message&gt;"</command>
      <purpose>create the commit with the formatted message</purpose>
    </step>
  </run>

  <report>
    <output-format>Return ONLY the commit message that was used (no other text)</output-format>
  </report>
</git-commit-creation>