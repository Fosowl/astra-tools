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
from typing import Literal

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
    prefix: str | None = Field(default=None, description="~20-100 chars before for disambiguation")
    suffix: str | None = Field(default=None, description="~20-100 chars after for disambiguation")


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
# Evidence
# =============================================================================


class Evidence(BaseModel):
    """Evidence from scientific literature with W3C-compliant selectors.

    References papers directly by DOI. At least one content selector
    (quote, figure, or table) is required. The FragmentSelector provides
    optional PDF location hints.

    For arXiv papers, the DOI format is: 10.48550/arXiv.{id}
    The version field is used for arXiv papers where version matters.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str = Field(min_length=1, description="Evidence ID")
    doi: str = Field(
        pattern=r"^10\.\d{4,}/.*$",
        description="DOI of the source paper (e.g., '10.48550/arXiv.1706.03762')",
    )
    version: int | None = Field(
        default=None,
        ge=1,
        description="Paper version for arXiv papers (version matters for reproducibility)",
    )

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

    @property
    def is_arxiv(self) -> bool:
        """Check if this evidence references an arXiv paper."""
        return self.doi.startswith("10.48550/arXiv.")

    @property
    def arxiv_id(self) -> str | None:
        """Extract arXiv ID from DOI if this is an arXiv paper."""
        if self.is_arxiv:
            return self.doi.replace("10.48550/arXiv.", "")
        return None


# =============================================================================
# Insight
# =============================================================================


class Insight(BaseModel):
    """A scientific insight with provenance and supporting evidence.

    Represents a discrete unit of scientific knowledge extracted from
    literature, with full traceability to source material via W3C-compliant
    text selectors. Evidence directly references papers by DOI.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    # Required
    id: str = Field(min_length=1, description="Unique identifier")
    claim: str = Field(min_length=1, description="What we learned (1-2 sentences)")
    created_at: datetime = Field(description="Creation timestamp (ISO 8601)")
    evidence: list[Evidence] = Field(min_length=1, description="Supporting evidence")

    # Optional classification
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="Confidence [0,1]")
    derived: bool = Field(default=False, description="True if synthesized/inferred")

    # Optional context
    scope: str | None = Field(default=None, description="Applicability conditions")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    notes: str | None = Field(default=None, description="Reasoning notes")


# =============================================================================
# Collection
# =============================================================================


class InsightCollection(BaseModel):
    """Collection of insights, usable standalone or embedded in an analysis."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "$schema": "http://json-schema.org/draft-07/schema#",
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
