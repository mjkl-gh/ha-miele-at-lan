"""Tests for hob state fallbacks used by newer Miele hob firmware."""

from custom_components.miele_lan.sensor import (
    _hob_plate_step,
    _hob_remaining_heat,
)


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
    assert _hob_remaining_heat(state, 1) is None
    assert _hob_remaining_heat(state, 2) == "low"


def test_existing_state_arrays_take_precedence() -> None:
    state = {
        "PlateStep": [9],
        "PlateRemainingHeat": [3],
        "ExtendedState": KM8684_ACTIVE,
    }

    assert _hob_plate_step(state, 0) == "5"
    assert _hob_remaining_heat(state, 0) == "high"
