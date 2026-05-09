"""
Edge-case tests for app.core.tools — covers input validation branches
that don't require real network calls.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestWebSearchEdgeCases:

    def test_empty_query(self):
        from app.core.tools import web_search
        result = web_search.invoke("")
        assert "too short" in result.lower() or "error" in result.lower()

    def test_short_query(self):
        from app.core.tools import web_search
        result = web_search.invoke("a")
        assert "too short" in result.lower() or "error" in result.lower()

    @patch("app.core.tools.DDGS")
    def test_news_keyword_triggers_news_search(self, mock_ddgs_cls):
        from app.core.tools import web_search
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.news.return_value = [
            {"title": "Breaking", "body": "News body", "href": "http://x.com", "date": "2026-01-01"}
        ]
        mock_ddgs_cls.return_value = mock_ddgs

        result = web_search.invoke("latest news today")
        assert "Breaking" in result
        mock_ddgs.news.assert_called_once()

    @patch("app.core.tools.DDGS")
    def test_no_results_returns_message(self, mock_ddgs_cls):
        from app.core.tools import web_search
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = []
        mock_ddgs_cls.return_value = mock_ddgs

        result = web_search.invoke("xyznonexistentquery123")
        assert "No results found" in result


class TestCalculatorEdgeCases:

    def test_parentheses(self):
        from app.core.tools import calculator
        assert calculator.invoke("(2 + 3) * 4") == "20"

    def test_division_by_zero(self):
        from app.core.tools import calculator
        result = calculator.invoke("1 / 0")
        assert "Error" in result


class TestHttpRequestEdgeCases:

    @patch("app.core.tools.httpx.Client")
    def test_post_method(self, mock_client_cls):
        from app.core.tools import http_request
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "OK"
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = http_request.invoke({"url": "http://example.com", "method": "POST", "payload": "{}"})
        assert result == "OK"

    def test_unsupported_method(self):
        from app.core.tools import http_request
        result = http_request.invoke({"url": "http://example.com", "method": "PATCH"})
        assert "not supported" in result


class TestWeatherEdgeCases:

    def test_empty_location(self):
        from app.core.tools import weather
        result = weather.invoke("")
        assert "No location" in result or "Error" in result
