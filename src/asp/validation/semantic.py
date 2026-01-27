"""Semantic validation for ASP specifications.

This module performs semantic validation (cross-references, constraints)
using dict-based data structures loaded from YAML files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from asp.helpers import load_yaml


class SemanticError:
    """A semantic validation error."""

    def __init__(self, code: str, message: str, path: str | None = None):
        self.code = code
        self.message = message
        self.path = path

    def __str__(self) -> str:
        if self.path:
            return f"[{self.code}] {self.path}: {self.message}"
        return f"[{self.code}] {self.message}"


def validate_analysis(data: dict[str, Any]) -> list[SemanticError]:
    """Validate an analysis specification semantically.

    Checks:
    - Default options exist in their decision's options
    - Evidence refs point to valid inputs
    - Constraint refs (requires, incompatible_with) point to valid decision.option pairs
    - Input/output IDs are unique

    Args:
        data: The analysis data as a dict.

    Returns:
        List of semantic errors (empty if valid).
    """
    errors: list[SemanticError] = []

    analysis_content = data.get("analysis", {})
    inputs = analysis_content.get("inputs", [])
    outputs = analysis_content.get("outputs", [])
    decisions = data.get("decisions", {})
    insights = data.get("insights", {})

    # Check for duplicate input IDs
    input_ids: set[str] = set()
    for inp in inputs:
        inp_id = inp.get("id")
        if inp_id in input_ids:
            errors.append(
                SemanticError(
                    "DUPLICATE_INPUT", f"Duplicate input ID: {inp_id}", f"inputs.{inp_id}"
                )
            )
        if inp_id:
            input_ids.add(inp_id)

    # Check for duplicate output IDs
    output_ids: set[str] = set()
    for out in outputs:
        out_id = out.get("id")
        if out_id in output_ids:
            errors.append(
                SemanticError(
                    "DUPLICATE_OUTPUT", f"Duplicate output ID: {out_id}", f"outputs.{out_id}"
                )
            )
        if out_id:
            output_ids.add(out_id)

    # Validate decisions
    for decision_id, decision in decisions.items():
        decision_path = f"decisions.{decision_id}"
        options = decision.get("options", {})

        # Check default option exists
        default = decision.get("default")
        if default is not None and default not in options:
            errors.append(
                SemanticError(
                    "INVALID_DEFAULT",
                    f"Default option '{default}' not found in options",
                    decision_path,
                )
            )

        # Validate options
        for option_id, option in options.items():
            option_path = f"{decision_path}.options.{option_id}"

            # Check evidence refs
            evidence_list = option.get("evidence") or []
            for i, evidence in enumerate(evidence_list):
                # Check insight reference
                insight_ref = evidence.get("insight")
                if insight_ref:
                    if insight_ref not in insights:
                        errors.append(
                            SemanticError(
                                "INVALID_INSIGHT_REF",
                                f"Evidence insight '{insight_ref}' not found in insights",
                                f"{option_path}.evidence[{i}]",
                            )
                        )
                # Check legacy input reference
                elif evidence.get("ref"):
                    ref = evidence["ref"]
                    if ref.startswith("inputs."):
                        ref_input_id = ref[7:]  # Remove "inputs." prefix
                        if ref_input_id not in input_ids:
                            errors.append(
                                SemanticError(
                                    "INVALID_EVIDENCE_REF",
                                    f"Evidence ref '{ref}' points to non-existent input",
                                    f"{option_path}.evidence[{i}]",
                                )
                            )

            # Check incompatible_with refs
            incompatible_with = option.get("incompatible_with") or []
            for ref in incompatible_with:
                errors.extend(_validate_constraint_ref(ref, decisions, option_path))

            # Check requires refs
            requires = option.get("requires") or []
            for ref in requires:
                errors.extend(_validate_constraint_ref(ref, decisions, option_path))

    # Validate phases
    phases = data.get("phases", {})
    if phases:
        errors.extend(_validate_phases(phases, input_ids, outputs, insights))

    return errors


def _validate_phases(
    phases: dict[str, Any],
    parent_input_ids: set[str],
    parent_outputs: list[dict[str, Any]],
    insights: dict[str, Any],
) -> list[SemanticError]:
    """Validate phase definitions, wiring, decisions, and DAG structure."""
    errors: list[SemanticError] = []

    phase_ids = set(phases.keys())

    # Collect output IDs per phase for validating sibling output refs
    phase_output_ids: dict[str, set[str]] = {}
    for phase_id, phase in phases.items():
        phase_outputs = phase.get("outputs") or []
        phase_output_ids[phase_id] = {
            out.get("id") for out in phase_outputs if out.get("id")
        }

    for phase_id, phase in phases.items():
        phase_path = f"phases.{phase_id}"

        # Validate no duplicate input IDs within phase
        phase_input_ids: set[str] = set()
        for inp in phase.get("inputs") or []:
            inp_id = inp.get("id")
            if inp_id in phase_input_ids:
                errors.append(
                    SemanticError(
                        "DUPLICATE_INPUT",
                        f"Duplicate input ID in phase: {inp_id}",
                        f"{phase_path}.inputs.{inp_id}",
                    )
                )
            if inp_id:
                phase_input_ids.add(inp_id)

        # Validate no duplicate output IDs within phase
        seen_output_ids: set[str] = set()
        for out in phase.get("outputs") or []:
            out_id = out.get("id")
            if out_id in seen_output_ids:
                errors.append(
                    SemanticError(
                        "DUPLICATE_OUTPUT",
                        f"Duplicate output ID in phase: {out_id}",
                        f"{phase_path}.outputs.{out_id}",
                    )
                )
            if out_id:
                seen_output_ids.add(out_id)

        # Validate input wiring references
        for inp in phase.get("inputs") or []:
            from_ref = inp.get("from")
            if not from_ref:
                continue
            errors.extend(
                _validate_phase_wiring_ref(
                    from_ref, parent_input_ids, phase_ids, phase_output_ids,
                    phase_id, phase_path,
                )
            )

        # Validate phase decisions
        phase_decisions = phase.get("decisions") or {}
        for decision_id, decision in phase_decisions.items():
            decision_path = f"{phase_path}.decisions.{decision_id}"
            options = decision.get("options", {})

            # Check default option exists
            default = decision.get("default")
            if default is not None and default not in options:
                errors.append(
                    SemanticError(
                        "INVALID_DEFAULT",
                        f"Default option '{default}' not found in options",
                        decision_path,
                    )
                )

            # Validate options
            for option_id, option in options.items():
                option_path = f"{decision_path}.options.{option_id}"

                # Check evidence insight refs → top-level insights
                evidence_list = option.get("evidence") or []
                for i, evidence in enumerate(evidence_list):
                    insight_ref = evidence.get("insight")
                    if insight_ref and insight_ref not in insights:
                        errors.append(
                            SemanticError(
                                "INVALID_INSIGHT_REF",
                                f"Evidence insight '{insight_ref}' not found in insights",
                                f"{option_path}.evidence[{i}]",
                            )
                        )

                # Check constraints (scoped to this phase's decisions)
                for ref in option.get("incompatible_with") or []:
                    errors.extend(
                        _validate_constraint_ref(ref, phase_decisions, option_path)
                    )
                for ref in option.get("requires") or []:
                    errors.extend(
                        _validate_constraint_ref(ref, phase_decisions, option_path)
                    )

    # Validate 'from' references on parent outputs
    for out in parent_outputs:
        from_ref = out.get("from")
        if from_ref:
            out_id = out.get("id", "?")
            parts = from_ref.split(".")
            if len(parts) != 2:
                errors.append(
                    SemanticError(
                        "INVALID_FROM_FORMAT",
                        f"Output 'from' value '{from_ref}' should be "
                        f"in 'phase_id.output_id' format",
                        f"outputs.{out_id}",
                    )
                )
            else:
                ref_phase_id, ref_output_id = parts
                if ref_phase_id not in phase_ids:
                    errors.append(
                        SemanticError(
                            "INVALID_FROM_REF",
                            f"Output 'from' references unknown phase '{ref_phase_id}'",
                            f"outputs.{out_id}",
                        )
                    )
                elif ref_output_id not in phase_output_ids.get(ref_phase_id, set()):
                    errors.append(
                        SemanticError(
                            "INVALID_FROM_OUTPUT_REF",
                            f"Output 'from' references unknown output "
                            f"'{ref_output_id}' in phase '{ref_phase_id}'",
                            f"outputs.{out_id}",
                        )
                    )

    # Check for cycles in the phase DAG
    errors.extend(_validate_phase_dag(phases))

    return errors


def _validate_phase_wiring_ref(
    ref: str,
    parent_input_ids: set[str],
    phase_ids: set[str],
    phase_output_ids: dict[str, set[str]],
    current_phase_id: str,
    phase_path: str,
) -> list[SemanticError]:
    """Validate a single phase input wiring reference."""
    errors: list[SemanticError] = []

    if ref.startswith("inputs."):
        # Reference to a parent input
        input_id = ref[7:]  # Remove "inputs." prefix
        if input_id not in parent_input_ids:
            errors.append(
                SemanticError(
                    "INVALID_WIRING_REF",
                    f"Wiring ref '{ref}' points to non-existent parent input '{input_id}'",
                    phase_path,
                )
            )
    else:
        # Reference to a sibling phase output: "phase_id.output_id"
        parts = ref.split(".")
        if len(parts) != 2:
            errors.append(
                SemanticError(
                    "INVALID_WIRING_FORMAT",
                    f"Wiring ref '{ref}' should be 'inputs.<id>' "
                    f"or '<phase_id>.<output_id>'",
                    phase_path,
                )
            )
        else:
            sibling_id, output_id = parts
            if sibling_id == current_phase_id:
                errors.append(
                    SemanticError(
                        "SELF_REFERENCE",
                        f"Phase '{current_phase_id}' cannot reference its own outputs",
                        phase_path,
                    )
                )
            elif sibling_id not in phase_ids:
                errors.append(
                    SemanticError(
                        "INVALID_WIRING_REF",
                        f"Wiring ref '{ref}' points to non-existent phase '{sibling_id}'",
                        phase_path,
                    )
                )
            elif output_id not in phase_output_ids.get(sibling_id, set()):
                errors.append(
                    SemanticError(
                        "INVALID_WIRING_OUTPUT_REF",
                        f"Wiring ref '{ref}' points to non-existent output "
                        f"'{output_id}' in phase '{sibling_id}'",
                        phase_path,
                    )
                )

    return errors


def _validate_phase_dag(
    phases: dict[str, Any],
) -> list[SemanticError]:
    """Validate that phase wiring forms a DAG (no cycles)."""
    errors: list[SemanticError] = []

    # Build dependency graph from input wiring
    dependencies: dict[str, set[str]] = {phase_id: set() for phase_id in phases}

    for phase_id, phase in phases.items():
        for inp in phase.get("inputs") or []:
            from_ref = inp.get("from", "")
            if not from_ref.startswith("inputs."):
                parts = from_ref.split(".")
                if len(parts) == 2 and parts[0] in phases:
                    dependencies[phase_id].add(parts[0])

    # Detect cycles using Kahn's algorithm
    in_degree = {phase_id: len(deps) for phase_id, deps in dependencies.items()}
    queue = [phase_id for phase_id, deg in in_degree.items() if deg == 0]
    visited = 0

    while queue:
        node = queue.pop(0)
        visited += 1
        for phase_id, deps in dependencies.items():
            if node in deps:
                in_degree[phase_id] -= 1
                if in_degree[phase_id] == 0:
                    queue.append(phase_id)

    if visited != len(phases):
        errors.append(
            SemanticError(
                "CYCLE_DETECTED",
                "Phase wiring contains a cycle",
                "phases",
            )
        )

    return errors


def _validate_constraint_ref(
    ref: str, decisions: dict[str, Any], option_path: str
) -> list[SemanticError]:
    """Validate a constraint reference (decision.option format)."""
    errors: list[SemanticError] = []

    parts = ref.split(".")
    if len(parts) != 2:
        errors.append(
            SemanticError(
                "INVALID_CONSTRAINT_FORMAT",
                f"Constraint '{ref}' should be in 'decision.option' format",
                option_path,
            )
        )
        return errors

    decision_id, option_id = parts

    if decision_id not in decisions:
        errors.append(
            SemanticError(
                "INVALID_CONSTRAINT_REF",
                f"Constraint ref '{ref}' points to non-existent decision '{decision_id}'",
                option_path,
            )
        )
    elif option_id not in decisions[decision_id].get("options", {}):
        errors.append(
            SemanticError(
                "INVALID_CONSTRAINT_REF",
                f"Constraint ref '{ref}' points to non-existent option '{option_id}'",
                option_path,
            )
        )

    return errors


def validate_universe(
    universe_data: dict[str, Any], analysis_data: dict[str, Any]
) -> list[SemanticError]:
    """Validate a universe against an analysis specification.

    Checks:
    - All decisions in the analysis have a selection in the universe
    - All selections point to valid options
    - No constraint violations (requires, incompatible_with)

    Args:
        universe_data: The universe data as a dict.
        analysis_data: The analysis data as a dict.

    Returns:
        List of semantic errors (empty if valid).
    """
    errors: list[SemanticError] = []

    universe_decisions = universe_data.get("decisions", {})
    analysis_decisions = analysis_data.get("decisions", {})

    # Check all decisions are covered
    for decision_id in analysis_decisions:
        if decision_id not in universe_decisions:
            errors.append(
                SemanticError(
                    "MISSING_DECISION",
                    f"Universe missing decision: {decision_id}",
                    f"decisions.{decision_id}",
                )
            )

    # Check all selections are valid
    for decision_id, option_id in universe_decisions.items():
        if decision_id not in analysis_decisions:
            errors.append(
                SemanticError(
                    "UNKNOWN_DECISION",
                    f"Universe references unknown decision: {decision_id}",
                    f"decisions.{decision_id}",
                )
            )
            continue

        decision = analysis_decisions[decision_id]
        options = decision.get("options", {})
        if option_id not in options:
            errors.append(
                SemanticError(
                    "UNKNOWN_OPTION",
                    f"Universe selects unknown option '{option_id}' for decision '{decision_id}'",
                    f"decisions.{decision_id}",
                )
            )

    # Check constraints
    errors.extend(_validate_universe_constraints(universe_data, analysis_data))

    # Check phase decision selections
    universe_phases = universe_data.get("phases", {})
    analysis_phases = analysis_data.get("phases", {})

    for phase_id in universe_phases:
        if phase_id not in analysis_phases:
            errors.append(
                SemanticError(
                    "UNKNOWN_PHASE",
                    f"Universe references unknown phase: {phase_id}",
                    f"phases.{phase_id}",
                )
            )
            continue

        # Validate decision selections within this phase
        phase_decisions = analysis_phases[phase_id].get("decisions", {})
        phase_selections = universe_phases[phase_id]

        for decision_id, option_id in phase_selections.items():
            if decision_id not in phase_decisions:
                errors.append(
                    SemanticError(
                        "UNKNOWN_DECISION",
                        f"Universe references unknown decision '{decision_id}' "
                        f"in phase '{phase_id}'",
                        f"phases.{phase_id}.{decision_id}",
                    )
                )
                continue

            options = phase_decisions[decision_id].get("options", {})
            if option_id not in options:
                errors.append(
                    SemanticError(
                        "UNKNOWN_OPTION",
                        f"Universe selects unknown option '{option_id}' for "
                        f"decision '{decision_id}' in phase '{phase_id}'",
                        f"phases.{phase_id}.{decision_id}",
                    )
                )

    # Check all phase decisions are covered
    for phase_id, phase in analysis_phases.items():
        phase_decisions = phase.get("decisions", {})
        if not phase_decisions:
            continue
        phase_selections = universe_phases.get(phase_id, {})
        for decision_id in phase_decisions:
            if decision_id not in phase_selections:
                errors.append(
                    SemanticError(
                        "MISSING_PHASE_DECISION",
                        f"Universe missing decision '{decision_id}' for phase '{phase_id}'",
                        f"phases.{phase_id}.{decision_id}",
                    )
                )

    # Check phase-level constraints
    for phase_id in universe_phases:
        if phase_id not in analysis_phases:
            continue
        phase_decisions = analysis_phases[phase_id].get("decisions", {})
        phase_selections = universe_phases[phase_id]
        errors.extend(
            _validate_phase_universe_constraints(
                phase_selections, phase_decisions, phase_id
            )
        )

    return errors


def _parse_constraint_ref(ref: str) -> tuple[str, str] | None:
    """Parse a constraint reference into (decision_id, option_id)."""
    parts = ref.split(".")
    if len(parts) == 2:
        return parts[0], parts[1]
    return None


def _validate_universe_constraints(
    universe_data: dict[str, Any], analysis_data: dict[str, Any]
) -> list[SemanticError]:
    """Validate that the universe respects all constraints."""
    errors: list[SemanticError] = []

    universe_decisions = universe_data.get("decisions", {})
    analysis_decisions = analysis_data.get("decisions", {})

    for decision_id, option_id in universe_decisions.items():
        decision = analysis_decisions.get(decision_id)
        if not decision:
            continue

        option = decision.get("options", {}).get(option_id)
        if not option:
            continue

        path = f"decisions.{decision_id}"

        # Check incompatible_with
        for ref in option.get("incompatible_with") or []:
            parsed = _parse_constraint_ref(ref)
            if parsed and universe_decisions.get(parsed[0]) == parsed[1]:
                errors.append(
                    SemanticError(
                        "INCOMPATIBLE_OPTIONS",
                        f"Option '{decision_id}.{option_id}' is incompatible with '{ref}'",
                        path,
                    )
                )

        # Check requires
        for ref in option.get("requires") or []:
            parsed = _parse_constraint_ref(ref)
            if parsed and universe_decisions.get(parsed[0]) != parsed[1]:
                actual = universe_decisions.get(parsed[0], "(not set)")
                errors.append(
                    SemanticError(
                        "MISSING_REQUIRED_OPTION",
                        f"Option '{decision_id}.{option_id}' requires '{ref}' but got '{actual}'",
                        path,
                    )
                )

    return errors


def _validate_phase_universe_constraints(
    phase_selections: dict[str, str],
    phase_decisions: dict[str, Any],
    phase_id: str,
) -> list[SemanticError]:
    """Validate that phase decision selections respect constraints."""
    errors: list[SemanticError] = []

    for decision_id, option_id in phase_selections.items():
        decision = phase_decisions.get(decision_id)
        if not decision:
            continue

        option = decision.get("options", {}).get(option_id)
        if not option:
            continue

        path = f"phases.{phase_id}.{decision_id}"

        # Check incompatible_with
        for ref in option.get("incompatible_with") or []:
            parsed = _parse_constraint_ref(ref)
            if parsed and phase_selections.get(parsed[0]) == parsed[1]:
                errors.append(
                    SemanticError(
                        "INCOMPATIBLE_OPTIONS",
                        f"Option '{decision_id}.{option_id}' is incompatible with '{ref}'",
                        path,
                    )
                )

        # Check requires
        for ref in option.get("requires") or []:
            parsed = _parse_constraint_ref(ref)
            if parsed and phase_selections.get(parsed[0]) != parsed[1]:
                actual = phase_selections.get(parsed[0], "(not set)")
                errors.append(
                    SemanticError(
                        "MISSING_REQUIRED_OPTION",
                        f"Option '{decision_id}.{option_id}' requires '{ref}' but got '{actual}'",
                        path,
                    )
                )

    return errors


def validate_analysis_file(path: str | Path) -> list[SemanticError]:
    """Load and validate an analysis file."""
    data = load_yaml(path)
    return validate_analysis(data)


def validate_universe_file(
    universe_path: str | Path,
    analysis_path: str | Path,
) -> list[SemanticError]:
    """Load and validate a universe file against an analysis."""
    analysis_data = load_yaml(analysis_path)
    universe_data = load_yaml(universe_path)
    return validate_universe(universe_data, analysis_data)
