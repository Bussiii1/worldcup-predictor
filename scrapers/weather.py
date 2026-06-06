import requests

STADIUMS = {
    "MetLife Stadium": (40.8128, -74.0742),
    "AT&T Stadium": (32.7473, -97.0945),
    "SoFi Stadium": (33.9534, -118.3392),
    "Rose Bowl": (34.1613, -118.1676),
    "Levi's Stadium": (37.4033, -121.9694),
    "BC Place": (49.2768, -123.1116),
    "Estadio Azteca": (19.3029, -99.1505),
    "Estadio Akron": (20.6893, -103.4673),
    "Hard Rock Stadium": (25.9580, -80.2389),
    "NRG Stadium": (29.6847, -95.4107),
    "Q2 Stadium": (30.3877, -97.7191),
    "Gillette Stadium": (42.0909, -71.2643),
    "Arrowhead Stadium": (39.0489, -94.4839),
    "Lumen Field": (47.5952, -122.3316),
    "Empower Field": (39.7439, -105.0201),
    "Allegiant Stadium": (36.0909, -115.1833),
    "Lincoln Financial Field": (39.9008, -75.1675),
    "BMO Field": (43.6333, -79.4186),
}

BASE_URL = "https://api.open-meteo.com/v1/forecast"


def _assess_conditions(temp: float | None, rain: float | None, wind: float | None) -> str:
    issues = []
    if temp is not None:
        if temp > 32:
            issues.append("extreme heat")
        elif temp > 28:
            issues.append("high heat")
    if rain is not None and rain > 10:
        issues.append("heavy rain")
    elif rain is not None and rain > 3:
        issues.append("light rain")
    if wind is not None and wind > 50:
        issues.append("strong wind")
    elif wind is not None and wind > 30:
        issues.append("moderate wind")

    if not issues:
        return "ideal"
    return f"affected by: {', '.join(issues)}"


async def get_weather(stadium: str, match_date: str) -> dict:
    try:
        coords = STADIUMS.get(stadium)
        if not coords:
            return {"stadium": stadium, "source": "open_meteo", "error": "stadium_not_found"}

        lat, lon = coords
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,precipitation_sum,wind_speed_10m_max",
            "start_date": match_date,
            "end_date": match_date,
            "timezone": "auto",
        }
        resp = requests.get(BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        daily = data.get("daily", {})
        temps = daily.get("temperature_2m_max", [None])
        rains = daily.get("precipitation_sum", [None])
        winds = daily.get("wind_speed_10m_max", [None])

        temp = temps[0] if temps else None
        rain = rains[0] if rains else None
        wind = winds[0] if winds else None

        conditions = _assess_conditions(temp, rain, wind)

        desc_parts = []
        if temp is not None:
            desc_parts.append(f"{temp}°C")
        if rain is not None:
            desc_parts.append(f"{rain}mm rain")
        if wind is not None:
            desc_parts.append(f"{wind}km/h wind")

        return {
            "stadium": stadium,
            "match_date": match_date,
            "temp_max_c": temp,
            "precipitation_mm": rain,
            "wind_speed_kmh": wind,
            "weather_description": ", ".join(desc_parts) if desc_parts else "data unavailable",
            "playing_conditions_assessment": conditions,
            "source": "open_meteo",
        }
    except Exception as e:
        return {
            "stadium": stadium,
            "temp_max_c": None,
            "precipitation_mm": None,
            "wind_speed_kmh": None,
            "weather_description": None,
            "playing_conditions_assessment": None,
            "source": "open_meteo",
            "error": str(e),
        }
