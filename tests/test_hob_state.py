"""Tests for hob state fallbacks used by newer Miele hob firmware."""

from custom_components.miele_lan.sensor import (
    _hob_plate_step,
    _hob_remaining_heat,
    _hob_remaining_minutes,
)
from custom_components.miele_lan.const import hob_zone_count


KM8684_ACTIVE = (
    "050000000200100B6600000D080065000000000000000000000000000000000001"
    "0000000000000000000000000000000000000000000000000100000000FF000000"
    "4925000000000000020A191A1A0000000000000000000000000000000000000000"
    "000000001A00"
)


def test_km8684_power_falls_back_to_extended_state() -> None:
    state = {"ExtendedState": KM8684_ACTIVE}

    assert _hob_plate_step(state, 0) == "residual_heat_medium"
    assert _hob_plate_step(state, 1) == "7"
    assert _hob_plate_step(state, 2) == "residual_heat_low"


def test_km8684_residual_heat_falls_back_to_extended_state() -> None:
    state = {"ExtendedState": KM8684_ACTIVE}

    assert _hob_remaining_heat(state, 0) == "medium"
    assert _hob_remaining_heat(state, 1) == "none"
    assert _hob_remaining_heat(state, 2) == "low"


def test_existing_state_arrays_take_precedence() -> None:
    state = {
        "PlateStep": [9],
        "PlateRemainingHeat": [3],
        "ExtendedState": KM8684_ACTIVE,
    }

    assert _hob_plate_step(state, 0) == "5"
    assert _hob_remaining_heat(state, 0) == "high"


def test_km8684_has_five_zones() -> None:
    assert hob_zone_count({"tech_type": "KM8684"}) == 5
    assert hob_zone_count({"tech_type": "KM7576"}) == 6


def test_km8684_timer_falls_back_to_extended_state() -> None:
    state = {
        "ExtendedState": (
            "050000000200120B000000660000010800660000660000000000000000000000"
            "0000000004000000000000000000000000000000000000000001000000FF000000"
            "492500000000000000000000000000000000000000000000000000000000000000"
            "000000000000000000000000000000000000000000000000000000000000000000"
            "000000000000000000000000000000000000000000000000000000000000000000"
        )
    }
    assert _hob_remaining_minutes(state, 2) == 4


def test_existing_timer_array_takes_precedence() -> None:
    assert _hob_remaining_minutes(
        {"PlateRemainingMinutes": [12], "ExtendedState": ""},
        0,
    ) == 12


def test_zero_timer_is_none() -> None:
    assert _hob_remaining_minutes({"PlateRemainingMinutes": [0]}, 0) is None
