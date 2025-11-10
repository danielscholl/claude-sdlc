---
description: Create detailed implementation specs for new features with deep codebase analysis
argument-hint: [feature-description]
allowed-tools: Write, Read, Glob, Grep, Task, mcp__archon__manage_project, mcp__archon__manage_task, mcp__archon__rag_search_knowledge_base
---

<feature-command>
  <objective>
    Create a comprehensive implementation specification in docs/specs/*.md for a new feature using deep codebase analysis and optional Archon task management.
  </objective>

  <documentation-structure>
    <directory path="docs/specs/">Feature implementation specifications</directory>
    <directory path="docs/decisions/">Architecture Decision Records (ADRs)</directory>
    <directory path="docs/design/">Requirements and design documents</directory>
  </documentation-structure>

  <research-phase>
    <step number="1" name="initial-analysis">
      <action>Read README.md and architecture documentation</action>
      <action>Check docs/design/ for existing requirements</action>
      <action>Review docs/decisions/ for relevant ADRs</action>
      <action>Check for CLAUDE.md or similar documentation</action>
      <action>Identify primary language and framework</action>
    </step>

    <step number="2" name="deep-codebase-analysis" importance="critical">
      <action>Launch codebase-analyst agent using Task tool</action>
      <analysis>
        <item>Architecture patterns and project structure</item>
        <item>Coding conventions and naming standards</item>
        <item>Integration patterns between components</item>
        <item>Testing approaches and validation commands</item>
        <item>External library usage and configuration</item>
      </analysis>
    </step>

    <step number="3" name="knowledge-base-search" optional="true">
      <condition>If Archon RAG is available</condition>
      <action>Search for relevant patterns and examples</action>
      <commands>
        <command>mcp__archon__rag_get_available_sources()</command>
        <command>mcp__archon__rag_search_knowledge_base(query)</command>
        <command>mcp__archon__rag_search_code_examples(query)</command>
      </commands>
    </step>

    <step number="4" name="targeted-research">
      <action>Based on codebase-analyst findings, search for:</action>
      <targets>
        <target>Similar feature implementations</target>
        <target>Integration points for new feature</target>
        <target>Existing utilities to reuse</target>
        <target>Test patterns and validation approaches</target>
      </targets>
    </step>
  </research-phase>

  <archon-integration optional="true">
    <condition>If Archon MCP is configured</condition>
    <action>Create project for feature tracking</action>
    <command>mcp__archon__manage_project("create", title="Feature: [name]")</command>
    <note>Store project_id in spec for execution phase</note>
  </archon-integration>

  <relevant-files>
    <focus>
      <file path="README.md">Project overview and instructions</file>
      <file path="app/server/**">Server codebase</file>
      <file path="app/client/**">Client codebase</file>
      <file path="scripts/**">Build and run scripts</file>
      <file path="docs/**">Documentation</file>
    </focus>
  </relevant-files>

  <spec-format>
    <template format="markdown">
      # Feature: [feature name]

      ## Feature Description
      [Describe the feature in detail, including its purpose and value to users]

      ## User Story
      As a [type of user]
      I want to [action/goal]
      So that [benefit/value]

      ## Problem Statement
      [Clearly define the specific problem or opportunity this feature addresses]

      ## Solution Statement
      [Describe the proposed solution approach and how it solves the problem]

      ## Related Documentation
      ### Requirements
      - [Reference any related requirements from docs/design/]

      ### Architecture Decisions
      - [Reference any related ADRs from docs/decisions/ that impact this feature]

      ## Codebase Analysis Findings
      [Include key findings from the codebase-analyst agent]
      - Architecture patterns: [patterns to follow]
      - Naming conventions: [conventions discovered]
      - Similar implementations: [references found]
      - Integration patterns: [how to integrate]

      ## Archon Project
      [If Archon is configured, include project_id: [ID]]

      ## Relevant Files
      ### Existing Files
      - [file path]: [why relevant]

      ### New Files
      - [file path]: [purpose]

      ## Implementation Plan

      ### Phase 1: Foundation
      [Describe foundational work needed before implementing the main feature]

      ### Phase 2: Core Implementation
      [Describe the main implementation work for the feature]

      ### Phase 3: Integration
      [Describe how the feature will integrate with existing functionality]

      ## Step by Step Tasks
      [Execute every step in order, top to bottom]

      ### Task 1: [Task Name]
      - Description: [what needs to be done]
      - Files to modify: [list files]
      - Archon task: [will be created during implementation]

      ### Task 2: [Task Name]
      - Description: [what needs to be done]
      - Files to modify: [list files]
      - Archon task: [will be created during implementation]

      [Continue with all tasks...]

      ## Testing Strategy

      ### Unit Tests
      [Describe unit tests needed - validator agent will create during implementation]

      ### Integration Tests
      [Describe integration tests needed]

      ### Edge Cases
      - [List edge cases that need to be tested]

      ## Acceptance Criteria
      - [ ] [Criterion 1]
      - [ ] [Criterion 2]
      - [ ] [Criterion n]

      ## Validation Commands
      ```bash
      # Run tests to validate the feature works with zero regressions
      cd app/server && uv run pytest
      ```

      [Include all validation commands]

      ## Notes
      [Any additional notes, future considerations, or patterns discovered by codebase-analyst]

      ## Execution
      This spec can be implemented using: `/implement docs/specs/[feature-name].md`
    </template>
  </spec-format>

  <instructions>
    <guideline>Create plan in docs/specs/*.md using kebab-case naming</guideline>
    <guideline importance="critical">Use codebase-analyst agent for deep pattern analysis</guideline>
    <guideline>Replace all placeholders with actual values</guideline>
    <guideline>Follow patterns discovered by codebase-analyst</guideline>
    <guideline>Design for extensibility and maintainability</guideline>
    <guideline>Reference related docs in docs/design/ and docs/decisions/</guideline>
  </instructions>

  <arguments>
    <variable>$ARGUMENTS</variable>
  </arguments>
</feature-command>
