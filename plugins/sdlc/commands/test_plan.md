---
description: Analyze unit tests and create comprehensive test documentation with Archon task management
argument-hint: [optional-module-filter] [--file] [--plan]
allowed-tools: Read, Glob, Grep, Task, Write, Bash, TodoWrite, mcp__archon__manage_project, mcp__archon__manage_task
---

<test-plan-command>
  <objective>
    Generate a comprehensive TEST PLAN + ASSESSMENT document with integrated Archon task management that:
    1. Assesses current state (what exists, coverage, quality)
    2. Provides clear test plan (objectives, scope, priorities, strategy)
    3. Delivers actionable recommendations tracked as Archon tasks
    4. Creates all improvement tasks in Archon for visibility and tracking

    The document serves both as historical assessment and forward-looking plan with full task management integration.
  </objective>

  <critical-rules>
    <priority level="P0" label="MUST NEVER VIOLATE">
      <rule name="archon-integration">NEVER skip, ONE task in "doing" at a time, track all phases</rule>
      <rule name="mature-wip-scoring">Score MATURE tests only (exclude ≤10% pass rate jobs), report WIP separately</rule>
      <rule name="state-separation">Current facts ≠ Future recommendations (label clearly: "Current State" vs "Recommended (Future)")</rule>
      <rule name="file-directory-writing">Only write files to the directory ___ and create it if it doesn't exist</rule>
      <rule name="file-writing">ONLY write `tests-info.md` if `--file` argument provided (otherwise output directly)</rule>
    </priority>

    <priority level="P1" label="MUST MAINTAIN">
      <rule name="number-consistency">Summary counts = Appendix exactly (use ~ only if genuinely approximate + explain why)</rule>
      <rule name="score-alignment">Maturity scores MUST match described gaps (many missing tests → 6-7/10, not 8+/10)</rule>
      <rule name="ci-detection-accuracy">
        - Coverage tool in pom.xml → "Configured (JaCoCo X.Y.Z)", NOT "Not configured"
        - No CI files → "Manual runs only" + mark CI sections as "Recommended (Future State)"
        - Don't show CI pipeline examples in "Current State" if no CI detected
      </rule>
    </priority>

    <priority level="P2" label="SHOULD FOLLOW">
      <rule name="template-quality">Front-load value (TL;DR first), limit examples (2-3 max), actionable checklists</rule>
      <rule name="terminology-standards">Use standardized operations (CRUD) and scenario types (Happy Path, etc.)</rule>
    </priority>
  </critical-rules>

  <patterns>
    <pattern name="archon-task-lifecycle">
      <description>Standard lifecycle for Archon task state management</description>
      <code>
        Phase Start:  mcp__archon__manage_task("update", task_id="...", status="doing")
                      (Only ONE task in "doing" at any time)
        Phase End:    mcp__archon__manage_task("update", task_id="...", status="review")
        Final:        Update all analysis tasks → "done"
      </code>
      <critical>Only ONE task in "doing" status at any time</critical>
    </pattern>

    <pattern name="test-file-discovery">
      <description>Comprehensive patterns for locating test files</description>
      <glob-patterns>
        **/test/**/*.*
        **/tests/**/*.*
        **/*Test.*
        **/*Tests.*
        **/*_test.*
        **/test_*.*
        **/*Spec.*
        **/*.spec.*
        **/src/test/**/*.*
        **/testing/**/*.*
      </glob-patterns>
      <tools>
        <tool name="Glob">Search by file patterns</tool>
        <tool name="Grep">Search for test annotations (@Test, describe, it)</tool>
      </tools>
    </pattern>

    <pattern name="test-analysis">
      <aaa-pattern label="Unit Tests">
        <arrange>Set up test data, mocks, preconditions</arrange>
        <act>Execute method under test</act>
        <assert>Verify expected outcomes</assert>
      </aaa-pattern>

      <given-when-then label="Integration/Acceptance Tests">
        <given>Initial context and preconditions</given>
        <when>Action or event occurs</when>
        <then>Expected outcomes and side effects</then>
      </given-when-then>

      <guidance>Use the best pattern based on what works best for the tests being analyzed</guidance>
    </pattern>

    <pattern name="ci-integration">
      <detection>
        <platform name="github">
          <check>ls .github/workflows/*.yml 2>/dev/null | head -1</check>
          <indicator>.github/workflows/*.yml exists</indicator>
        </platform>
        <platform name="gitlab">
          <check>test -f .gitlab-ci.yml &amp;&amp; echo "found"</check>
          <indicator>.gitlab-ci.yml exists</indicator>
        </platform>
        <priority>If both platforms detected, prefer GitHub</priority>
        <no-ci>
          <action>Score 2-3/10 for automation</action>
          <action>Skip CI history analysis</action>
          <action>Mark CI sections as "Recommended (Future State)"</action>
        </no-ci>
      </detection>

      <execution>
        <launch>Task(subagent_type="{platform}-ci-historian", prompt="Analyze test history...")</launch>
      </execution>

      <response-handling>
        <success mode="full">
          <extract>metrics.mature_test_execution.pass_rate_percent → use for Automation score</extract>
          <extract>assessment.key_findings → CI Reliability section</extract>
          <extract>metrics.wip_test_execution → report separately as "Capabilities in Development"</extract>
        </success>

        <limited mode="config-only">
          <score>6-7/10 (GitLab without glab CLI)</score>
          <note>Recommend installing glab for full metrics</note>
        </limited>

        <unavailable>
          <extract>reason from agent response</extract>
          <note>CI history unavailable: [reason]</note>
          <fallback>4-5/10 if CI configured, 2-3/10 if no CI</fallback>
        </unavailable>
      </response-handling>

      <critical>MATURE tests only for scoring (exclude pass_rate ≤10% or always-skipped WIP jobs)</critical>
    </pattern>
  </patterns>

  <maturity-scoring>
    <template format="markdown">
      ### Overall Maturity Calculation

      | Dimension | Weight | Score Criteria | Your Score |
      |-----------|--------|----------------|------------|
      | **Completeness** | 30% | 9-10: >90% critical paths covered&lt;br&gt;7-8: 70-89%&lt;br&gt;5-6: 50-69%&lt;br&gt;&lt;5: &lt;50% | [X]/10 |
      | **Quality** | 25% | 9-10: Excellent assertions, isolation, clarity&lt;br&gt;7-8: Good&lt;br&gt;5-6: Fair&lt;br&gt;&lt;5: Poor | [Y]/10 |
      | **Maintainability** | 20% | 9-10: Excellent DRY, organization&lt;br&gt;7-8: Good&lt;br&gt;5-6: Fair&lt;br&gt;&lt;5: Poor duplication | [Z]/10 |
      | **Security Focus** | 15% | 9-10: Comprehensive (auth, crypto, injection)&lt;br&gt;7-8: Good coverage&lt;br&gt;5-6: Basic&lt;br&gt;&lt;5: Minimal/None | [W]/10 |
      | **Automation** | 10% | See Automation table below | [V]/10 |
      | **TOTAL** | 100% | Weighted sum | **[Score]/10** |

      ### Automation Dimension Scoring

      | Mature Test Pass Rate | CI Status | Score | Notes |
      |----------------------|-----------|-------|-------|
      | ≥90% + stable + low flakiness | CI configured | 9-10 | Excellent reliability |
      | 70-89% + low flakiness | CI configured | 7-8 | Good, some instability |
      | 50-69% + medium flakiness | CI configured | 5-6 | Needs improvement |
      | &lt;50% or high flakiness | CI configured | 3-4 | Poor quality, blocking |
      | N/A (auth unavailable) | CI configured | 6-7 | Config verified, runtime unknown |
      | N/A | Coverage tool only, no CI | 4-5 | Partial automation |
      | N/A | No CI, no coverage | 2-3 | Manual only |

      **Critical Notes:**
      - Use `metrics.mature_test_execution.pass_rate_percent` from CI historian
      - Exclude WIP jobs (≤10% pass rate or always skipped) from score
      - Report WIP separately in "Capabilities in Development" section
      - If mature tests have &lt;70% pass rate, add to "Critical Gaps" in TL;DR
    </template>
  </maturity-scoring>

  <workflow>
    <phase number="1" name="archon-setup">
      <step number="1">
        <action>Create Archon project</action>
        <command>mcp__archon__manage_project("create", title="Test Analysis - [Project Name]")</command>
      </step>

      <step number="2">
        <action>Store project_id for use throughout execution</action>
        <important>Needed for all task creation and updates</important>
      </step>

      <step number="3">
        <action>Create 6 analysis phase tasks (all status="todo")</action>
        <tasks>
          <task>Discover test files and frameworks</task>
          <task>Fetch CI/CD test run history</task>
          <task>Inventory test classes and methods</task>
          <task>Analyze test patterns and quality</task>
          <task>Assess coverage and identify gaps</task>
          <task>Generate test plan and documentation</task>
        </tasks>
      </step>
    </phase>

    <phase number="2" name="discovery">
      <lifecycle>
        <start>Update "Discover test files and frameworks" task to status="doing"</start>
        <complete>Update task to status="review"</complete>
      </lifecycle>

      <step number="1" name="locate-test-files">
        <use-pattern>test-file-discovery</use-pattern>
        <action>Count ACTUAL files and methods (use ~ only if truly approximate + explain why)</action>
        <tools>Glob, Grep</tools>
      </step>

      <step number="2" name="identify-frameworks">
        <action>Check build files for testing frameworks</action>
        <build-files>pom.xml, build.gradle, package.json, requirements.txt, pyproject.toml</build-files>
        <frameworks>
          <java>JUnit 4/5, TestNG, Mockito</java>
          <python>pytest, unittest</python>
          <javascript>Jest, Mocha, Vitest</javascript>
          <dotnet>NUnit, xUnit, MSTest</dotnet>
        </frameworks>
        <action>Use Grep for framework-specific imports and annotations</action>
      </step>

      <step number="3" name="detect-coverage-ci">
        <coverage-detection>
          <check-build-files>Look for coverage tools in build configuration</check-build-files>
          <tools>JaCoCo, Cobertura, Istanbul, Coverage.py, pytest-cov</tools>
          <states>
            <state>"Configured (tool X.Y.Z) + enforced in CI" (plugin + CI validation)</state>
            <state>"Configured (tool X.Y.Z) - not enforced" (plugin but no CI)</state>
            <state>"Not configured" (no plugin in build files)</state>
          </states>
        </coverage-detection>

        <ci-detection>
          <check-files>.gitlab-ci.yml, .github/workflows/*.yml, Jenkinsfile, .circleci/config.yml</check-files>
          <states>
            <state>"Fully automated" (CI file with test stages)</state>
            <state>"Partially automated" (CI file, unclear test integration)</state>
            <state>"Manual only" (no CI files detected)</state>
          </states>
        </ci-detection>
      </step>

      <step number="4" name="map-test-structure">
        <analyze>
          <organization>by feature / layer / component</organization>
          <separation>unit vs integration vs e2e</separation>
          <correspondence>source ↔ test directory mapping</correspondence>
          <resources>fixtures, mocks, test data</resources>
        </analyze>
      </step>
    </phase>

    <phase number="2.5" name="ci-history" optional="true">
      <condition>Continue even if CI unavailable - mark unavailability and use fallback scores</condition>

      <lifecycle>
        <start>Update "Fetch CI/CD test run history" task to status="doing"</start>
        <complete>Update task to status="review"</complete>
      </lifecycle>

      <platform-detection>
        <check-github>ls .github/workflows/*.yml 2>/dev/null | head -1</check-github>
        <check-gitlab>test -f .gitlab-ci.yml &amp;&amp; echo "found"</check-gitlab>
        <priority>If both platforms detected, prefer GitHub</priority>
      </platform-detection>

      <execute>
        <apply-pattern>ci-integration</apply-pattern>
      </execute>

      <automation-score-mapping>
        <principle>Score reflects quality of completed test suites, not completeness of product capabilities</principle>
        <mature-tests-only>Agent returns 0-10 score based on MATURE test jobs only</mature-tests-only>
        <wip-tracking>Track WIP capabilities separately without penalizing established test reliability</wip-tracking>
      </automation-score-mapping>

      <example-scenario>
        <description>
          Real partition service:
          - All tests: 64.3% pass (includes CIMPL WIP: 0%)
          - Mature tests only: 81.8% pass (excludes CIMPL)
          - WIP: cimpl-acceptance-test (0/50 runs) - capability in development

          Correct scoring:
          - Automation score: 8/10 (based on 81.8% mature tests)
          - Note: "CIMPL capability in development, not affecting score"

          Incorrect (old approach):
          - Would be: 5-6/10 (based on 64.3% all tests) ❌
          - Problem: Penalizes team for incomplete product features
        </description>
      </example-scenario>
    </phase>

    <phase number="3" name="inventory">
      <lifecycle>
        <start>Update "Inventory test classes and methods" task to status="doing"</start>
        <complete>Update task to status="review"</complete>
      </lifecycle>

      <step number="1" name="catalog-test-classes">
        <extract>
          <item>Test class/suite names and purpose</item>
          <item>Package/module structure</item>
          <item>Class-level annotations (@RunWith, @ExtendWith, etc.)</item>
          <item>Setup/teardown methods (@Before, @After, @BeforeEach, etc.)</item>
          <item>Number of test methods per class</item>
        </extract>
      </step>

      <step number="2" name="catalog-test-methods">
        <extract>
          <item>Method name and readability</item>
          <item>Test annotations (@Test, test type, tags, parameters)</item>
          <item>Description or documentation</item>
          <item>Parameterized test variations</item>
        </extract>
      </step>

      <step number="3" name="build-inventory">
        <structure>
          Module/Component
            └─ Test Class/Suite
                └─ Test Method/Case
        </structure>

        <metrics>
          <metric>Total test files</metric>
          <metric>Total test classes</metric>
          <metric>Total test methods</metric>
          <metric>Tests per module/component</metric>
        </metrics>

        <critical>Keep detailed inventory for APPENDIX only. Main document has summary tables.</critical>
        <consistency-check>Ensure numbers in summary = appendix EXACTLY. If "56 test files" in summary, appendix lists exactly 56.</consistency-check>
      </step>
    </phase>

    <phase number="4" name="analysis">
      <lifecycle>
        <start>Update "Analyze test patterns and quality" task to status="doing"</start>
        <complete>Update task to status="review"</complete>
      </lifecycle>

      <step number="1" name="analyze-test-purpose">
        <scope>2-3 representative tests per major module</scope>
        <questions>
          <question>What is the subject under test (SUT)?</question>
          <question>What specific behavior is being validated?</question>
          <question>What is being asserted (expected outcome)?</question>
          <question>What input conditions or state is tested?</question>
        </questions>
        <method>Read test code, analyze using appropriate pattern (AAA or Given-When-Then)</method>
      </step>

      <step number="2" name="classify-test-types">
        <use-terminology>Standard operations and scenario types</use-terminology>
        <operations>Create, Read, Update, Delete, List</operations>
        <scenario-types>
          <type>Happy Path: Normal expected behavior with valid inputs</type>
          <type>Validation Error: Invalid inputs rejected with proper error messages</type>
          <type>Business Rule Violation: Valid inputs that violate business constraints</type>
          <type>System Failure: External dependencies unavailable or failing</type>
          <type>Edge Case: Boundary conditions (null, empty, max, min)</type>
          <type>Security: Authorization, authentication, injection prevention</type>
          <type>Performance: Response time, throughput, resource usage</type>
          <type>Concurrency: Race conditions, deadlocks, thread safety</type>
        </scenario-types>
        <accuracy>If literally ZERO concurrency tests, say "None" not "Minimal"</accuracy>
      </step>

      <step number="3" name="analyze-dependencies">
        <analyze>
          <item>What's mocked/stubbed?</item>
          <item>Mocking framework (Mockito, mock, sinon, etc.)</item>
          <item>Test isolation vs shared state</item>
          <item>External resources (databases, files, network)</item>
          <item>Test fixtures and data builders</item>
        </analyze>
      </step>

      <step number="4" name="analyze-assertions">
        <analyze>
          <item>Number and type per test</item>
          <item>Quality (specific vs generic)</item>
          <item>Assertion libraries (AssertJ, Chai, etc.)</item>
          <item>Completeness (partial vs full verification)</item>
        </analyze>
      </step>

      <step number="5" name="identify-risk-areas">
        <risk-dimensions>
          <dimension name="Business Impact">What breaks if this fails?</dimension>
          <dimension name="Change Frequency">How often does this code change?</dimension>
          <dimension name="Complexity">How hard to understand/maintain?</dimension>
          <dimension name="Security Sensitivity">Auth, encryption, PII handling?</dimension>
        </risk-dimensions>
        <output>Risk vs coverage matrix for the plan</output>
      </step>
    </phase>

    <phase number="5" name="pattern-recognition">
      <step number="1" name="naming-conventions">
        <analyze>
          <item>Test method patterns (should*, test*, given*When*Then*)</item>
          <item>Test class patterns (*Test, *Tests, *Spec)</item>
          <item>Consistency and readability</item>
          <item>Descriptiveness (clear what's tested?)</item>
        </analyze>
      </step>

      <step number="2" name="organizational-patterns">
        <analyze>
          <item>Grouping strategies (nested classes, describe blocks, suites)</item>
          <item>Test data management (builders, fixtures, factories)</item>
          <item>Setup/teardown usage</item>
          <item>Reusable utilities and helpers</item>
          <item>Base test classes or inheritance</item>
        </analyze>
        <note>Define "Test Design Heuristics" ONCE in dedicated section, don't repeat</note>
      </step>

      <step number="3" name="coding-patterns">
        <analyze>
          <item>Mocking patterns (setup, verification)</item>
          <item>Assertion styles</item>
          <item>Test data creation</item>
          <item>Exception testing</item>
          <item>Parameterized test usage</item>
        </analyze>
      </step>

      <step number="4" name="quality-metrics-scoring">
        <calculate>
          <metric>Average assertions per test</metric>
          <metric>Test method length (LOC)</metric>
          <metric>Test complexity (cyclomatic if detectable)</metric>
          <metric>Maintenance burden indicators</metric>
          <metric>Clarity score (naming, structure)</metric>
        </calculate>

        <apply-maturity-scoring>
          <show-calculation>
            <inline-formula>(Completeness×0.30) + (Quality×0.25) + (Maintainability×0.20) + (Security×0.15) + (Automation×0.10)</inline-formula>
            <table-format>For scannability</table-format>
          </show-calculation>
        </apply-maturity-scoring>
      </step>
    </phase>

    <phase number="6" name="value-assessment">
      <lifecycle>
        <start>Update "Assess coverage and identify gaps" task to status="doing"</start>
        <complete>Update task to status="review"</complete>
      </lifecycle>

      <step number="1" name="critical-path-coverage">
        <assess>
          <item>Core business logic paths well-tested?</item>
          <item>Critical data transformations validated?</item>
          <item>Important API endpoints/interfaces tested?</item>
          <item>Security-sensitive operations validated?</item>
        </assess>
      </step>

      <step number="2" name="edge-case-coverage">
        <assess>
          <item>Boundary conditions (null, empty, max, min)?</item>
          <item>Error conditions and exceptions?</item>
          <item>Concurrent/async scenarios?</item>
          <item>Failure modes and recovery paths?</item>
        </assess>
      </step>

      <step number="3" name="quality-indicators">
        <positive>
          <indicator>Clear, descriptive test names</indicator>
          <indicator>Focused tests (one thing)</indicator>
          <indicator>Proper isolation and mocking</indicator>
          <indicator>Good assertion quality</indicator>
          <indicator>Maintainable code</indicator>
        </positive>

        <negative>
          <indicator>Vague/unclear names</indicator>
          <indicator>Tests too much</indicator>
          <indicator>Brittle/flaky tests</indicator>
          <indicator>No assertions</indicator>
          <indicator>Duplicated code</indicator>
        </negative>
      </step>

      <step number="4" name="identify-gaps">
        <impact-analysis>For each gap, assess: What could go wrong? What's the business impact?</impact-analysis>
        <gaps>
          <gap>Untested/under-tested modules</gap>
          <gap>Missing error handling tests</gap>
          <gap>Missing edge case tests</gap>
          <gap>Missing integration tests</gap>
          <gap>Missing concurrency/performance tests</gap>
        </gaps>
      </step>

      <step number="5" name="assess-maintainability">
        <assess>
          <item>Easy to understand?</item>
          <item>Easy to modify?</item>
          <item>Excessive duplication?</item>
          <item>Test utilities well-organized?</item>
          <item>Would source changes require extensive test updates?</item>
        </assess>
      </step>
    </phase>

    <phase number="7" name="test-plan-generation">
      <lifecycle>
        <start>Update "Generate test plan and documentation" task to status="doing"</start>
        <complete>Update task to status="review"</complete>
      </lifecycle>

      <step number="1" name="define-objectives">
        <format>Punchy "confidence that" bullets (5-10 words max)</format>
        <example>
          Our tests should give confidence that:
          • CRUD works correctly across all providers
          • All providers behave identically at API level
          • Security invariants hold (authz, encryption, no leaks)
          • Caches are correct, not just fast
          • Errors are predictable with correct HTTP codes
        </example>
      </step>

      <step number="2" name="create-risk-priority-matrix">
        <format>Table with Risk Area, Business Impact, Current Coverage, Test Gap, Priority</format>
        <labels>Use consistent P1/P2/P3 labels here and in recommendations</labels>
      </step>

      <step number="3" name="define-test-environments">
        <for-each environment="Unit, Integration, Acceptance">
          <define>
            <item>Environment description</item>
            <item>External dependencies</item>
            <item>Configuration needs</item>
            <item>Run commands</item>
            <item>Expected runtime</item>
            <item>Prerequisites</item>
          </define>
        </for-each>
      </step>

      <step number="4" name="test-data-strategy">
        <define>
          <item>Seed data requirements</item>
          <item>ID/tenant/environment configuration</item>
          <item>Collision avoidance</item>
          <item>Fixture storage locations</item>
          <item>Test data factories/builders</item>
        </define>
      </step>

      <step number="5" name="acceptance-criteria">
        <format>Define "we can ship when..." criteria</format>
        <examples>
          <criterion>All unit/integration tests pass</criterion>
          <criterion>Acceptance tests pass (at least one env per provider)</criterion>
          <criterion>No new high-severity defects in critical flows</criterion>
          <criterion>Code coverage ≥ X% for core, 100% for security-sensitive</criterion>
        </examples>
      </step>

      <step number="6" name="out-of-scope">
        <action>Explicitly call out what's NOT covered</action>
        <examples>
          <item>Detailed performance/load testing</item>
          <item>Chaos/fault-injection testing</item>
          <item>Long-running soak tests</item>
          <item>UI/E2E testing (if applicable)</item>
        </examples>
      </step>
    </phase>

    <phase number="8" name="documentation-generation">
      <step number="1" name="synthesize-findings">
        <synthesize>
          <item>Overall test strategy and approach</item>
          <item>Strengths of current test suite</item>
          <item>Weaknesses and improvement areas</item>
          <item>Key patterns and conventions</item>
          <item>Actionable recommendations with checklists</item>
        </synthesize>
      </step>

      <step number="2" name="generate-documentation">
        <location>___/tests-info.md (in ___ directory, ONLY if --file argument provided)</location>

        <conditional>
          <if-file-flag>
            <action>Create ___ directory if it doesn't exist</action>
            <action>Write to ___/tests-info.md</action>
          </if-file-flag>
          <else>
            <action>Output directly (do NOT write file)</action>
          </else>
        </conditional>

        <follow>Documentation Schema (defined below)</follow>
        <exclude>Archon IDs - document must be tool-agnostic</exclude>
      </step>
    </phase>

    <phase number="9" name="create-improvement-tasks">
      <condition>ONLY execute this phase if --plan argument is provided</condition>

      <objective>Create Archon tasks for ALL identified improvements</objective>

      <effort-sizing>
        <description>Use T-shirt sizes to indicate complexity, NOT day estimates</description>
        <small>Low complexity, isolated change, minimal risk</small>
        <medium>Moderate complexity, some dependencies, manageable risk</medium>
        <large>High complexity, many dependencies, significant risk</large>
      </effort-sizing>

      <step number="1" name="p1-critical-tasks">
        <for-each recommendation="priority:P1">
          <create>
            <command>mcp__archon__manage_task("create", project_id=..., title="[P1 Improvement Name]", description="[Details + risk mitigation]", status="todo")</command>
            <tag>Priority:P1, Type:Critical, Effort:Small|Medium|Large</tag>
          </create>
        </for-each>
      </step>

      <step number="2" name="p2-important-tasks">
        <for-each recommendation="priority:P2">
          <create>
            <command>mcp__archon__manage_task("create", project_id=..., title="[P2 Improvement Name]", description="[Details + risk mitigation]", status="todo")</command>
            <tag>Priority:P2, Type:Important, Effort:Small|Medium|Large</tag>
          </create>
        </for-each>
      </step>

      <step number="3" name="p3-nice-to-have-tasks">
        <for-each recommendation="priority:P3">
          <create>
            <command>mcp__archon__manage_task("create", project_id=..., title="[P3 Improvement Name]", description="[Brief description]", status="todo")</command>
            <tag>Priority:P3, Type:Nice-to-have, Effort:Small|Medium|Large</tag>
          </create>
        </for-each>
      </step>

      <step number="4" name="migration-tasks" optional="true">
        <example>
          <command>mcp__archon__manage_task("create", project_id=..., title="Migrate from JUnit 4 to JUnit 5", description="[Migration checklist with steps]", status="todo")</command>
          <tag>Type:Migration, Effort:Large</tag>
        </example>
      </step>

      <step number="5" name="link-tasks-to-risks">
        <update-descriptions>
          <item>Which risk from risk matrix it mitigates</item>
          <item>Expected impact and success criteria</item>
          <item>Effort justification (why Small/Medium/Large)</item>
        </update-descriptions>
      </step>
    </phase>

    <phase number="10" name="finalize-analysis">
      <step number="1" name="mark-tasks-done">
        <for-each task="in 6 analysis phase tasks">
          <command>mcp__archon__manage_task("update", task_id=..., status="done")</command>
        </for-each>
      </step>

      <step number="2" name="generate-final-report">
        <critical>Do NOT include Archon project IDs or task references in tests-info.md — document must be tool-agnostic</critical>

        <summary>
          <item>Total analysis tasks completed: 6</item>
          <item>Total improvement tasks created: [X] (if --plan provided)</item>
          <item>P1 Critical: [Y]</item>
          <item>P2 Important: [Z]</item>
          <item>P3 Nice-to-have: [W]</item>
          <item>Effort distribution: Small:[A], Medium:[B], Large:[C] (if --plan provided)</item>
          <item>Documentation: ___/tests-info.md (if --file provided)</item>
        </summary>
      </step>

      <step number="3" name="provide-next-steps">
        <for-team>
          <item>Review ___/tests-info.md document</item>
          <item>Prioritize P1 tasks for next sprint</item>
          <item>Create work items in team's tracking system (Jira, GitHub Issues, etc.)</item>
          <item>Update task estimates based on capacity</item>
        </for-team>
      </step>
    </phase>
  </workflow>

  <documentation-schema>
    <template format="markdown">
      ### Required Sections (Order Matters)

      1. **Header** → Title, document type, audience, purpose, analysis date
      2. **TL;DR** → Maturity score TABLE + 3 strengths/gaps/actions + Mature test performance + WIP capabilities (if exist)
      3. **How to Use** → Audience guide (Tech Leads, Developers, QA, New Members)
      4. **Executive Summary** → 6 subsections:
         - Overview (2-3 sentence summary)
         - Test Suite Snapshot (Current State) — table with metrics
         - CI Test Reliability (Last 10 Runs) — mature tests vs WIP vs pipeline context
         - Module Distribution — summary table
         - Test Architecture Layers — 3 layers described
         - Test Quality Snapshot — strengths/weaknesses
      5. **Test Plan (Forward Looking)** → All future/desired state:
         - Test Objectives (punchy bullets)
         - Risk-Based Prioritization (matrix with P1/P2/P3)
         - Test Environments &amp; Configuration
         - Test Data Strategy
         - Acceptance Criteria (checklist)
         - Out of Scope (explicit exclusions)
      6. **Current State Assessment** → Assumes reader knows architecture:
         - Representative Test Examples (2-3 max, most illustrative)
         - Test Design Heuristics (defined ONCE, not repeated)
      7. **Test Coverage Analysis**:
         - Critical Path Coverage (well-covered vs under-covered)
         - Edge Case &amp; Error Handling
         - Security Testing Coverage
      8. **Test Quality Metrics**:
         - Maturity Score Breakdown (table + dimension details)
         - Quantitative Metrics (table)
      9. **Recommendations &amp; Action Plan**:
         - P1 Critical (next sprint) — full details with checklists + risk cross-refs
         - P2 Important (2-3 sprints) — full details
         - P3 Nice-to-Have (backlog) — bullet list
         - Migration Plans (if applicable) — checklist + constraints
      10. **Test Execution &amp; Automation**:
          - Current State (how tests run today)
          - Recommended CI/CD Pipeline (Future State) — YAML example
          - Local Developer Workflow (Cheat Sheet)
      11. **Terminology** → Standard operations (CRUD) and scenario types
      12. **Appendices**:
          - A: Complete Test Inventory (numbers MUST match summary)
          - B: Testing Framework Details
          - C: Related Documentation (links)

      ### Template Principles

      - **Front-load value:** TL;DR with score TABLE first
      - **State separation:** "Current State" vs "Recommended (Future)" with CLEAR labels
      - **Limit examples:** 2-3 most illustrative, rest in appendix
      - **Define once:** Patterns/heuristics in dedicated section, not repeated
      - **Actionable:** Every recommendation has checklist + risk cross-reference
      - **Consistent:** Summary counts MUST match appendix exactly
      - **Avoid repetition:** Don't repeat architecture overview (Exec Summary has it)
      - **Mark references:** Label detailed commands as "Developer Cheat Sheet" or optional
      - **Scannability:** Use tables for scores, matrices, metrics
    </template>
  </documentation-schema>

  <terminology>
    <operations>
      <operation name="Create">Adding new entities</operation>
      <operation name="Read">Retrieving entities</operation>
      <operation name="Update">Modifying existing entities</operation>
      <operation name="Delete">Removing entities</operation>
      <operation name="List">Querying multiple entities</operation>
    </operations>

    <scenario-types>
      <type name="Happy Path">Normal expected behavior with valid inputs</type>
      <type name="Validation Error">Invalid inputs rejected with proper error messages</type>
      <type name="Business Rule Violation">Valid inputs violating business constraints</type>
      <type name="System Failure">External dependencies unavailable or failing</type>
      <type name="Edge Case">Boundary conditions (null, empty, max, min)</type>
      <type name="Security">Authorization, authentication, injection prevention</type>
      <type name="Performance">Response time, throughput, resource usage</type>
      <type name="Concurrency">Race conditions, deadlocks, thread safety</type>
    </scenario-types>
  </terminology>

  <error-handling>
    <scenario name="Archon fails">
      <action>Retry operation</action>
      <action>If no archon available then manage your own task system</action>
    </scenario>

    <scenario name="No tests found">
      <action>Create initial test plan from scratch</action>
      <action>Create Archon tasks for implementation</action>
    </scenario>

    <scenario name="CI unavailable">
      <action>Note reason</action>
      <action>Use fallback score</action>
      <action>Continue analysis</action>
    </scenario>

    <scenario name="Agent error">
      <action>Log error</action>
      <action>Continue without CI data</action>
      <action>Use config-based scoring</action>
    </scenario>
  </error-handling>

  <arguments>
    <syntax>[module-filter] [--file] [--plan]</syntax>

    <arg name="module-filter" optional="true">
      <description>Analyze specific modules/paths only</description>
      <example>partition-core</example>
    </arg>

    <arg name="--file" optional="true" flag="true">
      <description>Write results to ___/tests-info.md file (creates ___ directory if needed)</description>
      <default>Output directly, no file write</default>
    </arg>

    <arg name="--plan" optional="true" flag="true">
      <description>Create Archon improvement tasks from recommendations</description>
      <default>Skip task creation, only generate documentation</default>
      <creates>P1/P2/P3 tasks with T-shirt size effort estimates (Small/Medium/Large)</creates>
    </arg>

    <examples>
      <example command="partition-core">Analyze partition-core module, output directly</example>
      <example command="--file">Analyze all modules, write to ___/tests-info.md</example>
      <example command="--plan">Analyze all modules, output directly, create Archon tasks</example>
      <example command="partition-core --file --plan">Analyze partition-core, write to ___/tests-info.md, create Archon tasks</example>
    </examples>
  </arguments>

  <output>
    <if-file-flag>
      <action>Create ___ directory if it doesn't exist</action>
      <action>Write comprehensive test plan and assessment to ___/tests-info.md</action>
      <include>All sections from Documentation Schema</include>
      <exclude>Archon project IDs (tool-agnostic document)</exclude>
    </if-file-flag>

    <else>
      <action>Display comprehensive test plan and assessment directly</action>
      <action>Do NOT write any file</action>
      <content>Same content as file would contain</content>
    </else>
  </output>
</test-plan-command>
