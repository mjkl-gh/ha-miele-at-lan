"""Tests for hob state fallbacks used by newer Miele hob firmware."""

import json
from pathlib import Path

from custom_components.miele_lan import enums
from custom_components.miele_lan.sensor import (
    _hob_plate_step,
    _hob_remaining_heat,
    _hob_remaining_minutes,
)
from custom_components.miele_lan.extended_state import (
    hob_zone_count,
    parse_hob_extended_state,
)

_STRINGS_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components" / "miele_lan" / "strings.json"
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
    # Byte 7 (Kochfeldinformationen) = 0x0B: (0x0B >> 1) & 0xF == 5 stations.
    assert hob_zone_count({"ExtendedState": KM8684_ACTIVE}) == 5
    ext = parse_hob_extended_state(KM8684_ACTIVE)
    assert len(ext.zones) == 5


def test_zone_count_defaults_to_six_without_extended_state() -> None:
    assert hob_zone_count({}) == 6


def test_zone_count_falls_back_to_six_when_byte_is_zero() -> None:
    blob = bytearray(56)
    blob[7] = 0x00
    state = {"ExtendedState": bytes(blob).hex()}

    assert hob_zone_count(state) == 6
    assert len(parse_hob_extended_state(state["ExtendedState"]).zones) == 6


def test_zone_count_falls_back_to_six_when_out_of_range() -> None:
    blob = bytearray(56)
    blob[7] = 0x3F  # (0x3F >> 1) & 0xF == 15, > 6
    state = {"ExtendedState": bytes(blob).hex()}

    assert hob_zone_count(state) == 6
    assert len(parse_hob_extended_state(state["ExtendedState"]).zones) == 6


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


def test_residual_heat_codes_defined_once() -> None:
    # HobPlateStep's "residual_heat_*" labels must derive from the exact same
    # code->severity table the plain plate_N_remaining_heat vocabulary uses,
    # so the two families of sensor can never disagree about a given code.
    for code, level in enums.RESIDUAL_HEAT_LEVELS.items():
        assert enums.HobPlateStep[code] == f"residual_heat_{level}"


def test_residual_heat_matches_declared_sensor_states() -> None:
    strings = json.loads(_STRINGS_PATH.read_text())
    declared = set(
        strings["entity"]["sensor"]["plate_1_remaining_heat"]["state"]
    )
    assert declared == {"none", "low", "medium", "high"}
    assert set(enums.RESIDUAL_HEAT_LEVELS.values()) <= declared
