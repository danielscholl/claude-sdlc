---
description: Meta Prompt for creating detailed plans to implement new features.
argument-hint: [feature-description]
allowed-tools: Write, Read, Glob, Grep
---

<feature-planning>
  <description>
    Create a new plan in ai-specs/*.md to implement the Feature using the exact specified markdown Plan Format.
    Follow the Instructions to create the plan and use the Relevant Files to focus on the right files.
  </description>

  <instructions>
    <guideline>You're writing a plan to implement a net new feature that will add value to the application.</guideline>
    <guideline>Create the plan in the ai-specs/*.md file. Name it appropriately based on the Feature.</guideline>
    <guideline>Use the Plan Format below to create the plan.</guideline>
    <guideline>Research the codebase to understand existing patterns, architecture, and conventions before planning the feature.</guideline>
    <guideline importance="high">Replace every &lt;placeholder&gt; in the Plan Format with the requested value. Add as much detail as needed to implement the feature successfully.</guideline>
    <guideline>Use your reasoning model: ultrathink about the feature requirements, design, and implementation approach.</guideline>
    <guideline>Follow existing patterns and conventions in the codebase. Don't reinvent the wheel.</guideline>
    <guideline>Design for extensibility and maintainability.</guideline>
    <guideline>If you need a new library, use uv add and be sure to report it in the Notes section of the Plan Format.</guideline>
    <guideline>Respect requested files in the Relevant Files section.</guideline>
    <guideline>Start your research by reading the README.md file.</guideline>
  </instructions>

  <relevant-files>
    <focus>
      <file path="README.md">Contains the project overview and instructions.</file>
      <file path="app/server/**">Contains the codebase server.</file>
      <file path="app/client/**">Contains the codebase client.</file>
      <file path="scripts/**">Contains the scripts to start and stop the server + client.</file>
    </focus>
    <ignore>Ignore all other files in the codebase.</ignore>
  </relevant-files>

  <plan-format>
    <template format="markdown">
      <section name="Feature">
        <placeholder>feature name</placeholder>
      </section>

      <section name="Feature Description">
        <description>describe the feature in detail, including its purpose and value to users</description>
      </section>

      <section name="User Story">
        <template>
          As a &lt;type of user&gt;
          I want to &lt;action/goal&gt;
          So that &lt;benefit/value&gt;
        </template>
      </section>

      <section name="Problem Statement">
        <description>clearly define the specific problem or opportunity this feature addresses</description>
      </section>

      <section name="Solution Statement">
        <description>describe the proposed solution approach and how it solves the problem</description>
      </section>

      <section name="Relevant Files">
        <content>Use these files to implement the feature:</content>
        <description>
          find and list the files that are relevant to the feature describe why they are relevant in bullet points.
          If there are new files that need to be created to implement the feature, list them in an h3 'New Files' section.
        </description>
      </section>

      <section name="Implementation Plan">
        <phase number="1" name="Foundation">
          <description>describe the foundational work needed before implementing the main feature</description>
        </phase>
        <phase number="2" name="Core Implementation">
          <description>describe the main implementation work for the feature</description>
        </phase>
        <phase number="3" name="Integration">
          <description>describe how the feature will integrate with existing functionality</description>
        </phase>
      </section>

      <section name="Step by Step Tasks">
        <note importance="high">Execute every step in order, top to bottom.</note>
        <description>
          list step by step tasks as h3 headers plus bullet points. use as many h3 headers as needed to implement the feature.
          Order matters, start with the foundational shared changes required then move on to the specific implementation.
          Include creating tests throughout the implementation process. Your last step should be running the Validation Commands
          to validate the feature works correctly with zero regressions.
        </description>
      </section>

      <section name="Testing Strategy">
        <subsection name="Unit Tests">
          <description>describe unit tests needed for the feature</description>
        </subsection>
        <subsection name="Integration Tests">
          <description>describe integration tests needed for the feature</description>
        </subsection>
        <subsection name="Edge Cases">
          <description>list edge cases that need to be tested</description>
        </subsection>
      </section>

      <section name="Acceptance Criteria">
        <description>list specific, measurable criteria that must be met for the feature to be considered complete</description>
      </section>

      <section name="Validation Commands">
        <content>Execute every command to validate the feature works correctly with zero regressions.</content>
        <description>
          list commands you'll use to validate with 100% confidence the feature is implemented correctly with zero regressions.
          every command must execute without errors so be specific about what you want to run to validate the feature works
          as expected. Include commands to test the feature end-to-end.
        </description>
        <example>
          <command>cd app/server &amp;&amp; uv run pytest</command>
          <purpose>Run server tests to validate the feature works with zero regressions</purpose>
        </example>
      </section>

      <section name="Notes">
        <description>
          optionally list any additional notes, future considerations, or context that are relevant to the feature that will be helpful to the developer
        </description>
      </section>
    </template>
  </plan-format>

  <arguments>
    <variable>$ARGUMENTS</variable>
  </arguments>
</feature-planning>

