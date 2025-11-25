"""Unit tests for gitlab module."""

import json
import os
from subprocess import CalledProcessError
from unittest.mock import Mock, patch

import pytest

from sdlc.lib.gitlab import (
    create_merge_request,
    extract_project_path,
    fetch_issue,
    fetch_issue_notes,
    fetch_open_issues,
    get_gitlab_env,
    get_gitlab_host,
    get_repo_url,
    make_issue_comment,
    mark_issue_in_progress,
)


class TestGetGitlabEnv:
    """Tests for get_gitlab_env function."""

    def test_returns_none_without_token(self):
        """Test returns None when GITLAB_TOKEN is not set."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_gitlab_env()
            assert result is None

    def test_returns_env_with_token(self):
        """Test returns environment dict when GITLAB_TOKEN is set."""
        with patch.dict(os.environ, {"GITLAB_TOKEN": "test-token", "PATH": "/usr/bin"}):
            result = get_gitlab_env()
            assert result is not None
            assert result["GITLAB_TOKEN"] == "test-token"
            assert "PATH" in result


class TestExtractProjectPath:
    """Tests for extract_project_path function."""

    def test_extracts_from_https_url(self):
        """Test extraction from HTTPS URL."""
        url = "https://gitlab.com/owner/repo"
        result = extract_project_path(url)
        assert result == "owner/repo"

    def test_extracts_from_https_url_with_git_suffix(self):
        """Test extraction from HTTPS URL with .git suffix."""
        url = "https://gitlab.com/owner/repo.git"
        result = extract_project_path(url)
        assert result == "owner/repo"

    def test_extracts_from_self_hosted_url(self):
        """Test extraction from self-hosted GitLab URL."""
        url = "https://community.opengroup.org/danielscholl/osdu-agent"
        result = extract_project_path(url)
        assert result == "danielscholl/osdu-agent"

    def test_extracts_from_ssh_url(self):
        """Test extraction from SSH URL."""
        url = "git@gitlab.com:owner/repo.git"
        result = extract_project_path(url)
        assert result == "owner/repo"

    def test_extracts_from_nested_group_url(self):
        """Test extraction from URL with nested groups."""
        url = "https://gitlab.com/group/subgroup/repo"
        result = extract_project_path(url)
        assert result == "group/subgroup/repo"

    def test_handles_trailing_slash(self):
        """Test handles trailing slash in URL."""
        url = "https://gitlab.com/owner/repo/"
        result = extract_project_path(url)
        assert result == "owner/repo"

    def test_raises_on_invalid_url(self):
        """Test raises ValueError on invalid URL."""
        url = "not-a-valid-url"
        with pytest.raises(ValueError):
            extract_project_path(url)


class TestGetGitlabHost:
    """Tests for get_gitlab_host function."""

    def test_extracts_from_https_url(self):
        """Test extraction from HTTPS URL."""
        url = "https://gitlab.com/owner/repo"
        result = get_gitlab_host(url)
        assert result == "gitlab.com"

    def test_extracts_from_self_hosted_url(self):
        """Test extraction from self-hosted GitLab URL."""
        url = "https://community.opengroup.org/owner/repo"
        result = get_gitlab_host(url)
        assert result == "community.opengroup.org"

    def test_extracts_from_ssh_url(self):
        """Test extraction from SSH URL."""
        url = "git@gitlab.com:owner/repo.git"
        result = get_gitlab_host(url)
        assert result == "gitlab.com"

    def test_returns_default_for_unknown(self):
        """Test returns default for unknown format."""
        url = "invalid"
        result = get_gitlab_host(url)
        assert result == "gitlab.com"


class TestGetRepoUrl:
    """Tests for get_repo_url function."""

    @patch("subprocess.run")
    def test_returns_git_remote_url(self, mock_run):
        """Test returns URL from git remote."""
        mock_result = Mock()
        mock_result.stdout = "https://gitlab.com/owner/repo.git\n"
        mock_run.return_value = mock_result

        result = get_repo_url()
        assert result == "https://gitlab.com/owner/repo.git"

    @patch("subprocess.run")
    def test_raises_on_no_remote(self, mock_run):
        """Test raises when no git remote exists."""
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(1, "git")

        with pytest.raises(ValueError, match="No git remote"):
            get_repo_url()


class TestFetchIssue:
    """Tests for fetch_issue function."""

    @patch("sdlc.lib.gitlab.get_gitlab_env")
    @patch("subprocess.run")
    def test_fetches_issue_successfully(self, mock_run, mock_env):
        """Test successful issue fetch."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "iid": 123,
            "title": "Test Issue",
            "description": "Issue body",
            "state": "opened",
            "author": {"id": 1, "username": "testuser"},
            "assignees": [],
            "labels": [],
            "notes": [],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "web_url": "https://gitlab.com/owner/repo/-/issues/123",
        })
        mock_run.return_value = mock_result

        result = fetch_issue("123", "owner/repo")
        assert result.iid == 123
        assert result.title == "Test Issue"
        assert result.number == 123  # Test alias property

    @patch("sdlc.lib.gitlab.get_gitlab_env")
    @patch("subprocess.run")
    def test_uses_glab_cli(self, mock_run, mock_env):
        """Test uses glab CLI."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "iid": 123,
            "title": "Test",
            "state": "opened",
            "author": {"id": 1, "username": "test"},
            "assignees": [],
            "labels": [],
            "notes": [],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "web_url": "https://gitlab.com/test",
        })
        mock_run.return_value = mock_result

        fetch_issue("123", "owner/repo")

        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "glab"
        assert "issue" in call_args
        assert "view" in call_args
        assert "123" in call_args


class TestMakeIssueComment:
    """Tests for make_issue_comment function."""

    @patch("sdlc.lib.gitlab.get_gitlab_env")
    @patch("sdlc.lib.gitlab.extract_project_path")
    @patch("sdlc.lib.gitlab.get_repo_url")
    @patch("subprocess.run")
    def test_posts_comment_successfully(self, mock_run, mock_get_url, mock_extract, mock_env, capsys):
        """Test successful comment posting."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_get_url.return_value = "https://gitlab.com/owner/repo.git"
        mock_extract.return_value = "owner/repo"
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        make_issue_comment("123", "Test comment")

        call_args = mock_run.call_args[0][0]
        assert "glab" in call_args
        assert "issue" in call_args
        assert "note" in call_args
        assert "123" in call_args

    @patch("sdlc.lib.gitlab.get_gitlab_env")
    @patch("subprocess.run")
    def test_uses_provided_project_path(self, mock_run, mock_env, capsys):
        """Test uses provided project path."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        make_issue_comment("123", "Test comment", project_path="custom/path")

        call_args = mock_run.call_args[0][0]
        assert "custom/path" in call_args


class TestMarkIssueInProgress:
    """Tests for mark_issue_in_progress function."""

    @patch("sdlc.lib.gitlab.get_gitlab_env")
    @patch("sdlc.lib.gitlab.extract_project_path")
    @patch("sdlc.lib.gitlab.get_repo_url")
    @patch("subprocess.run")
    def test_adds_label_and_assigns(self, mock_run, mock_get_url, mock_extract, mock_env):
        """Test adds label and assigns issue."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_get_url.return_value = "https://gitlab.com/owner/repo.git"
        mock_extract.return_value = "owner/repo"
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        mark_issue_in_progress("123")

        # Should make two calls: one for label, one for assignee
        assert mock_run.call_count == 2


class TestFetchOpenIssues:
    """Tests for fetch_open_issues function."""

    @patch("sdlc.lib.gitlab.get_gitlab_env")
    @patch("subprocess.run")
    def test_fetches_open_issues(self, mock_run, mock_env, capsys):
        """Test successful fetch of open issues."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([
            {
                "iid": 1,
                "title": "Issue 1",
                "description": "Body 1",
                "labels": ["bug"],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
            {
                "iid": 2,
                "title": "Issue 2",
                "labels": [],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
        ])
        mock_run.return_value = mock_result

        result = fetch_open_issues("owner/repo")
        assert len(result) == 2
        assert result[0].iid == 1
        assert result[1].iid == 2

    @patch("sdlc.lib.gitlab.get_gitlab_env")
    @patch("subprocess.run")
    def test_returns_empty_on_failure(self, mock_run, mock_env, capsys):
        """Test returns empty list on failure."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_run.side_effect = CalledProcessError(1, "glab", stderr="Error")

        result = fetch_open_issues("owner/repo")
        assert result == []


class TestCreateMergeRequest:
    """Tests for create_merge_request function."""

    @patch("sdlc.lib.gitlab.get_gitlab_env")
    @patch("sdlc.lib.gitlab.extract_project_path")
    @patch("sdlc.lib.gitlab.get_repo_url")
    @patch("subprocess.run")
    def test_creates_mr_successfully(self, mock_run, mock_get_url, mock_extract, mock_env):
        """Test successful MR creation."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_get_url.return_value = "https://gitlab.com/owner/repo.git"
        mock_extract.return_value = "owner/repo"

        # First call for git push, second for MR creation
        push_result = Mock()
        push_result.returncode = 0
        push_result.stdout = ""

        mr_result = Mock()
        mr_result.returncode = 0
        mr_result.stdout = "https://gitlab.com/owner/repo/-/merge_requests/1"

        mock_run.side_effect = [push_result, mr_result]

        result = create_merge_request(
            title="Test MR",
            description="MR description",
            source_branch="feature/test",
        )

        assert "merge_requests" in result

    @patch("sdlc.lib.gitlab.get_gitlab_env")
    @patch("sdlc.lib.gitlab.extract_project_path")
    @patch("sdlc.lib.gitlab.get_repo_url")
    @patch("subprocess.run")
    def test_uses_default_target_branch(self, mock_run, mock_get_url, mock_extract, mock_env):
        """Test uses main as default target branch."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_get_url.return_value = "https://gitlab.com/owner/repo.git"
        mock_extract.return_value = "owner/repo"

        push_result = Mock()
        push_result.returncode = 0
        push_result.stdout = ""

        mr_result = Mock()
        mr_result.returncode = 0
        mr_result.stdout = "https://gitlab.com/owner/repo/-/merge_requests/1"

        mock_run.side_effect = [push_result, mr_result]

        create_merge_request(
            title="Test MR",
            description="MR description",
            source_branch="feature/test",
        )

        # Second call is for MR creation
        mr_call_args = mock_run.call_args_list[1][0][0]
        assert "--target-branch" in mr_call_args
        assert "main" in mr_call_args

    @patch("sdlc.lib.gitlab.get_gitlab_env")
    @patch("sdlc.lib.gitlab.extract_project_path")
    @patch("sdlc.lib.gitlab.get_repo_url")
    @patch("subprocess.run")
    def test_returns_none_on_failure(self, mock_run, mock_get_url, mock_extract, mock_env, capsys):
        """Test returns None when MR creation fails."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_get_url.return_value = "https://gitlab.com/owner/repo.git"
        mock_extract.return_value = "owner/repo"

        push_result = Mock()
        push_result.returncode = 0
        push_result.stdout = ""

        mr_result = Mock()
        mr_result.returncode = 1
        mr_result.stderr = "Error creating MR"

        mock_run.side_effect = [push_result, mr_result]

        result = create_merge_request(
            title="Test MR",
            description="MR description",
            source_branch="feature/test",
        )

        assert result is None


class TestFetchIssueNotes:
    """Tests for fetch_issue_notes function."""

    @patch("sdlc.lib.gitlab.get_gitlab_env")
    @patch("subprocess.run")
    def test_fetches_notes_successfully(self, mock_run, mock_env):
        """Test successful notes fetch."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "iid": 123,
            "notes": [
                {
                    "id": 1,
                    "body": "First comment",
                    "created_at": "2024-01-01T00:00:00Z",
                },
                {
                    "id": 2,
                    "body": "Second comment",
                    "created_at": "2024-01-02T00:00:00Z",
                },
            ],
        })
        mock_run.return_value = mock_result

        result = fetch_issue_notes("owner/repo", 123)
        assert len(result) == 2
        assert result[0]["body"] == "First comment"
        assert result[1]["body"] == "Second comment"

    @patch("sdlc.lib.gitlab.get_gitlab_env")
    @patch("subprocess.run")
    def test_returns_empty_on_failure(self, mock_run, mock_env, capsys):
        """Test returns empty list on failure."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_run.side_effect = CalledProcessError(1, "glab", stderr="Error")

        result = fetch_issue_notes("owner/repo", 123)
        assert result == []

    @patch("sdlc.lib.gitlab.get_gitlab_env")
    @patch("subprocess.run")
    def test_sorts_notes_by_creation_time(self, mock_run, mock_env):
        """Test that notes are sorted by creation time."""
        mock_env.return_value = {"GITLAB_TOKEN": "test"}
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "iid": 123,
            "notes": [
                {
                    "id": 2,
                    "body": "Later comment",
                    "created_at": "2024-01-02T00:00:00Z",
                },
                {
                    "id": 1,
                    "body": "Earlier comment",
                    "created_at": "2024-01-01T00:00:00Z",
                },
            ],
        })
        mock_run.return_value = mock_result

        result = fetch_issue_notes("owner/repo", 123)
        # Should be sorted by created_at, earliest first
        assert result[0]["created_at"] == "2024-01-01T00:00:00Z"
        assert result[1]["created_at"] == "2024-01-02T00:00:00Z"
