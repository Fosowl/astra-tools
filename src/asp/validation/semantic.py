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

    # Validate sub-analyses
    sub_analyses = data.get("sub_analyses", {})
    if sub_analyses:
        errors.extend(
            _validate_sub_analyses(sub_analyses, input_ids, output_ids, outputs)
        )

    return errors


def _validate_sub_analyses(
    sub_analyses: dict[str, Any],
    parent_input_ids: set[str],
    parent_output_ids: set[str],
    parent_outputs: list[dict[str, Any]],
) -> list[SemanticError]:
    """Validate sub-analysis references and wiring."""
    errors: list[SemanticError] = []

    # Collect all sub-analysis IDs and their declared output IDs (for sibling references)
    sub_analysis_ids = set(sub_analyses.keys())

    # Validate each sub-analysis reference
    for sub_id, sub_ref in sub_analyses.items():
        sub_path = f"sub_analyses.{sub_id}"

        # Validate input wiring references
        input_wiring = sub_ref.get("inputs") or {}
        for input_id, source_ref in input_wiring.items():
            errors.extend(
                _validate_wiring_ref(
                    source_ref, parent_input_ids, sub_analysis_ids, sub_id, sub_path
                )
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
                        f"in 'sub_analysis_id.output_id' format",
                        f"outputs.{out_id}",
                    )
                )
            elif parts[0] not in sub_analysis_ids:
                errors.append(
                    SemanticError(
                        "INVALID_FROM_REF",
                        f"Output 'from' references unknown sub-analysis '{parts[0]}'",
                        f"outputs.{out_id}",
                    )
                )

    # Check for cycles in the sub-analysis DAG
    errors.extend(_validate_sub_analysis_dag(sub_analyses))

    return errors


def _validate_wiring_ref(
    ref: str,
    parent_input_ids: set[str],
    sub_analysis_ids: set[str],
    current_sub_id: str,
    sub_path: str,
) -> list[SemanticError]:
    """Validate a single input wiring reference."""
    errors: list[SemanticError] = []

    if ref.startswith("inputs."):
        # Reference to a parent input
        input_id = ref[7:]  # Remove "inputs." prefix
        if input_id not in parent_input_ids:
            errors.append(
                SemanticError(
                    "INVALID_WIRING_REF",
                    f"Wiring ref '{ref}' points to non-existent parent input '{input_id}'",
                    sub_path,
                )
            )
    else:
        # Reference to a sibling sub-analysis output: "sub_id.output_id"
        parts = ref.split(".")
        if len(parts) != 2:
            errors.append(
                SemanticError(
                    "INVALID_WIRING_FORMAT",
                    f"Wiring ref '{ref}' should be 'inputs.<id>' "
                    f"or '<sub_analysis_id>.<output_id>'",
                    sub_path,
                )
            )
        else:
            sibling_id = parts[0]
            if sibling_id == current_sub_id:
                errors.append(
                    SemanticError(
                        "SELF_REFERENCE",
                        f"Sub-analysis '{current_sub_id}' cannot reference its own outputs",
                        sub_path,
                    )
                )
            elif sibling_id not in sub_analysis_ids:
                errors.append(
                    SemanticError(
                        "INVALID_WIRING_REF",
                        f"Wiring ref '{ref}' points to non-existent sub-analysis '{sibling_id}'",
                        sub_path,
                    )
                )

    return errors


def _validate_sub_analysis_dag(
    sub_analyses: dict[str, Any],
) -> list[SemanticError]:
    """Validate that sub-analysis wiring forms a DAG (no cycles)."""
    errors: list[SemanticError] = []

    # Build adjacency list from wiring references
    # An edge from A -> B means B depends on A (B uses A's output)
    dependencies: dict[str, set[str]] = {sub_id: set() for sub_id in sub_analyses}

    for sub_id, sub_ref in sub_analyses.items():
        input_wiring = sub_ref.get("inputs") or {}
        for source_ref in input_wiring.values():
            if not source_ref.startswith("inputs."):
                parts = source_ref.split(".")
                if len(parts) == 2 and parts[0] in sub_analyses:
                    dependencies[sub_id].add(parts[0])

    # Detect cycles using topological sort (Kahn's algorithm)
    in_degree = {sub_id: len(deps) for sub_id, deps in dependencies.items()}
    queue = [sub_id for sub_id, deg in in_degree.items() if deg == 0]
    visited = 0

    while queue:
        node = queue.pop(0)
        visited += 1
        for sub_id, deps in dependencies.items():
            if node in deps:
                in_degree[sub_id] -= 1
                if in_degree[sub_id] == 0:
                    queue.append(sub_id)

    if visited != len(sub_analyses):
        errors.append(
            SemanticError(
                "CYCLE_DETECTED",
                "Sub-analysis wiring contains a cycle",
                "sub_analyses",
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

    # Check sub-analysis universe references
    universe_sub_analyses = universe_data.get("sub_analyses", {})
    analysis_sub_analyses = analysis_data.get("sub_analyses", {})

    for sub_id in universe_sub_analyses:
        if sub_id not in analysis_sub_analyses:
            errors.append(
                SemanticError(
                    "UNKNOWN_SUB_ANALYSIS",
                    f"Universe references unknown sub-analysis: {sub_id}",
                    f"sub_analyses.{sub_id}",
                )
            )

    for sub_id in analysis_sub_analyses:
        if sub_id not in universe_sub_analyses and analysis_sub_analyses:
            errors.append(
                SemanticError(
                    "MISSING_SUB_ANALYSIS_UNIVERSE",
                    f"Universe missing sub-analysis universe selection: {sub_id}",
                    f"sub_analyses.{sub_id}",
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
