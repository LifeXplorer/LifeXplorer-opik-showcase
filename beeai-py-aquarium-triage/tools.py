"""Two read-only tools over the fictional fish-room data in data/.

Plain functions hold the logic (easy to unit test); BeeAI's @tool wraps them so
the ReAct agent can call them.
"""
import json
from pathlib import Path

from beeai_framework.tools import StringToolOutput, tool

DATA = Path(__file__).parent / "data"
TANKS: dict = json.loads((DATA / "tanks.json").read_text())
RANGES: dict = json.loads((DATA / "water_ranges.json").read_text())


def tank_profile(tank_id: str) -> dict:
    """Return the tank record, or an error dict listing the valid ids."""
    tank = TANKS.get(tank_id.strip().lower())
    if tank is None:
        return {"error": f"unknown tank '{tank_id}'", "valid_ids": sorted(TANKS)}
    return {"tank_id": tank_id.strip().lower(), **tank}


def safe_range(tank_type: str, parameter: str) -> dict:
    """Return the safe band and urgent thresholds for one parameter in one tank type."""
    by_param = RANGES.get(tank_type.strip().lower())
    if by_param is None:
        return {"error": f"unknown tank type '{tank_type}'", "valid_types": sorted(RANGES)}
    entry = by_param.get(parameter.strip().lower())
    if entry is None:
        return {"error": f"no range for '{parameter}'", "valid_parameters": sorted(by_param)}
    return {"tank_type": tank_type, "parameter": parameter, **entry}


@tool
def lookup_tank(tank_id: str) -> StringToolOutput:
    """Look up a tank by id (e.g. 'reef-01'): its type, volume, inhabitants, last water change and keeper."""
    # Tool calls show up in Opik as tool spans with this input and output.
    return StringToolOutput(json.dumps(tank_profile(tank_id)))


@tool
def lookup_safe_range(tank_type: str, parameter: str) -> StringToolOutput:
    """Get the safe range and urgent thresholds for a water parameter. tank_type is one of reef, shrimp,
    freshwater_community. parameter is one of ammonia_ppm, nitrate_ppm, ph, salinity_ppt, temperature_c."""
    return StringToolOutput(json.dumps(safe_range(tank_type, parameter)))
