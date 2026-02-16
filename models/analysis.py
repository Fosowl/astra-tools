"""Pydantic models for ASP analysis specifications."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from models.insight import Insight


class Checksum(BaseModel):
    """Checksum for data integrity verification."""

    model_config = ConfigDict(extra="forbid")

    algorithm: Literal["sha256", "sha512", "md5"] = Field(description="Hash algorithm")
    value: str = Field(description="Hash value")


class Input(BaseModel):
    """An input to the analysis.

    Two kinds of inputs:
    - ``type: data`` — a dataset, file, or external resource (specify ``source``)
    - ``type: analysis`` — outputs from another ASP analysis (specify ``ref``)

    Sub-analysis inputs can also use ``from`` to reference a parent input
    or a sibling's output (e.g., ``from: sibling_id.output_id``).
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str = Field(
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Unique identifier for the input",
    )
    type: Literal["data", "analysis"] = Field(description="Type of input")
    description: str | None = Field(default=None, description="Description of the input")

    # Data inputs
    source: str | None = Field(
        default=None, description="URI or path to the data source"
    )
    checksum: Checksum | None = Field(
        default=None, description="Checksum for data integrity verification"
    )

    # Analysis inputs
    ref: str | None = Field(
        default=None, description="Reference to another ASP analysis"
    )
    ref_version: str | None = Field(
        default=None, description="Version of the referenced analysis"
    )
    use_outputs: list[str] | None = Field(
        default=None, description="Specific outputs to use from referenced analysis"
    )

    # Sub-analysis wiring
    from_: str | None = Field(
        default=None,
        alias="from",
        description="Reference to parent input or sibling output "
        "(e.g., 'input_id' or 'sibling.output_id')",
    )


class Output(BaseModel):
    """An expected output from the analysis.

    Outputs can declare their provenance via ``from`` to trace which
    sub-analysis produces them (e.g., ``from: inference.posterior``).
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str = Field(
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Unique identifier for the output",
    )
    type: Literal["metric", "figure", "table", "data", "report"] = Field(
        description="Type of output"
    )
    description: str | None = Field(default=None, description="Description of the output")

    # Provenance: which sub-analysis produces this output
    from_: str | None = Field(
        default=None,
        alias="from",
        description="Sub-analysis output that produces this "
        "(e.g., 'sub_analysis.output_id')",
    )


class Resources(BaseModel):
    """Compute resource requirements for a recipe."""

    model_config = ConfigDict(extra="forbid")

    cpus: int | None = Field(default=None, ge=1, description="Number of CPUs")
    memory: str | None = Field(default=None, description="Memory requirement (e.g., '8GB', '512MB')")
    gpus: int | None = Field(default=None, ge=1, description="Number of GPUs")
    time_limit: str | None = Field(
        default=None, description="Maximum wall time (e.g., '2h', '30m')"
    )


class Recipe(BaseModel):
    """A build rule that produces one or more outputs.

    Recipes are the execution contract: run this command (optionally in a
    container) to produce the declared outputs.  Dependencies between
    recipes within the same analysis node form a DAG.
    """

    model_config = ConfigDict(extra="forbid")

    command: str = Field(description="Command to execute (e.g., 'python src/train.py')")
    outputs: list[str] = Field(
        min_length=1,
        description="Output IDs this recipe produces (must match declared outputs)",
    )
    container: str | None = Field(
        default=None,
        description="Container image override (defaults to node-level container)",
    )
    depends_on: list[str] | None = Field(
        default=None,
        description="Recipe IDs that must complete before this recipe runs",
    )
    resources: Resources | None = Field(
        default=None,
        description="Compute resource requirements",
    )


class Option(BaseModel):
    """An option for a decision."""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(description="Human-readable name for the option")
    description: str | None = Field(default=None, description="Detailed description of the option")
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
    rationale: str | None = Field(default=None, description="Why this decision exists")
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


class Analysis(BaseModel):
    """A self-similar analysis specification.

    Every level has the same structure: description, inputs, outputs,
    decisions, insights, and optional sub-analyses. A sub-analysis extracted
    to its own file is a valid Analysis on its own.

    At the root level, ``version`` and ``name`` are additionally required.
    Sub-analyses must declare ``inputs`` and ``outputs`` (enforced by
    semantic validation).  Use ``parent_decisions`` to declare dependencies
    on parent-scope decisions for cross-level constraints.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "https://asp-spec.org/v1/analysis.schema.json",
            "title": "ASP Analysis Specification",
        },
    )

    # Document metadata
    schema_: str | None = Field(default=None, alias="$schema", description="JSON Schema reference")
    version: str | None = Field(
        default=None,
        pattern=r"^\d+\.\d+$",
        description="ASP specification version",
    )

    # Analysis identity
    name: str | None = Field(default=None, description="Human-readable name for the analysis")
    authors: list[str] | None = Field(default=None, description="List of authors")
    tags: list[str] | None = Field(default=None, description="Tags for categorization")

    # Analysis content
    description: str | None = Field(
        default=None, description="Description of what this analysis aims to achieve"
    )
    success_criteria: list[str] | None = Field(
        default=None,
        description="Concrete criteria for determining if this analysis succeeded.",
    )
    inputs: list[Input] | None = Field(
        default=None,
        description="List of inputs for this analysis",
    )
    outputs: list[Output] | None = Field(
        default=None,
        description="List of expected outputs from this analysis",
    )
    decisions: dict[str, Decision] = Field(
        default_factory=dict,
        description="Map of decision IDs to decision specifications",
    )
    insights: dict[str, Insight] = Field(
        default_factory=dict,
        description="Map of insight IDs to insight specifications",
    )

    # Cross-level dependencies
    parent_decisions: list[str] | None = Field(
        default=None,
        description="Decision IDs from parent scope that this sub-analysis depends on. "
        "Makes parent decisions available for constraints and enables standalone packaging.",
    )

    # Execution
    container: str | None = Field(
        default=None,
        description="Default container image for recipes in this node",
    )
    recipes: dict[str, Recipe] | None = Field(
        default=None,
        description="Map of recipe IDs to build rules that produce outputs",
    )

    # Self-similar nesting
    analyses: dict[str, Analysis] | None = Field(
        default=None,
        description="Map of sub-analysis IDs to nested analyses",
    )


# Required for Pydantic self-referencing models
Analysis.model_rebuild()
