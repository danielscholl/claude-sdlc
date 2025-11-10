---
description: Install & Prime - Install dependencies and run setup scripts
---

<install-command>
  <objective>
    Install all project dependencies and prepare the development environment for immediate use.
  </objective>

  <steps>
    <step number="1" name="detect-environment">
      <action>Identify project type and package managers from README.md and config files</action>
      <checks>
        <check>package.json for npm/yarn/pnpm</check>
        <check>requirements.txt or pyproject.toml for Python</check>
        <check>go.mod for Go</check>
        <check>Cargo.toml for Rust</check>
        <check>pom.xml or build.gradle for Java</check>
        <check>Gemfile for Ruby</check>
        <check>composer.json for PHP</check>
      </checks>
    </step>

    <step number="2" name="read-documentation">
      <action>Read README.md and identify installation instructions</action>
      <focus>
        <section>Installation</section>
        <section>Setup</section>
        <section>Getting Started</section>
        <section>Quick Start</section>
        <section>Prerequisites</section>
      </focus>
    </step>

    <step number="3" name="install-dependencies">
      <action>Run appropriate install commands based on README instructions or detected environment</action>
      <priority>Follow README.md instructions first, then use standard commands</priority>
    </step>

    <step number="4" name="environment-configuration">
      <action>Set up environment configuration</action>
      <tasks>
        <task>Copy .env.example or .env.sample to .env if it exists</task>
        <task>Check for required environment variables</task>
        <task>Create necessary directories</task>
      </tasks>
    </step>

    <step number="5" name="run-setup-scripts">
      <action>Execute any setup or bootstrap scripts</action>
      <scripts>
        <script>setup.sh or setup.bat</script>
        <script>bootstrap.sh</script>
        <script>npm run setup</script>
        <script>make setup</script>
      </scripts>
    </step>

    <step number="6" name="database-setup" optional="true">
      <action>Initialize database if needed</action>
      <commands>
        <migrate>Run migration commands from README</migrate>
        <seed>Run seed commands if specified</seed>
      </commands>
    </step>

    <step number="7" name="verification">
      <action>Verify installation success</action>
      <checks>
        <check>Run test command to ensure setup works</check>
        <check>Try to start development server</check>
        <check>Check for any error messages</check>
      </checks>
    </step>

    <step number="8" name="prime-understanding">
      <action>Prime understanding of the codebase</action>
      <tasks>
        <task>Run git ls-files to understand project structure</task>
        <task>Explore docs/ directory structure</task>
        <task>Identify main entry points and architecture</task>
        <task>Review docs/design/ for requirements</task>
        <task>Check docs/decisions/ for ADRs</task>
      </tasks>
    </step>
  </steps>

  <output>
    <summary>
      <item>Project purpose and functionality</item>
      <item>Key technologies and frameworks</item>
      <item>Project structure and main components</item>
      <item>Installation status and readiness</item>
      <item>Next recommended steps</item>
    </summary>
  </output>
</install-command>