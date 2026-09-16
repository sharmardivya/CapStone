"""
Weather tool for the Weather Intelligence Agent.

Uses the free wttr.in API (no API key needed).
"""

import httpx
from langchain_core.tools import tool


@tool
async def fetch_weather_data(city: str) -> str:
    """Fetch current weather data for a city from the wttr.in public API."""
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.get(
                f"https://wttr.in/{city}?format=j1",
                headers={"User-Agent": "LangChain-A2A-Demo/1.0"},
            )
        if response.status_code != 200:
            return f"Weather service returned HTTP {response.status_code} for '{city}'"

        data = response.json()
        current = data["current_condition"][0]
        country = data["nearest_area"][0]["country"][0]["value"]
        return (
            f"City: {city}, Country: {country}, "
            f"Temp: {current['temp_C']}°C ({current['temp_F']}°F), "
            f"FeelsLike: {current['FeelsLikeC']}°C, "
            f"Humidity: {current['humidity']}%, "
            f"Wind: {current['windspeedKmph']} km/h, "
            f"Visibility: {current['visibility']} km, "
            f"Conditions: {current['weatherDesc'][0]['value']}"
        )
    except Exception as exc:
        # Return the problem as text so the agent can still answer something useful.
        return f"Weather data unavailable for '{city}': {str(exc)[:80]}"
