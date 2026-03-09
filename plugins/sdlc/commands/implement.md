---
description: Implement a feature specification with structured task tracking
argument-hint: [spec-file-path]
allowed-tools: Edit, Write, Read, Bash, Glob, Grep, Task, TodoWrite
---

<implement-command>
  <objective>
    Execute a comprehensive feature specification with structured task tracking throughout the entire development process.
  </objective>

  <requirements>
    <mandatory>Track task progress using TodoWrite throughout execution</mandatory>
    <mandatory>Only work on ONE task at a time</mandatory>
    <mandatory>Validate all work before marking tasks as complete</mandatory>
  </requirements>

  <documentation-structure>
    <directory path=".claude/specs/">Feature implementation specifications</directory>
    <directory path="docs/decisions/">Architecture Decision Records (ADRs)</directory>
    <directory path="docs/design/">Requirements and design documents</directory>
  </documentation-structure>

  <phase number="1" name="read-spec">
    <action>Read specification file from: $ARGUMENTS</action>
    <extract>
      <item>Task list for implementation</item>
      <item>Codebase integration points</item>
      <item>Related documentation references</item>
      <item>Codebase analysis findings</item>
      <item>Testing strategy</item>
      <item>Acceptance criteria</item>
    </extract>
  </phase>

  <phase number="2" name="create-tasks">
    <action>Create ALL tasks in TodoWrite upfront from the spec</action>
    <for-each task="in spec">
      <create>Add task with description and phase tag (Foundation/Core/Integration)</create>
    </for-each>
    <important>Ensures complete visibility of work scope before starting</important>
  </phase>

  <phase number="3" name="codebase-analysis">
    <action>Review codebase analysis findings from spec</action>
    <action>Verify patterns with Grep and Glob tools</action>
    <action>Read all referenced files and components</action>
    <action>Review related ADRs and requirements</action>
    <action>Build comprehensive understanding of context</action>
  </phase>

  <phase number="4" name="implementation-cycle">
    <for-each task="in sequence">
      <step name="start-task">
        <action>Mark current task as in-progress in TodoWrite</action>
      </step>

      <step name="implement">
        <follow>Task requirements from spec</follow>
        <follow>Codebase patterns and conventions</follow>
        <follow>Related ADRs and requirements</follow>
        <ensure>Code quality and consistency</ensure>
      </step>

      <step name="complete-task">
        <action>Mark task as complete in TodoWrite</action>
        <note>Verify implementation before marking complete</note>
      </step>
    </for-each>
    <critical>Only work on ONE task at a time</critical>
  </phase>

  <phase number="5" name="validation">
    <step name="launch-validator" importance="critical">
      <action>Launch validator agent using Task tool</action>
      <provide>
        <item>Detailed description of what was built</item>
        <item>List of features and files modified</item>
        <item>Testing strategy from spec</item>
      </provide>
      <validator-will>
        <item>Create focused unit tests</item>
        <item>Test edge cases and error handling</item>
        <item>Run tests using project framework</item>
        <item>Report results and issues</item>
      </validator-will>
    </step>

    <step name="additional-validation">
      <action>Run all validation commands from spec</action>
      <action>Check integration between components</action>
      <action>Ensure acceptance criteria are met</action>
      <action>Verify pattern adherence</action>
    </step>
  </phase>

  <phase number="6" name="documentation">
    <step name="update-spec">
      <action>Mark completed items in acceptance criteria</action>
      <action>Note any deviations from original plan</action>
      <action>Document new patterns discovered</action>
    </step>

    <step name="create-adr" optional="true">
      <condition>If significant architectural decisions were made</condition>
      <action>Create ADR in docs/decisions/</action>
      <action>Reference the implementation spec</action>
    </step>

    <step name="update-requirements" optional="true">
      <condition>If requirements evolved during implementation</condition>
      <action>Update docs/design/ documentation</action>
    </step>
  </phase>

  <phase number="7" name="final-report">
    <summary>
      <item>Total tasks created and completed</item>
      <item>Tasks remaining in review and why</item>
      <item>Test coverage achieved</item>
      <item>Key features implemented</item>
      <item>Issues encountered and resolutions</item>
      <item>Deviations from original spec</item>
      <item>New patterns established</item>
      <item>Documentation created/updated</item>
    </summary>
    <git-status>
      <command>git diff --stat</command>
      <purpose>Report files and total lines changed</purpose>
    </git-status>
  </phase>

  <workflow-rules>
    <rule>ALWAYS create all tasks before starting</rule>
    <rule>WORK on one task at a time</rule>
    <rule>VALIDATE before marking complete</rule>
    <rule>TRACK progress continuously with TodoWrite</rule>
    <rule>ANALYZE codebase thoroughly first</rule>
    <rule>TEST everything with validator agent</rule>
    <rule>FOLLOW patterns from codebase analysis</rule>
    <rule>DOCUMENT significant decisions</rule>
  </workflow-rules>
</implement-command>