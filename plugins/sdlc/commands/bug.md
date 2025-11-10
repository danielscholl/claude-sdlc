---
description: Create detailed bug fix specifications with deep codebase analysis
argument-hint: [bug-description]
allowed-tools: Write, Read, Glob, Grep, Task, mcp__archon__manage_project, mcp__archon__manage_task, mcp__archon__rag_search_knowledge_base
---

<bug-command>
  <objective>
    Create a comprehensive bug fix specification in docs/specs/*.md using deep codebase analysis and optional Archon task management.
  </objective>

  <documentation-structure>
    <directory path="docs/specs/">Bug fix specifications</directory>
    <directory path="docs/decisions/">Architecture Decision Records (ADRs)</directory>
    <directory path="docs/design/">Requirements and design documents</directory>
  </documentation-structure>

  <research-phase>
    <step number="1" name="initial-analysis">
      <action>Read README.md and architecture documentation</action>
      <action>Check docs/design/ for related requirements</action>
      <action>Review docs/decisions/ for relevant ADRs</action>
      <action>Check for CLAUDE.md or similar documentation</action>
      <action>Identify the area of code affected by the bug</action>
    </step>

    <step number="2" name="deep-codebase-analysis" importance="critical">
      <action>Launch codebase-analyst agent using Task tool</action>
      <analysis>
        <item>Architecture patterns in the affected area</item>
        <item>Error handling patterns</item>
        <item>Similar bug fixes in history</item>
        <item>Testing patterns for validation</item>
        <item>Dependencies and side effects</item>
      </analysis>
    </step>

    <step number="3" name="knowledge-base-search" optional="true">
      <condition>If Archon RAG is available</condition>
      <action>Search for similar bugs and fixes</action>
      <commands>
        <command>mcp__archon__rag_get_available_sources()</command>
        <command>mcp__archon__rag_search_knowledge_base(query)</command>
        <command>mcp__archon__rag_search_code_examples(query)</command>
      </commands>
    </step>

    <step number="4" name="targeted-research">
      <action>Based on codebase-analyst findings, search for:</action>
      <targets>
        <target>Code that triggers the bug</target>
        <target>Related functionality that might be affected</target>
        <target>Existing error handling mechanisms</target>
        <target>Test coverage in the affected area</target>
      </targets>
    </step>

    <step number="5" name="reproduction">
      <action>Attempt to reproduce the bug</action>
      <verify>
        <item>Confirm bug exists</item>
        <item>Document exact reproduction steps</item>
        <item>Capture error messages or unexpected behavior</item>
        <item>Note environment conditions</item>
      </verify>
    </step>
  </research-phase>

  <archon-integration optional="true">
    <condition>If Archon MCP is configured</condition>
    <action>Create project for bug tracking</action>
    <command>mcp__archon__manage_project("create", title="Bug Fix: [name]")</command>
    <note>Store project_id in spec for execution phase</note>
  </archon-integration>

  <relevant-files>
    <focus>
      <file path="README.md">Project overview and instructions</file>
      <file path="app/**">Application codebase</file>
      <file path="scripts/**">Build and run scripts</file>
      <file path="tests/**">Test files</file>
      <file path="docs/**">Documentation</file>
    </focus>
  </relevant-files>

  <spec-format>
    <template format="markdown">
      # Bug Fix: [bug name]

      ## Bug Description
      [Describe the bug in detail, including symptoms and expected vs actual behavior]

      ## Problem Statement
      [Clearly define the specific problem that needs to be solved]

      ## Solution Statement
      [Describe the proposed solution approach to fix the bug]

      ## Steps to Reproduce
      1. [Step 1]
      2. [Step 2]
      3. [Expected result vs actual result]

      ## Root Cause Analysis
      [Analyze and explain the root cause of the bug based on codebase investigation]

      ## Related Documentation
      ### Requirements
      - [Reference any related requirements from docs/design/ that define correct behavior]

      ### Architecture Decisions
      - [Reference any related ADRs from docs/decisions/ that impact the fix]

      ## Codebase Analysis Findings
      [Include key findings from the codebase-analyst agent]
      - Error patterns: [patterns in the affected area]
      - Similar fixes: [references to similar bug fixes]
      - Dependencies: [code that depends on the buggy component]
      - Side effects: [potential impacts of the fix]

      ## Archon Project
      [If Archon is configured, include project_id: [ID]]

      ## Relevant Files
      ### Files to Fix
      - [file path]: [what needs to be fixed]

      ### Files to Test
      - [file path]: [how to validate the fix]

      ### New Files (if needed)
      - [file path]: [purpose]

      ## Implementation Plan

      ### Phase 1: Immediate Fix
      [Describe the minimal changes needed to fix the bug]

      ### Phase 2: Validation
      [Describe testing and validation of the fix]

      ### Phase 3: Prevention
      [Describe any additional changes to prevent regression]

      ## Step by Step Tasks
      [Execute every step in order, top to bottom]

      ### Task 1: [Task Name]
      - Description: [what needs to be done]
      - Files to modify: [list files]
      - Changes: [specific changes needed]
      - Archon task: [will be created during implementation]

      ### Task 2: [Task Name]
      - Description: [what needs to be done]
      - Files to modify: [list files]
      - Changes: [specific changes needed]
      - Archon task: [will be created during implementation]

      [Continue with all tasks...]

      ## Testing Strategy

      ### Regression Tests
      [Tests to ensure the bug is fixed - validator agent will create during implementation]

      ### Edge Case Tests
      [Tests for related edge cases]

      ### Impact Tests
      - [Tests to ensure no new bugs were introduced]

      ## Acceptance Criteria
      - [ ] Bug no longer reproduces with original steps
      - [ ] All existing tests still pass
      - [ ] New tests added to prevent regression
      - [ ] No performance degradation
      - [ ] [Additional criteria specific to the bug]

      ## Validation Commands
      ```bash
      # Reproduce bug before fix (should fail)
      [command to reproduce bug]

      # Run tests to validate the fix
      cd app/server && uv run pytest

      # Verify bug is fixed (should succeed)
      [command that previously reproduced bug]
      ```

      [Include all validation commands]

      ## Notes
      [Any additional notes about the fix, potential side effects, or future improvements]
      [Document any workarounds or temporary measures]

      ## Execution
      This spec can be implemented using: `/implement docs/specs/bug-[bug-name].md`
    </template>
  </spec-format>

  <instructions>
    <guideline>Create plan in docs/specs/*.md using kebab-case naming (bug-[name])</guideline>
    <guideline importance="critical">Use codebase-analyst agent for deep analysis of affected code</guideline>
    <guideline importance="critical">Be surgical with the fix - minimal changes that solve the root cause</guideline>
    <guideline>Replace all placeholders with actual values</guideline>
    <guideline>Follow patterns discovered by codebase-analyst</guideline>
    <guideline>Ensure fix doesn't introduce new bugs</guideline>
    <guideline>Add tests to prevent regression</guideline>
    <guideline>Reference related docs in docs/design/ and docs/decisions/</guideline>
    <guideline>Don't use decorators - keep it simple</guideline>
  </instructions>

  <arguments>
    <variable>$ARGUMENTS</variable>
  </arguments>
</bug-command>