---
description: Prime understanding of the codebase by exploring files and reading documentation
allowed-tools: Bash, Read, Glob, Grep, Task
---

<prime-command>
  <objective>
    Build comprehensive understanding of the codebase structure, patterns, and conventions to prepare for effective development.
  </objective>

  <phase number="1" name="project-overview">
    <step name="explore-structure">
      <action>Get complete file listing to understand project organization</action>
      <command>git ls-files</command>
      <purpose>Map out all tracked files and directory structure</purpose>
    </step>

    <step name="read-readme">
      <action>Read primary documentation</action>
      <file>README.md</file>
      <extract>
        <item>Project purpose and goals</item>
        <item>Technology stack</item>
        <item>Architecture overview</item>
        <item>Development workflow</item>
      </extract>
    </step>
  </phase>

  <phase number="2" name="documentation-discovery">
    <step name="command-structure">
      <action>Understand available commands</action>
      <read>
        <file>.claude/commands/install.md</file>
        <file>.claude/commands/feature.md</file>
        <file>.claude/commands/implement.md</file>
      </read>
      <purpose>Learn development workflow and command capabilities</purpose>
    </step>

    <step name="agent-capabilities">
      <action>Review available agents if present</action>
      <check>.claude/agents/</check>
      <agents>
        <agent>codebase-analyst</agent>
        <agent>validator</agent>
      </agents>
    </step>

    <step name="project-documentation">
      <action>Explore documentation structure</action>
      <directories>
        <dir path="docs/specs/">Feature specifications</dir>
        <dir path="docs/decisions/">Architecture Decision Records</dir>
        <dir path="docs/design/">Requirements and design documents</dir>
      </directories>
    </step>

    <step name="configuration-files">
      <action>Check for project configuration and rules</action>
      <files>
        <file>CLAUDE.md</file>
        <file>.claude/claude.md</file>
        <file>cursorrules</file>
        <file>.cursorrules</file>
      </files>
    </step>
  </phase>

  <phase number="3" name="codebase-analysis">
    <step name="identify-structure">
      <action>Analyze main code directories</action>
      <explore>
        <directory>app/</directory>
        <directory>src/</directory>
        <directory>lib/</directory>
        <directory>packages/</directory>
        <directory>services/</directory>
      </explore>
      <identify>
        <item>Main entry points</item>
        <item>Core modules</item>
        <item>Shared utilities</item>
      </identify>
    </step>

    <step name="technology-detection">
      <action>Identify technologies and frameworks</action>
      <config-files>
        <file>package.json</file>
        <file>pyproject.toml</file>
        <file>requirements.txt</file>
        <file>go.mod</file>
        <file>Cargo.toml</file>
        <file>pom.xml</file>
        <file>build.gradle</file>
        <file>Gemfile</file>
        <file>composer.json</file>
      </config-files>
    </step>

    <step name="test-structure">
      <action>Understand testing approach</action>
      <explore>
        <directory>tests/</directory>
        <directory>test/</directory>
        <directory>spec/</directory>
        <directory>__tests__/</directory>
      </explore>
      <identify>
        <item>Test framework</item>
        <item>Test organization</item>
        <item>Coverage approach</item>
      </identify>
    </step>
  </phase>

  <phase number="4" name="pattern-discovery">
    <step name="launch-analyst" optional="true">
      <condition>For deep pattern analysis</condition>
      <action>Launch codebase-analyst agent using Task tool</action>
      <purpose>Discover architecture patterns, conventions, and best practices</purpose>
    </step>

    <step name="quick-patterns">
      <action>Identify common patterns</action>
      <search>
        <pattern>API endpoints</pattern>
        <pattern>Database models</pattern>
        <pattern>Component structure</pattern>
        <pattern>Service layers</pattern>
      </search>
    </step>
  </phase>

  <phase number="5" name="summarize">
    <summary>
      <section name="Project Overview">
        <item>Purpose and main functionality</item>
        <item>Target users and use cases</item>
      </section>

      <section name="Technology Stack">
        <item>Primary language and framework</item>
        <item>Key dependencies and libraries</item>
        <item>Build and deployment tools</item>
      </section>

      <section name="Architecture">
        <item>High-level structure</item>
        <item>Main components and their relationships</item>
        <item>Data flow and processing</item>
      </section>

      <section name="Development Workflow">
        <item>Available commands (/install, /feature, /implement)</item>
        <item>Documentation structure (specs, ADRs, requirements)</item>
        <item>Testing approach</item>
      </section>

      <section name="Patterns and Conventions">
        <item>Coding standards observed</item>
        <item>File and directory naming</item>
        <item>Common implementation patterns</item>
      </section>

      <section name="Key Files and Directories">
        <item>Main entry points</item>
        <item>Core business logic locations</item>
        <item>Configuration files</item>
      </section>

      <section name="Next Steps">
        <item>Recommended starting points</item>
        <item>Areas needing attention</item>
        <item>Suggested improvements</item>
      </section>
    </summary>
  </phase>

  <instructions>
    <guideline>Execute phases sequentially for comprehensive understanding</guideline>
    <guideline>Focus on understanding overall architecture before details</guideline>
    <guideline>Note any inconsistencies or areas for improvement</guideline>
    <guideline>Identify the most important patterns to follow</guideline>
    <guideline>Create actionable summary for future development</guideline>
  </instructions>
</prime-command>