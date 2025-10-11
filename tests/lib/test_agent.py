"""Tests for Agent execution module."""

import pytest
import subprocess
from unittest.mock import Mock, patch, MagicMock
import logging

from sdlc.lib.agent import (
    parse_agent_command,
    classify_issue,
    create_branch,
    build_plan,
    locate_plan_file,
    commit_changes,
    implement_plan,
    create_pull_request,
    execute_agent_workflow,
)
from sdlc.lib.models import GitHubIssue, GitHubUser, AgentPromptResponse


@pytest.fixture
def mock_issue():
    """Create a mock GitHub issue."""
    return GitHubIssue(
        number=123,
        title="Test Issue",
        body="This is a test issue description",
        state="open",
        author=GitHubUser(login="testuser"),
        assignees=[],
        labels=[],
        comments=[],
        createdAt="2024-01-01T00:00:00Z",
        updatedAt="2024-01-01T00:00:00Z",
        url="https://github.com/test/repo/issues/123"
    )


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    return Mock(spec=logging.Logger)


class TestParseAgentCommand:
    """Tests for parse_agent_command function."""

    def test_explicit_chore_command(self):
        """Test parsing explicit /chore command."""
        comment = "sdlc /chore fix this bug"
        command, remaining, plan_only = parse_agent_command(comment)
        assert command == "/chore"
        assert remaining == "fix this bug"
        assert plan_only is False

    def test_explicit_feature_command(self):
        """Test parsing explicit /feature command."""
        comment = "sdlc /feature add dark mode"
        command, remaining, plan_only = parse_agent_command(comment)
        assert command == "/feature"
        assert remaining == "add dark mode"
        assert plan_only is False

    def test_explicit_bug_command(self):
        """Test parsing explicit /bug command."""
        comment = "sdlc /bug the login is broken"
        command, remaining, plan_only = parse_agent_command(comment)
        assert command == "/bug"
        assert remaining == "the login is broken"
        assert plan_only is False

    def test_no_explicit_command(self):
        """Test parsing without explicit command."""
        comment = "sdlc please implement this feature"
        command, remaining, plan_only = parse_agent_command(comment)
        assert command is None
        assert remaining == "please implement this feature"
        assert plan_only is False

    def test_case_insensitive(self):
        """Test case-insensitive parsing."""
        comment = "SDLC /chore Fix This"
        command, remaining, plan_only = parse_agent_command(comment)
        assert command == "/chore"
        assert remaining == "Fix This"
        assert plan_only is False

    def test_extra_whitespace(self):
        """Test handling of extra whitespace."""
        comment = "sdlc    /feature    add  feature"
        command, remaining, plan_only = parse_agent_command(comment)
        assert command == "/feature"
        assert "add" in remaining
        assert plan_only is False

    def test_plan_only_flag_double_dash(self):
        """Test parsing --plan-only flag."""
        comment = "sdlc /feature add dark mode --plan-only"
        command, remaining, plan_only = parse_agent_command(comment)
        assert command == "/feature"
        assert "add dark mode" in remaining
        assert plan_only is True

    def test_plan_only_flag_words(self):
        """Test parsing 'plan only' flag."""
        comment = "sdlc /bug fix login plan only"
        command, remaining, plan_only = parse_agent_command(comment)
        assert command == "/bug"
        assert "fix login" in remaining
        assert plan_only is True

    def test_dont_implement_flag(self):
        """Test parsing 'don't implement' flag."""
        comment = "sdlc /chore update deps don't implement"
        command, remaining, plan_only = parse_agent_command(comment)
        assert command == "/chore"
        assert "update deps" in remaining
        assert plan_only is True

    def test_no_implementation_flag(self):
        """Test parsing 'no implementation' flag."""
        comment = "sdlc /feature add feature no implementation"
        command, remaining, plan_only = parse_agent_command(comment)
        assert command == "/feature"
        assert "add feature" in remaining
        assert plan_only is True

    def test_plan_only_without_explicit_command(self):
        """Test parsing plan-only flag without explicit command."""
        comment = "sdlc please create a plan only"
        command, remaining, plan_only = parse_agent_command(comment)
        assert command is None
        assert "please create a" in remaining
        assert plan_only is True


class TestClassifyIssue:
    """Tests for classify_issue function."""

    @patch('sdlc.lib.claude.execute_prompt')
    def test_classify_as_feature(self, mock_execute, mock_issue, mock_logger):
        """Test classifying issue as feature."""
        mock_execute.return_value = AgentPromptResponse(
            output="/feature",
            success=True,
            session_id="test-session"
        )

        command, error = classify_issue(mock_issue, "test-adw", mock_logger)

        assert command == "/feature"
        assert error is None

    @patch('sdlc.lib.claude.execute_prompt')
    def test_classify_as_bug(self, mock_execute, mock_issue, mock_logger):
        """Test classifying issue as bug."""
        mock_execute.return_value = AgentPromptResponse(
            output="/bug",
            success=True,
            session_id="test-session"
        )

        command, error = classify_issue(mock_issue, "test-adw", mock_logger)

        assert command == "/bug"
        assert error is None

    @patch('sdlc.lib.claude.execute_prompt')
    def test_classification_failure(self, mock_execute, mock_issue, mock_logger):
        """Test classification failure."""
        mock_execute.return_value = AgentPromptResponse(
            output="Error classifying",
            success=False,
            session_id=None
        )

        command, error = classify_issue(mock_issue, "test-adw", mock_logger)

        assert command is None
        assert error is not None

    @patch('sdlc.lib.claude.execute_prompt')
    def test_invalid_classification(self, mock_execute, mock_issue, mock_logger):
        """Test invalid classification result."""
        mock_execute.return_value = AgentPromptResponse(
            output="/invalid",
            success=True,
            session_id="test-session"
        )

        command, error = classify_issue(mock_issue, "test-adw", mock_logger)

        assert command is None
        assert "Invalid classification" in error


class TestCreateBranch:
    """Tests for create_branch function."""

    @patch('sdlc.lib.agent.execute_slash_command')
    @patch('sdlc.lib.agent.resolve_slash_command')
    def test_successful_branch_creation(self, mock_resolve, mock_execute, mock_issue, mock_logger):
        """Test successful branch creation."""
        mock_resolve.return_value = "/branch"
        mock_execute.return_value = AgentPromptResponse(
            output="feat-123-test-adw-test-issue",
            success=True,
            session_id="test-session"
        )

        branch_name, error = create_branch(mock_issue, "/feature", "test-adw", mock_logger)

        assert branch_name == "feat-123-test-adw-test-issue"
        assert error is None

    @patch('sdlc.lib.agent.execute_slash_command')
    @patch('sdlc.lib.agent.resolve_slash_command')
    def test_failed_branch_creation(self, mock_resolve, mock_execute, mock_issue, mock_logger):
        """Test failed branch creation."""
        mock_resolve.return_value = "/branch"
        mock_execute.return_value = AgentPromptResponse(
            output="Branch creation failed",
            success=False,
            session_id=None
        )

        branch_name, error = create_branch(mock_issue, "/feature", "test-adw", mock_logger)

        assert branch_name is None
        assert error is not None


class TestBuildPlan:
    """Tests for build_plan function."""

    @patch('sdlc.lib.agent.execute_slash_command')
    @patch('sdlc.lib.agent.resolve_slash_command')
    def test_successful_plan_build(self, mock_resolve, mock_execute, mock_issue, mock_logger):
        """Test successful plan building."""
        mock_resolve.return_value = "/feature"
        mock_execute.return_value = AgentPromptResponse(
            output="Plan created successfully",
            success=True,
            session_id="test-session"
        )

        output, error = build_plan(mock_issue, "/feature", "test-adw", mock_logger)

        assert output == "Plan created successfully"
        assert error is None

    @patch('sdlc.lib.agent.execute_slash_command')
    @patch('sdlc.lib.agent.resolve_slash_command')
    def test_command_resolution(self, mock_resolve, mock_execute, mock_issue, mock_logger):
        """Test that command resolution is called."""
        mock_resolve.return_value = "/sdlc:feature"
        mock_execute.return_value = AgentPromptResponse(
            output="Plan created",
            success=True,
            session_id="test-session"
        )

        build_plan(mock_issue, "/feature", "test-adw", mock_logger)

        mock_resolve.assert_called_once_with("/feature")


class TestLocatePlanFile:
    """Tests for locate_plan_file function."""

    @patch('subprocess.run')
    def test_successful_locate(self, mock_run, mock_logger):
        """Test successful plan file location using git status."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="?? ai-specs/test-plan.md\nM  some-file.py",
            stderr=""
        )

        file_path, error = locate_plan_file("Previous output", "test-adw", mock_logger)

        assert file_path == "ai-specs/test-plan.md"
        assert error is None

    @patch('subprocess.run')
    def test_no_file_found(self, mock_run, mock_logger):
        """Test when no plan file is found."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="M  some-file.py\nM  another-file.py",
            stderr=""
        )

        file_path, error = locate_plan_file("Previous output", "test-adw", mock_logger)

        assert file_path is None
        assert "No plan file found" in error

    @patch('subprocess.run')
    def test_git_status_failure(self, mock_run, mock_logger):
        """Test when git status fails."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "git status", stderr="Git error"
        )

        file_path, error = locate_plan_file("Previous output", "test-adw", mock_logger)

        assert file_path is None
        assert "Git status failed" in error


class TestCommitChanges:
    """Tests for commit_changes function."""

    @patch('subprocess.run')
    def test_successful_commit(self, mock_run, mock_logger):
        """Test successful commit."""
        # Mock git add
        mock_run.side_effect = [
            Mock(returncode=0),  # git add
            Mock(returncode=0, stdout="chore: add implementation plan"),  # aipr commit
            Mock(returncode=0),  # git commit
        ]

        success, error = commit_changes("plan", mock_logger)

        assert success is True
        assert error is None
        assert mock_run.call_count == 3

    @patch('subprocess.run')
    def test_failed_commit(self, mock_run, mock_logger):
        """Test failed commit."""
        mock_run.side_effect = Exception("Git error")

        success, error = commit_changes("plan", mock_logger)

        assert success is False
        assert error is not None


class TestImplementPlan:
    """Tests for implement_plan function."""

    @patch('sdlc.lib.agent.execute_slash_command')
    @patch('sdlc.lib.agent.resolve_slash_command')
    def test_successful_implementation(self, mock_resolve, mock_execute, mock_logger):
        """Test successful plan implementation."""
        mock_resolve.return_value = "/implement"
        mock_execute.return_value = AgentPromptResponse(
            output="Implementation completed",
            success=True,
            session_id="test-session"
        )

        output, error = implement_plan("ai-specs/plan.md", "test-adw", mock_logger)

        assert output == "Implementation completed"
        assert error is None


class TestCreatePullRequest:
    """Tests for create_pull_request function."""

    @patch('sdlc.lib.agent.execute_slash_command')
    @patch('sdlc.lib.agent.resolve_slash_command')
    def test_successful_pr_creation(self, mock_resolve, mock_execute, mock_issue, mock_logger):
        """Test successful PR creation."""
        mock_resolve.return_value = "/pull_request"
        mock_execute.return_value = AgentPromptResponse(
            output="https://github.com/test/repo/pull/456",
            success=True,
            session_id="test-session"
        )

        pr_url, error = create_pull_request(
            "feat-123-test",
            mock_issue,
            "ai-specs/plan.md",
            "test-adw",
            mock_logger
        )

        assert pr_url == "https://github.com/test/repo/pull/456"
        assert error is None


class TestExecuteAgentWorkflow:
    """Tests for execute_agent_workflow function."""

    @patch('sdlc.lib.agent.check_claude_installed')
    @patch('sdlc.lib.agent.classify_issue')
    @patch('sdlc.lib.agent.create_branch')
    @patch('sdlc.lib.agent.build_plan')
    @patch('sdlc.lib.agent.locate_plan_file')
    @patch('sdlc.lib.agent.commit_changes')
    @patch('sdlc.lib.agent.implement_plan')
    @patch('sdlc.lib.agent.create_pull_request')
    @patch('sdlc.lib.agent.make_issue_comment')
    def test_successful_workflow(
        self,
        mock_comment,
        mock_pr,
        mock_implement,
        mock_commit,
        mock_locate,
        mock_plan,
        mock_branch,
        mock_classify,
        mock_claude,
        mock_issue,
        mock_logger
    ):
        """Test successful complete workflow."""
        # Mock all steps to succeed
        mock_claude.return_value = True
        mock_classify.return_value = ("/feature", None)
        mock_branch.return_value = ("feat-123-test", None)
        mock_plan.return_value = ("Plan output", None)
        mock_locate.return_value = ("ai-specs/plan.md", None)
        mock_commit.return_value = (True, None)
        mock_implement.return_value = ("Implementation output", None)
        mock_pr.return_value = ("https://github.com/test/repo/pull/456", None)

        success, error = execute_agent_workflow(
            issue=mock_issue,
            issue_number="123",
            adw_id="test-adw",
            logger=mock_logger,
        )

        assert success is True
        assert error is None
        # Verify all steps were called
        mock_classify.assert_called_once()
        mock_branch.assert_called_once()
        mock_plan.assert_called_once()
        mock_locate.assert_called_once()
        assert mock_commit.call_count == 1  # Single commit with plan + implementation
        mock_implement.assert_called_once()
        mock_pr.assert_called_once()

    @patch('sdlc.lib.agent.check_claude_installed')
    @patch('sdlc.lib.agent.make_issue_comment')
    def test_claude_not_installed(self, mock_comment, mock_claude, mock_issue, mock_logger):
        """Test workflow when Claude is not installed."""
        mock_claude.return_value = False

        success, error = execute_agent_workflow(
            issue=mock_issue,
            issue_number="123",
            adw_id="test-adw",
            logger=mock_logger,
        )

        assert success is False
        assert "not installed" in error.lower()

    @patch('sdlc.lib.agent.check_claude_installed')
    @patch('sdlc.lib.agent.classify_issue')
    @patch('sdlc.lib.agent.make_issue_comment')
    def test_classification_failure(self, mock_comment, mock_classify, mock_claude, mock_issue, mock_logger):
        """Test workflow when classification fails."""
        mock_claude.return_value = True
        mock_classify.return_value = (None, "Classification error")

        success, error = execute_agent_workflow(
            issue=mock_issue,
            issue_number="123",
            adw_id="test-adw",
            logger=mock_logger,
        )

        assert success is False
        assert error == "Classification error"

    @patch('sdlc.lib.agent.check_claude_installed')
    @patch('sdlc.lib.agent.make_issue_comment')
    def test_explicit_command(self, mock_comment, mock_claude, mock_issue, mock_logger):
        """Test workflow with explicit command."""
        mock_claude.return_value = True

        with patch('sdlc.lib.agent.create_branch') as mock_branch:
            mock_branch.return_value = (None, "Branch error")

            success, error = execute_agent_workflow(
                issue=mock_issue,
                issue_number="123",
                adw_id="test-adw",
                logger=mock_logger,
                explicit_command="/chore"
            )

            # Should skip classification and use explicit command
            assert success is False
            mock_branch.assert_called_once()
            # Verify the explicit command was used
            call_args = mock_branch.call_args
            assert call_args[0][1] == "/chore"

    @patch('sdlc.lib.agent.check_claude_installed')
    @patch('sdlc.lib.agent.classify_issue')
    @patch('sdlc.lib.agent.create_branch')
    @patch('sdlc.lib.agent.build_plan')
    @patch('sdlc.lib.agent.commit_changes')
    @patch('sdlc.lib.agent.locate_plan_file')
    @patch('sdlc.lib.agent.implement_plan')
    @patch('sdlc.lib.agent.create_pull_request')
    @patch('sdlc.lib.agent.make_issue_comment')
    def test_plan_only_workflow(
        self,
        mock_comment,
        mock_pr,
        mock_implement,
        mock_locate,
        mock_commit,
        mock_plan,
        mock_branch,
        mock_classify,
        mock_claude,
        mock_issue,
        mock_logger
    ):
        """Test plan-only workflow skips implementation and PR."""
        # Mock all steps to succeed
        mock_claude.return_value = True
        mock_classify.return_value = ("/feature", None)
        mock_branch.return_value = ("feat-123-test", None)
        mock_plan.return_value = ("Plan output", None)
        mock_commit.return_value = (True, None)

        success, error = execute_agent_workflow(
            issue=mock_issue,
            issue_number="123",
            adw_id="test-adw",
            logger=mock_logger,
            plan_only=True
        )

        assert success is True
        assert error is None

        # Verify steps 1-4 were called
        mock_classify.assert_called_once()
        mock_branch.assert_called_once()
        mock_plan.assert_called_once()
        assert mock_commit.call_count == 1  # Only plan commit, not implementation

        # Verify steps 5-8 were NOT called
        mock_locate.assert_not_called()
        mock_implement.assert_not_called()
        mock_pr.assert_not_called()
