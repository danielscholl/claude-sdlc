---
description: Prime understanding of the codebase by exploring files and reading documentation
allowed-tools: Bash, Read, Glob, Grep
---

<prime-command>
  <objective>
    Build a lightweight understanding of codebase structure and conventions.
  </objective>

  <constraints>
    <rule>MINIMIZE context usage - aim for under 20k tokens total</rule>
    <rule>DO NOT read source code files (.py, .ts, .js, etc.) - only list them</rule>
    <rule>DO NOT read test files - only note their existence</rule>
    <rule>DO NOT read agent definitions - only list available agents</rule>
    <rule>DO NOT launch subagents - this is a quick overview only</rule>
    <rule>ONLY read: README.md, config files (pyproject.toml, package.json), and CLAUDE.md</rule>
  </constraints>

  <phase number="1" name="structure-discovery">
    <step name="file-listing">
      <action>Get file listing and summarize structure</action>
      <command>git ls-files | head -100</command>
      <output>List directories and count files per directory - do not enumerate every file</output>
    </step>

    <step name="read-readme">
      <action>Read README.md only</action>
      <extract>Project purpose, tech stack, key commands</extract>
    </step>
  </phase>

  <phase number="2" name="config-detection">
    <step name="find-config">
      <action>Identify which config file exists (only ONE)</action>
      <priority>pyproject.toml > package.json > go.mod > Cargo.toml > pom.xml</priority>
      <read>Read ONLY the first config file found</read>
    </step>

    <step name="check-claude-config">
      <action>Check for CLAUDE.md if it exists</action>
      <glob>**/CLAUDE.md</glob>
    </step>
  </phase>

  <phase number="3" name="inventory-only">
    <step name="list-commands">
      <action>List available slash commands (filenames only)</action>
      <glob>.claude/commands/*.md OR plugins/*/commands/*.md</glob>
      <output>List names only, do not read contents</output>
    </step>

    <step name="list-agents">
      <action>List available agents (filenames only)</action>
      <glob>.claude/agents/*.md OR plugins/*/agents/*.md</glob>
      <output>List names only, do not read contents</output>
    </step>

    <step name="list-tests">
      <action>Note test directory existence</action>
      <glob>tests/**/*.py OR test/**/*.js OR __tests__/**/*</glob>
      <output>Report count only (e.g., "12 test files found")</output>
    </step>
  </phase>

  <phase number="4" name="summarize">
    <format>Concise markdown summary with:</format>
    <sections>
      <section>Project: 1-2 sentence description</section>
      <section>Tech: Language, framework, package manager</section>
      <section>Structure: Key directories (3-5 max)</section>
      <section>Commands: List available /commands</section>
      <section>Agents: List available agents</section>
      <section>Tests: Framework and count</section>
      <section>Next: What to run for deeper analysis</section>
    </sections>
  </phase>

  <anti-patterns>
    <avoid>Reading full source files to "understand patterns"</avoid>
    <avoid>Reading test files to "understand testing approach"</avoid>
    <avoid>Reading multiple similar files</avoid>
    <avoid>Launching codebase-analyst agent (use /feature for deep analysis)</avoid>
    <avoid>Producing multi-page summaries</avoid>
  </anti-patterns>
</prime-command>