---
description: Meta Prompt for creating detailed plans to make changes to the codebase.
argument-hint: [chore-description]
allowed-tools: Write, Read, Glob, Grep
---

<chore-planning>
  <description>
    Create a new plan in ai-specs/*.md to resolve the Chore using the exact specified markdown Plan Format.
    Follow the Instructions to create the plan and use the Relevant Files to focus on the right files.
  </description>

  <instructions>
    <guideline>You're writing a plan to resolve a chore, it should be simple but we need to be thorough and precise so we don't miss anything or waste time with any second round of changes.</guideline>
    <guideline>Create the plan in the ai-specs/*.md file. Name it appropriately based on the Chore.</guideline>
    <guideline>Use the plan format below to create the plan.</guideline>
    <guideline>Research the codebase and put together a plan to accomplish the chore.</guideline>
    <guideline importance="high">Replace every &lt;placeholder&gt; in the Plan Format with the requested value. Add as much detail as needed to accomplish the chore.</guideline>
    <guideline>Use your reasoning model: ultrathink about the plan and the steps to accomplish the chore.</guideline>
    <guideline>Respect requested files in the Relevant Files section.</guideline>
    <guideline>Start your research by reading the README.md file.</guideline>
  </instructions>

  <relevant-files>
    <focus>
      <file path="README.md">Contains the project overview and instructions.</file>
      <file path="app/**">Contains the codebase client/server.</file>
      <file path="scripts/**">Contains the scripts to start and stop the server + client.</file>
    </focus>
    <ignore>Ignore all other files in the codebase.</ignore>
  </relevant-files>

  <plan-format>
    <template format="markdown">
      <section name="Chore">
        <placeholder>chore name</placeholder>
      </section>

      <section name="Chore Description">
        <description>describe the chore in detail</description>
      </section>

      <section name="Relevant Files">
        <content>Use these files to resolve the chore:</content>
        <description>
          find and list the files that are relevant to the chore describe why they are relevant in bullet points.
          If there are new files that need to be created to accomplish the chore, list them in an h3 'New Files' section.
        </description>
      </section>

      <section name="Step by Step Tasks">
        <note importance="high">Execute every step in order, top to bottom.</note>
        <description>
          list step by step tasks as h3 headers plus bullet points. use as many h3 headers as needed to accomplish the chore.
          Order matters, start with the foundational shared changes required to fix the chore then move on to the specific
          changes required to fix the chore. Your last step should be running the Validation Commands to validate the chore
          is complete with zero regressions.
        </description>
      </section>

      <section name="Validation Commands">
        <content>Execute every command to validate the chore is complete with zero regressions.</content>
        <description>
          list commands you'll use to validate with 100% confidence the chore is complete with zero regressions.
          every command must execute without errors so be specific about what you want to run to validate the chore
          is complete with zero regressions. Don't validate with curl commands.
        </description>
        <example>
          <command>cd app/server &amp;&amp; uv run pytest</command>
          <purpose>Run server tests to validate the chore is complete with zero regressions</purpose>
        </example>
      </section>

      <section name="Notes">
        <description>
          optionally list any additional notes or context that are relevant to the chore that will be helpful to the developer
        </description>
      </section>
    </template>
  </plan-format>

  <arguments>
    <variable>$ARGUMENTS</variable>
  </arguments>
</chore-planning>

