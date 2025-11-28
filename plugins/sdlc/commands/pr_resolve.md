---
description: Resolve PR review comments in parallel using pr-comment-resolver agents
argument-hint: [PR-number] [--dry-run]
allowed-tools: Read, Edit, Write, Bash(git:*), Bash(gh:*), Bash(glab:*), Glob, Grep, Task, TodoWrite
---

<pr-comment-resolution>
  <description>
    Analyze PR review comments, plan resolution order based on dependencies, spawn parallel
    pr-comment-resolver agents to address each comment, then commit and push the changes.
  </description>

  <variables>
    <variable name="pr_number">$1</variable>
    <variable name="dry_run">$2 (optional: --dry-run to skip commit/push)</variable>
  </variables>

  <phase name="analyze" order="1">
    <description>Gather all unresolved review comments from the PR</description>

    <step order="1">
      <action>Fetch PR review comments</action>
      <github>
        <command>gh api repos/{owner}/{repo}/pulls/{pr_number}/comments --jq '.[] | {id, path, line, body, user: .user.login}'</command>
      </github>
      <gitlab>
        <command>glab api projects/{project}/merge_requests/{mr_iid}/discussions</command>
      </gitlab>
    </step>

    <step order="2">
      <action>Fetch PR review threads for context</action>
      <github>
        <command>gh pr view {pr_number} --json reviews,comments</command>
      </github>
    </step>

    <step order="3">
      <action>Parse and categorize each comment</action>
      <categories>
        <category type="bug">Fix defects or broken functionality</category>
        <category type="refactor">Extract, rename, move, restructure code</category>
        <category type="style">Naming, formatting, convention changes</category>
        <category type="docs">Add or update documentation/comments</category>
        <category type="security">Address security concerns</category>
        <category type="performance">Optimize for performance</category>
        <category type="question">Clarification needed (may not require code change)</category>
      </categories>
    </step>

    <step order="4">
      <action>Create list of unresolved comments</action>
      <output>List of comments with: id, file, line, category, description</output>
    </step>
  </phase>

  <phase name="plan" order="2">
    <description>Analyze dependencies and create execution plan with parallel groupings</description>

    <step order="1">
      <action>Identify dependencies between comments</action>
      <dependency-types>
        <type>Same file - may conflict if both edit same lines</type>
        <type>Rename - must complete before others reference new name</type>
        <type>Extract - must complete before others can use extracted code</type>
        <type>Delete - must verify no other changes depend on deleted code</type>
      </dependency-types>
    </step>

    <step order="2">
      <action>Create TodoWrite list of all unresolved items</action>
      <grouping>Group by dependency order - items that can run in parallel together</grouping>
    </step>

    <step order="3">
      <action>Generate Mermaid dependency diagram</action>
      <format>
        ```mermaid
        graph TD
          subgraph "Wave 1 - Run First"
            C1[Comment 1: Rename variable]
          end
          subgraph "Wave 2 - Parallel"
            C2[Comment 2: Add error handling]
            C3[Comment 3: Update docs]
            C4[Comment 4: Fix style]
          end
          subgraph "Wave 3 - After Wave 2"
            C5[Comment 5: Extract method using renamed var]
          end
          C1 --> C2
          C1 --> C3
          C1 --> C4
          C2 --> C5
          C3 --> C5
          C4 --> C5
        ```
      </format>
      <purpose>Visual execution plan showing parallel opportunities and required sequencing</purpose>
    </step>

    <step order="4">
      <action>Report the plan</action>
      <output>
        - Total comments to resolve
        - Number of waves/batches
        - Which comments can run in parallel
        - Which comments have dependencies
      </output>
    </step>
  </phase>

  <phase name="implement" order="3">
    <description>Execute resolution using parallel pr-comment-resolver agents</description>

    <critical-instruction>
      For EACH wave of comments that can run in parallel, spawn ALL pr-comment-resolver
      agents simultaneously using multiple Task tool calls in a SINGLE message.
    </critical-instruction>

    <execution-pattern>
      <wave number="1">
        <description>Execute blocking/dependency comments first (sequentially if needed)</description>
        <example>
          Task(subagent_type="sdlc:pr-comment-resolver", prompt="Resolve comment C1: [details]")
        </example>
      </wave>

      <wave number="2+">
        <description>Execute independent comments in parallel</description>
        <example>
          <!-- In a SINGLE message, call multiple Tasks: -->
          Task(subagent_type="sdlc:pr-comment-resolver", prompt="Resolve comment C2: [details]")
          Task(subagent_type="sdlc:pr-comment-resolver", prompt="Resolve comment C3: [details]")
          Task(subagent_type="sdlc:pr-comment-resolver", prompt="Resolve comment C4: [details]")
        </example>
      </wave>
    </execution-pattern>

    <agent-prompt-template>
      Resolve PR review comment:

      - Comment ID: {comment_id}
      - File: {file_path}
      - Line: {line_number}
      - Author: {reviewer}
      - Comment: {comment_body}

      Context from PR #{pr_number}

      Make the requested change and report what was modified.
    </agent-prompt-template>

    <step order="1">
      <action>For each wave, spawn agents in parallel</action>
      <parallel-execution>true</parallel-execution>
    </step>

    <step order="2">
      <action>Collect results from all agents</action>
      <track>
        <item>Which comments were resolved</item>
        <item>Which comments need clarification</item>
        <item>Which comments failed</item>
        <item>Files modified by each agent</item>
      </track>
    </step>

    <step order="3">
      <action>Update TodoWrite with completion status</action>
    </step>
  </phase>

  <phase name="commit-and-resolve" order="4">
    <description>Commit changes and optionally push to remote</description>

    <skip-if>dry_run flag is set</skip-if>

    <step order="1">
      <action>Review all changes made</action>
      <command>git diff --stat</command>
    </step>

    <step order="2">
      <action>Stage all changes</action>
      <command>git add -A</command>
    </step>

    <step order="3">
      <action>Create commit with summary of resolved comments</action>
      <commit-message-format>fix(review): address PR review comments

Resolved comments:
- {list of resolved comment summaries}

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt;</commit-message-format>
    </step>

    <step order="4">
      <action>Push changes to remote</action>
      <command>git push</command>
    </step>

    <step order="5">
      <action>Post resolution replies to PR comments (optional)</action>
      <github>
        <command>gh api --method POST repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies -f body="Resolved in latest commit"</command>
      </github>
    </step>
  </phase>

  <report>
    <output-format>
      ## PR Comment Resolution Summary

      **PR:** #{pr_number}
      **Comments Processed:** {total}
      **Resolved:** {resolved_count}
      **Needs Clarification:** {clarification_count}
      **Failed:** {failed_count}

      ### Execution Plan
      ```mermaid
      {dependency_diagram}
      ```

      ### Resolution Details
      | Comment | File | Status | Summary |
      |---------|------|--------|---------|
      | C1 | path/file.py | ✅ Resolved | Renamed variable |
      | C2 | path/other.py | ✅ Resolved | Added error handling |
      | C3 | path/docs.md | ⚠️ Clarification | Asked for specifics |

      ### Files Modified
      - {list of files changed}

      ### Commit
      {commit_hash}: {commit_message}

      ### Next Steps
      - {any pending items or follow-ups}
    </output-format>
  </report>
</pr-comment-resolution>
