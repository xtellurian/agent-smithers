"""GitHub API client implementation."""

from typing import Any

from pydantic import BaseModel

from github import Github, Repository


class GitHubClientConfig(BaseModel):
    """Configuration for the GitHub client."""

    auth_token: str
    """The GitHub personal access token."""


class GitHubClient:
    """Client for interacting with the GitHub API."""

    def __init__(self, config: GitHubClientConfig):
        """Initialize the GitHub client.

        Args:
            config: The client configuration.
        """
        self.config = config
        self._client = Github(auth=config.auth_token)

    def get_repository(self, full_name: str) -> Repository.Repository:
        """Get a repository by its full name.

        Args:
            full_name: The full name of the repository (e.g. 'owner/repo').

        Returns:
            The repository object.
        """
        return self._client.get_repo(full_name)

    def search_repositories(self, query: str) -> list[Repository.Repository]:
        """Search for repositories matching a query.

        Args:
            query: The search query.

        Returns:
            A list of matching repositories.
        """
        return list(self._client.search_repositories(query))
