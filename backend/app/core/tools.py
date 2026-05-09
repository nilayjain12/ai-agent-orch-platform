from langchain_core.tools import tool
import httpx
import logging
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

@tool
def web_search(query: str) -> str:
    """
    Tool: web_search
    Purpose: Search the web for current information, news, and general knowledge.
    Use when: The user asks for information that requires searching the internet, such as news, current events, or facts not in the model's training data.
    Inputs: query (string): The search query to look up.
    Returns: A formatted string containing titles, snippets, and links to relevant web pages.
    Constraints: May be subject to rate limits; results are limited to the top 5 relevant findings.
    """
    try:
        logger.info(f"Executing web_search with query: '{query}'")
        if not query or len(query.strip()) < 2:
            return "Error: Search query is too short or empty."

        # Check if the query is news-related
        news_keywords = ["news", "today", "latest", "trending", "breaking"]
        is_news = any(keyword in query.lower() for keyword in news_keywords)

        results = []
        try:
            with DDGS() as ddgs:
                if is_news:
                    logger.info(f"Attempting news search for: {query}")
                    results = list(ddgs.news(query, max_results=5))
                
                if not results:
                    logger.info(f"Attempting text search for: {query}")
                    results = list(ddgs.text(query, max_results=5))
        except Exception as e:
            logger.error(f"DuckDuckGo search core failure: {str(e)}")
            return f"Error performing web search: {str(e)}. This might be due to rate limits or connectivity issues."
            
        if not results:
            logger.warning(f"No results returned for query: {query}")
            return f"No results found for the query '{query}'. Please try a different query or be more specific."
            
        formatted_results = []
        for r in results:
            title = r.get("title", "No Title")
            snippet = r.get("body") or r.get("snippet") or "No Snippet available"
            link = r.get("href") or r.get("url") or "No Link"
            date = f" (Date: {r.get('date')})" if r.get('date') else ""
            formatted_results.append(f"Title: {title}{date}\nSnippet: {snippet}\nLink: {link}")
            
        return "\n\n---\n\n".join(formatted_results)
    except Exception as e:
        logger.exception("Unexpected error in web_search tool")
        return f"Error performing web search: {str(e)}"

@tool
def calculator(expression: str) -> str:
    """
    Tool: calculator
    Purpose: Perform basic mathematical calculations.
    Use when: The user provides a mathematical expression that needs to be evaluated (e.g., addition, subtraction, multiplication, division).
    Inputs: expression (string): The mathematical expression to evaluate (e.g., '2 + 2').
    Returns: The numerical result of the calculation as a string.
    Constraints: Only supports basic arithmetic operators and parentheses.
    """
    try:
        # Very basic safe eval
        allowed_chars = "0123456789+-*/(). "
        if any(c not in allowed_chars for c in expression):
            return "Error: Invalid characters in math expression. Only basic math is supported."
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"

@tool
def http_request(url: str, method: str = "GET", payload: str = "") -> str:
    """
    Tool: http_request
    Purpose: Fetch data from a specific URL using an HTTP request.
    Use when: The user provides a specific URL and wants to retrieve its content or interact with an API.
    Inputs: url (string): The target URL; method (string): The HTTP method (GET or POST); payload (string): Optional data for POST requests.
    Returns: The raw response text from the server (truncated to 2000 characters).
    Constraints: Only supports GET and POST; requires a valid URL.
    """
    try:
        with httpx.Client() as client:
            if method.upper() == "GET":
                response = client.get(url)
            elif method.upper() == "POST":
                # Assuming JSON payload for simplicity
                response = client.post(url, data=payload)
            else:
                return f"Error: Method {method} not supported."
            response.raise_for_status()
            return response.text[:2000] # Limit output size
    except Exception as e:
        return f"Error making HTTP request: {str(e)}"

@tool
def weather(location: str) -> str:
    """
    Tool: weather
    Purpose: Retrieve current weather information for a given location.
    Use when: The user asks for the current weather, temperature, or conditions in a specific city or region.
    Inputs: location (string): The city or location name (e.g., 'London, UK').
    Returns: A summary of the current weather including temperature, conditions, wind, and humidity.
    Constraints: Requires a valid location name; data is provided by Open-Meteo.
    """
    try:
        logger.info(f"Fetching weather for location: '{location}'")
        if not location:
            return "Error: No location provided."

        with httpx.Client() as client:
            # 1. Geocoding: Get coordinates for the location
            geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
            geo_params = {
                "name": location,
                "count": 1,
                "language": "en",
                "format": "json"
            }
            geo_response = client.get(geocoding_url, params=geo_params)
            geo_response.raise_for_status()
            geo_data = geo_response.json()

            if not geo_data.get("results"):
                # Try a fallback: strip country/state if present
                short_name = location.split(',')[0].strip()
                if short_name != location:
                    logger.info(f"Retrying geocoding with short name: '{short_name}'")
                    geo_params["name"] = short_name
                    geo_response = client.get(geocoding_url, params=geo_params)
                    geo_data = geo_response.json()

                if not geo_data.get("results"):
                    return f"Error: Could not find location '{location}'. Please try being more specific (e.g. 'New York City' instead of just 'New York')."

            result = geo_data["results"][0]
            lat = result["latitude"]
            lon = result["longitude"]
            full_name = f"{result.get('name', '')}, {result.get('admin1', '')}, {result.get('country', '')}".strip(", ")

            # 2. Weather: Get current weather for the coordinates
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m"
            weather_response = client.get(weather_url)
            weather_response.raise_for_status()
            weather_data = weather_response.json()

            current = weather_data.get("current", {})
            temp = current.get("temperature_2m")
            humidity = current.get("relative_humidity_2m")
            wind = current.get("wind_speed_10m")
            code = current.get("weather_code")

            # WMO Weather interpretation codes (WW)
            wmo_codes = {
                0: "Clear sky",
                1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Fog", 48: "Depositing rime fog",
                51: "Drizzle: Light", 53: "Drizzle: Moderate", 55: "Drizzle: Dense intensity",
                56: "Freezing Drizzle: Light", 57: "Freezing Drizzle: Dense intensity",
                61: "Rain: Slight", 63: "Rain: Moderate", 65: "Rain: Heavy intensity",
                66: "Freezing Rain: Light", 67: "Freezing Rain: Heavy intensity",
                71: "Snow fall: Slight", 73: "Snow fall: Moderate", 75: "Snow fall: Heavy intensity",
                77: "Snow grains",
                80: "Rain showers: Slight", 81: "Rain showers: Moderate", 82: "Rain showers: Violent",
                85: "Snow showers: Slight", 86: "Snow showers: Heavy",
                95: "Thunderstorm: Slight or moderate",
                96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
            }
            condition = wmo_codes.get(code, "Unknown condition")

            return f"Weather for {full_name}: {condition}, {temp}°C (Apparent: {current.get('apparent_temperature')}°C), Humidity: {humidity}%, Wind: {wind} km/h"
    except Exception as e:
        return f"Error fetching weather: {str(e)}"

AVAILABLE_TOOLS = {
    "web_search": web_search,
    "calculator": calculator,
    "http_request": http_request,
    "weather": weather
}
