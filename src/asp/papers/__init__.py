"""Paper management for ASP.

Provides DOI-based paper acquisition and caching for evidence verification.
"""

from asp.papers.cache import PaperCache, PaperMetadata
from asp.papers.download import download_paper, resolve_doi

__all__ = [
    "PaperCache",
    "PaperMetadata",
    "download_paper",
    "resolve_doi",
]
