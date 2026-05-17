from src.agents.tools import date_tool as date_module


def test_get_datetime_context_includes_city_and_iso_timestamps():
    result = date_module.get_datetime_context.invoke({"city": "Berlin"})

    assert result.city == "Berlin"
    assert "T" in result.utc_iso
    assert "T" in result.local_iso
