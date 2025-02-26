"""Tests for the Notion API integration."""

from unittest.mock import MagicMock, patch

import pytest

from agent_smithers.notion import NotionClient, NotionClientConfig


def test_notion_client_config():
    """Test Notion client configuration."""
    config = NotionClientConfig(auth_token="test-token")
    assert config.auth_token == "test-token"


@pytest.fixture
def mock_notion_client():
    """Fixture for mocked Notion client."""
    with (
        patch("agent_smithers.notion.client.Client") as mock_client,
        patch("agent_smithers.notion.client.AsyncClient"),
    ):  # We need to mock both client types
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance


def test_get_page(mock_notion_client):
    """Test getting a page."""
    expected_page = {"id": "test-page-id", "title": "Test Page"}
    mock_notion_client.pages.retrieve.return_value = expected_page

    client = NotionClient(NotionClientConfig(auth_token="test-token"))
    page = client.get_page("test-page-id")

    assert page == expected_page
    mock_notion_client.pages.retrieve.assert_called_once_with("test-page-id")


def test_search_pages(mock_notion_client):
    """Test searching pages."""
    expected_results = [
        {"id": "page-1", "title": "Page 1"},
        {"id": "page-2", "title": "Page 2"},
    ]
    mock_notion_client.search.return_value = {"results": expected_results}

    client = NotionClient(NotionClientConfig(auth_token="test-token"))
    results = client.search_pages("test query")

    assert results == expected_results
    mock_notion_client.search.assert_called_once_with(query="test query")
