"""Integration tests for gitlab_watcher command."""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from sdlc.commands.gitlab_watcher import gitlab_watcher


class TestGitlabWatcherCommand:
    """Tests for gitlab-watcher CLI command."""

    def test_command_help_text(self):
        """Test gitlab-watcher command help text."""
        runner = CliRunner()
        result = runner.invoke(gitlab_watcher, ["--help"])

        assert result.exit_code == 0
        assert "Start GitLab webhook watcher server" in result.output
        assert "--remove" in result.output
        assert "--port" in result.output
        assert "--tunnel-id" in result.output

    def test_default_port_is_8002(self):
        """Test default port is 8002 (different from GitHub watcher)."""
        runner = CliRunner()
        result = runner.invoke(gitlab_watcher, ["--help"])

        assert result.exit_code == 0
        assert "8002" in result.output

    @patch("sdlc.commands.gitlab_watcher.delete_devtunnel")
    @patch("sdlc.commands.gitlab_watcher.remove_devtunnel_webhooks")
    @patch("sdlc.commands.gitlab_watcher.extract_project_path")
    @patch("sdlc.commands.gitlab_watcher.get_repo_url")
    @patch("sdlc.commands.gitlab_watcher.resolve_devtunnel_id")
    def test_remove_flag_cleans_up(
        self, mock_resolve, mock_get_url, mock_extract, mock_remove_webhooks, mock_delete
    ):
        """Test --remove flag cleans up resources."""
        runner = CliRunner()
        mock_resolve.return_value = "test-tunnel"
        mock_get_url.return_value = "https://gitlab.com/user/repo.git"
        mock_extract.return_value = "user/repo"
        mock_remove_webhooks.return_value = 1
        mock_delete.return_value = True

        result = runner.invoke(gitlab_watcher, ["--remove"])

        assert result.exit_code == 0
        mock_remove_webhooks.assert_called_once_with("user/repo", silent=True)
        mock_delete.assert_called_once_with("test-tunnel", silent=True)

    @patch("sdlc.commands.gitlab_watcher.uvicorn.run")
    @patch("sdlc.commands.gitlab_watcher.get_webhook_url_from_tunnel")
    @patch("sdlc.commands.gitlab_watcher.configure_devtunnel_port")
    @patch("sdlc.commands.gitlab_watcher.show_devtunnel")
    @patch("sdlc.commands.gitlab_watcher.resolve_devtunnel_id")
    @patch("sdlc.commands.gitlab_watcher.check_devtunnel_authenticated")
    @patch("sdlc.commands.gitlab_watcher.check_devtunnel_installed")
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
        mock_get_url.return_value = "https://test-tunnel-8002.region.devtunnels.ms/gl-webhook"

        # Run in standalone mode to avoid hanging
        runner.invoke(gitlab_watcher, [], catch_exceptions=False, standalone_mode=False)

        mock_installed.assert_called_once()
        mock_authenticated.assert_called_once()
        mock_uvicorn.assert_called_once()

    @patch("sdlc.commands.gitlab_watcher.check_devtunnel_installed")
    def test_exits_when_devtunnel_not_installed(self, mock_installed):
        """Test exits with error when devtunnel not installed."""
        runner = CliRunner()
        mock_installed.return_value = False

        result = runner.invoke(gitlab_watcher, [])

        assert result.exit_code == 1
        assert "devtunnel CLI is not installed" in result.output

    @patch("sdlc.commands.gitlab_watcher.login_devtunnel")
    @patch("sdlc.commands.gitlab_watcher.check_devtunnel_authenticated")
    @patch("sdlc.commands.gitlab_watcher.check_devtunnel_installed")
    def test_exits_when_not_authenticated_and_login_fails(
        self, mock_installed, mock_authenticated, mock_login
    ):
        """Test exits with error when not authenticated and auto-login fails."""
        runner = CliRunner()
        mock_installed.return_value = True
        mock_authenticated.return_value = False
        mock_login.return_value = False  # Login fails

        result = runner.invoke(gitlab_watcher, [])

        assert result.exit_code == 1
        assert "Not authenticated with devtunnel" in result.output
        mock_login.assert_called_once()  # Should attempt login

    @patch("sdlc.commands.gitlab_watcher.uvicorn.run")
    @patch("sdlc.commands.gitlab_watcher.get_webhook_url_from_tunnel")
    @patch("sdlc.commands.gitlab_watcher.configure_devtunnel_port")
    @patch("sdlc.commands.gitlab_watcher.show_devtunnel")
    @patch("sdlc.commands.gitlab_watcher.resolve_devtunnel_id")
    @patch("sdlc.commands.gitlab_watcher.login_devtunnel")
    @patch("sdlc.commands.gitlab_watcher.check_devtunnel_authenticated")
    @patch("sdlc.commands.gitlab_watcher.check_devtunnel_installed")
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
        mock_get_url.return_value = "https://test-tunnel-8002.region.devtunnels.ms/gl-webhook"

        runner.invoke(gitlab_watcher, [], standalone_mode=False)

        # Should have attempted login
        mock_login.assert_called_once()
        # Should have called authenticated twice (before and after login)
        assert mock_authenticated.call_count == 2

    @patch("sdlc.commands.gitlab_watcher.uvicorn.run")
    @patch("sdlc.commands.gitlab_watcher.get_webhook_url_from_tunnel")
    @patch("sdlc.commands.gitlab_watcher.configure_devtunnel_port")
    @patch("sdlc.commands.gitlab_watcher.show_devtunnel")
    @patch("sdlc.commands.gitlab_watcher.resolve_devtunnel_id")
    @patch("sdlc.commands.gitlab_watcher.check_devtunnel_authenticated")
    @patch("sdlc.commands.gitlab_watcher.check_devtunnel_installed")
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
        mock_get_url.return_value = "https://test-tunnel-9000.region.devtunnels.ms/gl-webhook"

        runner.invoke(gitlab_watcher, ["--port", "9000"], standalone_mode=False)

        mock_configure.assert_called_with("test-tunnel", 9000)

    @patch("sdlc.commands.gitlab_watcher.uvicorn.run")
    @patch("sdlc.commands.gitlab_watcher.get_webhook_url_from_tunnel")
    @patch("sdlc.commands.gitlab_watcher.configure_devtunnel_port")
    @patch("sdlc.commands.gitlab_watcher.show_devtunnel")
    @patch("sdlc.commands.gitlab_watcher.resolve_devtunnel_id")
    @patch("sdlc.commands.gitlab_watcher.check_devtunnel_authenticated")
    @patch("sdlc.commands.gitlab_watcher.check_devtunnel_installed")
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
        mock_get_url.return_value = "https://custom-tunnel-8002.region.devtunnels.ms/gl-webhook"

        runner.invoke(
            gitlab_watcher, ["--tunnel-id", "custom-tunnel"], standalone_mode=False
        )

        # Should not call resolve since tunnel-id was provided
        mock_resolve.assert_not_called()


class TestFastAPIApp:
    """Tests for FastAPI app creation and endpoints."""

    def test_webhook_endpoint_handles_push_test(self):
        """Test webhook endpoint handles GitLab push test events."""
        from sdlc.commands.gitlab_watcher import create_fastapi_app
        from fastapi.testclient import TestClient

        app = create_fastapi_app("test-tunnel", 8002)
        client = TestClient(app)

        response = client.post(
            "/gl-webhook",
            json={"object_kind": "push", "commits": []},
            headers={"X-Gitlab-Event": "Push Hook"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    @patch("sdlc.commands.gitlab_watcher.setup_logger")
    @patch("sdlc.commands.gitlab_watcher.fetch_issue")
    @patch("sdlc.commands.gitlab_watcher.extract_project_path")
    @patch("sdlc.commands.gitlab_watcher.get_repo_url")
    def test_webhook_endpoint_triggers_on_issue_opened(
        self, mock_get_url, mock_extract, mock_fetch, mock_logger
    ):
        """Test webhook triggers agent workflow on issue opened."""
        from sdlc.commands.gitlab_watcher import create_fastapi_app
        from sdlc.lib.gitlab_models import GitLabIssue, GitLabUser
        from fastapi.testclient import TestClient

        # Mock the GitLab calls
        mock_get_url.return_value = "https://gitlab.com/user/repo.git"
        mock_extract.return_value = "user/repo"
        mock_fetch.return_value = GitLabIssue(
            iid=123,
            title="Test Issue",
            description="Test body",
            state="opened",
            author=GitLabUser(id=1, username="testuser"),
            assignees=[],
            labels=[],
            notes=[],
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
            web_url="https://gitlab.com/user/repo/-/issues/123",
        )
        mock_logger.return_value = Mock()

        app = create_fastapi_app("test-tunnel", 8002)
        client = TestClient(app)

        response = client.post(
            "/gl-webhook",
            json={
                "object_kind": "issue",
                "object_attributes": {
                    "action": "open",
                    "iid": 123,
                    "title": "Test Issue",
                    "description": "Test body",
                },
                "project": {
                    "id": 456,
                    "path_with_namespace": "user/repo",
                },
            },
            headers={"X-Gitlab-Event": "Issue Hook"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["issue"] == 123
        assert "adw_id" in data

    @patch("sdlc.commands.gitlab_watcher.setup_logger")
    @patch("sdlc.commands.gitlab_watcher.fetch_issue")
    @patch("sdlc.commands.gitlab_watcher.extract_project_path")
    @patch("sdlc.commands.gitlab_watcher.get_repo_url")
    def test_webhook_endpoint_triggers_on_sdlc_comment(
        self, mock_get_url, mock_extract, mock_fetch, mock_logger
    ):
        """Test webhook triggers agent workflow on 'sdlc' comment."""
        from sdlc.commands.gitlab_watcher import create_fastapi_app
        from sdlc.lib.gitlab_models import GitLabIssue, GitLabUser
        from fastapi.testclient import TestClient

        # Mock the GitLab calls
        mock_get_url.return_value = "https://gitlab.com/user/repo.git"
        mock_extract.return_value = "user/repo"
        mock_fetch.return_value = GitLabIssue(
            iid=456,
            title="Test Issue",
            description="Test body",
            state="opened",
            author=GitLabUser(id=1, username="testuser"),
            assignees=[],
            labels=[],
            notes=[],
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
            web_url="https://gitlab.com/user/repo/-/issues/456",
        )
        mock_logger.return_value = Mock()

        app = create_fastapi_app("test-tunnel", 8002)
        client = TestClient(app)

        response = client.post(
            "/gl-webhook",
            json={
                "object_kind": "note",
                "object_attributes": {
                    "noteable_type": "Issue",
                    "note": "sdlc /feature implement this",
                },
                "issue": {
                    "iid": 456,
                    "title": "Test Issue",
                },
                "project": {
                    "id": 789,
                    "path_with_namespace": "user/repo",
                },
            },
            headers={"X-Gitlab-Event": "Note Hook"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["issue"] == 456
        assert data["command"] == "/feature"

    def test_webhook_ignores_non_issue_notes(self):
        """Test webhook ignores notes on non-issues."""
        from sdlc.commands.gitlab_watcher import create_fastapi_app
        from fastapi.testclient import TestClient

        app = create_fastapi_app("test-tunnel", 8002)
        client = TestClient(app)

        response = client.post(
            "/gl-webhook",
            json={
                "object_kind": "note",
                "object_attributes": {
                    "noteable_type": "MergeRequest",
                    "note": "sdlc do something",
                },
                "merge_request": {
                    "iid": 123,
                },
                "project": {
                    "id": 456,
                    "path_with_namespace": "user/repo",
                },
            },
            headers={"X-Gitlab-Event": "Note Hook"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"

    def test_webhook_ignores_comments_without_sdlc(self):
        """Test webhook ignores comments without 'sdlc' trigger."""
        from sdlc.commands.gitlab_watcher import create_fastapi_app
        from fastapi.testclient import TestClient

        app = create_fastapi_app("test-tunnel", 8002)
        client = TestClient(app)

        response = client.post(
            "/gl-webhook",
            json={
                "object_kind": "note",
                "object_attributes": {
                    "noteable_type": "Issue",
                    "note": "This is just a regular comment",
                },
                "issue": {
                    "iid": 123,
                },
                "project": {
                    "id": 456,
                    "path_with_namespace": "user/repo",
                },
            },
            headers={"X-Gitlab-Event": "Note Hook"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"

    def test_health_endpoint_exists(self):
        """Test health endpoint exists and responds."""
        from sdlc.commands.gitlab_watcher import create_fastapi_app
        from fastapi.testclient import TestClient

        app = create_fastapi_app("test-tunnel", 8002)
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["service"] == "adw-gitlab-webhook-watcher"


class TestWebhookPayloadParsing:
    """Tests for webhook payload parsing."""

    @patch("sdlc.commands.gitlab_watcher.setup_logger")
    @patch("sdlc.commands.gitlab_watcher.fetch_issue")
    @patch("sdlc.commands.gitlab_watcher.extract_project_path")
    @patch("sdlc.commands.gitlab_watcher.get_repo_url")
    def test_detects_plan_only_flag(
        self, mock_get_url, mock_extract, mock_fetch, mock_logger
    ):
        """Test detects plan-only flag in comment."""
        from sdlc.commands.gitlab_watcher import create_fastapi_app
        from sdlc.lib.gitlab_models import GitLabIssue, GitLabUser
        from fastapi.testclient import TestClient

        mock_get_url.return_value = "https://gitlab.com/user/repo.git"
        mock_extract.return_value = "user/repo"
        mock_fetch.return_value = GitLabIssue(
            iid=123,
            title="Test",
            description="Body",
            state="opened",
            author=GitLabUser(id=1, username="test"),
            assignees=[],
            labels=[],
            notes=[],
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
            web_url="https://gitlab.com/test",
        )
        mock_logger.return_value = Mock()

        app = create_fastapi_app("test-tunnel", 8002)
        client = TestClient(app)

        response = client.post(
            "/gl-webhook",
            json={
                "object_kind": "note",
                "object_attributes": {
                    "noteable_type": "Issue",
                    "note": "sdlc /feature plan only",
                },
                "issue": {"iid": 123},
                "project": {"id": 456, "path_with_namespace": "user/repo"},
            },
            headers={"X-Gitlab-Event": "Note Hook"},
        )

        data = response.json()
        assert data["status"] == "accepted"
        assert data["plan_only"] is True
