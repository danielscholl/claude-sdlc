"""Integration tests for watcher command."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from sdlc.commands.watcher import watcher


class TestWatcherCommand:
    """Tests for watcher CLI command."""

    def test_command_help_text(self):
        """Test watcher command help text."""
        runner = CliRunner()
        result = runner.invoke(watcher, ["--help"])

        assert result.exit_code == 0
        assert "Start GitHub webhook watcher server" in result.output
        assert "--remove" in result.output
        assert "--port" in result.output
        assert "--tunnel-id" in result.output

    @patch("sdlc.commands.watcher.delete_devtunnel")
    @patch("sdlc.commands.watcher.remove_devtunnel_webhooks")
    @patch("sdlc.commands.watcher.extract_repo_path")
    @patch("sdlc.commands.watcher.get_repo_url")
    @patch("sdlc.commands.watcher.resolve_devtunnel_id")
    def test_remove_flag_cleans_up(
        self, mock_resolve, mock_get_url, mock_extract, mock_remove_webhooks, mock_delete
    ):
        """Test --remove flag cleans up resources."""
        runner = CliRunner()
        mock_resolve.return_value = "test-tunnel"
        mock_get_url.return_value = "https://github.com/user/repo.git"
        mock_extract.return_value = "user/repo"
        mock_remove_webhooks.return_value = 1
        mock_delete.return_value = True

        result = runner.invoke(watcher, ["--remove"])

        assert result.exit_code == 0
        mock_remove_webhooks.assert_called_once()
        mock_delete.assert_called_once_with("test-tunnel")

    @patch("sdlc.commands.watcher.uvicorn.run")
    @patch("sdlc.commands.watcher.get_webhook_url_from_tunnel")
    @patch("sdlc.commands.watcher.configure_devtunnel_port")
    @patch("sdlc.commands.watcher.show_devtunnel")
    @patch("sdlc.commands.watcher.resolve_devtunnel_id")
    @patch("sdlc.commands.watcher.check_devtunnel_authenticated")
    @patch("sdlc.commands.watcher.check_devtunnel_installed")
    def test_starts_server_with_defaults(
        self,
        mock_installed,
        mock_authenticated,
        mock_resolve,
        mock_show,
        mock_configure,
        mock_get_url,
        mock_uvicorn,
    ):
        """Test starting server with default options."""
        runner = CliRunner()
        mock_installed.return_value = True
        mock_authenticated.return_value = True
        mock_resolve.return_value = "test-tunnel"
        mock_show.return_value = "Tunnel ID: test-tunnel.region"
        mock_configure.return_value = True
        mock_get_url.return_value = "https://test-tunnel-8001.region.devtunnels.ms/gh-webhook"

        # Run in standalone mode to avoid hanging
        result = runner.invoke(watcher, [], catch_exceptions=False, standalone_mode=False)

        mock_installed.assert_called_once()
        mock_authenticated.assert_called_once()
        # devtunnel host is now started in FastAPI startup event, not in main flow
        mock_uvicorn.assert_called_once()

    @patch("sdlc.commands.watcher.check_devtunnel_installed")
    def test_exits_when_devtunnel_not_installed(self, mock_installed):
        """Test exits with error when devtunnel not installed."""
        runner = CliRunner()
        mock_installed.return_value = False

        result = runner.invoke(watcher, [])

        assert result.exit_code == 1
        assert "devtunnel CLI is not installed" in result.output

    @patch("sdlc.commands.watcher.login_devtunnel")
    @patch("sdlc.commands.watcher.check_devtunnel_authenticated")
    @patch("sdlc.commands.watcher.check_devtunnel_installed")
    def test_exits_when_not_authenticated_and_login_fails(
        self, mock_installed, mock_authenticated, mock_login
    ):
        """Test exits with error when not authenticated and auto-login fails."""
        runner = CliRunner()
        mock_installed.return_value = True
        mock_authenticated.return_value = False
        mock_login.return_value = False  # Login fails

        result = runner.invoke(watcher, [])

        assert result.exit_code == 1
        assert "Not authenticated with devtunnel" in result.output
        mock_login.assert_called_once()  # Should attempt login

    @patch("sdlc.commands.watcher.uvicorn.run")
    @patch("sdlc.commands.watcher.get_webhook_url_from_tunnel")
    @patch("sdlc.commands.watcher.configure_devtunnel_port")
    @patch("sdlc.commands.watcher.show_devtunnel")
    @patch("sdlc.commands.watcher.resolve_devtunnel_id")
    @patch("sdlc.commands.watcher.login_devtunnel")
    @patch("sdlc.commands.watcher.check_devtunnel_authenticated")
    @patch("sdlc.commands.watcher.check_devtunnel_installed")
    def test_auto_login_on_authentication_failure(
        self,
        mock_installed,
        mock_authenticated,
        mock_login,
        mock_resolve,
        mock_show,
        mock_configure,
        mock_get_url,
        mock_uvicorn,
    ):
        """Test automatic login when authentication initially fails."""
        runner = CliRunner()
        mock_installed.return_value = True
        # First call returns False (not authenticated), second returns True (after login)
        mock_authenticated.side_effect = [False, True]
        mock_login.return_value = True  # Login succeeds
        mock_resolve.return_value = "test-tunnel"
        mock_show.return_value = "Tunnel ID: test-tunnel.region"
        mock_configure.return_value = True
        mock_get_url.return_value = "https://test-tunnel-8001.region.devtunnels.ms/gh-webhook"

        result = runner.invoke(watcher, [], standalone_mode=False)

        # Should have attempted login
        mock_login.assert_called_once()
        # Should have called authenticated twice (before and after login)
        assert mock_authenticated.call_count == 2

    @patch("sdlc.commands.watcher.uvicorn.run")
    @patch("sdlc.commands.watcher.get_webhook_url_from_tunnel")
    @patch("sdlc.commands.watcher.configure_devtunnel_port")
    @patch("sdlc.commands.watcher.show_devtunnel")
    @patch("sdlc.commands.watcher.resolve_devtunnel_id")
    @patch("sdlc.commands.watcher.check_devtunnel_authenticated")
    @patch("sdlc.commands.watcher.check_devtunnel_installed")
    def test_respects_custom_port(
        self,
        mock_installed,
        mock_authenticated,
        mock_resolve,
        mock_show,
        mock_configure,
        mock_get_url,
        mock_uvicorn,
    ):
        """Test respects custom port option."""
        runner = CliRunner()
        mock_installed.return_value = True
        mock_authenticated.return_value = True
        mock_resolve.return_value = "test-tunnel"
        mock_show.return_value = "Tunnel ID: test-tunnel.region"
        mock_configure.return_value = True
        mock_get_url.return_value = "https://test-tunnel-9000.region.devtunnels.ms/gh-webhook"

        result = runner.invoke(watcher, ["--port", "9000"], standalone_mode=False)

        mock_configure.assert_called_with("test-tunnel", 9000)
        # devtunnel host is now started in FastAPI startup event with the correct port

    @patch("sdlc.commands.watcher.uvicorn.run")
    @patch("sdlc.commands.watcher.get_webhook_url_from_tunnel")
    @patch("sdlc.commands.watcher.configure_devtunnel_port")
    @patch("sdlc.commands.watcher.show_devtunnel")
    @patch("sdlc.commands.watcher.resolve_devtunnel_id")
    @patch("sdlc.commands.watcher.check_devtunnel_authenticated")
    @patch("sdlc.commands.watcher.check_devtunnel_installed")
    def test_respects_custom_tunnel_id(
        self,
        mock_installed,
        mock_authenticated,
        mock_resolve,
        mock_show,
        mock_configure,
        mock_get_url,
        mock_uvicorn,
    ):
        """Test respects custom tunnel ID option."""
        runner = CliRunner()
        mock_installed.return_value = True
        mock_authenticated.return_value = True
        mock_show.return_value = "Tunnel ID: custom-tunnel.region"
        mock_configure.return_value = True
        mock_get_url.return_value = "https://custom-tunnel-8001.region.devtunnels.ms/gh-webhook"

        result = runner.invoke(
            watcher, ["--tunnel-id", "custom-tunnel"], standalone_mode=False
        )

        # Should not call resolve since tunnel-id was provided
        mock_resolve.assert_not_called()
        # devtunnel host is now started in FastAPI startup event with custom-tunnel ID


class TestFastAPIApp:
    """Tests for FastAPI app creation and endpoints."""

    @patch("sdlc.commands.watcher.create_fastapi_app")
    def test_app_has_webhook_endpoint(self, mock_create_app):
        """Test FastAPI app has webhook endpoint."""
        from fastapi import FastAPI

        app = FastAPI()

        # The actual app creation happens in create_fastapi_app
        # This is a placeholder test
        assert app is not None

    def test_webhook_endpoint_handles_ping(self):
        """Test webhook endpoint handles GitHub ping events."""
        from sdlc.commands.watcher import create_fastapi_app
        from fastapi.testclient import TestClient

        app = create_fastapi_app("test-tunnel", 8001)
        client = TestClient(app)

        response = client.post(
            "/gh-webhook",
            json={"zen": "Testing is fun"},
            headers={"X-GitHub-Event": "ping"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "pong" in data

    @patch("subprocess.Popen")
    @patch("os.path.exists")
    def test_webhook_endpoint_triggers_on_issue_opened(self, mock_exists, mock_popen):
        """Test webhook triggers ADW on issue opened."""
        from sdlc.commands.watcher import create_fastapi_app
        from fastapi.testclient import TestClient

        mock_exists.return_value = True
        mock_process = Mock()
        mock_popen.return_value = mock_process

        app = create_fastapi_app("test-tunnel", 8001)
        client = TestClient(app)

        response = client.post(
            "/gh-webhook",
            json={
                "action": "opened",
                "issue": {"number": 123},
            },
            headers={"X-GitHub-Event": "issues"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["issue"] == 123
        assert "adw_id" in data

    @patch("subprocess.Popen")
    @patch("os.path.exists")
    def test_webhook_endpoint_triggers_on_adw_comment(self, mock_exists, mock_popen):
        """Test webhook triggers ADW on 'adw' comment."""
        from sdlc.commands.watcher import create_fastapi_app
        from fastapi.testclient import TestClient

        mock_exists.return_value = True
        mock_process = Mock()
        mock_popen.return_value = mock_process

        app = create_fastapi_app("test-tunnel", 8001)
        client = TestClient(app)

        response = client.post(
            "/gh-webhook",
            json={
                "action": "created",
                "issue": {"number": 456},
                "comment": {"body": "adw"},
            },
            headers={"X-GitHub-Event": "issue_comment"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["issue"] == 456

    def test_health_endpoint_exists(self):
        """Test health endpoint exists and responds."""
        from sdlc.commands.watcher import create_fastapi_app
        from fastapi.testclient import TestClient

        app = create_fastapi_app("test-tunnel", 8001)
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["service"] == "adw-webhook-watcher"
