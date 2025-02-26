"""Notion API client implementation."""

from typing import Any, Dict, List, Optional

from notion_client import AsyncClient, Client
from pydantic import BaseModel


class NotionClientConfig(BaseModel):
    """Configuration for the Notion client."""

    auth_token: str
    """The Notion integration token."""


class NotionClient:
    """Client for interacting with the Notion API."""

    def __init__(self, config: NotionClientConfig):
        """Initialize the Notion client.

        Args:
            config: The client configuration.
        """
        self.config = config
        self._client = Client(auth=config.auth_token)
        self._async_client = AsyncClient(auth=config.auth_token)

    def get_page(self, page_id: str) -> Dict[str, Any]:
        """Get a page by its ID.

        Args:
            page_id: The ID of the page to retrieve.

        Returns:
            The page data as a dictionary.
        """
        return self._client.pages.retrieve(page_id)

    def search_pages(self, query: str) -> List[Dict[str, Any]]:
        """Search for pages matching a query.

        Args:
            query: The search query.

        Returns:
            A list of matching pages.
        """
        response = self._client.search(query=query)
        return response.get("results", [])
