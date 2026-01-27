"""Dict-based helper utilities for ASP.

These utilities work with raw dict data structures loaded from YAML files,
avoiding the need for Pydantic model imports in the validation path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML file and return its contents as a dict.

    Args:
        path: Path to the YAML file.

    Returns:
        The parsed YAML content as a dictionary.
    """
    with open(path) as f:
        data: dict[str, Any] = yaml.safe_load(f)
        return data


def save_yaml(data: dict[str, Any], path: str | Path) -> None:
    """Save data to a YAML file.

    Args:
        data: The data to save.
        path: Path to write the YAML file.
    """
    with open(path, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


def get_input(data: dict[str, Any], input_id: str) -> dict[str, Any] | None:
    """Get an input by ID from analysis data.

    Args:
        data: Analysis data as a dict.
        input_id: The input ID to find.

    Returns:
        The input dict if found, None otherwise.
    """
    inputs: list[dict[str, Any]] = data.get("analysis", {}).get("inputs", [])
    for inp in inputs:
        if inp.get("id") == input_id:
            return inp
    return None


def get_output(data: dict[str, Any], output_id: str) -> dict[str, Any] | None:
    """Get an output by ID from analysis data.

    Args:
        data: Analysis data as a dict.
        output_id: The output ID to find.

    Returns:
        The output dict if found, None otherwise.
    """
    outputs: list[dict[str, Any]] = data.get("analysis", {}).get("outputs", [])
    for out in outputs:
        if out.get("id") == output_id:
            return out
    return None


def get_decision(
    data: dict[str, Any], decision_id: str, phase_id: str | None = None
) -> dict[str, Any] | None:
    """Get a decision by ID from analysis data.

    Searches across all phases, or within a specific phase if phase_id is given.

    Args:
        data: Analysis data as a dict.
        decision_id: The decision ID to find.
        phase_id: Optional phase ID to search within.

    Returns:
        The decision dict if found, None otherwise.
    """
    phases: dict[str, dict[str, Any]] = data.get("phases", {})
    if phase_id is not None:
        phase = phases.get(phase_id, {})
        return phase.get("decisions", {}).get(decision_id)
    # Search all phases
    for phase in phases.values():
        decisions = phase.get("decisions", {})
        if decision_id in decisions:
            return decisions[decision_id]
    return None


def get_insight(data: dict[str, Any], insight_id: str) -> dict[str, Any] | None:
    """Get an insight by ID from analysis data.

    Args:
        data: Analysis data as a dict.
        insight_id: The insight ID to find.

    Returns:
        The insight dict if found, None otherwise.
    """
    insights: dict[str, dict[str, Any]] = data.get("insights", {})
    return insights.get(insight_id)


def get_default_universe(data: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Get the default universe based on decision defaults across all phases.

    Args:
        data: Analysis data as a dict.

    Returns:
        Dict mapping phase_id to dict of decision_id to default option_id.
    """
    result: dict[str, dict[str, str]] = {}
    phases = data.get("phases", {})
    for phase_id, phase in phases.items():
        phase_defaults: dict[str, str] = {}
        for decision_id, decision in phase.get("decisions", {}).items():
            default = decision.get("default")
            if default is not None:
                phase_defaults[decision_id] = default
        if phase_defaults:
            result[phase_id] = phase_defaults
    return result


def create_universe_from_defaults(
    data: dict[str, Any],
    universe_id: str = "baseline",
    description: str | None = None,
) -> dict[str, Any]:
    """Create a universe dict from the default options in an analysis.

    Args:
        data: Analysis data as a dict.
        universe_id: ID for the new universe.
        description: Optional description for the universe.

    Returns:
        A universe dict with the default decisions selected under phases.
    """
    universe: dict[str, Any] = {
        "id": universe_id,
        "description": description or "Default configuration using standard practices",
        "phases": get_default_universe(data),
    }

    return universe


def get_input_ids(data: dict[str, Any]) -> set[str]:
    """Get all input IDs from analysis data.

    Args:
        data: Analysis data as a dict.

    Returns:
        Set of input IDs.
    """
    inputs = data.get("analysis", {}).get("inputs", [])
    return {inp.get("id") for inp in inputs if inp.get("id")}


def get_output_ids(data: dict[str, Any]) -> set[str]:
    """Get all output IDs from analysis data.

    Args:
        data: Analysis data as a dict.

    Returns:
        Set of output IDs.
    """
    outputs = data.get("analysis", {}).get("outputs", [])
    return {out.get("id") for out in outputs if out.get("id")}


def get_decision_ids(data: dict[str, Any]) -> set[str]:
    """Get all decision IDs from analysis data (across all phases).

    Args:
        data: Analysis data as a dict.

    Returns:
        Set of decision IDs.
    """
    result: set[str] = set()
    for phase in data.get("phases", {}).values():
        result.update(phase.get("decisions", {}).keys())
    return result


def get_insight_ids(data: dict[str, Any]) -> set[str]:
    """Get all insight IDs from analysis data.

    Args:
        data: Analysis data as a dict.

    Returns:
        Set of insight IDs.
    """
    return set(data.get("insights", {}).keys())


def get_inputs(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Get all inputs from analysis data.

    Args:
        data: Analysis data as a dict.

    Returns:
        List of input dicts.
    """
    result: list[dict[str, Any]] = data.get("analysis", {}).get("inputs", [])
    return result


def get_outputs(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Get all outputs from analysis data.

    Args:
        data: Analysis data as a dict.

    Returns:
        List of output dicts.
    """
    result: list[dict[str, Any]] = data.get("analysis", {}).get("outputs", [])
    return result


def get_decisions(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Get all decisions from analysis data (collected from all phases).

    Args:
        data: Analysis data as a dict.

    Returns:
        Dict mapping decision_id to decision dict.
    """
    result: dict[str, dict[str, Any]] = {}
    for phase in data.get("phases", {}).values():
        result.update(phase.get("decisions", {}))
    return result


def get_phase_decisions(data: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    """Get all decisions grouped by phase.

    Args:
        data: Analysis data as a dict.

    Returns:
        Dict mapping phase_id to dict of decision_id to decision dict.
    """
    result: dict[str, dict[str, dict[str, Any]]] = {}
    for phase_id, phase in data.get("phases", {}).items():
        decisions = phase.get("decisions", {})
        if decisions:
            result[phase_id] = decisions
    return result


def get_option(decision: dict[str, Any], option_id: str) -> dict[str, Any] | None:
    """Get an option from a decision by ID.

    Args:
        decision: Decision dict.
        option_id: The option ID to find.

    Returns:
        The option dict if found, None otherwise.
    """
    result: dict[str, Any] | None = decision.get("options", {}).get(option_id)
    return result


def get_option_value(decision: dict[str, Any], option_id: str) -> Any:
    """Get the value from an option, or option_id if no value field.

    Args:
        decision: Decision dict.
        option_id: The option ID to get the value from.

    Returns:
        The option's value field if present, otherwise the option_id string.
    """
    option = get_option(decision, option_id)
    if option is None:
        return option_id
    return option.get("value", option_id)
