"""Pydantic models for ASP specifications.

These models are used for schema generation and are NOT installed as part
of the asp package. They are only used by tools/generate_schemas.py.
"""

from models.analysis import Analysis, Artefact, Chunk, Decision, Evidence, Input, Option, Output
from models.insight import (
    ArxivSource,
    DoiSource,
    FigureSelector,
    FragmentSelector,
    Insight,
    InsightCollection,
    InsightSource,
    TableSelector,
    TextQuoteSelector,
)
from models.insight import (
    Evidence as InsightEvidence,
)
from models.universe import Universe

__all__ = [
    # Analysis
    "Analysis",
    "Artefact",
    "Chunk",
    "Decision",
    "Evidence",
    "Input",
    "Option",
    "Output",
    # Universe
    "Universe",
    # Insight - Sources
    "ArxivSource",
    "DoiSource",
    "InsightSource",
    # Insight - W3C Selectors
    "TextQuoteSelector",
    "FragmentSelector",
    "FigureSelector",
    "TableSelector",
    # Insight - Core
    "Insight",
    "InsightCollection",
    "InsightEvidence",
]
