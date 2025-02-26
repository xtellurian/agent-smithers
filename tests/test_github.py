"""Tests for the GitHub API integration."""

from unittest.mock import MagicMock, patch

import pytest
from github import Repository

from agent_smithers.github import GitHubClient, GitHubClientConfig


def test_github_client_config():
    """Test GitHub client configuration."""
    config = GitHubClientConfig(auth_token="test-token")
    assert config.auth_token == "test-token"


@pytest.fixture
def mock_github_client():
    """Fixture for mocked GitHub client."""
    with patch("agent_smithers.github.client.Github") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance


def test_get_repository(mock_github_client):
    """Test getting a repository."""
    mock_repo = MagicMock(spec=Repository.Repository)
    mock_repo.full_name = "owner/test-repo"
    mock_github_client.get_repo.return_value = mock_repo

    client = GitHubClient(GitHubClientConfig(auth_token="test-token"))
    repo = client.get_repository("owner/test-repo")

    assert repo.full_name == "owner/test-repo"
    mock_github_client.get_repo.assert_called_once_with("owner/test-repo")


def test_search_repositories(mock_github_client):
    """Test searching repositories."""
    mock_repo1 = MagicMock(spec=Repository.Repository)
    mock_repo1.full_name = "owner/repo1"
    mock_repo2 = MagicMock(spec=Repository.Repository)
    mock_repo2.full_name = "owner/repo2"

    mock_paginated_list = [mock_repo1, mock_repo2]
    mock_github_client.search_repositories.return_value = mock_paginated_list

    client = GitHubClient(GitHubClientConfig(auth_token="test-token"))
    results = client.search_repositories("test query")

    assert len(results) == 2
    assert results[0].full_name == "owner/repo1"
    assert results[1].full_name == "owner/repo2"
    mock_github_client.search_repositories.assert_called_once_with("test query")
