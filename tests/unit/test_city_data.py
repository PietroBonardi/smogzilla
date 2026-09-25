"""Unit tests for utils/city_data.py."""

import pytest

from utils.city_data import CITIES, City

pytestmark = pytest.mark.unit


def test_cities_is_not_empty():
    assert len(CITIES) > 0


def test_cities_keys_are_lowercase_and_match_lookup_convention():
    assert all(key == key.lower() for key in CITIES)


def test_every_value_is_a_city():
    assert all(isinstance(city, City) for city in CITIES.values())


@pytest.mark.parametrize("key", ["milano", "roma", "torino"])
def test_known_cities_present(key):
    assert key in CITIES


def test_coordinates_are_within_italy_bounds():
    for key, city in CITIES.items():
        assert 35.0 <= city.lat <= 47.5, f"{key} lat out of bounds"
        assert 6.0 <= city.lng <= 19.0, f"{key} lng out of bounds"


def test_city_dataclass_is_frozen():
    city = City("Test", 1.0, 2.0, "TS", "Testland")
    with pytest.raises(Exception):
        city.name = "Changed"
