"""Unit tests for devtunnel module."""

import os
import subprocess
from unittest.mock import MagicMock, Mock, patch

import pytest

from sdlc.lib.devtunnel import (
    check_devtunnel_authenticated,
    check_devtunnel_installed,
    configure_devtunnel_port,
    create_devtunnel,
    delete_devtunnel,
    get_devtunnel_url,
    login_devtunnel,
    resolve_devtunnel_id,
    show_devtunnel,
    start_devtunnel_host,
)


class TestResolveDevtunnelId:
    """Tests for resolve_devtunnel_id function."""

    def test_uses_env_var_when_set(self, monkeypatch):
        """Test that DEVTUNNEL_ID env var takes priority."""
        monkeypatch.setenv("DEVTUNNEL_ID", "my-custom-tunnel")
        result = resolve_devtunnel_id()
        assert result == "my-custom-tunnel"

    @patch("subprocess.run")
    def test_uses_git_repo_name_when_no_env(self, mock_run, monkeypatch):
        """Test that git repo name is used when no env var."""
        monkeypatch.delenv("DEVTUNNEL_ID", raising=False)

        mock_result = Mock()
        mock_result.stdout = "https://github.com/user/my-repo.git\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = resolve_devtunnel_id()
        assert result == "my-repo-tunnel"

    @patch("subprocess.run")
    def test_strips_git_extension(self, mock_run, monkeypatch):
        """Test that .git extension is stripped from repo name."""
        monkeypatch.delenv("DEVTUNNEL_ID", raising=False)

        mock_result = Mock()
        mock_result.stdout = "https://github.com/user/test-repo.git"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = resolve_devtunnel_id()
        assert result == "test-repo-tunnel"

    @patch("subprocess.run")
    def test_falls_back_to_default(self, mock_run, monkeypatch):
        """Test that default is used when git command fails."""
        monkeypatch.delenv("DEVTUNNEL_ID", raising=False)
        mock_run.side_effect = Exception("Git not found")

        result = resolve_devtunnel_id()
        assert result == "webhook-tunnel"


class TestCheckDevtunnelInstalled:
    """Tests for check_devtunnel_installed function."""

    @patch("subprocess.run")
    def test_returns_true_when_installed(self, mock_run):
        """Test returns True when devtunnel is installed."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = check_devtunnel_installed()
        assert result is True
        mock_run.assert_called_once_with(
            ["devtunnel", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )

    @patch("subprocess.run")
    def test_returns_false_when_not_installed(self, mock_run):
        """Test returns False when devtunnel is not installed."""
        mock_run.side_effect = FileNotFoundError()

        result = check_devtunnel_installed()
        assert result is False

    @patch("subprocess.run")
    def test_returns_false_on_timeout(self, mock_run):
        """Test returns False when command times out."""
        mock_run.side_effect = subprocess.TimeoutExpired("devtunnel", 5)

        result = check_devtunnel_installed()
        assert result is False


class TestCheckDevtunnelAuthenticated:
    """Tests for check_devtunnel_authenticated function."""

    @patch("subprocess.run")
    def test_returns_true_when_authenticated(self, mock_run):
        """Test returns True when authenticated."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_result.stdout = "User authenticated"
        mock_run.return_value = mock_result

        result = check_devtunnel_authenticated()
        assert result is True

    @patch("subprocess.run")
    def test_returns_false_when_not_authenticated(self, mock_run):
        """Test returns False when not authenticated."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Not authenticated"
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        result = check_devtunnel_authenticated()
        assert result is False

    @patch("subprocess.run")
    def test_returns_false_when_token_expired(self, mock_run):
        """Test returns False when login token is expired."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Login token expired"
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        result = check_devtunnel_authenticated()
        assert result is False

    @patch("subprocess.run")
    def test_returns_false_when_login_required(self, mock_run):
        """Test returns False when login is required."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Login required"
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        result = check_devtunnel_authenticated()
        assert result is False

    @patch("subprocess.run")
    def test_returns_false_when_not_logged_in(self, mock_run):
        """Test returns False when not logged in."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_result.stdout = "Not logged in."
        mock_run.return_value = mock_result

        result = check_devtunnel_authenticated()
        assert result is False


class TestLoginDevtunnel:
    """Tests for login_devtunnel function."""

    @patch("subprocess.run")
    def test_successful_login(self, mock_run, capsys):
        """Test successful devtunnel login."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = login_devtunnel()
        assert result is True

        captured = capsys.readouterr()
        assert "Logging in to devtunnel" in captured.out
        assert "Successfully logged in" in captured.out

    @patch("subprocess.run")
    def test_failed_login(self, mock_run, capsys):
        """Test failed devtunnel login."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = login_devtunnel()
        assert result is False

    @patch("subprocess.run")
    def test_login_timeout(self, mock_run, capsys):
        """Test login timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("devtunnel", 120)

        result = login_devtunnel()
        assert result is False


class TestCreateDevtunnel:
    """Tests for create_devtunnel function."""

    @patch("subprocess.run")
    def test_creates_tunnel_successfully(self, mock_run, capsys):
        """Test successful tunnel creation."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = create_devtunnel("test-tunnel")
        assert result is True

        captured = capsys.readouterr()
        assert "Created devtunnel: test-tunnel" in captured.out

    @patch("subprocess.run")
    def test_handles_creation_failure(self, mock_run, capsys):
        """Test handles creation failure gracefully."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Error creating tunnel"
        mock_run.return_value = mock_result

        result = create_devtunnel("test-tunnel")
        assert result is False


class TestConfigureDevtunnelPort:
    """Tests for configure_devtunnel_port function."""

    @patch("subprocess.run")
    def test_configures_port_successfully(self, mock_run, capsys):
        """Test successful port configuration."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = configure_devtunnel_port("test-tunnel", 8001)
        assert result is True

    @patch("subprocess.run")
    def test_handles_existing_port(self, mock_run, capsys):
        """Test handles already configured port."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Port already exists"
        mock_run.return_value = mock_result

        result = configure_devtunnel_port("test-tunnel", 8001)
        assert result is True


class TestShowDevtunnel:
    """Tests for show_devtunnel function."""

    @patch("subprocess.run")
    def test_returns_tunnel_info(self, mock_run):
        """Test returns tunnel information."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Tunnel ID: test-tunnel.usw2.devtunnels.ms"
        mock_run.return_value = mock_result

        result = show_devtunnel("test-tunnel")
        assert result == "Tunnel ID: test-tunnel.usw2.devtunnels.ms"

    @patch("subprocess.run")
    def test_returns_none_on_failure(self, mock_run):
        """Test returns None when tunnel not found."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Tunnel not found"
        mock_run.return_value = mock_result

        result = show_devtunnel("test-tunnel")
        assert result is None


class TestDeleteDevtunnel:
    """Tests for delete_devtunnel function."""

    @patch("subprocess.run")
    def test_deletes_tunnel_successfully(self, mock_run, capsys):
        """Test successful tunnel deletion."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = delete_devtunnel("test-tunnel")
        assert result is True

    @patch("subprocess.run")
    def test_handles_already_deleted(self, mock_run, capsys):
        """Test handles already deleted tunnel."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Tunnel not found"
        mock_run.return_value = mock_result

        result = delete_devtunnel("test-tunnel")
        assert result is True


class TestStartDevtunnelHost:
    """Tests for start_devtunnel_host function."""

    @patch("subprocess.Popen")
    def test_starts_host_successfully(self, mock_popen, capsys):
        """Test successful host start."""
        mock_process = Mock()
        mock_popen.return_value = mock_process

        result = start_devtunnel_host("test-tunnel")
        assert result == mock_process

    @patch("subprocess.Popen")
    def test_handles_start_failure(self, mock_popen, capsys):
        """Test handles host start failure."""
        mock_popen.side_effect = Exception("Failed to start")

        result = start_devtunnel_host("test-tunnel")
        assert result is None


class TestGetDevtunnelUrl:
    """Tests for get_devtunnel_url function."""

    @patch("sdlc.lib.devtunnel.show_devtunnel")
    def test_constructs_url_correctly(self, mock_show):
        """Test URL construction from tunnel info."""
        # Real devtunnel output format: just "tunnel-name.region", not the full domain
        mock_show.return_value = "Tunnel ID: test-tunnel.usw2\nOther info"

        result = get_devtunnel_url("test-tunnel", 8001)
        assert result == "https://test-tunnel-8001.usw2.devtunnels.ms"

    @patch("sdlc.lib.devtunnel.show_devtunnel")
    def test_returns_none_when_show_fails(self, mock_show):
        """Test returns None when show_devtunnel fails."""
        mock_show.return_value = None

        result = get_devtunnel_url("test-tunnel", 8001)
        assert result is None

    @patch("sdlc.lib.devtunnel.show_devtunnel")
    def test_returns_none_when_no_tunnel_id(self, mock_show):
        """Test returns None when Tunnel ID not found in output."""
        mock_show.return_value = "Some other output\nNo tunnel ID here"

        result = get_devtunnel_url("test-tunnel", 8001)
        assert result is None
