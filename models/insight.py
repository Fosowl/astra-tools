"""Pydantic models for scientific insights.

Simplified insight model with W3C Web Annotation-compliant selectors
for referencing content in scientific papers.

W3C Web Annotation compliance:
- TextQuoteSelector: https://www.w3.org/TR/annotation-model/#text-quote-selector
- FragmentSelector: https://www.w3.org/TR/annotation-model/#fragment-selector
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

# =============================================================================
# W3C Web Annotation Selectors
# =============================================================================


class TextQuoteSelector(BaseModel):
    """W3C TextQuoteSelector for locating text in a document.

    See: https://www.w3.org/TR/annotation-model/#text-quote-selector

    The authoritative anchor for verification. Text should be normalized
    (HTML/XML tags removed, entities decoded).
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    type: Literal["TextQuoteSelector"] = "TextQuoteSelector"
    exact: str = Field(min_length=1, description="Exact quoted text (1-3 sentences)")
    prefix: str | None = Field(
        default=None, description="~20-100 chars before for disambiguation"
    )
    suffix: str | None = Field(
        default=None, description="~20-100 chars after for disambiguation"
    )


class FragmentSelector(BaseModel):
    """W3C FragmentSelector for PDF locations.

    See: https://www.w3.org/TR/annotation-model/#fragment-selector
    Conforms to RFC 3778/8118 for PDF fragments.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    type: Literal["FragmentSelector"] = "FragmentSelector"
    conforms_to: Literal["http://tools.ietf.org/rfc/rfc3778"] = Field(
        default="http://tools.ietf.org/rfc/rfc3778",
        alias="conformsTo",
    )
    value: str | None = Field(default=None, description="Fragment (e.g., 'page=6')")
    page: int | None = Field(default=None, ge=1, description="1-indexed page number")


class FigureSelector(BaseModel):
    """Selector for referencing figures in scientific papers.

    Extension of W3C selector pattern for scientific literature.
    The label is the authoritative identifier (e.g., "Figure 3a").
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    type: Literal["FigureSelector"] = "FigureSelector"
    label: str = Field(min_length=1, description="Figure label (e.g., 'Figure 3a', 'Fig. 1')")
    caption: str | None = Field(default=None, description="Caption text for verification")


class TableSelector(BaseModel):
    """Selector for referencing tables in scientific papers.

    Extension of W3C selector pattern for scientific literature.
    The label is the authoritative identifier (e.g., "Table 2").
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    type: Literal["TableSelector"] = "TableSelector"
    label: str = Field(min_length=1, description="Table label (e.g., 'Table 1', 'Tab. 2')")
    caption: str | None = Field(default=None, description="Caption/header text for verification")
    region: str | None = Field(default=None, description="Specific region (e.g., 'row 3')")


# =============================================================================
# Sources
# =============================================================================


class ArxivSource(BaseModel):
    """Versioned arXiv paper source for reproducible references.

    The version is mandatory to ensure reproducibility - arXiv papers
    can be updated, and we need to reference a specific snapshot.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str = Field(min_length=1, description="Local ID for evidence references")
    type: Literal["arxiv"] = "arxiv"
    arxiv_id: str = Field(
        pattern=r"^\d{4}\.\d{4,5}$|^[a-z-]+/\d{7}$",
        description="arXiv ID without version (e.g., '1706.03762')",
    )
    version: int = Field(ge=1, description="arXiv version number")

    # Verification
    content_sha256: str | None = Field(
        default=None,
        pattern=r"^[a-fA-F0-9]{64}$",
        description="SHA-256 of PDF bytes for verification",
    )
    retrieved_at: datetime | None = Field(default=None, description="When PDF was fetched")

    # Optional metadata
    title: str | None = Field(default=None)
    authors: list[str] | None = Field(default=None)

    @property
    def canonical(self) -> str:
        """Canonical arXiv reference (e.g., 'arXiv:1706.03762v7')."""
        return f"arXiv:{self.arxiv_id}v{self.version}"

    @property
    def abs_url(self) -> str:
        """Versioned abstract URL."""
        return f"https://arxiv.org/abs/{self.arxiv_id}v{self.version}"

    @property
    def pdf_url(self) -> str:
        """Versioned PDF URL."""
        return f"https://arxiv.org/pdf/{self.arxiv_id}v{self.version}"


class DoiSource(BaseModel):
    """DOI-based paper source for non-arXiv publications."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str = Field(min_length=1, description="Local ID for evidence references")
    type: Literal["doi"] = "doi"
    doi: str = Field(
        pattern=r"^10\.\d{4,}/.*$",
        description="DOI (e.g., '10.1038/s41586-023-06221-2')",
    )

    # Optional metadata
    title: str | None = Field(default=None)
    authors: list[str] | None = Field(default=None)

    @property
    def url(self) -> str:
        """DOI resolver URL."""
        return f"https://doi.org/{self.doi}"


# Discriminated union for type-safe source parsing
InsightSource = Annotated[
    ArxivSource | DoiSource,
    Field(discriminator="type"),
]


# =============================================================================
# Evidence
# =============================================================================


class Evidence(BaseModel):
    """Evidence from scientific literature with W3C-compliant selectors.

    At least one content selector (quote, figure, or table) is required.
    The FragmentSelector provides optional PDF location hints.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str = Field(min_length=1, description="Evidence ID")
    source_ref: str = Field(min_length=1, description="References source.id")

    # Content selectors (at least one required)
    quote: TextQuoteSelector | None = Field(default=None, description="Text quote anchor")
    figure: FigureSelector | None = Field(default=None, description="Figure reference")
    table: TableSelector | None = Field(default=None, description="Table reference")

    # Location hint
    location: FragmentSelector | None = Field(default=None, description="PDF location hint")

    @model_validator(mode="after")
    def require_at_least_one_selector(self) -> Evidence:
        """Ensure at least one content selector is provided."""
        if not (self.quote or self.figure or self.table):
            raise ValueError(
                "Evidence must have at least one content selector: quote, figure, or table"
            )
        return self


# =============================================================================
# Insight
# =============================================================================


class Insight(BaseModel):
    """A scientific insight with provenance and supporting evidence.

    Represents a discrete unit of scientific knowledge extracted from
    literature, with full traceability to source material via W3C-compliant
    text selectors.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    # Required
    id: str = Field(min_length=1, description="Unique identifier")
    claim: str = Field(min_length=1, description="What we learned (1-2 sentences)")
    created_at: datetime = Field(description="Creation timestamp (ISO 8601)")
    sources: list[InsightSource] = Field(min_length=1, description="Source paper(s)")
    evidence: list[Evidence] = Field(min_length=1, description="Supporting evidence")

    # Optional classification
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="Confidence [0,1]")
    derived: bool = Field(default=False, description="True if synthesized/inferred")

    # Optional context
    scope: str | None = Field(default=None, description="Applicability conditions")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    notes: str | None = Field(default=None, description="Reasoning notes")

    @model_validator(mode="after")
    def validate_evidence_refs(self) -> Insight:
        """Validate evidence source references exist."""
        source_ids = {s.id for s in self.sources}

        for ev in self.evidence:
            if ev.source_ref not in source_ids:
                raise ValueError(
                    f"Evidence '{ev.id}' references unknown source '{ev.source_ref}'. "
                    f"Available: {source_ids}"
                )

        return self


# =============================================================================
# Collection
# =============================================================================


class InsightCollection(BaseModel):
    """Collection of insights, usable standalone or embedded in an analysis."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://asp-spec.org/v1/insights.schema.json",
            "title": "ASP Insights Collection",
        },
    )

    schema_: str | None = Field(default=None, alias="$schema")
    insights: dict[str, Insight] = Field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str | Path) -> InsightCollection:
        """Load from YAML file."""
        with open(path) as f:
            return cls.model_validate(yaml.safe_load(f))

    def to_yaml(self, path: str | Path) -> None:
        """Save to YAML file."""
        with open(path, "w") as f:
            yaml.safe_dump(
                self.model_dump(by_alias=True, exclude_none=True, mode="json"),
                f,
                sort_keys=False,
                allow_unicode=True,
            )

    def get_insight(self, insight_id: str) -> Insight | None:
        """Get insight by ID."""
        return self.insights.get(insight_id)
