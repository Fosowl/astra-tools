"""Functions for parsing CWL workflow results and updating universe files."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def parse_cwltool_output(stdout: str) -> dict[str, Any]:
    """Parse JSON output from cwltool.

    cwltool outputs JSON to stdout when successful. This function extracts
    and parses that JSON.

    Args:
        stdout: The stdout from cwltool execution.

    Returns:
        Parsed JSON as a dictionary.

    Raises:
        ValueError: If no valid JSON found in output.
    """
    # cwltool outputs JSON on success - find the last JSON object
    # (there may be progress messages before it)
    lines = stdout.strip().split("\n")

    # Try parsing from the end, looking for a complete JSON object
    for i in range(len(lines) - 1, -1, -1):
        # Check if this line starts a JSON object
        if lines[i].strip().startswith("{"):
            json_text = "\n".join(lines[i:])
            try:
                return json.loads(json_text)
            except json.JSONDecodeError:
                continue

    raise ValueError("No valid JSON found in cwltool output")


def cwltool_to_results(
    cwl_output: dict[str, Any],
    analysis: dict[str, Any],
    outdir: Path,
    workflow_path: str,
    duration_seconds: float,
) -> dict[str, Any]:
    """Convert cwltool output to ASP results format.

    Args:
        cwl_output: Parsed JSON output from cwltool.
        analysis: The ASP analysis specification (for output/artefact metadata).
        outdir: Output directory where files were written.
        workflow_path: Path to the CWL workflow (relative to project).
        duration_seconds: How long the workflow took to run.

    Returns:
        Results dict in ASP format.
    """
    results: dict[str, Any] = {
        "_meta": {
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "workflow": workflow_path,
            "duration_seconds": round(duration_seconds, 2),
        },
    }

    # Build lookup for output types
    output_types: dict[str, str] = {}
    for output in analysis.get("analysis", {}).get("outputs", []):
        output_types[output["id"]] = output.get("type", "data")

    # Build lookup for artefact types (chunk_id -> artefact_id -> type)
    artefact_types: dict[str, dict[str, str]] = {}
    for chunk_id, chunk in analysis.get("chunks", {}).items():
        artefact_types[chunk_id] = {}
        for artefact in chunk.get("artefacts", []) or []:
            artefact_types[chunk_id][artefact["id"]] = artefact.get("type", "data")

    outputs: dict[str, Any] = {}
    artefacts: dict[str, dict[str, Any]] = {}

    for key, value in cwl_output.items():
        # Check if this is a file output
        if isinstance(value, dict) and value.get("class") == "File":
            result_value = _file_to_result_value(value, outdir, output_types.get(key, "data"))

            # Determine if this is an output or an artefact
            # Artefact keys follow pattern: chunk_id__artefact_id
            if "__" in key:
                chunk_id, artefact_id = key.split("__", 1)
                if chunk_id not in artefacts:
                    artefacts[chunk_id] = {}
                art_type = artefact_types.get(chunk_id, {}).get(artefact_id, "data")
                result_value["type"] = art_type
                artefacts[chunk_id][artefact_id] = result_value
            else:
                outputs[key] = result_value

        # Check for inline values (metrics, etc.)
        elif not isinstance(value, dict) or value.get("class") != "Directory":
            # This is a scalar value (metric)
            output_type = output_types.get(key, "metric")
            outputs[key] = {
                "type": output_type,
                "value": value,
            }

    if outputs:
        results["outputs"] = outputs
    if artefacts:
        results["artefacts"] = artefacts

    return results


def _file_to_result_value(
    file_output: dict[str, Any],
    outdir: Path,
    default_type: str,
) -> dict[str, Any]:
    """Convert a CWL File output to ResultValue format.

    Args:
        file_output: CWL File object with location, size, etc.
        outdir: Output directory for computing relative paths.
        default_type: Default type if not determinable.

    Returns:
        ResultValue dict.
    """
    location = file_output.get("location", file_output.get("path", ""))

    # Convert file:// URL to path
    if location.startswith("file://"):
        location = location[7:]

    # Make path relative to outdir's parent (project root)
    try:
        abs_path = Path(location).resolve()
        rel_path = abs_path.relative_to(outdir.parent.resolve())
        path_str = str(rel_path)
    except (ValueError, TypeError):
        path_str = location

    # Determine format from extension
    format_str = None
    if "." in path_str:
        format_str = path_str.rsplit(".", 1)[-1].lower()

    result: dict[str, Any] = {
        "type": default_type,
        "path": path_str,
    }

    if format_str:
        result["format"] = format_str

    if file_output.get("size"):
        result["size"] = file_output["size"]

    return result


def update_universe_results(universe_path: Path, results: dict[str, Any]) -> None:
    """Update a universe file with workflow results.

    Preserves existing content and only updates/adds the results section.

    Args:
        universe_path: Path to the universe YAML file.
        results: Results dict to write.
    """
    # Load existing universe
    with open(universe_path) as f:
        content = f.read()

    # Parse YAML
    universe = yaml.safe_load(content)

    # Update results
    universe["results"] = results

    # Write back with preserved formatting where possible
    with open(universe_path, "w") as f:
        yaml.safe_dump(
            universe,
            f,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )


def clear_universe_results(universe_path: Path) -> None:
    """Remove results section from a universe file.

    Args:
        universe_path: Path to the universe YAML file.
    """
    with open(universe_path) as f:
        universe = yaml.safe_load(f)

    if "results" in universe:
        del universe["results"]

        with open(universe_path, "w") as f:
            yaml.safe_dump(
                universe,
                f,
                sort_keys=False,
                allow_unicode=True,
                default_flow_style=False,
            )
