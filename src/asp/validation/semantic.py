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
    - Input/output IDs are unique
    - Decisions: defaults exist, evidence refs valid, constraint refs valid
    - Sub-analysis validation (recursive)
    - `from` reference validation on sub-analysis inputs

    Args:
        data: The analysis data as a dict.

    Returns:
        List of semantic errors (empty if valid).
    """
    errors: list[SemanticError] = []

    analysis_content = data.get("analysis", {})
    inputs = analysis_content.get("inputs", [])
    outputs = analysis_content.get("outputs", [])
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

    # Validate root-level decisions
    root_decisions = analysis_content.get("decisions") or {}
    errors.extend(_validate_decisions(root_decisions, insights, "analysis"))

    # Validate sub-analyses recursively
    sub_analyses = analysis_content.get("analyses") or {}
    for analysis_id, analysis_node in sub_analyses.items():
        errors.extend(
            _validate_analysis_node(
                analysis_id,
                analysis_node,
                insights,
                parent_input_ids=input_ids,
                sibling_analyses=sub_analyses,
                path_prefix="analysis.analyses",
            )
        )

    return errors


def _validate_analysis_node(
    node_id: str,
    node: dict[str, Any],
    insights: dict[str, Any],
    parent_input_ids: set[str],
    sibling_analyses: dict[str, Any],
    path_prefix: str,
) -> list[SemanticError]:
    """Validate a single analysis node's decisions, inputs, and sub-analyses."""
    errors: list[SemanticError] = []
    node_path = f"{path_prefix}.{node_id}"

    # Validate node inputs (check `from` references)
    node_inputs = node.get("inputs") or []
    node_input_ids: set[str] = set()
    for inp in node_inputs:
        inp_id = inp.get("id")
        if inp_id:
            node_input_ids.add(inp_id)
        from_ref = inp.get("from")
        if from_ref:
            errors.extend(
                _validate_from_ref(from_ref, parent_input_ids, sibling_analyses, node_id, node_path)
            )

    # Validate node output IDs are unique
    node_output_ids: set[str] = set()
    for out in node.get("outputs") or []:
        out_id = out.get("id")
        if out_id in node_output_ids:
            errors.append(
                SemanticError(
                    "DUPLICATE_OUTPUT",
                    f"Duplicate output ID in analysis node: {out_id}",
                    f"{node_path}.outputs.{out_id}",
                )
            )
        if out_id:
            node_output_ids.add(out_id)

    # Validate decisions
    node_decisions = node.get("decisions") or {}
    errors.extend(_validate_decisions(node_decisions, insights, node_path))

    # Recurse into sub-analyses
    sub_analyses = node.get("analyses") or {}
    for sub_id, sub_node in sub_analyses.items():
        errors.extend(
            _validate_analysis_node(
                sub_id,
                sub_node,
                insights,
                parent_input_ids=node_input_ids,
                sibling_analyses=sub_analyses,
                path_prefix=f"{node_path}.analyses",
            )
        )

    return errors


def _validate_decisions(
    decisions: dict[str, Any],
    insights: dict[str, Any],
    path_prefix: str,
) -> list[SemanticError]:
    """Validate a set of decisions at a given node."""
    errors: list[SemanticError] = []

    for decision_id, decision in decisions.items():
        decision_path = f"{path_prefix}.decisions.{decision_id}"
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

            # Check insight references
            insight_refs = option.get("insights") or []
            for i, insight_ref in enumerate(insight_refs):
                if insight_ref not in insights:
                    errors.append(
                        SemanticError(
                            "INVALID_INSIGHT_REF",
                            f"Option insight '{insight_ref}' not found in insights",
                            f"{option_path}.insights[{i}]",
                        )
                    )

            # Check incompatible_with refs (scoped to this node's decisions)
            incompatible_with = option.get("incompatible_with") or []
            for ref in incompatible_with:
                errors.extend(_validate_constraint_ref(ref, decisions, option_path))

            # Check requires refs (scoped to this node's decisions)
            requires = option.get("requires") or []
            for ref in requires:
                errors.extend(_validate_constraint_ref(ref, decisions, option_path))

    return errors


def _validate_from_ref(
    from_ref: str,
    parent_input_ids: set[str],
    sibling_analyses: dict[str, Any],
    current_node_id: str,
    node_path: str,
) -> list[SemanticError]:
    """Validate a `from` reference on a sub-analysis input.

    `from: input_id` references a parent input.
    `from: sibling.output_id` references a sibling's output.
    """

    def _error(message: str) -> list[SemanticError]:
        return [SemanticError("INVALID_FROM_REF", message, node_path)]

    parts = from_ref.split(".")
    if len(parts) == 1:
        if from_ref not in parent_input_ids:
            return _error(f"from reference '{from_ref}' not found in parent inputs")
        return []

    if len(parts) == 2:
        sibling_id, output_id = parts
        if sibling_id == current_node_id:
            return _error(f"from reference '{from_ref}' cannot reference own outputs")
        if sibling_id not in sibling_analyses:
            return _error(
                f"from reference '{from_ref}' points to non-existent sibling '{sibling_id}'"
            )
        sibling_outputs = sibling_analyses[sibling_id].get("outputs") or []
        sibling_output_ids = {o.get("id") for o in sibling_outputs if o.get("id")}
        if output_id not in sibling_output_ids:
            return _error(
                f"from reference '{from_ref}' points to non-existent output "
                f"'{output_id}' in sibling '{sibling_id}'"
            )
        return []

    return _error(
        f"from reference '{from_ref}' has invalid format "
        "(expected 'input_id' or 'sibling.output_id')"
    )


def _validate_constraint_ref(
    ref: str, decisions: dict[str, Any], option_path: str
) -> list[SemanticError]:
    """Validate a constraint reference (decision.option format)."""
    parts = ref.split(".")
    if len(parts) != 2:
        return [
            SemanticError(
                "INVALID_CONSTRAINT_FORMAT",
                f"Constraint '{ref}' should be in 'decision.option' format",
                option_path,
            )
        ]

    decision_id, option_id = parts

    if decision_id not in decisions:
        return [
            SemanticError(
                "INVALID_CONSTRAINT_REF",
                f"Constraint ref '{ref}' points to non-existent decision '{decision_id}'",
                option_path,
            )
        ]

    if option_id not in decisions[decision_id].get("options", {}):
        return [
            SemanticError(
                "INVALID_CONSTRAINT_REF",
                f"Constraint ref '{ref}' points to non-existent option '{option_id}'",
                option_path,
            )
        ]

    return []


def validate_universe(
    universe_data: dict[str, Any], analysis_data: dict[str, Any]
) -> list[SemanticError]:
    """Validate a universe against an analysis specification.

    Universe mirrors the analysis tree: root-level decisions + recursive analyses.

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
    return _validate_universe_node(
        universe_data,
        analysis_data.get("analysis", {}),
        path_prefix="",
    )


def _validate_universe_node(
    universe_node: dict[str, Any],
    analysis_node: dict[str, Any],
    path_prefix: str,
) -> list[SemanticError]:
    """Recursively validate a universe node against an analysis node.

    Validates decisions at this level, checks for unknown/missing analyses,
    then recurses into sub-analyses.
    """
    errors: list[SemanticError] = []

    # Validate decisions at this level
    analysis_decisions = analysis_node.get("decisions") or {}
    universe_decisions = universe_node.get("decisions") or {}
    decisions_path = f"{path_prefix}.decisions" if path_prefix else "decisions"

    # Check for unknown decisions in universe
    for decision_id, option_id in universe_decisions.items():
        if decision_id not in analysis_decisions:
            errors.append(
                SemanticError(
                    "UNKNOWN_DECISION",
                    f"Universe references unknown decision '{decision_id}'",
                    f"{decisions_path}.{decision_id}",
                )
            )
            continue

        options = analysis_decisions[decision_id].get("options", {})
        if option_id not in options:
            errors.append(
                SemanticError(
                    "UNKNOWN_OPTION",
                    f"Universe selects unknown option '{option_id}' for decision '{decision_id}'",
                    f"{decisions_path}.{decision_id}",
                )
            )

    # Check all analysis decisions are covered
    for decision_id in analysis_decisions:
        if decision_id not in universe_decisions:
            errors.append(
                SemanticError(
                    "MISSING_DECISION",
                    f"Universe missing decision '{decision_id}'",
                    f"{decisions_path}.{decision_id}",
                )
            )

    # Check constraints
    errors.extend(
        _validate_node_universe_constraints(universe_decisions, analysis_decisions, decisions_path)
    )

    # Recurse into sub-analyses
    analysis_sub = analysis_node.get("analyses") or {}
    universe_sub = universe_node.get("analyses") or {}
    analyses_prefix = f"{path_prefix}.analyses" if path_prefix else "analyses"

    for analysis_id in universe_sub:
        if analysis_id not in analysis_sub:
            errors.append(
                SemanticError(
                    "UNKNOWN_ANALYSIS",
                    f"Universe references unknown analysis: {analysis_id}",
                    f"{analyses_prefix}.{analysis_id}",
                )
            )

    for analysis_id, sub_analysis_node in analysis_sub.items():
        errors.extend(
            _validate_universe_node(
                universe_sub.get(analysis_id, {}),
                sub_analysis_node,
                path_prefix=f"{analyses_prefix}.{analysis_id}",
            )
        )

    return errors


def _parse_constraint_ref(ref: str) -> tuple[str, str] | None:
    """Parse a constraint reference into (decision_id, option_id)."""
    parts = ref.split(".")
    if len(parts) == 2:
        return parts[0], parts[1]
    return None


def _validate_node_universe_constraints(
    universe_decisions: dict[str, str],
    analysis_decisions: dict[str, Any],
    path_prefix: str,
) -> list[SemanticError]:
    """Validate that decision selections respect constraints at one node."""
    errors: list[SemanticError] = []

    for decision_id, option_id in universe_decisions.items():
        decision = analysis_decisions.get(decision_id)
        if not decision:
            continue

        option = decision.get("options", {}).get(option_id)
        if not option:
            continue

        path = f"{path_prefix}.{decision_id}"

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
