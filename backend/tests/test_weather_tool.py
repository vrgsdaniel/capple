from urllib.error import URLError

from src.agents.tools import weather_tool as weather_module


class _FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_fetch_weather_context_returns_parsed_payload(monkeypatch):
    payload = b'{"current": {"temperature_2m": 21.4, "precipitation_probability": 25, "weather_code": 2}}'

    def fake_urlopen(_url, timeout):
        assert timeout == 4
        return _FakeResponse(payload)

    monkeypatch.setattr(weather_module, "urlopen", fake_urlopen)

    result = weather_module.fetch_weather_context_for_city("Berlin", 52.52, 13.405)

    assert result.city == "Berlin"
    assert result.temperature == 21.4
    assert result.precipitation_probability == 25
    assert result.weather_label == "partly cloudy"


def test_fetch_weather_context_returns_fallback_on_network_error(monkeypatch):
    def fake_urlopen(_url, timeout):
        raise URLError("network down")

    monkeypatch.setattr(weather_module, "urlopen", fake_urlopen)

    result = weather_module.fetch_weather_context_for_city("Madrid", 40.4168, -3.7038)

    assert result.city == "Madrid"
    assert result.temperature is None
    assert result.precipitation_probability is None
    assert result.weather_label == "unavailable"
