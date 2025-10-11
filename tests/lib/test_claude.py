"""Tests for Claude Code CLI interaction module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess
import os

from sdlc.lib.claude import (
    check_claude_installed,
    execute_claude_command,
    execute_slash_command,
    execute_prompt,
    check_slash_command_exists,
    resolve_slash_command,
)
from sdlc.lib.models import AgentPromptResponse


class TestCheckClaudeInstalled:
    """Tests for check_claude_installed function."""

    @patch('subprocess.run')
    def test_claude_installed(self, mock_run):
        """Test when Claude CLI is installed."""
        mock_run.return_value = Mock(returncode=0)
        assert check_claude_installed() is True
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_claude_not_installed(self, mock_run):
        """Test when Claude CLI is not installed."""
        mock_run.side_effect = FileNotFoundError()
        assert check_claude_installed() is False

    @patch('subprocess.run')
    def test_claude_timeout(self, mock_run):
        """Test when Claude CLI check times out."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd='claude', timeout=5)
        assert check_claude_installed() is False


class TestExecuteClaudeCommand:
    """Tests for execute_claude_command function."""

    @patch('subprocess.Popen')
    def test_successful_execution(self, mock_popen):
        """Test successful command execution."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = iter(['{"session_id": "test-123", "result": "Success"}\n'])
        mock_process.stderr = Mock()
        mock_process.wait = Mock()
        mock_popen.return_value = mock_process

        success, output, session_id = execute_claude_command(
            command=["claude", "--print", "test"],
            adw_id="test-adw",
        )

        assert success is True
        assert output == "Success"
        assert session_id == "test-123"

    @patch('subprocess.Popen')
    def test_failed_execution(self, mock_popen):
        """Test failed command execution."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = iter([])
        mock_process.stderr.read = Mock(return_value='Error occurred')
        mock_process.wait = Mock()
        mock_popen.return_value = mock_process

        success, output, session_id = execute_claude_command(
            command=["claude", "--print", "test"],
            adw_id="test-adw",
        )

        assert success is False
        assert "Error occurred" in output
        assert session_id is None

    @patch('subprocess.Popen')
    def test_timeout(self, mock_popen):
        """Test command timeout."""
        mock_process = Mock()
        mock_process.stdout = iter([])
        mock_process.wait = Mock(side_effect=subprocess.TimeoutExpired(cmd='claude', timeout=10))
        mock_popen.return_value = mock_process

        success, output, session_id = execute_claude_command(
            command=["claude", "--print", "test"],
            adw_id="test-adw",
            timeout=10
        )

        assert success is False
        assert "timed out" in output.lower()
        assert session_id is None


class TestExecuteSlashCommand:
    """Tests for execute_slash_command function."""

    @patch('sdlc.lib.claude.execute_claude_command')
    def test_successful_slash_command(self, mock_execute):
        """Test successful slash command execution."""
        mock_execute.return_value = (True, "Branch created: feat-123-test", "session-123")

        response = execute_slash_command(
            slash_command="/branch",
            args=["feature", "test-adw", '{"number": 123}'],
            adw_id="test-adw",
        )

        assert response.success is True
        assert "Branch created" in response.output
        assert response.session_id == "session-123"

    @patch('sdlc.lib.claude.execute_claude_command')
    def test_failed_slash_command(self, mock_execute):
        """Test failed slash command execution."""
        mock_execute.return_value = (False, "Command failed", None)

        response = execute_slash_command(
            slash_command="/feature",
            args=["Test feature"],
            adw_id="test-adw",
        )

        assert response.success is False
        assert "failed" in response.output.lower()


class TestExecutePrompt:
    """Tests for execute_prompt function."""

    @patch('sdlc.lib.claude.execute_claude_command')
    def test_successful_prompt(self, mock_execute):
        """Test successful prompt execution."""
        mock_execute.return_value = (True, "Response to prompt", "session-456")

        response = execute_prompt(
            prompt="Test prompt",
            adw_id="test-adw",
        )

        assert response.success is True
        assert response.output == "Response to prompt"
        assert response.session_id == "session-456"

    @patch('sdlc.lib.claude.execute_claude_command')
    def test_multi_turn_prompt(self, mock_execute):
        """Test multi-turn prompt with session ID."""
        mock_execute.return_value = (True, "Follow-up response", "session-456")

        response = execute_prompt(
            prompt="Follow-up prompt",
            adw_id="test-adw",
            session_id="session-456"
        )

        assert response.success is True
        # Verify session ID was passed in command with --resume flag
        call_args = mock_execute.call_args
        assert "--resume" in call_args[1]["command"]


class TestCheckSlashCommandExists:
    """Tests for check_slash_command_exists function."""

    @patch('os.path.exists')
    def test_command_exists(self, mock_exists):
        """Test when slash command exists."""
        mock_exists.return_value = True
        assert check_slash_command_exists("/feature") is True

    @patch('os.path.exists')
    def test_command_not_exists(self, mock_exists):
        """Test when slash command does not exist."""
        mock_exists.return_value = False
        assert check_slash_command_exists("/nonexistent") is False


class TestResolveSlashCommand:
    """Tests for resolve_slash_command function."""

    @patch('sdlc.lib.claude.check_slash_command_exists')
    def test_user_command_exists(self, mock_check):
        """Test when user-defined command exists."""
        mock_check.side_effect = lambda cmd: cmd == "/feature"
        result = resolve_slash_command("/feature")
        assert result == "/feature"

    @patch('sdlc.lib.claude.check_slash_command_exists')
    def test_fallback_to_sdlc_command(self, mock_check):
        """Test fallback to SDLC plugin command."""
        mock_check.side_effect = lambda cmd: cmd == "/sdlc:feature"
        result = resolve_slash_command("/feature")
        assert result == "/sdlc:feature"

    @patch('sdlc.lib.claude.check_slash_command_exists')
    def test_neither_exists(self, mock_check):
        """Test when neither command exists."""
        mock_check.return_value = False
        result = resolve_slash_command("/feature")
        # Should return original command to let it fail gracefully
        assert result == "/feature"
