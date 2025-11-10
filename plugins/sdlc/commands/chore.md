---
description: Create detailed specifications for maintenance tasks and codebase improvements
argument-hint: [chore-description]
allowed-tools: Write, Read, Glob, Grep, Task, mcp__archon__manage_project, mcp__archon__manage_task, mcp__archon__rag_search_knowledge_base
---

<chore-command>
  <objective>
    Create a comprehensive chore specification in docs/specs/*.md for maintenance tasks using deep codebase analysis and optional Archon task management.
  </objective>

  <documentation-structure>
    <directory path="docs/specs/">Chore specifications</directory>
    <directory path="docs/decisions/">Architecture Decision Records (ADRs)</directory>
    <directory path="docs/design/">Requirements and design documents</directory>
  </documentation-structure>

  <research-phase>
    <step number="1" name="initial-analysis">
      <action>Read README.md and architecture documentation</action>
      <action>Check docs/design/ for related documentation</action>
      <action>Review docs/decisions/ for relevant ADRs</action>
      <action>Check for CLAUDE.md or similar documentation</action>
      <action>Identify the scope and impact of the chore</action>
    </step>

    <step number="2" name="deep-codebase-analysis" importance="critical">
      <action>Launch codebase-analyst agent using Task tool</action>
      <analysis>
        <item>Current implementation patterns</item>
        <item>Code organization and structure</item>
        <item>Dependencies that might be affected</item>
        <item>Similar refactoring patterns</item>
        <item>Testing requirements</item>
      </analysis>
    </step>

    <step number="3" name="knowledge-base-search" optional="true">
      <condition>If Archon RAG is available</condition>
      <action>Search for best practices and patterns</action>
      <commands>
        <command>mcp__archon__rag_get_available_sources()</command>
        <command>mcp__archon__rag_search_knowledge_base(query)</command>
        <command>mcp__archon__rag_search_code_examples(query)</command>
      </commands>
    </step>

    <step number="4" name="targeted-research">
      <action>Based on codebase-analyst findings, search for:</action>
      <targets>
        <target>Code that needs to be updated</target>
        <target>Dependencies and imports</target>
        <target>Test files that need updates</target>
        <target>Documentation that needs changes</target>
      </targets>
    </step>

    <step number="5" name="impact-analysis">
      <action>Analyze the impact of the chore</action>
      <assess>
        <item>Files that will be modified</item>
        <item>Components that depend on changed code</item>
        <item>Breaking changes (if any)</item>
        <item>Performance implications</item>
      </assess>
    </step>
  </research-phase>

  <archon-integration optional="true">
    <condition>If Archon MCP is configured</condition>
    <action>Create project for chore tracking</action>
    <command>mcp__archon__manage_project("create", title="Chore: [name]")</command>
    <note>Store project_id in spec for execution phase</note>
  </archon-integration>

  <relevant-files>
    <focus>
      <file path="README.md">Project overview and instructions</file>
      <file path="app/**">Application codebase</file>
      <file path="scripts/**">Build and run scripts</file>
      <file path="tests/**">Test files</file>
      <file path="docs/**">Documentation</file>
      <file path="config/**">Configuration files</file>
    </focus>
  </relevant-files>

  <spec-format>
    <template format="markdown">
      # Chore: [chore name]

      ## Chore Description
      [Describe the chore in detail, including its purpose and expected outcome]

      ## Motivation
      [Explain why this chore is needed - technical debt, performance, maintainability, etc.]

      ## Scope
      [Define what is included and what is explicitly out of scope]

      ## Related Documentation
      ### Requirements
      - [Reference any related requirements from docs/design/]

      ### Architecture Decisions
      - [Reference any related ADRs from docs/decisions/]

      ## Codebase Analysis Findings
      [Include key findings from the codebase-analyst agent]
      - Current patterns: [existing implementation patterns]
      - Dependencies: [components that depend on affected code]
      - Similar changes: [references to similar refactoring]
      - Impact assessment: [potential impacts of the changes]

      ## Archon Project
      [If Archon is configured, include project_id: [ID]]

      ## Relevant Files
      ### Files to Modify
      - [file path]: [what changes are needed]

      ### Files to Review
      - [file path]: [files that might be affected]

      ### New Files (if needed)
      - [file path]: [purpose]

      ## Implementation Plan

      ### Phase 1: Preparation
      [Describe any preparatory work - backups, documentation, etc.]

      ### Phase 2: Core Changes
      [Describe the main refactoring or maintenance work]

      ### Phase 3: Cleanup
      [Describe cleanup tasks - removing old code, updating docs, etc.]

      ## Step by Step Tasks
      [Execute every step in order, top to bottom]

      ### Task 1: [Task Name]
      - Description: [what needs to be done]
      - Files to modify: [list files]
      - Expected outcome: [what should result]
      - Archon task: [will be created during implementation]

      ### Task 2: [Task Name]
      - Description: [what needs to be done]
      - Files to modify: [list files]
      - Expected outcome: [what should result]
      - Archon task: [will be created during implementation]

      [Continue with all tasks...]

      ## Testing Strategy

      ### Smoke Tests
      [Quick tests to ensure nothing is broken]

      ### Regression Tests
      [Tests to ensure existing functionality still works]

      ### Performance Tests (if applicable)
      [Tests to verify performance improvements or no degradation]

      ## Acceptance Criteria
      - [ ] All specified changes completed
      - [ ] No regression in existing functionality
      - [ ] All tests pass
      - [ ] Code follows established patterns
      - [ ] Documentation updated
      - [ ] [Additional criteria specific to the chore]

      ## Validation Commands
      ```bash
      # Run tests to ensure no regressions
      cd app/server && uv run pytest

      # Run linting to ensure code quality
      [linting commands]

      # Verify the chore outcome
      [specific validation commands]
      ```

      [Include all validation commands]

      ## Rollback Plan
      [If applicable, describe how to rollback changes if needed]

      ## Notes
      [Any additional notes about the chore, future improvements, or technical decisions]
      [Document any temporary workarounds or technical debt created/removed]

      ## Execution
      This spec can be implemented using: `/implement docs/specs/chore-[chore-name].md`
    </template>
  </spec-format>

  <instructions>
    <guideline>Create plan in docs/specs/*.md using kebab-case naming (chore-[name])</guideline>
    <guideline importance="critical">Use codebase-analyst agent for understanding current patterns</guideline>
    <guideline importance="critical">Be thorough to avoid multiple rounds of changes</guideline>
    <guideline>Replace all placeholders with actual values</guideline>
    <guideline>Follow patterns discovered by codebase-analyst</guideline>
    <guideline>Consider impact on dependent components</guideline>
    <guideline>Update tests and documentation as needed</guideline>
    <guideline>Reference related docs in docs/design/ and docs/decisions/</guideline>
    <guideline>Keep changes focused and well-scoped</guideline>
  </instructions>

  <arguments>
    <variable>$ARGUMENTS</variable>
  </arguments>
</chore-command>