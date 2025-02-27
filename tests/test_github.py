"""Tests for the GitHub API integration."""

from unittest.mock import MagicMock, patch
import pytest
from github import ContentFile, Organization, Repository

from agent_smithers.github import GitHubClient, GitHubClientConfig

# Constants
NUM_TEST_REPOS = 2


def test_github_client_config():
    """Test GitHub client configuration."""
    config = GitHubClientConfig(organization="test-org")
    assert config.organization == "test-org"


@pytest.fixture
def mock_github_client():
    """Fixture for mocked GitHub client."""
    with patch("agent_smithers.github.client.Github") as mock_client:
        mock_instance = MagicMock()
        mock_org = MagicMock(spec=Organization.Organization)
        mock_instance.get_organization.return_value = mock_org
        mock_client.return_value = mock_instance
        yield mock_instance


def test_get_repository(mock_github_client):
    """Test getting a repository."""
    mock_repo = MagicMock(spec=Repository.Repository)
    mock_repo.full_name = "test-org/test-repo"
    mock_org = mock_github_client.get_organization.return_value
    mock_org.get_repo.return_value = mock_repo

    client = GitHubClient(GitHubClientConfig(organization="test-org"))
    repo = client.get_repository("test-repo")

    assert repo.full_name == "test-org/test-repo"
    mock_org.get_repo.assert_called_once_with("test-repo")


def test_search_repositories(mock_github_client):
    """Test searching repositories."""
    mock_repo1 = MagicMock(spec=Repository.Repository)
    mock_repo1.full_name = "test-org/repo1"
    mock_repo2 = MagicMock(spec=Repository.Repository)
    mock_repo2.full_name = "test-org/repo2"

    mock_paginated_list = [mock_repo1, mock_repo2]
    mock_github_client.search_repositories.return_value = mock_paginated_list

    client = GitHubClient(GitHubClientConfig(organization="test-org"))
    results = client.search_repositories("test query")

    assert len(results) == NUM_TEST_REPOS
    assert results[0].full_name == "test-org/repo1"
    assert results[1].full_name == "test-org/repo2"
    mock_github_client.search_repositories.assert_called_once_with(
        "test query org:test-org"
    )


def test_search_code_in_repository(mock_github_client):
    """Test searching code within a repository."""
    mock_content1 = MagicMock(spec=ContentFile.ContentFile)
    mock_content1.repository.full_name = "test-org/test-repo"
    mock_content1.path = "src/test.py"
    mock_content1.html_url = (
        "https://github.com/test-org/test-repo/blob/main/src/test.py"
    )
    mock_content1.decoded_content = b"def test_function():\n    pass"

    mock_content2 = MagicMock(spec=ContentFile.ContentFile)
    mock_content2.repository.full_name = "test-org/test-repo"
    mock_content2.path = "src/main.py"
    mock_content2.html_url = (
        "https://github.com/test-org/test-repo/blob/main/src/main.py"
    )
    mock_content2.decoded_content = b"def main():\n    print('hello')"

    mock_paginated_list = [mock_content1, mock_content2]
    mock_github_client.search_code.return_value = mock_paginated_list

    client = GitHubClient(GitHubClientConfig(organization="test-org"))
    results = client.search_code_in_repository("test-repo", "def")

    assert len(results) == 2
    assert results[0]["path"] == "src/test.py"
    assert results[0]["content"] == "def test_function():\n    pass"
    mock_github_client.search_code.assert_called_once_with(
        "def repo:test-org/test-repo"
    )
