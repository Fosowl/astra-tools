"""Pydantic models for ASP analysis specifications."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from models.insight import Insight


class Checksum(BaseModel):
    """Checksum for data integrity verification."""

    model_config = ConfigDict(extra="forbid")

    algorithm: Literal["sha256", "sha512", "md5"] = Field(description="Hash algorithm")
    value: str = Field(description="Hash value")


class Source(BaseModel):
    """Source specification for inputs."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["url", "s3", "sklearn", "asp", "file"] = Field(description="Type of source")
    url: str | None = Field(default=None, description="URL for url type sources")
    bucket: str | None = Field(default=None, description="S3 bucket name")
    key: str | None = Field(default=None, description="S3 object key")
    version_id: str | None = Field(default=None, description="S3 version ID")
    region: str | None = Field(default=None, description="AWS region")
    dataset: str | None = Field(default=None, description="sklearn dataset name")
    analysis: str | None = Field(default=None, description="ASP analysis reference")
    version: str | None = Field(default=None, description="Version of referenced analysis")
    output: str | None = Field(default=None, description="Output ID from referenced analysis")
    execution: str | None = Field(default=None, description="Specific execution ID")
    path: str | None = Field(default=None, description="Local file path")
    checksum: Checksum | None = Field(default=None, description="Checksum for verification")


class Input(BaseModel):
    """An input to the analysis."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str = Field(
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Unique identifier for the input",
    )
    type: Literal["data", "analysis", "literature"] = Field(description="Type of input")
    source: str | Source | None = Field(
        default=None, description="Source specification for the input"
    )
    from_: str | None = Field(
        default=None,
        alias="from",
        description="Reference to parent input or sibling output (e.g., 'input_id' or "
        "'sibling.output_id')",
    )
    ref: str | None = Field(
        default=None, description="Reference to another analysis (for type: analysis)"
    )
    version: str | None = Field(default=None, description="Version of the referenced analysis")
    use_outputs: list[str] | None = Field(
        default=None, description="Specific outputs to use from referenced analysis"
    )
    description: str | None = Field(default=None, description="Description of the input")


class Output(BaseModel):
    """An expected output from the analysis."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Unique identifier for the output",
    )
    type: Literal["metric", "figure", "table", "data", "model", "report"] = Field(
        description="Type of output"
    )
    dtype: Literal["float", "int", "bool", "string"] | None = Field(
        default=None, description="Data type for metrics"
    )
    range: tuple[float, float] | None = Field(
        default=None, description="Valid range for numeric metrics [min, max]"
    )
    formats: list[str] | None = Field(
        default=None, description="Supported file formats for artifacts"
    )
    path: str | None = Field(
        default=None, description="Relative path for result file within results directory"
    )
    description: str | None = Field(default=None, description="Description of the output")


class Option(BaseModel):
    """An option for a decision."""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(description="Human-readable name for the option")
    description: str | None = Field(default=None, description="Detailed description of the option")
    value: Any | None = Field(default=None, description="Configuration value for this option")
    insights: list[str] | None = Field(
        default=None, description="List of insight IDs supporting this option"
    )
    incompatible_with: list[str] | None = Field(
        default=None,
        description="List of decision.option pairs that cannot be selected together",
    )
    requires: list[str] | None = Field(
        default=None,
        description="List of decision.option pairs that must also be selected",
    )


class Decision(BaseModel):
    """A decision point in the analysis."""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(description="Human-readable name for the decision")
    type: Literal["data", "method", "parameter"] = Field(description="Category of decision")
    importance: int = Field(
        ge=1,
        le=5,
        default=3,
        description="Importance level (1=critical, 5=implementation detail)",
    )
    rationale: str | None = Field(default=None, description="Why this decision exists")
    reviewed: bool | None = Field(
        default=None,
        description="Whether a human has reviewed and confirmed this decision",
    )
    default: str | None = Field(
        default=None, description="Default option ID for baseline universes"
    )
    options: dict[str, Option] = Field(description="Map of option IDs to option specifications")

    @model_validator(mode="after")
    def validate_default_exists(self) -> Decision:
        """Ensure default option exists in options."""
        if self.default is not None and self.default not in self.options:
            raise ValueError(f"Default option '{self.default}' not found in options")
        return self


class AnalysisNode(BaseModel):
    """A self-similar analysis node. Can contain sub-analyses recursively."""

    model_config = ConfigDict(extra="forbid")

    problem: str | None = Field(
        default=None,
        description="Problem statement for this analysis node",
    )
    description: str | None = Field(
        default=None, description="Detailed description of this analysis node"
    )
    success_criteria: list[str] | None = Field(
        default=None,
        description="Concrete criteria for determining if this analysis node succeeded.",
    )
    plan: str | None = Field(
        default=None,
        description="Relative path to implementation notes "
        "(e.g. steps/main/PLAN.md). Documents approach, libraries, and "
        "how decisions map to code.",
    )
    inputs: list[Input] | None = Field(
        default=None,
        description="List of inputs for this analysis node",
    )
    outputs: list[Output] | None = Field(
        default=None,
        description="List of expected outputs from this analysis node",
    )
    decisions: dict[str, Decision] = Field(
        default_factory=dict,
        description="Map of decision IDs to decision specifications",
    )
    analyses: dict[str, AnalysisNode] | None = Field(
        default=None,
        description="Map of sub-analysis IDs to nested analysis nodes",
    )


# Required for Pydantic self-referencing models
AnalysisNode.model_rebuild()


class AnalysisContent(BaseModel):
    """The content of an analysis specification (root level with metadata)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Human-readable name for the analysis")
    description: str | None = Field(
        default=None, description="Detailed description of the analysis"
    )
    authors: list[str] | None = Field(default=None, description="List of authors")
    tags: list[str] | None = Field(default=None, description="Tags for categorization")
    problem: str = Field(
        description="Problem statement describing what the analysis aims to achieve"
    )
    success_criteria: list[str] | None = Field(
        default=None,
        description="Concrete criteria for determining if the analysis succeeded. "
        "Each criterion should be specific and verifiable.",
    )
    inputs: list[Input] = Field(description="List of inputs for the analysis")
    outputs: list[Output] = Field(description="List of expected outputs")
    decisions: dict[str, Decision] = Field(
        default_factory=dict,
        description="Map of decision IDs to decision specifications",
    )
    analyses: dict[str, AnalysisNode] | None = Field(
        default=None,
        description="Map of sub-analysis IDs to nested analysis nodes",
    )


class Analysis(BaseModel):
    """Complete ASP analysis specification."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "https://asp-spec.org/v1/analysis.schema.json",
            "title": "ASP Analysis Specification",
        },
    )

    schema_: str | None = Field(default=None, alias="$schema", description="JSON Schema reference")
    version: str = Field(pattern=r"^\d+\.\d+$", description="ASP specification version")
    analysis: AnalysisContent = Field(description="The analysis specification")
    insights: dict[str, Insight] = Field(
        default_factory=dict,
        description="Map of insight IDs to insight specifications",
    )

    @classmethod
    def from_yaml(cls, path: str | Path) -> Analysis:
        """Load an analysis from a YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)

    def to_yaml(self, path: str | Path) -> None:
        """Save the analysis to a YAML file."""
        data = self.model_dump(by_alias=True, exclude_none=True)
        with open(path, "w") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

    def get_input(self, input_id: str) -> Input | None:
        """Get an input by ID."""
        for inp in self.analysis.inputs:
            if inp.id == input_id:
                return inp
        return None

    def get_output(self, output_id: str) -> Output | None:
        """Get an output by ID."""
        for out in self.analysis.outputs:
            if out.id == output_id:
                return out
        return None

    def get_decision(self, decision_id: str, path: str | None = None) -> Decision | None:
        """Get a decision by ID, optionally scoped to a path.

        Args:
            decision_id: The decision ID to find.
            path: Dot-separated path to a sub-analysis (e.g., 'build_mocks').
                  If None, searches root decisions then all sub-analyses.
        """
        if path is not None:
            node = self._resolve_node(path)
            if node is not None:
                return node.decisions.get(decision_id)
            return None
        # Search root decisions first
        if decision_id in self.analysis.decisions:
            return self.analysis.decisions[decision_id]
        # Search sub-analyses
        if self.analysis.analyses:
            for sub in self.analysis.analyses.values():
                found = self._search_node_decision(sub, decision_id)
                if found is not None:
                    return found
        return None

    def _resolve_node(self, path: str) -> AnalysisNode | None:
        """Resolve a dot-separated path to a sub-analysis node."""
        analyses = self.analysis.analyses
        for part in path.split("."):
            if analyses is None or part not in analyses:
                return None
            node = analyses[part]
            analyses = node.analyses
        return node

    def _search_node_decision(self, node: AnalysisNode, decision_id: str) -> Decision | None:
        """Recursively search a node and its children for a decision."""
        if decision_id in node.decisions:
            return node.decisions[decision_id]
        if node.analyses:
            for sub in node.analyses.values():
                found = self._search_node_decision(sub, decision_id)
                if found is not None:
                    return found
        return None

    def get_insight(self, insight_id: str) -> Insight | None:
        """Get an insight by ID."""
        return self.insights.get(insight_id)

    def get_default_universe(self) -> dict[str, Any]:
        """Get the default universe based on decision defaults across entire tree."""
        result: dict[str, Any] = {}
        # Root decisions
        root_defaults: dict[str, str] = {}
        for decision_id, decision in self.analysis.decisions.items():
            if decision.default is not None:
                root_defaults[decision_id] = decision.default
        if root_defaults:
            result["decisions"] = root_defaults
        # Sub-analyses
        if self.analysis.analyses:
            analyses_defaults: dict[str, Any] = {}
            for node_id, node in self.analysis.analyses.items():
                node_defaults = self._get_node_defaults(node)
                if node_defaults:
                    analyses_defaults[node_id] = node_defaults
            if analyses_defaults:
                result["analyses"] = analyses_defaults
        return result

    def _get_node_defaults(self, node: AnalysisNode) -> dict[str, Any]:
        """Recursively get defaults from a node."""
        result: dict[str, Any] = {}
        decisions: dict[str, str] = {}
        for decision_id, decision in node.decisions.items():
            if decision.default is not None:
                decisions[decision_id] = decision.default
        if decisions:
            result["decisions"] = decisions
        if node.analyses:
            analyses_defaults: dict[str, Any] = {}
            for sub_id, sub_node in node.analyses.items():
                sub_defaults = self._get_node_defaults(sub_node)
                if sub_defaults:
                    analyses_defaults[sub_id] = sub_defaults
            if analyses_defaults:
                result["analyses"] = analyses_defaults
        return result
