"""Pydantic models for ASP universe specifications."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from models.analysis import Analysis


class ResultMeta(BaseModel):
    """Metadata about when and how results were computed."""

    model_config = ConfigDict(extra="forbid")

    computed_at: str = Field(description="ISO 8601 timestamp when results were computed")
    workflow: str | None = Field(default=None, description="Path to the CWL workflow used")
    duration_seconds: float | None = Field(default=None, description="Execution duration in seconds")


class ResultValue(BaseModel):
    """A single result value - either an inline value or a file reference."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(description="Result type (metric, figure, table, data, model, report)")
    value: Any | None = Field(default=None, description="Inline value for metrics")
    path: str | None = Field(default=None, description="Relative path to output file")
    format: str | None = Field(default=None, description="File format (e.g., png, parquet, joblib)")
    size: int | None = Field(default=None, description="File size in bytes")


class Results(BaseModel):
    """Results from running a workflow on this universe."""

    model_config = ConfigDict(extra="forbid")

    meta: ResultMeta | None = Field(default=None, alias="_meta")
    outputs: dict[str, ResultValue] | None = Field(
        default=None, description="Analysis-level output results"
    )
    artefacts: dict[str, dict[str, ResultValue]] | None = Field(
        default=None, description="Chunk-level artefact results (chunk_id -> artefact_id -> value)"
    )


class Universe(BaseModel):
    """A universe specification - a complete set of decisions organized by chunk."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "https://asp-spec.org/v1/universe.schema.json",
            "title": "ASP Universe Specification",
        },
    )

    schema_: str | None = Field(default=None, alias="$schema", description="JSON Schema reference")
    id: str = Field(
        pattern=r"^[a-z][a-z0-9_-]*$",
        description="Unique identifier for the universe",
    )
    description: str | None = Field(default=None, description="What this universe represents")
    chunks: dict[str, dict[str, str]] = Field(
        description="Map of chunk ID to decision selections (decision_id -> option_id) "
        "for that chunk",
    )
    results: Results | None = Field(
        default=None,
        description="Results from running a workflow on this universe",
    )

    @classmethod
    def from_yaml(cls, path: str | Path) -> Universe:
        """Load a universe from a YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)

    def to_yaml(self, path: str | Path) -> None:
        """Save the universe to a YAML file."""
        data = self.model_dump(by_alias=True, exclude_none=True)
        with open(path, "w") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

    @classmethod
    def from_defaults(
        cls,
        analysis: Analysis,
        universe_id: str = "baseline",
        description: str | None = None,
    ) -> Universe:
        """Create a universe from the default options in an analysis."""
        from models.analysis import Analysis

        if not isinstance(analysis, Analysis):
            raise TypeError("analysis must be an Analysis instance")

        chunks = analysis.get_default_universe()

        return cls(
            id=universe_id,
            description=description or "Default configuration using standard practices",
            chunks=chunks,
        )
