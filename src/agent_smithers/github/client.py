"""GitHub API client implementation."""

from agent_smithers.env import GITHUB_TOKEN
from github import Auth, Github, Repository


class GitHubClientConfig:
    """Configuration for the GitHub client."""

    def __init__(self, organization: str):
        """Initialize the GitHub client configuration.

        Args:
            organization: The GitHub organization name to scope operations to.
        """
        self.organization = organization


class GitHubClient:
    """Client for interacting with the GitHub API, scoped to an organization."""

    def __init__(self, config: GitHubClientConfig):
        """Initialize the GitHub client.

        Args:
            config: The client configuration containing organization settings.
        """
        self._client = Github(auth=Auth.Token(GITHUB_TOKEN))
        self._organization = self._client.get_organization(config.organization)
        self._org_name = config.organization

    def get_repository(self, name: str) -> Repository.Repository:
        """Get a repository within the organization by its name.

        Args:
            name: The repository name within the organization.

        Returns:
            The repository object.
        """
        return self._organization.get_repo(name)

    def search_repositories(self, query: str) -> list[Repository.Repository]:
        """Search for repositories matching a query within the organization.

        Args:
            query: The search query.

        Returns:
            A list of matching repositories.
        """
        qualified_query = f"{query} org:{self._org_name}"
        return list(self._client.search_repositories(qualified_query))

    def search_code_in_repository(self, repository: str, query: str) -> list[dict]:
        """Search for code within a specific repository in the organization.

        Args:
            repository: The repository name within the organization
            query: The search query for code

        Returns:
            A list of matching code snippets with metadata
        """
        if "/" in repository:
            full_repo_name = repository
        else:
            full_repo_name = f"{self._org_name}/{repository}"
        qualified_query = f"{query} repo:{full_repo_name}"
        code_results = self._client.search_code(qualified_query)

        results = [
            {
                "repository": code.repository.full_name,
                "path": code.path,
                "url": code.html_url,
                "content": code.decoded_content.decode("utf-8")
                if code.decoded_content
                else None,
            }
            for code in code_results
        ]
        return results[:5]  # Limit to top 5 results

    def list_accessible_repositories(self) -> list[Repository.Repository]:
        """List all repositories accessible within the organization.

        Returns:
            A list of accessible repositories.
        """
        return list(self._organization.get_repos(sort="updated"))
