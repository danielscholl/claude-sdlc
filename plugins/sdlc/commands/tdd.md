---
description: Implement features using strict Test-Driven Development (Red-Green-Refactor cycle)
argument-hint: [feature-description-or-spec-path]
allowed-tools: Edit, Write, Read, Bash, Glob, Grep, Task
---

<tdd-command>
  <objective>
    Implement features using strict Test-Driven Development methodology with continuous test feedback.
    Follow the Red-Green-Refactor cycle for each increment, ensuring tests drive the design.
  </objective>

  <philosophy>
    <principle name="test-first">Write tests BEFORE implementation code</principle>
    <principle name="minimal-code">Write only enough code to pass the failing test</principle>
    <principle name="refactor-safely">Improve code only while tests are green</principle>
    <principle name="small-steps">One test at a time, one behavior at a time</principle>
    <principle name="design-emerges">Let the design emerge from the tests</principle>
  </philosophy>

  <test-runner-detection>
    <description>Detect project's test framework and runner</description>

    <detection-patterns>
      <pattern language="python">
        <files>pyproject.toml, pytest.ini, setup.cfg, requirements*.txt</files>
        <indicators>pytest, unittest</indicators>
        <watch-tool>ptw (pytest-watch) or pytest --looponfail</watch-tool>
        <run-command>pytest -v</run-command>
        <log-file>/tmp/test-watch.log</log-file>
      </pattern>

      <pattern language="javascript">
        <files>package.json, jest.config.*, vitest.config.*</files>
        <indicators>jest, vitest, mocha</indicators>
        <watch-tool>jest --watch or vitest or npm test -- --watch</watch-tool>
        <run-command>npm test</run-command>
        <log-file>/tmp/test-watch.log</log-file>
      </pattern>

      <pattern language="typescript">
        <files>package.json, jest.config.*, vitest.config.*, tsconfig.json</files>
        <indicators>jest, vitest, ts-jest</indicators>
        <watch-tool>jest --watch or vitest</watch-tool>
        <run-command>npm test</run-command>
        <log-file>/tmp/test-watch.log</log-file>
      </pattern>

      <pattern language="java">
        <files>pom.xml, build.gradle, build.gradle.kts</files>
        <indicators>junit, testng, jupiter</indicators>
        <watch-tool>./gradlew test --continuous or mvn test -Dtest=*</watch-tool>
        <run-command>mvn test or ./gradlew test</run-command>
        <log-file>/tmp/test-watch.log</log-file>
      </pattern>

      <pattern language="go">
        <files>go.mod, go.sum</files>
        <indicators>testing package, *_test.go files</indicators>
        <watch-tool>gotestsum --watch or go test ./...</watch-tool>
        <run-command>go test -v ./...</run-command>
        <log-file>/tmp/test-watch.log</log-file>
      </pattern>

      <pattern language="rust">
        <files>Cargo.toml</files>
        <indicators>#[test], #[cfg(test)]</indicators>
        <watch-tool>cargo watch -x test</watch-tool>
        <run-command>cargo test</run-command>
        <log-file>/tmp/test-watch.log</log-file>
      </pattern>

      <pattern language="dotnet">
        <files>*.csproj, *.sln</files>
        <indicators>xunit, nunit, mstest</indicators>
        <watch-tool>dotnet watch test</watch-tool>
        <run-command>dotnet test</run-command>
        <log-file>/tmp/test-watch.log</log-file>
      </pattern>
    </detection-patterns>
  </test-runner-detection>

  <phase number="0" name="setup">
    <step number="1" name="detect-environment">
      <action>Identify project language and test framework</action>
      <action>Check for existing test configuration files</action>
      <action>Locate test directory structure</action>
      <use>test-runner-detection patterns</use>
    </step>

    <step number="2" name="start-test-watcher" optional="true">
      <condition>If watch tool is available for the detected framework</condition>
      <action>Start test watcher in background</action>
      <command-template>[watch-command] > /tmp/test-watch.log 2>&amp;1 &amp;</command-template>
      <action>Store PID for cleanup</action>
      <action>Verify watcher is running</action>
      <fallback>If no watcher available, run tests manually after each change</fallback>
    </step>

    <step number="3" name="understand-requirement">
      <action>Parse the feature description or read spec file</action>
      <action>Break down into testable increments</action>
      <action>Identify first behavior to implement</action>
      <guidance>Start with the simplest, most fundamental behavior</guidance>
    </step>
  </phase>

  <phase number="1" name="red" label="Write Failing Test">
    <objective>Write a test that fails for the right reason</objective>

    <step number="1" name="write-test">
      <action>Write ONE test for ONE specific behavior</action>
      <guidelines>
        <guideline>Test should be focused and descriptive</guideline>
        <guideline>Name should clearly state expected behavior</guideline>
        <guideline>Follow project's existing test patterns</guideline>
        <guideline>Use AAA (Arrange-Act-Assert) or Given-When-Then structure</guideline>
      </guidelines>
      <naming-patterns>
        <pattern language="python">test_should_[behavior]_when_[condition]</pattern>
        <pattern language="javascript">it('should [behavior] when [condition]')</pattern>
        <pattern language="java">shouldBehaviorWhenCondition()</pattern>
        <pattern language="go">TestShouldBehaviorWhenCondition</pattern>
      </naming-patterns>
    </step>

    <step number="2" name="verify-failure">
      <action>Wait for test watcher (2-3 seconds) or run tests manually</action>
      <action>Check test output for expected failure</action>
      <verify>
        <expected>FAILED, ERROR, NameError, ImportError, undefined, not found</expected>
        <explanation>Test MUST fail - this proves the test works</explanation>
      </verify>
      <command-template>tail -50 /tmp/test-watch.log | grep -E 'FAIL|ERROR|passed'</command-template>
    </step>

    <step number="3" name="validate-failure-reason">
      <action>Confirm test fails for the RIGHT reason</action>
      <right-reasons>
        <reason>Missing function/method/class (NameError, undefined)</reason>
        <reason>Wrong return value (AssertionError)</reason>
        <reason>Missing behavior (assertion fails)</reason>
      </right-reasons>
      <wrong-reasons>
        <reason>Syntax error in test</reason>
        <reason>Import error in test file</reason>
        <reason>Test framework misconfiguration</reason>
      </wrong-reasons>
      <if-wrong>Fix the test itself, then re-verify failure</if-wrong>
    </step>

    <step number="4" name="document-failure">
      <action>Show the failing test output to confirm RED state</action>
    </step>

    <critical>If test passes, the test is WRONG - it doesn't test new behavior</critical>
    <critical>NEVER proceed to GREEN phase without a failing test</critical>
  </phase>

  <phase number="2" name="green" label="Make It Pass">
    <objective>Write the MINIMUM code to make the test pass</objective>

    <step number="1" name="minimal-implementation">
      <action>Write ONLY enough code to pass the failing test</action>
      <guidelines>
        <guideline>Hardcode values if that makes the test pass</guideline>
        <guideline>Don't generalize yet</guideline>
        <guideline>Don't add error handling for untested cases</guideline>
        <guideline>Don't optimize</guideline>
        <guideline>Fake it till you make it</guideline>
      </guidelines>
      <mantra>Do the simplest thing that could possibly work</mantra>
    </step>

    <step number="2" name="verify-pass">
      <action>Wait for test watcher (2-3 seconds) or run tests manually</action>
      <action>Check test output for success</action>
      <verify>
        <expected>PASSED, OK, green checkmark, all tests pass</expected>
      </verify>
      <command-template>tail -50 /tmp/test-watch.log | grep -E 'passed|PASSED|OK'</command-template>
    </step>

    <step number="3" name="all-tests-green">
      <action>Verify ALL tests still pass (not just the new one)</action>
      <action>Check for regressions</action>
      <if-regression>
        <action>Fix implementation to pass both old and new tests</action>
        <action>Re-verify all tests pass</action>
      </if-regression>
    </step>

    <step number="4" name="document-success">
      <action>Show the passing test output to confirm GREEN state</action>
    </step>

    <critical>Do NOT proceed until ALL tests pass</critical>
    <critical>Do NOT add features that aren't tested</critical>
  </phase>

  <phase number="3" name="refactor" label="Improve While Green">
    <objective>Improve code quality without changing behavior</objective>

    <step number="1" name="identify-improvements">
      <optional>This phase is OPTIONAL - skip if code is already clean</optional>
      <candidates>
        <candidate>Remove duplication (DRY)</candidate>
        <candidate>Improve naming</candidate>
        <candidate>Extract methods/functions</candidate>
        <candidate>Simplify conditionals</candidate>
        <candidate>Improve readability</candidate>
      </candidates>
      <not-now>
        <item>Adding new features</item>
        <item>Fixing bugs not covered by tests</item>
        <item>Performance optimization (unless tested)</item>
      </not-now>
    </step>

    <step number="2" name="refactor-incrementally">
      <action>Make ONE small change at a time</action>
      <action>Wait for test watcher or run tests</action>
      <action>Verify tests still pass</action>
      <repeat>Until satisfied with code quality</repeat>
    </step>

    <step number="3" name="verify-still-green">
      <action>Confirm ALL tests still pass after refactoring</action>
      <command-template>tail -50 /tmp/test-watch.log | grep -E 'passed|PASSED'</command-template>
      <if-broken>
        <action>IMMEDIATELY revert the change</action>
        <action>Try a different approach</action>
      </if-broken>
    </step>

    <step number="4" name="consider-test-refactoring">
      <optional>Refactor tests too if needed</optional>
      <candidates>
        <candidate>Extract test utilities</candidate>
        <candidate>Improve test names</candidate>
        <candidate>Remove test duplication</candidate>
        <candidate>Add test fixtures/factories</candidate>
      </candidates>
    </step>

    <critical>Tests MUST stay green throughout refactoring</critical>
    <critical>If tests break, revert IMMEDIATELY</critical>
  </phase>

  <cycle-repeat>
    <description>Repeat RED-GREEN-REFACTOR for each behavior</description>

    <iteration-flow>
      <step>Identify next behavior to implement</step>
      <step>Enter RED phase (write failing test)</step>
      <step>Enter GREEN phase (minimal implementation)</step>
      <step>Enter REFACTOR phase (improve code)</step>
      <step>Commit the increment (optional)</step>
      <step>Return to start for next behavior</step>
    </iteration-flow>

    <completion-criteria>
      <criterion>All planned behaviors implemented</criterion>
      <criterion>All tests pass</criterion>
      <criterion>Code is clean and well-factored</criterion>
      <criterion>No obvious duplication remains</criterion>
    </completion-criteria>
  </cycle-repeat>

  <verification-commands>
    <command purpose="check-status">tail -50 /tmp/test-watch.log | grep -E 'passed|FAILED|ERROR'</command>
    <command purpose="see-failures">tail -50 /tmp/test-watch.log | grep -A 10 'FAILED\|ERROR\|AssertionError'</command>
    <command purpose="get-summary">tail -10 /tmp/test-watch.log</command>
    <command purpose="watch-realtime">tail -f /tmp/test-watch.log</command>
    <note>Commands assume test watcher logging to /tmp/test-watch.log</note>
    <fallback>Run test command directly if no watcher configured</fallback>
  </verification-commands>

  <rules>
    <rule priority="critical">NEVER skip RED phase - failing test proves test works</rule>
    <rule priority="critical">NEVER proceed with failing tests</rule>
    <rule priority="critical">ALWAYS show test output after each phase</rule>
    <rule priority="critical">ALWAYS wait for test feedback before proceeding</rule>
    <rule priority="high">Write ONE test at a time</rule>
    <rule priority="high">Implement MINIMAL code to pass</rule>
    <rule priority="high">Refactor ONLY when green</rule>
    <rule priority="medium">Use descriptive test names</rule>
    <rule priority="medium">Follow existing project patterns</rule>
  </rules>

  <error-recovery>
    <scenario name="tests-hang">
      <action>Check test watcher log for details</action>
      <action>Restart test watcher if needed</action>
      <action>Run tests manually to diagnose</action>
    </scenario>

    <scenario name="tests-wont-pass">
      <action>Show full traceback</action>
      <action>Analyze the failure reason</action>
      <action>Check if test expectation is correct</action>
      <action>Check if implementation matches requirement</action>
    </scenario>

    <scenario name="import-fails">
      <action>This counts as RED phase - test is failing</action>
      <action>Create the missing module/class/function</action>
      <action>Verify import works, then assertion should fail</action>
    </scenario>

    <scenario name="watcher-unavailable">
      <action>Run tests manually after each change</action>
      <command-template>[run-command] 2>&amp;1 | tail -50</command-template>
    </scenario>
  </error-recovery>

  <cleanup>
    <action>Kill test watcher process when done</action>
    <action>Remove temporary log files</action>
    <command>kill $TEST_WATCHER_PID 2>/dev/null; rm -f /tmp/test-watch.log</command>
  </cleanup>

  <final-report>
    <summary>
      <item>Total TDD cycles completed</item>
      <item>Total tests written</item>
      <item>All tests passing status</item>
      <item>Key behaviors implemented</item>
      <item>Refactoring improvements made</item>
    </summary>
    <git-status>
      <command>git diff --stat</command>
      <purpose>Report files and lines changed</purpose>
    </git-status>
  </final-report>

  <arguments>
    <variable>$ARGUMENTS</variable>
    <usage>
      <example>/tdd Add user authentication with email and password</example>
      <example>/tdd .claude/specs/feature-xyz.md</example>
      <example>/tdd Implement caching layer for API responses</example>
    </usage>
  </arguments>
</tdd-command>
