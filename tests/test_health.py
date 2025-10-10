"""Tests for health command."""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from sdlc.commands.health import (
    check_env_vars,
    check_git_repo,
    health,
    CheckResult,
)


def test_check_result_model():
    """Test CheckResult pydantic model."""
    result = CheckResult(success=True)
    assert result.success is True
    assert result.error is None
    assert result.warning is None
    assert result.details == {}


def test_check_result_with_error():
    """Test CheckResult with error."""
    result = CheckResult(success=False, error="Test error")
    assert result.success is False
    assert result.error == "Test error"


@patch.dict("os.environ", {}, clear=True)
def test_check_env_vars_missing_required():
    """Test check_env_vars detects missing required variables."""
    result = check_env_vars()
    assert result.success is False
    assert result.error == "Missing required environment variables"
    assert len(result.details["missing_required"]) > 0


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=True)
def test_check_env_vars_with_api_key():
    """Test check_env_vars with API key set."""
    result = check_env_vars()
    assert result.success is True
    assert result.error is None


@patch("sdlc.commands.health.get_repo_url")
@patch("sdlc.commands.health.extract_repo_path")
def test_check_git_repo_success(mock_extract, mock_get_url):
    """Test successful git repo check."""
    mock_get_url.return_value = "https://github.com/test/repo.git"
    mock_extract.return_value = "test/repo"

    result = check_git_repo()
    assert result.success is True
    assert result.details["repo_path"] == "test/repo"


@patch("sdlc.commands.health.get_repo_url")
def test_check_git_repo_failure(mock_get_url):
    """Test git repo check when not in a repo."""
    mock_get_url.side_effect = ValueError("No git remote found")

    result = check_git_repo()
    assert result.success is False
    assert "No git remote found" in result.error


def test_health_command_help():
    """Test health command help text."""
    runner = CliRunner()
    result = runner.invoke(health, ["--help"])
    assert result.exit_code == 0
    assert "health checks" in result.output.lower()


@patch("sdlc.commands.health.run_health_check")
def test_health_command_basic(mock_run_health):
    """Test basic health command execution."""
    from sdlc.commands.health import HealthCheckResult, CheckResult

    # Mock successful health check
    mock_result = HealthCheckResult(
        success=True,
        timestamp="2024-01-01T00:00:00",
        checks={
            "environment": CheckResult(success=True),
            "git_repository": CheckResult(success=True),
        },
        warnings=[],
        errors=[],
    )
    mock_run_health.return_value = mock_result

    runner = CliRunner()
    result = runner.invoke(health)

    # Should exit with 0 for successful health check
    assert result.exit_code == 0
    assert "HEALTHY" in result.output


@patch("sdlc.commands.health.run_health_check")
def test_health_command_with_failures(mock_run_health):
    """Test health command with failures."""
    from sdlc.commands.health import HealthCheckResult, CheckResult

    # Mock failed health check
    mock_result = HealthCheckResult(
        success=False,
        timestamp="2024-01-01T00:00:00",
        checks={
            "environment": CheckResult(
                success=False, error="Missing ANTHROPIC_API_KEY"
            ),
        },
        warnings=[],
        errors=["Missing ANTHROPIC_API_KEY"],
    )
    mock_run_health.return_value = mock_result

    runner = CliRunner()
    result = runner.invoke(health)

    # Should exit with 1 for failed health check
    assert result.exit_code == 1
    assert "UNHEALTHY" in result.output
