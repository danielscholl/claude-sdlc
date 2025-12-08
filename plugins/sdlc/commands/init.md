---
description: Analyze codebase and generate AI agent guidance file (CLAUDE.md, AGENT.md, CODEX.md, etc.)
argument-hint: [agent-type] (claude, agent, codex, copilot, cursor, etc.)
allowed-tools: Read, Glob, Grep, Task, Write
---

<init-command>
  <argument>
    <name>agent-type</name>
    <default>claude</default>
    <examples>claude, agent, codex, copilot, cursor, aider, cody</examples>
    <usage>The type determines the output filename: [AGENT-TYPE].md (uppercase)</usage>
  </argument>

  <objective>
    Analyze a codebase to discover its principles, patterns, and standards, then generate
    an AI-optimized guidance file that serves as permanent guidance for AI assistants
    working with the project.
  </objective>

  <output>
    <file>${AGENT_TYPE}.md (e.g., CLAUDE.md, AGENT.md, CODEX.md)</file>
    <format>AI-optimized markdown with directive tone, scannable structure, critical rules first</format>
  </output>

  <constraints>
    <rule>DO NOT include code snippets - keep it principle-focused</rule>
    <rule>DO NOT include specific bash commands - reference docs instead</rule>
    <rule>DO NOT create verbose documentation - aim for concise, scannable content</rule>
    <rule>PRIORITIZE existing AI guidance files if found (CLAUDE.md, AGENT.md, copilot-instructions.md, etc.)</rule>
    <rule>FOCUS on what AI assistants get wrong - anti-patterns are critical</rule>
    <rule>OUTPUT filename must be uppercase: ${AGENT_TYPE}.md (e.g., CLAUDE.md, AGENT.md)</rule>
    <rule>ABSTRACT over specifics - describe principles, patterns, and concepts, NOT exact file paths, class names, or command sequences</rule>
    <rule>WRITE for portability - another developer should be able to apply the same principles to a similar project</rule>
    <rule>DESCRIBE the WHAT and WHY, not the HOW - "inject dependencies via constructors" not "pass AgentSettings to __init__"</rule>
  </constraints>

  <abstraction-guidance>
    <principle>The goal is PRINCIPLES that guide behavior, not a MAP of the codebase</principle>

    <good-examples>
      <example context="architecture">"CLI Layer: User interaction, commands, session management" NOT "cli/ directory contains app.py, commands.py, session.py"</example>
      <example context="testing">"Use mock clients for all tests except explicit integration tests" NOT "Use MockChatClient from tests/mocks/mock_client.py"</example>
      <example context="quality">"All code must pass: formatting, linting, type checking, tests with coverage" NOT "uv run black && uv run ruff && uv run mypy && uv run pytest"</example>
      <example context="patterns">"Single base exception with domain-specific subclasses" NOT "AgentError is the base, with ProviderAPIError, SkillError, ToolError subclasses"</example>
      <example context="config">"Environment variables override config file which overrides defaults" NOT "reads from ~/.agent/settings.json with OPENAI_API_KEY override"</example>
    </good-examples>

    <bad-patterns>
      <pattern>Listing specific file paths or directory structures</pattern>
      <pattern>Including exact command sequences to run - even in code blocks</pattern>
      <pattern>Naming specific classes, functions, or modules (e.g., "MockChatClient", "AgentSettings")</pattern>
      <pattern>Describing features unique to this project (skills, providers, etc.) in detail</pattern>
      <pattern>Creating a reference manual instead of guiding principles</pattern>
      <pattern>Listing specific environment variables or config file paths</pattern>
    </bad-patterns>

    <command-block-rule>
      IMPORTANT: Never include ```bash or ``` code blocks with commands.
      Instead of: "Run `uv run pytest -m 'not llm' -n auto --cov=src/agent`"
      Write: "All code must pass: formatting, linting, type checking, tests with coverage"
      The CONTRIBUTING.md or README has the actual commands - reference those docs instead.
    </command-block-rule>
  </abstraction-guidance>

  <phase number="1" name="quick-discovery">
    <purpose>Get rapid overview before deep analysis</purpose>

    <step name="structure">
      <action>List top-level directories and key files</action>
      <identify>Project type, language, framework indicators</identify>
    </step>

    <step name="existing-guidance">
      <action>Check for existing AI guidance files</action>
      <glob>**/CLAUDE.md, **/AGENT.md, **/copilot-instructions.md, **/CONTRIBUTING.md</glob>
      <priority>These contain pre-defined rules - extract and preserve them</priority>
    </step>

    <step name="config-files">
      <action>Read primary config file for tech stack</action>
      <priority>pyproject.toml > package.json > go.mod > Cargo.toml > pom.xml</priority>
      <extract>Language version, dependencies, dev tools, test framework, linting config</extract>
    </step>
  </phase>

  <phase number="2" name="parallel-deep-analysis">
    <purpose>Launch parallel exploration agents for comprehensive analysis</purpose>
    <method>Use Task tool with Explore subagent for each area</method>

    <exploration name="architecture">
      <focus>Project structure, layers, design patterns, component organization</focus>
      <look-for>Dependency injection, event systems, plugin architectures</look-for>
    </exploration>

    <exploration name="testing">
      <focus>Test organization, frameworks, markers, fixtures, coverage requirements</focus>
      <look-for>Mock patterns, test utilities, CI enforcement</look-for>
    </exploration>

    <exploration name="documentation">
      <focus>Docstring style, README structure, ADRs, inline comment patterns</focus>
      <look-for>Type hints usage, API documentation approach</look-for>
    </exploration>

    <exploration name="code-quality">
      <focus>Linting tools, formatters, type checking, CI/CD gates</focus>
      <look-for>Pre-commit hooks, quality enforcement, style guides</look-for>
    </exploration>

    <exploration name="principles">
      <focus>Error handling patterns, logging approach, configuration management</focus>
      <look-for>Design principles (SOLID, KISS, DRY), anti-patterns avoided</look-for>
    </exploration>
  </phase>

  <phase number="3" name="targeted-reading">
    <purpose>Read specific files that define project standards</purpose>

    <read-if-exists>
      <file>README.md</file>
      <file>CONTRIBUTING.md</file>
      <file>docs/design/architecture.md or similar</file>
      <file>docs/decisions/*.md (scan for key ADRs)</file>
      <file>tests/README.md</file>
      <file>.github/copilot-instructions.md</file>
    </read-if-exists>
  </phase>

  <phase number="4" name="synthesis">
    <purpose>Combine findings into structured knowledge</purpose>

    <identify>
      <item name="core-principles">Non-negotiable rules (type safety, testing, etc.)</item>
      <item name="tech-stack">Language, framework, tools with specific versions/configs</item>
      <item name="architecture">Layers, patterns, key design decisions</item>
      <item name="testing-strategy">Organization, markers, coverage requirements, mock patterns</item>
      <item name="documentation-standards">Docstring style, type hints, comment patterns</item>
      <item name="error-handling">Exception hierarchy, error response patterns</item>
      <item name="logging">Logging approach, observability integration</item>
      <item name="configuration">Config sources, priority, management approach</item>
      <item name="workflow">Quality gates, commit standards, PR requirements</item>
      <item name="anti-patterns">What NOT to do - critical for AI guidance</item>
      <item name="adr-process">When/how to create Architecture Decision Records (if project uses them)</item>
    </identify>

    <required-sections>
      <section name="Documentation Standards">Always include if project has docstring/type hint conventions</section>
      <section name="ADR Process">Include if docs/decisions/ or similar exists - explain when to create ADRs</section>
      <section name="Quality Gates">List what must pass (formatting, linting, types, tests) - NO commands</section>
    </required-sections>
  </phase>

  <phase number="5" name="generate-claude-md">
    <purpose>Create AI-optimized CLAUDE.md file</purpose>

    <format-principles>
      <principle>Critical rules first - ALWAYS/NEVER lists at the top</principle>
      <principle>Directive tone - "Do X" not "X is how we do things"</principle>
      <principle>Scannable - tables, lists, bold for emphasis</principle>
      <principle>Concise - every token should earn its place</principle>
      <principle>No code snippets - principle-focused only</principle>
      <principle>No numbered sections - clean headers only</principle>
    </format-principles>
  </phase>

  <agent-file-template>
    <note>Keep content ABSTRACT - describe principles and patterns, not specific implementations</note>
    <note>Aim for ~150-200 lines - concise guidance, not comprehensive documentation</note>
    <structure>
      # ${AGENT_TYPE}.md

      This file provides guidance to AI coding assistants when working with code in this repository.

      ---

      ## Critical Rules

      **ALWAYS:**
      - [Most important rules the AI must follow]
      - [Type safety, testing, patterns to use]
      - [Project-specific requirements]

      **NEVER:**
      - [Anti-patterns specific to this project]
      - [Common mistakes AI might make]
      - [Things that break the build/tests]

      ---

      ## Core Principles

      ### [PRINCIPLE NAME IN CAPS]
      [1-3 sentences explaining the principle and why it matters]

      [Repeat for each core principle - typically 3-6 principles]

      ---

      ## Tech Stack

      | Component | Technology |
      |-----------|------------|
      | Language | [Language and version] |
      | Framework | [Primary framework] |
      | Package Manager | [Package manager] |
      | [Other key components...] | |

      ---

      ## Architecture

      ### Layers
      - **[Abstract Layer Name]**: [Purpose - no specific file paths]
      [Use conceptual names like "CLI Layer", "Domain Layer", "Service Layer", "Infrastructure"]

      ### Key Patterns
      - **[Pattern Name]**: [Why it's used - no specific class names]
      [e.g., "Dependency Injection: Testability, no global state"]

      ---

      ## Testing

      ### Organization
      - **[Test type]**: [Purpose - no specific paths]
      [e.g., "Unit: Fast, isolated, mocked dependencies"]

      ### Rules
      - [Key testing rules - principles not commands]
      - [Coverage requirements as a number]
      - [Mock patterns as concepts, not class names]

      ---

      ## Documentation Standards

      ### Docstrings
      - **Style**: [Google/NumPy/Sphinx - whichever the project uses]
      - **Module-level**: [What to include]
      - **Class-level**: [What to include]
      - **Method-level**: [Brevity guidance]

      ### Type Hints
      [Requirements for type hints on public APIs]

      ---

      ## Error Handling

      ### Exception Hierarchy
      [Describe pattern abstractly - base exception with domain subclasses]

      ### Rules
      [Key error handling principles]

      ---

      ## Logging and Observability

      [Logging patterns, what to include/exclude, observability approach]

      ---

      ## Configuration

      ### Priority Order
      [Environment > config file > defaults - no specific paths]

      ---

      ## Commits and PRs

      [Conventional commits format, PR requirements]

      ---

      ## Quality Gates

      Before committing, all code must pass:
      1. [Formatter name] formatting
      2. [Linter name] linting
      3. [Type checker] type checking
      4. Tests with [X]% coverage

      ---

      ## Architecture Decision Records

      Create an ADR when:
      - [Conditions that warrant an ADR]

      [Where ADRs live - just the directory name]

      ---

      ## References

      - **[File]** - [What it contains]
      [List key reference documents]
    </structure>
  </agent-file-template>

  <quality-checks>
    <check>Critical Rules section exists and has both ALWAYS and NEVER lists</check>
    <check>NO code blocks (```) anywhere in the output - this is critical</check>
    <check>NO bash commands or command sequences - reference docs instead</check>
    <check>Tech stack is presented in scannable table format</check>
    <check>Anti-patterns are prominently featured</check>
    <check>References point to actual files in the repo</check>
    <check>Content is directive, not descriptive</check>
    <check>Total length is reasonable (aim for under 200 lines)</check>
    <check>No specific file paths like "src/agent/tools/" or "tests/fixtures/"</check>
    <check>No specific class/function names like "MockChatClient" or "AgentSettings"</check>
    <check>No specific environment variable names or config file paths</check>
    <check>Principles are portable - could apply to a similar project type</check>
    <check>Documentation Standards section exists if project has docstring conventions</check>
    <check>ADR section exists if project has docs/decisions/ or similar</check>
    <check>Quality Gates section lists WHAT must pass, not HOW to run it</check>
  </quality-checks>

  <anti-patterns>
    <avoid>Including implementation details that change frequently</avoid>
    <avoid>Duplicating content from existing docs verbatim</avoid>
    <avoid>Writing for humans instead of AI assistants</avoid>
    <avoid>Including obvious things any AI would know</avoid>
    <avoid>Creating a comprehensive manual instead of focused guidance</avoid>
    <avoid>Burying critical rules deep in the document</avoid>
    <avoid>Being too codebase-specific - listing exact files, paths, class names, or commands</avoid>
    <avoid>Including project-unique features in excessive detail (progressive disclosure, specific plugins, etc.)</avoid>
    <avoid>Writing a README or architecture doc - this is GUIDANCE for AI behavior</avoid>
  </anti-patterns>

  <success-criteria>
    <criterion>AI reading the file immediately knows the critical rules</criterion>
    <criterion>Anti-patterns prevent common AI mistakes in this codebase</criterion>
    <criterion>Tech stack is clear without reading other files</criterion>
    <criterion>Testing expectations are unambiguous</criterion>
    <criterion>Document is scannable in under 30 seconds</criterion>
    <criterion>Principles are abstract enough to apply to similar projects</criterion>
    <criterion>No specific file paths, class names, or command sequences appear</criterion>
  </success-criteria>

  <usage-examples>
    <example>/init claude → Creates CLAUDE.md</example>
    <example>/init agent → Creates AGENT.md</example>
    <example>/init codex → Creates CODEX.md</example>
    <example>/init copilot → Creates COPILOT.md</example>
    <example>/init cursor → Creates CURSOR.md</example>
    <example>/init → Creates CLAUDE.md (default)</example>
  </usage-examples>

  <arguments>
    <variable>$ARGUMENTS → agent-type (default: claude)</variable>
  </arguments>
</init-command>
