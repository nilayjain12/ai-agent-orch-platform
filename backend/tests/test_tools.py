import pytest
from app.core.tools import web_search, calculator, http_request, weather

def test_calculator():
    assert calculator.invoke("2 + 2") == "4"
    assert calculator.invoke("10 / 2") == "5.0"
    assert "Error" in calculator.invoke("invalid expression")
    assert "Error" in calculator.invoke("import os; os.system('ls')")

def test_weather_success():
    # Test with a known location
    result = weather.invoke("London")
    assert "Weather for London" in result
    assert "°C" in result
    assert "Humidity" in result
    assert "Wind" in result

def test_weather_invalid_location():
    result = weather.invoke("ThisLocationDoesNotExist12345")
    assert "Error: Could not find location" in result

def test_web_search():
    # DuckDuckGo search might be rate limited or fail in CI, but let's try a simple query
    result = web_search.invoke("Python programming")
    assert isinstance(result, str)
    # We don't assert content because it's dynamic, but it shouldn't be an error message if successful
    assert "Error performing web search" not in result

def test_http_request():
    # Test with a reliable public API
    result = http_request.invoke("https://api.github.com/zen")
    assert isinstance(result, str)
    assert len(result) > 0
    
    # Test error case
    result = http_request.invoke("https://thisdomain-does-not-exist.com")
    assert "Error making HTTP request" in result
