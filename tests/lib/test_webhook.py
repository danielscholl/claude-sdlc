"""Unit tests for webhook module."""

import json
from unittest.mock import Mock, patch

import pytest

from sdlc.lib.webhook import (
    create_github_webhook,
    delete_github_webhook,
    ensure_webhook_configured,
    get_webhook_url_from_tunnel,
    list_github_webhooks,
    remove_devtunnel_webhooks,
)


class TestGetWebhookUrlFromTunnel:
    """Tests for get_webhook_url_from_tunnel function."""

    @patch("sdlc.lib.webhook.get_devtunnel_url")
    def test_constructs_webhook_url(self, mock_get_url):
        """Test webhook URL construction."""
        mock_get_url.return_value = "https://tunnel-8001.region.devtunnels.ms"

        result = get_webhook_url_from_tunnel("test-tunnel", 8001)
        assert result == "https://tunnel-8001.region.devtunnels.ms/gh-webhook"

    @patch("sdlc.lib.webhook.get_devtunnel_url")
    def test_adds_leading_slash_to_endpoint(self, mock_get_url):
        """Test that endpoint gets leading slash if missing."""
        mock_get_url.return_value = "https://tunnel-8001.region.devtunnels.ms"

        result = get_webhook_url_from_tunnel("test-tunnel", 8001, "webhook")
        assert result == "https://tunnel-8001.region.devtunnels.ms/webhook"

    @patch("sdlc.lib.webhook.get_devtunnel_url")
    def test_returns_none_when_tunnel_url_fails(self, mock_get_url):
        """Test returns None when devtunnel URL cannot be obtained."""
        mock_get_url.return_value = None

        result = get_webhook_url_from_tunnel("test-tunnel", 8001)
        assert result is None


class TestListGithubWebhooks:
    """Tests for list_github_webhooks function."""

    @patch("sdlc.lib.webhook.get_github_env")
    @patch("subprocess.run")
    def test_lists_webhooks_successfully(self, mock_run, mock_env):
        """Test successful webhook listing."""
        mock_env.return_value = {"GH_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([
            {"id": 1, "config": {"url": "https://example.com/webhook"}},
            {"id": 2, "config": {"url": "https://tunnel.devtunnels.ms/webhook"}},
        ])
        mock_run.return_value = mock_result

        result = list_github_webhooks("owner/repo")
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2

    @patch("sdlc.lib.webhook.get_github_env")
    @patch("subprocess.run")
    def test_returns_empty_list_on_failure(self, mock_run, mock_env):
        """Test returns empty list when API call fails."""
        mock_env.return_value = {"GH_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "API error"
        mock_run.return_value = mock_result

        result = list_github_webhooks("owner/repo")
        assert result == []


class TestCreateGithubWebhook:
    """Tests for create_github_webhook function."""

    @patch("sdlc.lib.webhook.get_github_env")
    @patch("subprocess.run")
    def test_creates_webhook_successfully(self, mock_run, mock_env, capsys):
        """Test successful webhook creation."""
        mock_env.return_value = {"GH_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"id": 123})
        mock_run.return_value = mock_result

        result = create_github_webhook("owner/repo", "https://example.com/webhook")
        assert result == 123

    @patch("sdlc.lib.webhook.get_github_env")
    @patch("subprocess.run")
    def test_uses_default_events(self, mock_run, mock_env):
        """Test uses default events when none specified."""
        mock_env.return_value = {"GH_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"id": 123})
        mock_run.return_value = mock_result

        create_github_webhook("owner/repo", "https://example.com/webhook")

        # Verify the command included default events
        call_args = mock_run.call_args[0][0]
        assert "-f" in call_args
        assert "events[]=issues" in call_args
        assert "events[]=issue_comment" in call_args

    @patch("sdlc.lib.webhook.get_github_env")
    @patch("subprocess.run")
    def test_returns_none_on_failure(self, mock_run, mock_env, capsys):
        """Test returns None when creation fails."""
        mock_env.return_value = {"GH_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Creation failed"
        mock_run.return_value = mock_result

        result = create_github_webhook("owner/repo", "https://example.com/webhook")
        assert result is None


class TestDeleteGithubWebhook:
    """Tests for delete_github_webhook function."""

    @patch("sdlc.lib.webhook.get_github_env")
    @patch("subprocess.run")
    def test_deletes_webhook_successfully(self, mock_run, mock_env, capsys):
        """Test successful webhook deletion."""
        mock_env.return_value = {"GH_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = delete_github_webhook("owner/repo", 123)
        assert result is True

    @patch("sdlc.lib.webhook.get_github_env")
    @patch("subprocess.run")
    def test_handles_204_response(self, mock_run, mock_env):
        """Test handles 204 No Content response."""
        mock_env.return_value = {"GH_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 204
        mock_run.return_value = mock_result

        result = delete_github_webhook("owner/repo", 123)
        assert result is True

    @patch("sdlc.lib.webhook.get_github_env")
    @patch("subprocess.run")
    def test_returns_false_on_failure(self, mock_run, mock_env, capsys):
        """Test returns False when deletion fails."""
        mock_env.return_value = {"GH_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Deletion failed"
        mock_run.return_value = mock_result

        result = delete_github_webhook("owner/repo", 123)
        assert result is False


class TestRemoveDevtunnelWebhooks:
    """Tests for remove_devtunnel_webhooks function."""

    @patch("sdlc.lib.webhook.delete_github_webhook")
    @patch("sdlc.lib.webhook.list_github_webhooks")
    def test_removes_all_devtunnel_webhooks(self, mock_list, mock_delete, capsys):
        """Test removes all devtunnel webhooks."""
        mock_list.return_value = [
            {"id": 1, "config": {"url": "https://example.com/webhook"}},
            {"id": 2, "config": {"url": "https://tunnel.devtunnels.ms/webhook"}},
            {"id": 3, "config": {"url": "https://another-tunnel.devtunnels.ms/webhook"}},
        ]
        mock_delete.return_value = True

        result = remove_devtunnel_webhooks("owner/repo")
        assert result == 2
        assert mock_delete.call_count == 2

    @patch("sdlc.lib.webhook.list_github_webhooks")
    def test_handles_no_devtunnel_webhooks(self, mock_list, capsys):
        """Test handles case with no devtunnel webhooks."""
        mock_list.return_value = [
            {"id": 1, "config": {"url": "https://example.com/webhook"}},
        ]

        result = remove_devtunnel_webhooks("owner/repo")
        assert result == 0


class TestEnsureWebhookConfigured:
    """Tests for ensure_webhook_configured function."""

    @patch("sdlc.lib.webhook.create_github_webhook")
    @patch("sdlc.lib.webhook.remove_devtunnel_webhooks")
    @patch("sdlc.lib.webhook.list_github_webhooks")
    def test_skips_creation_when_exists(self, mock_list, mock_remove, mock_create, capsys):
        """Test skips creation when webhook already exists."""
        webhook_url = "https://tunnel.devtunnels.ms/webhook"
        mock_list.return_value = [
            {"id": 1, "config": {"url": webhook_url}},
        ]

        result = ensure_webhook_configured("owner/repo", webhook_url)
        assert result is True
        mock_create.assert_not_called()
        mock_remove.assert_not_called()

    @patch("sdlc.lib.webhook.create_github_webhook")
    @patch("sdlc.lib.webhook.remove_devtunnel_webhooks")
    @patch("sdlc.lib.webhook.list_github_webhooks")
    def test_creates_webhook_when_not_exists(self, mock_list, mock_remove, mock_create, capsys):
        """Test creates webhook when it doesn't exist."""
        webhook_url = "https://tunnel.devtunnels.ms/webhook"
        mock_list.return_value = [
            {"id": 1, "config": {"url": "https://other.com/webhook"}},
        ]
        mock_remove.return_value = 0
        mock_create.return_value = 123

        result = ensure_webhook_configured("owner/repo", webhook_url)
        assert result is True
        mock_remove.assert_called_once()
        mock_create.assert_called_once()

    @patch("sdlc.lib.webhook.create_github_webhook")
    @patch("sdlc.lib.webhook.remove_devtunnel_webhooks")
    @patch("sdlc.lib.webhook.list_github_webhooks")
    def test_returns_false_when_creation_fails(self, mock_list, mock_remove, mock_create):
        """Test returns False when webhook creation fails."""
        webhook_url = "https://tunnel.devtunnels.ms/webhook"
        mock_list.return_value = []
        mock_remove.return_value = 0
        mock_create.return_value = None

        result = ensure_webhook_configured("owner/repo", webhook_url)
        assert result is False
