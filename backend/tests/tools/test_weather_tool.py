from src.agents.tools import weather_tool


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self) -> dict:
        return self._payload


def test_fetch_weather_context_returns_parsed_payload(monkeypatch):
    geocode_payload = {"results": [{"latitude": 52.52437, "longitude": 13.41053}]}
    weather_payload = {"current": {"temperature_2m": 21.4, "precipitation_probability": 25, "weather_code": 2}}

    def fake_get(url, params, timeout):
        assert timeout == 4
        if "geocoding-api.open-meteo.com" in url:
            assert params["name"] == "Berlin"
            return _FakeResponse(geocode_payload)
        if "api.open-meteo.com" in url:
            assert params["latitude"] == 52.52437
            assert params["longitude"] == 13.41053
            return _FakeResponse(weather_payload)
        raise AssertionError("unexpected url")

    monkeypatch.setattr(weather_tool.requests, "get", fake_get)

    result = weather_tool.get_weather_context_for_city("Berlin")

    assert result.city == "Berlin"
    assert result.temperature == 21.4
    assert result.precipitation_probability == 25
    assert result.weather_label == "partly cloudy"


def test_fetch_weather_context_returns_fallback_on_geocoding_error(monkeypatch):
    def fake_get(_url, params, timeout):
        raise weather_tool.requests.RequestException("network down")

    monkeypatch.setattr(weather_tool.requests, "get", fake_get)

    result = weather_tool.get_weather_context_for_city("Madrid")

    assert result.city == "Madrid"
    assert result.temperature is None
    assert result.precipitation_probability is None
    assert result.weather_label == "unavailable"


def test_fetch_weather_context_returns_fallback_on_forecast_error(monkeypatch):
    geocode_payload = {"results": [{"latitude": 40.4168, "longitude": -3.7038}]}

    def fake_get(url, params, timeout):
        assert timeout == 4
        if "geocoding-api.open-meteo.com" in url:
            return _FakeResponse(geocode_payload)
        raise weather_tool.requests.RequestException("forecast unavailable")

    monkeypatch.setattr(weather_tool.requests, "get", fake_get)

    result = weather_tool.get_weather_context_for_city("Madrid")

    assert result.city == "Madrid"
    assert result.temperature is None
    assert result.precipitation_probability is None
    assert result.weather_label == "unavailable"
