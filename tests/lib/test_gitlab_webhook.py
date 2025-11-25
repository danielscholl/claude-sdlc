"""Unit tests for gitlab_webhook module."""

import json
from unittest.mock import Mock, patch

import pytest

from sdlc.lib.gitlab_webhook import (
    create_gitlab_webhook,
    delete_gitlab_webhook,
    ensure_webhook_configured,
    get_project_id,
    get_webhook_url_from_tunnel,
    list_gitlab_webhooks,
    remove_devtunnel_webhooks,
)


class TestGetWebhookUrlFromTunnel:
    """Tests for get_webhook_url_from_tunnel function."""

    @patch("sdlc.lib.gitlab_webhook.get_devtunnel_url")
    def test_constructs_webhook_url(self, mock_get_url):
        """Test webhook URL construction."""
        mock_get_url.return_value = "https://tunnel-8002.region.devtunnels.ms"

        result = get_webhook_url_from_tunnel("test-tunnel", 8002)
        assert result == "https://tunnel-8002.region.devtunnels.ms/gl-webhook"

    @patch("sdlc.lib.gitlab_webhook.get_devtunnel_url")
    def test_uses_custom_endpoint(self, mock_get_url):
        """Test uses custom endpoint when provided."""
        mock_get_url.return_value = "https://tunnel-8002.region.devtunnels.ms"

        result = get_webhook_url_from_tunnel("test-tunnel", 8002, "/custom-endpoint")
        assert result == "https://tunnel-8002.region.devtunnels.ms/custom-endpoint"

    @patch("sdlc.lib.gitlab_webhook.get_devtunnel_url")
    def test_adds_leading_slash_to_endpoint(self, mock_get_url):
        """Test that endpoint gets leading slash if missing."""
        mock_get_url.return_value = "https://tunnel-8002.region.devtunnels.ms"

        result = get_webhook_url_from_tunnel("test-tunnel", 8002, "webhook")
        assert result == "https://tunnel-8002.region.devtunnels.ms/webhook"

    @patch("sdlc.lib.gitlab_webhook.get_devtunnel_url")
    def test_returns_none_when_tunnel_url_fails(self, mock_get_url):
        """Test returns None when devtunnel URL cannot be obtained."""
        mock_get_url.return_value = None

        result = get_webhook_url_from_tunnel("test-tunnel", 8002)
        assert result is None


class TestGetProjectId:
    """Tests for get_project_id function."""

    def test_encodes_simple_path(self):
        """Test URL encoding of simple project path."""
        result = get_project_id("owner/repo")
        assert result == "owner%2Frepo"

    def test_encodes_nested_path(self):
        """Test URL encoding of nested group path."""
        result = get_project_id("group/subgroup/repo")
        assert result == "group%2Fsubgroup%2Frepo"


class TestListGitlabWebhooks:
    """Tests for list_gitlab_webhooks function."""

    @patch("sdlc.lib.gitlab_webhook.get_gitlab_env")
    @patch("subprocess.run")
    def test_lists_webhooks_successfully(self, mock_run, mock_env):
        """Test successful webhook listing."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([
            {"id": 1, "url": "https://example.com/webhook"},
            {"id": 2, "url": "https://tunnel.devtunnels.ms/webhook"},
        ])
        mock_run.return_value = mock_result

        result = list_gitlab_webhooks("owner/repo")
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2

    @patch("sdlc.lib.gitlab_webhook.get_gitlab_env")
    @patch("subprocess.run")
    def test_uses_glab_api(self, mock_run, mock_env):
        """Test uses glab api command."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "[]"
        mock_run.return_value = mock_result

        list_gitlab_webhooks("owner/repo")

        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "glab"
        assert call_args[1] == "api"
        assert "hooks" in call_args[2]

    @patch("sdlc.lib.gitlab_webhook.get_gitlab_env")
    @patch("subprocess.run")
    def test_returns_empty_list_on_failure(self, mock_run, mock_env, capsys):
        """Test returns empty list when API call fails."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "API error"
        mock_run.return_value = mock_result

        result = list_gitlab_webhooks("owner/repo")
        assert result == []


class TestCreateGitlabWebhook:
    """Tests for create_gitlab_webhook function."""

    @patch("sdlc.lib.gitlab_webhook.get_gitlab_env")
    @patch("subprocess.run")
    def test_creates_webhook_successfully(self, mock_run, mock_env):
        """Test successful webhook creation."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"id": 123})
        mock_run.return_value = mock_result

        result = create_gitlab_webhook("owner/repo", "https://example.com/webhook")
        assert result == 123

    @patch("sdlc.lib.gitlab_webhook.get_gitlab_env")
    @patch("subprocess.run")
    def test_sets_default_events(self, mock_run, mock_env):
        """Test sets default events (issues and notes)."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"id": 123})
        mock_run.return_value = mock_result

        create_gitlab_webhook("owner/repo", "https://example.com/webhook")

        call_args = mock_run.call_args[0][0]
        assert "issues_events=true" in call_args
        assert "note_events=true" in call_args

    @patch("sdlc.lib.gitlab_webhook.get_gitlab_env")
    @patch("subprocess.run")
    def test_returns_none_on_failure(self, mock_run, mock_env, capsys):
        """Test returns None when creation fails."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Creation failed"
        mock_run.return_value = mock_result

        result = create_gitlab_webhook("owner/repo", "https://example.com/webhook")
        assert result is None


class TestDeleteGitlabWebhook:
    """Tests for delete_gitlab_webhook function."""

    @patch("sdlc.lib.gitlab_webhook.get_gitlab_env")
    @patch("subprocess.run")
    def test_deletes_webhook_successfully(self, mock_run, mock_env):
        """Test successful webhook deletion."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = delete_gitlab_webhook("owner/repo", 123)
        assert result is True

    @patch("sdlc.lib.gitlab_webhook.get_gitlab_env")
    @patch("subprocess.run")
    def test_uses_delete_method(self, mock_run, mock_env):
        """Test uses DELETE HTTP method."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        delete_gitlab_webhook("owner/repo", 123)

        call_args = mock_run.call_args[0][0]
        assert "-X" in call_args
        assert "DELETE" in call_args

    @patch("sdlc.lib.gitlab_webhook.get_gitlab_env")
    @patch("subprocess.run")
    def test_returns_false_on_failure(self, mock_run, mock_env, capsys):
        """Test returns False when deletion fails."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Deletion failed"
        mock_run.return_value = mock_result

        result = delete_gitlab_webhook("owner/repo", 123)
        assert result is False


class TestRemoveDevtunnelWebhooks:
    """Tests for remove_devtunnel_webhooks function."""

    @patch("sdlc.lib.gitlab_webhook.delete_gitlab_webhook")
    @patch("sdlc.lib.gitlab_webhook.list_gitlab_webhooks")
    def test_removes_all_devtunnel_webhooks(self, mock_list, mock_delete):
        """Test removes all devtunnel webhooks."""
        mock_list.return_value = [
            {"id": 1, "url": "https://example.com/webhook"},
            {"id": 2, "url": "https://tunnel.devtunnels.ms/webhook"},
            {"id": 3, "url": "https://another-tunnel.devtunnels.ms/webhook"},
        ]
        mock_delete.return_value = True

        result = remove_devtunnel_webhooks("owner/repo")
        assert result == 2
        assert mock_delete.call_count == 2

    @patch("sdlc.lib.gitlab_webhook.list_gitlab_webhooks")
    def test_handles_no_devtunnel_webhooks(self, mock_list, capsys):
        """Test handles case with no devtunnel webhooks."""
        mock_list.return_value = [
            {"id": 1, "url": "https://example.com/webhook"},
        ]

        result = remove_devtunnel_webhooks("owner/repo")
        assert result == 0

    @patch("sdlc.lib.gitlab_webhook.list_gitlab_webhooks")
    def test_silent_mode_suppresses_output(self, mock_list, capsys):
        """Test silent mode suppresses output."""
        mock_list.return_value = []

        result = remove_devtunnel_webhooks("owner/repo", silent=True)
        assert result == 0

        captured = capsys.readouterr()
        assert "No devtunnel webhooks" not in captured.out


class TestEnsureWebhookConfigured:
    """Tests for ensure_webhook_configured function."""

    @patch("sdlc.lib.gitlab_webhook.create_gitlab_webhook")
    @patch("sdlc.lib.gitlab_webhook.remove_devtunnel_webhooks")
    @patch("sdlc.lib.gitlab_webhook.list_gitlab_webhooks")
    def test_skips_creation_when_exists(self, mock_list, mock_remove, mock_create):
        """Test skips creation when webhook already exists."""
        webhook_url = "https://tunnel.devtunnels.ms/gl-webhook"
        mock_list.return_value = [
            {"id": 1, "url": webhook_url},
        ]

        result = ensure_webhook_configured("owner/repo", webhook_url)
        assert result is True
        mock_create.assert_not_called()
        mock_remove.assert_not_called()

    @patch("sdlc.lib.gitlab_webhook.create_gitlab_webhook")
    @patch("sdlc.lib.gitlab_webhook.remove_devtunnel_webhooks")
    @patch("sdlc.lib.gitlab_webhook.list_gitlab_webhooks")
    def test_creates_webhook_when_not_exists(self, mock_list, mock_remove, mock_create):
        """Test creates webhook when it doesn't exist."""
        webhook_url = "https://tunnel.devtunnels.ms/gl-webhook"
        mock_list.return_value = [
            {"id": 1, "url": "https://other.com/webhook"},
        ]
        mock_remove.return_value = 0
        mock_create.return_value = 123

        result = ensure_webhook_configured("owner/repo", webhook_url)
        assert result is True
        mock_remove.assert_called_once()
        mock_create.assert_called_once()

    @patch("sdlc.lib.gitlab_webhook.create_gitlab_webhook")
    @patch("sdlc.lib.gitlab_webhook.remove_devtunnel_webhooks")
    @patch("sdlc.lib.gitlab_webhook.list_gitlab_webhooks")
    def test_returns_false_when_creation_fails(self, mock_list, mock_remove, mock_create):
        """Test returns False when webhook creation fails."""
        webhook_url = "https://tunnel.devtunnels.ms/gl-webhook"
        mock_list.return_value = []
        mock_remove.return_value = 0
        mock_create.return_value = None

        result = ensure_webhook_configured("owner/repo", webhook_url)
        assert result is False

    @patch("sdlc.lib.gitlab_webhook.create_gitlab_webhook")
    @patch("sdlc.lib.gitlab_webhook.remove_devtunnel_webhooks")
    @patch("sdlc.lib.gitlab_webhook.list_gitlab_webhooks")
    def test_passes_event_options(self, mock_list, mock_remove, mock_create):
        """Test passes event options to create webhook."""
        webhook_url = "https://tunnel.devtunnels.ms/gl-webhook"
        mock_list.return_value = []
        mock_remove.return_value = 0
        mock_create.return_value = 123

        ensure_webhook_configured(
            "owner/repo",
            webhook_url,
            issues_events=True,
            note_events=True,
        )

        mock_create.assert_called_once_with(
            "owner/repo",
            webhook_url,
            issues_events=True,
            note_events=True,
        )
