---
description: Analyze unit tests and create comprehensive test documentation with Archon task management
argument-hint: [optional-module-filter] [--file] [--plan]
allowed-tools: Read, Glob, Grep, Task, Write, Bash, TodoWrite, mcp__archon__manage_project, mcp__archon__manage_task
---

# Test Analysis Command

## Objective

Generate a comprehensive **TEST PLAN + ASSESSMENT** document with integrated Archon task management that:
1. Assesses current state (what exists, coverage, quality)
2. Provides clear test plan (objectives, scope, priorities, strategy)
3. Delivers actionable recommendations tracked as Archon tasks
4. Creates all improvement tasks in Archon for visibility and tracking

The document serves both as historical assessment and forward-looking plan with full task management integration.

---

## Critical Consistency Rules (Priority Order)

### P0 - MUST NEVER VIOLATE

1. **Archon Integration**: NEVER skip, ONE task in "doing" at a time, track all phases
2. **Mature/WIP Scoring**: Score MATURE tests only (exclude ≤10% pass rate jobs), report WIP separately
3. **State Separation**: Current facts ≠ Future recommendations (label clearly: "Current State" vs "Recommended (Future)")
4. **File Writing**: ONLY write `tests-info.md` if `--file` argument provided (otherwise output directly)

### P1 - MUST MAINTAIN

5. **Number Consistency**: Summary counts = Appendix exactly (use ~ only if genuinely approximate + explain why)
6. **Score Alignment**: Maturity scores MUST match described gaps (many missing tests → 6-7/10, not 8+/10)
7. **CI Detection Accuracy**:
   - Coverage tool in pom.xml → "Configured (JaCoCo X.Y.Z)", NOT "Not configured"
   - No CI files → "Manual runs only" + mark CI sections as "Recommended (Future State)"
   - Don't show CI pipeline examples in "Current State" if no CI detected

### P2 - SHOULD FOLLOW

8. **Template Quality**: Front-load value (TL;DR first), limit examples (2-3 max), actionable checklists
9. **Terminology Standards**: Use standardized operations (CRUD) and scenario types (Happy Path, etc.)

---

## Common Patterns (Define Once, Reference Many)

### Archon Task Lifecycle Pattern

```
Phase Start:  mcp__archon__manage_task("update", task_id="...", status="doing")
              (Only ONE task in "doing" at any time)
Phase End:    mcp__archon__manage_task("update", task_id="...", status="review")
Final:        Update all analysis tasks → "done"
```

### Test File Discovery Patterns

```
Patterns: **/test/**/*.*, **/tests/**/*.*, **/*Test.*, **/*Tests.*, 
          **/*_test.*, **/test_*.*, **/*Spec.*, **/*.spec.*, 
          **/src/test/**/*.*, **/testing/**/*.*
Tools: Glob (search patterns), Grep (test annotations: @Test, describe, it)
```

### Test Analysis Patterns

**AAA Pattern (Unit Tests):**
```
Arrange: Set up test data, mocks, preconditions
Act:     Execute method under test
Assert:  Verify expected outcomes
```

**Given-When-Then Pattern (Integration/Acceptance Tests):**
```
Given: Initial context and preconditions
When:  Action or event occurs
Then:  Expected outcomes and side effects
```

Use the best pattern based on what works best for the tests being analyzed.

### CI Integration Pattern

```
Detection:
  .github/workflows/*.yml → platform=github
  .gitlab-ci.yml → platform=gitlab
  Neither → no CI detected, score 2-3/10, skip CI history

Execution:
  Launch: Task(subagent_type="{platform}-ci-historian", prompt="Analyze test history...")
  
Response Handling:
  ✅ SUCCESS (full mode):
     Extract: metrics.mature_test_execution.pass_rate_percent → use for Automation score
     Extract: assessment.key_findings → CI Reliability section
     Extract: metrics.wip_test_execution → report separately as "Capabilities in Development"
     
  ⚠️ LIMITED (config-only):
     Score: 6-7/10 (GitLab without glab CLI)
     Note: Recommend installing glab for full metrics
     
  ❌ UNAVAILABLE:
     Extract: reason from agent response
     Note: "CI history unavailable: [reason]"
     Fallback: 4-5/10 if CI configured, 2-3/10 if no CI

Critical: MATURE tests only for scoring (exclude pass_rate ≤10% or always-skipped WIP jobs)
```

---

## Maturity Scoring Tables

### Overall Maturity Calculation

| Dimension | Weight | Score Criteria | Your Score |
|-----------|--------|----------------|------------|
| **Completeness** | 30% | 9-10: >90% critical paths covered<br>7-8: 70-89%<br>5-6: 50-69%<br><5: <50% | [X]/10 |
| **Quality** | 25% | 9-10: Excellent assertions, isolation, clarity<br>7-8: Good<br>5-6: Fair<br><5: Poor | [Y]/10 |
| **Maintainability** | 20% | 9-10: Excellent DRY, organization<br>7-8: Good<br>5-6: Fair<br><5: Poor duplication | [Z]/10 |
| **Security Focus** | 15% | 9-10: Comprehensive (auth, crypto, injection)<br>7-8: Good coverage<br>5-6: Basic<br><5: Minimal/None | [W]/10 |
| **Automation** | 10% | See Automation table below | [V]/10 |
| **TOTAL** | 100% | Weighted sum | **[Score]/10** |

### Automation Dimension Scoring

| Mature Test Pass Rate | CI Status | Score | Notes |
|----------------------|-----------|-------|-------|
| ≥90% + stable + low flakiness | CI configured | 9-10 | Excellent reliability |
| 70-89% + low flakiness | CI configured | 7-8 | Good, some instability |
| 50-69% + medium flakiness | CI configured | 5-6 | Needs improvement |
| <50% or high flakiness | CI configured | 3-4 | Poor quality, blocking |
| N/A (auth unavailable) | CI configured | 6-7 | Config verified, runtime unknown |
| N/A | Coverage tool only, no CI | 4-5 | Partial automation |
| N/A | No CI, no coverage | 2-3 | Manual only |

**Critical Notes:**
- Use `metrics.mature_test_execution.pass_rate_percent` from CI historian
- Exclude WIP jobs (≤10% pass rate or always skipped) from score
- Report WIP separately in "Capabilities in Development" section
- If mature tests have <70% pass rate, add to "Critical Gaps" in TL;DR

---

## 10-Phase Workflow

### PHASE 1 - Archon Setup

**Steps:**
1. Create Archon project: `mcp__archon__manage_project("create", title="Test Analysis - [Project Name]")`
2. Store `project_id` for use throughout execution
3. Create 6 analysis phase tasks (all status="todo"):
   - Discover test files and frameworks
   - Fetch CI/CD test run history
   - Inventory test classes and methods
   - Analyze test patterns and quality
   - Assess coverage and identify gaps
   - Generate test plan and documentation

---

### PHASE 2 - Discovery (Apply Archon Lifecycle)

**Update task status to "doing"**

**Step 1 - Locate Test Files**
- Use Test File Discovery Patterns (above)
- Count ACTUAL files and methods (use ~ only if truly approximate + explain why)
- Tools: Glob, Grep

**Step 2 - Identify Testing Frameworks**
- Check build files: `pom.xml`, `build.gradle`, `package.json`, `requirements.txt`
- Look for: JUnit 4/5, TestNG, Mockito, pytest, unittest, Jest, Mocha, NUnit, xUnit
- Use Grep for framework-specific imports and annotations

**Step 3 - Detect Coverage & CI Configuration**

*Coverage Detection:*
- Check for JaCoCo, Cobertura, Istanbul, Coverage.py in build files
- States:
  - "Configured (tool X.Y.Z) + enforced in CI" (plugin + CI validation)
  - "Configured (tool X.Y.Z) - not enforced" (plugin but no CI)
  - "Not configured" (no plugin in build files)

*CI Detection:*
- Look for: `.gitlab-ci.yml`, `.github/workflows/*.yml`, `Jenkinsfile`, `.circleci/config.yml`
- States:
  - "Fully automated" (CI file with test stages)
  - "Partially automated" (CI file, unclear test integration)
  - "Manual only" (no CI files detected)

**Step 4 - Map Test Structure**
- Organization: by feature / layer / component
- Test type separation: unit vs integration vs e2e
- Source ↔ test directory correspondence
- Test resources: fixtures, mocks, test data

**Complete: Update task status to "review"**

---

### PHASE 2.5 - CI History (Optional, Continue if Unavailable)

**Update CI history task to "doing"**

**Platform Detection:**
```bash
# Check GitHub
ls .github/workflows/*.yml 2>/dev/null | head -1

# Check GitLab
test -f .gitlab-ci.yml && echo "found"

# Priority: If both, prefer GitHub
```

**Execute CI Integration Pattern** (defined above)

**Automation Score Mapping:**
- Agent returns 0-10 score based on MATURE test jobs only
- Principle: Score reflects quality of completed test suites, not completeness of product capabilities
- WIP capabilities tracked separately without penalizing established test reliability

**Example Scenario:**
```
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
```

**Complete: Update task status to "review"**

---

### PHASE 3 - Inventory (Apply Archon Lifecycle)

**Update inventory task to "doing"**

**Step 1 - Catalog Test Classes**

Extract from each test file:
- Test class/suite names and purpose
- Package/module structure
- Class-level annotations (@RunWith, @ExtendWith, etc.)
- Setup/teardown methods (@Before, @After, @BeforeEach, etc.)
- Number of test methods per class

**Step 2 - Catalog Test Methods**

Extract for each test method:
- Method name and readability
- Test annotations (@Test, test type, tags, parameters)
- Description or documentation
- Parameterized test variations

**Step 3 - Build Structured Inventory**

Structure:
```
Module/Component
  └─ Test Class/Suite
      └─ Test Method/Case
```

Metrics:
- Total test files
- Total test classes
- Total test methods
- Tests per module/component

**Critical:** Keep detailed inventory for APPENDIX only. Main document has summary tables.

**Consistency Check:** Ensure numbers in summary = appendix EXACTLY. If "56 test files" in summary, appendix lists exactly 56.

**Complete: Update task status to "review"**

---

### PHASE 4 - Analysis (Apply Archon Lifecycle)

**Update analyze task to "doing"**

**Step 1 - Analyze Test Purpose** (2-3 representative tests per major module)

For each representative test:
- What is the subject under test (SUT)?
- What specific behavior is being validated?
- What is being asserted (expected outcome)?
- What input conditions or state is tested?

Method: Read test code, analyze using appropriate pattern:
- **AAA pattern** for unit tests (Arrange-Act-Assert)
- **Given-When-Then pattern** for integration/acceptance tests

**Step 2 - Classify Test Types** (Use Standardized Terminology)

**Operations:** Create, Read, Update, Delete, List

**Scenario Types:**
- **Happy Path:** Normal expected behavior with valid inputs
- **Validation Error:** Invalid inputs rejected with proper error messages
- **Business Rule Violation:** Valid inputs that violate business constraints
- **System Failure:** External dependencies unavailable or failing
- **Edge Case:** Boundary conditions (null, empty, max, min)
- **Security:** Authorization, authentication, injection prevention
- **Performance:** Response time, throughput, resource usage
- **Concurrency:** Race conditions, deadlocks, thread safety

**Accuracy:** If literally ZERO concurrency tests, say "None" not "Minimal"

**Step 3 - Analyze Dependencies**
- What's mocked/stubbed?
- Mocking framework (Mockito, mock, sinon, etc.)
- Test isolation vs shared state
- External resources (databases, files, network)
- Test fixtures and data builders

**Step 4 - Analyze Assertions**
- Number and type per test
- Quality (specific vs generic)
- Assertion libraries (AssertJ, Chai, etc.)
- Completeness (partial vs full verification)

**Step 5 - Identify Risk Areas**

Risk Dimensions:
- **Business Impact:** What breaks if this fails?
- **Change Frequency:** How often does this code change?
- **Complexity:** How hard to understand/maintain?
- **Security Sensitivity:** Auth, encryption, PII handling?

Output: Risk vs coverage matrix for the plan

**Complete: Update task status to "review"**

---

### PHASE 5 - Pattern Recognition

**Step 1 - Naming Conventions**
- Test method patterns (should*, test*, given*When*Then*)
- Test class patterns (*Test, *Tests, *Spec)
- Consistency and readability
- Descriptiveness (clear what's tested?)

**Step 2 - Organizational Patterns**
- Grouping strategies (nested classes, describe blocks, suites)
- Test data management (builders, fixtures, factories)
- Setup/teardown usage
- Reusable utilities and helpers
- Base test classes or inheritance

**Note:** Define "Test Design Heuristics" ONCE in dedicated section, don't repeat

**Step 3 - Coding Patterns**
- Mocking patterns (setup, verification)
- Assertion styles
- Test data creation
- Exception testing
- Parameterized test usage

**Step 4 - Quality Metrics & Maturity Scoring**

Calculate:
- Average assertions per test
- Test method length (LOC)
- Test complexity (cyclomatic if detectable)
- Maintenance burden indicators
- Clarity score (naming, structure)

**Apply Maturity Scoring Tables** (from above)

Show calculation in BOTH:
1. Inline formula: `(Completeness×0.30) + (Quality×0.25) + ...`
2. Table format (for scannability)

---

### PHASE 6 - Value Assessment (Apply Archon Lifecycle)

**Update assess task to "doing"**

**Step 1 - Critical Path Coverage**
- Core business logic paths well-tested?
- Critical data transformations validated?
- Important API endpoints/interfaces tested?
- Security-sensitive operations validated?

**Step 2 - Edge Case Coverage**
- Boundary conditions (null, empty, max, min)?
- Error conditions and exceptions?
- Concurrent/async scenarios?
- Failure modes and recovery paths?

**Step 3 - Quality Indicators**

Positive:
- Clear, descriptive test names
- Focused tests (one thing)
- Proper isolation and mocking
- Good assertion quality
- Maintainable code

Negative:
- Vague/unclear names
- Tests too much
- Brittle/flaky tests
- No assertions
- Duplicated code

**Step 4 - Identify Gaps with Impact Analysis**

For each gap, assess:
- What could go wrong?
- What's the business impact?

Gaps:
- Untested/under-tested modules
- Missing error handling tests
- Missing edge case tests
- Missing integration tests
- Missing concurrency/performance tests

**Step 5 - Assess Maintainability**
- Easy to understand?
- Easy to modify?
- Excessive duplication?
- Test utilities well-organized?
- Would source changes require extensive test updates?

**Complete: Update task status to "review"**

---

### PHASE 7 - Test Plan Generation (Apply Archon Lifecycle)

**Update plan task to "doing"**

**Step 1 - Define Test Objectives**

Format as punchy "confidence that" bullets (5-10 words max):
```
Our tests should give confidence that:
• CRUD works correctly across all providers
• All providers behave identically at API level
• Security invariants hold (authz, encryption, no leaks)
• Caches are correct, not just fast
• Errors are predictable with correct HTTP codes
```

**Step 2 - Create Risk-Priority Matrix**

| Risk Area | Business Impact | Current Coverage | Test Gap | Priority |
|-----------|-----------------|------------------|----------|----------|
| Concurrent partition ops | Data corruption | None | High | P1 |
| Cache unavailability | Service outage | Low | High | P1 |
| Token expiry/revocation | Security breach | Medium | Medium | P2 |

**Use consistent P1/P2/P3 labels** here and in recommendations

**Step 3 - Define Test Environments**

For each (Unit, Integration, Acceptance):
- Environment description
- External dependencies
- Configuration needs
- Run commands
- Expected runtime
- Prerequisites

**Step 4 - Test Data Strategy**
- Seed data requirements
- ID/tenant/environment configuration
- Collision avoidance
- Fixture storage locations
- Test data factories/builders

**Step 5 - Acceptance Criteria**

Define "we can ship when..." criteria:
- All unit/integration tests pass
- Acceptance tests pass (at least one env per provider)
- No new high-severity defects in critical flows
- Code coverage ≥ X% for core, 100% for security-sensitive

**Step 6 - Out of Scope**

Explicitly call out what's NOT covered:
- Detailed performance/load testing
- Chaos/fault-injection testing
- Long-running soak tests
- UI/E2E testing (if applicable)

**Complete: Update task status to "review"**

---

### PHASE 8 - Documentation Generation

**Step 1 - Synthesize Findings**
- Overall test strategy and approach
- Strengths of current test suite
- Weaknesses and improvement areas
- Key patterns and conventions
- Actionable recommendations with checklists

**Step 2 - Generate Documentation**

**Location:** `tests-info.md` in project root (ONLY if `--file` argument provided)

**Important:**
- If `--file` argument: Write to `tests-info.md`
- If NO `--file` argument: Output directly (do NOT write file)

**Follow Documentation Schema** (see below)

**Exclude Archon IDs:** Document must be tool-agnostic

---

### PHASE 9 - Create Improvement Tasks (Conditional)

**Objective:** Create Archon tasks for ALL identified improvements

**ONLY execute this phase if `--plan` argument is provided**

**Effort Sizing:** Use T-shirt sizes to indicate complexity, NOT day estimates:
- **Small:** Low complexity, isolated change, minimal risk
- **Medium:** Moderate complexity, some dependencies, manageable risk
- **Large:** High complexity, many dependencies, significant risk

**Step 1 - P1 Critical Tasks**

For each P1 recommendation:
```
mcp__archon__manage_task("create", 
  project_id=..., 
  title="[P1 Improvement Name]", 
  description="[Details + risk mitigation]",
  status="todo")
Tag: Priority:P1, Type:Critical, Effort:Small|Medium|Large
```

**Step 2 - P2 Important Tasks**

For each P2 recommendation:
```
mcp__archon__manage_task("create", 
  project_id=..., 
  title="[P2 Improvement Name]", 
  description="[Details + risk mitigation]",
  status="todo")
Tag: Priority:P2, Type:Important, Effort:Small|Medium|Large
```

**Step 3 - P3 Nice-to-Have Tasks**

For each P3 recommendation:
```
mcp__archon__manage_task("create", 
  project_id=..., 
  title="[P3 Improvement Name]", 
  description="[Brief description]",
  status="todo")
Tag: Priority:P3, Type:Nice-to-have, Effort:Small|Medium|Large
```

**Step 4 - Migration Tasks** (if applicable)

Example:
```
mcp__archon__manage_task("create",
  project_id=...,
  title="Migrate from JUnit 4 to JUnit 5",
  description="[Migration checklist with steps]",
  status="todo")
Tag: Type:Migration, Effort:Large
```

**Step 5 - Link Tasks to Risks**

Update each task description with:
- Which risk from risk matrix it mitigates
- Expected impact and success criteria
- Effort justification (why Small/Medium/Large)

---

### PHASE 10 - Finalize Analysis

**Step 1 - Mark All Analysis Tasks Done**

For each of the 6 analysis phase tasks:
```
mcp__archon__manage_task("update", task_id=..., status="done")
```

**Step 2 - Generate Final Report**

**Critical:** Do NOT include Archon project IDs or task references in `tests-info.md` — document must be tool-agnostic

Summary:
- Total analysis tasks completed: 6
- Total improvement tasks created: [X] (if --plan provided)
- P1 Critical: [Y]
- P2 Important: [Z]
- P3 Nice-to-have: [W]
- Effort distribution: Small:[A], Medium:[B], Large:[C] (if --plan provided)
- Documentation: tests-info.md (if --file provided)

**Step 3 - Provide Next Steps**

For the team:
1. Review tests-info.md document
2. Prioritize P1 tasks for next sprint
3. Create work items in team's tracking system (Jira, GitHub Issues, etc.)
4. Update task estimates based on capacity

---

## Documentation Schema

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
   - Test Environments & Configuration
   - Test Data Strategy
   - Acceptance Criteria (checklist)
   - Out of Scope (explicit exclusions)
6. **Current State Assessment** → Assumes reader knows architecture:
   - Representative Test Examples (2-3 max, most illustrative)
   - Test Design Heuristics (defined ONCE, not repeated)
7. **Test Coverage Analysis**:
   - Critical Path Coverage (well-covered vs under-covered)
   - Edge Case & Error Handling
   - Security Testing Coverage
8. **Test Quality Metrics**:
   - Maturity Score Breakdown (table + dimension details)
   - Quantitative Metrics (table)
9. **Recommendations & Action Plan**:
   - P1 Critical (next sprint) — full details with checklists + risk cross-refs
   - P2 Important (2-3 sprints) — full details
   - P3 Nice-to-Have (backlog) — bullet list
   - Migration Plans (if applicable) — checklist + constraints
10. **Test Execution & Automation**:
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

---

## Terminology Standards

**Operation Names:**
- **Create:** Adding new entities
- **Read:** Retrieving entities
- **Update:** Modifying existing entities
- **Delete:** Removing entities
- **List:** Querying multiple entities

**Scenario Types:**
- **Happy Path:** Normal expected behavior with valid inputs
- **Validation Error:** Invalid inputs rejected with proper error messages
- **Business Rule Violation:** Valid inputs violating business constraints
- **System Failure:** External dependencies unavailable or failing
- **Edge Case:** Boundary conditions (null, empty, max, min)
- **Security:** Authorization, authentication, injection prevention
- **Performance:** Response time, throughput, resource usage
- **Concurrency:** Race conditions, deadlocks, thread safety

---

## Error Handling

| Scenario | Action |
|----------|--------|
| Archon fails | Retry operation, if no archon available then manage your own task system |
| No tests found | Create initial test plan from scratch, create Archon tasks for implementation |
| CI unavailable | Note reason, use fallback score, continue analysis |
| Agent error | Log error, continue without CI data, use config-based scoring |

---

## Arguments

**Syntax:** `[module-filter] [--file] [--plan]`

**module-filter** (optional): Analyze specific modules/paths only
- Example: `partition-core`

**--file** (optional): Write results to `tests-info.md` file
- Default: Output directly, no file write

**--plan** (optional): Create Archon improvement tasks from recommendations
- Default: Skip task creation, only generate documentation
- Creates P1/P2/P3 tasks with T-shirt size effort estimates (Small/Medium/Large)

**Examples:**
- `partition-core` — Analyze partition-core module, output directly
- `--file` — Analyze all modules, write to tests-info.md
- `--plan` — Analyze all modules, output directly, create Archon tasks
- `partition-core --file --plan` — Analyze partition-core, write to tests-info.md, create Archon tasks

---

## Output

**If `--file` argument provided:**
- Write comprehensive test plan and assessment to `tests-info.md`
- Include all sections from Documentation Schema
- Exclude Archon project IDs (tool-agnostic document)

**If NO `--file` argument:**
- Display comprehensive test plan and assessment directly
- Do NOT write any file
- Same content as file would contain

---
