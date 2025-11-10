---
description: Implement a feature specification with full Archon task management integration
argument-hint: [spec-file-path]
allowed-tools: Edit, Write, Read, Bash, Glob, Grep, Task, TodoWrite, mcp__archon__manage_project, mcp__archon__manage_task
---

<implement-command>
  <objective>
    Execute a comprehensive feature specification with integrated Archon task management throughout the entire development process.
  </objective>

  <requirements>
    <mandatory>Maintain continuous Archon task management throughout execution</mandatory>
    <mandatory>Create all tasks in Archon before starting implementation</mandatory>
    <mandatory>Only ONE task in "doing" status at any time</mandatory>
    <mandatory>Validate all work before marking tasks as "done"</mandatory>
  </requirements>

  <documentation-structure>
    <directory path="docs/specs/">Feature implementation specifications</directory>
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

  <phase number="2" name="archon-setup">
    <step number="1">Check if project_id exists in spec</step>
    <step number="2">Check CLAUDE.md for project references</step>
    <step number="3">If no project exists:
      <action>Create new project: mcp__archon__manage_project("create", title="[Feature Name]")</action>
      <action>Store project_id for use throughout execution</action>
    </step>
  </phase>

  <phase number="3" name="create-tasks">
    <action>Create ALL tasks in Archon upfront</action>
    <for-each task="in spec">
      <create>mcp__archon__manage_task("create", project_id=..., title=..., description=..., status="todo")</create>
      <tag>Tag with phase: Foundation/Core/Integration</tag>
    </for-each>
    <important>Ensures complete visibility of work scope</important>
  </phase>

  <phase number="4" name="codebase-analysis">
    <action>Review codebase analysis findings from spec</action>
    <action>Verify patterns with Grep and Glob tools</action>
    <action>Read all referenced files and components</action>
    <action>Review related ADRs and requirements</action>
    <action>Build comprehensive understanding of context</action>
  </phase>

  <phase number="5" name="implementation-cycle">
    <for-each task="in sequence">
      <step name="start-task">
        <archon>mcp__archon__manage_task("update", task_id=..., status="doing")</archon>
        <local>Use TodoWrite for subtask tracking if needed</local>
      </step>

      <step name="implement">
        <follow>Task requirements from spec</follow>
        <follow>Codebase patterns and conventions</follow>
        <follow>Related ADRs and requirements</follow>
        <ensure>Code quality and consistency</ensure>
      </step>

      <step name="complete-task">
        <archon>mcp__archon__manage_task("update", task_id=..., status="review")</archon>
        <note>Do NOT mark as "done" yet - comes after validation</note>
      </step>
    </for-each>
    <critical>Only ONE task in "doing" status at any time</critical>
  </phase>

  <phase number="6" name="validation">
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

  <phase number="7" name="documentation">
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

  <phase number="8" name="finalize-tasks">
    <for-each task="with test coverage">
      <archon>mcp__archon__manage_task("update", task_id=..., status="done")</archon>
    </for-each>
    <for-each task="without test coverage">
      <leave>Status as "review" for future attention</leave>
      <document>Reason for review status</document>
    </for-each>
  </phase>

  <phase number="9" name="final-report">
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

  <error-handling>
    <if-archon-fails>
      <action>Retry the operation</action>
      <action>If persistent, document but continue locally</action>
      <action>Never abandon Archon integration</action>
    </if-archon-fails>
  </error-handling>

  <workflow-rules>
    <rule>NEVER skip Archon task management</rule>
    <rule>ALWAYS create all tasks before starting</rule>
    <rule>MAINTAIN one task in "doing" at a time</rule>
    <rule>VALIDATE before marking "done"</rule>
    <rule>TRACK progress continuously</rule>
    <rule>ANALYZE codebase thoroughly first</rule>
    <rule>TEST everything with validator agent</rule>
    <rule>FOLLOW patterns from codebase analysis</rule>
    <rule>DOCUMENT significant decisions</rule>
  </workflow-rules>
</implement-command>