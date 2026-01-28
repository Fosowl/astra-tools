"""Core verification logic for ASP insights.

Verifies that evidence (quotes, figures, tables) exists in source documents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from asp.verification.pdf import PDFDocument, extract_text_from_pdf, get_arxiv_pdf


class VerificationStatus(str, Enum):
    """Status of a verification check."""

    VERIFIED = "verified"  # Evidence found in source
    NOT_FOUND = "not_found"  # Evidence not found in source
    WRONG_PAGE = "wrong_page"  # Found but on different page
    SKIPPED = "skipped"  # Could not verify (e.g., DOI source, figure/table)
    ERROR = "error"  # Error during verification


@dataclass
class EvidenceVerification:
    """Result of verifying a single piece of evidence.

    Attributes:
        evidence_id: ID of the evidence being verified.
        status: Overall verification status.
        quote_status: Status of quote verification (if quote present).
        quote_found_pages: Pages where quote was found (1-indexed).
        expected_page: Expected page from location hint.
        message: Human-readable description of result.
    """

    evidence_id: str
    status: VerificationStatus
    quote_status: VerificationStatus | None = None
    quote_found_pages: list[int] = field(default_factory=list)
    expected_page: int | None = None
    message: str = ""

    @property
    def is_valid(self) -> bool:
        """Check if evidence is verified or skipped (not an error)."""
        return self.status in (VerificationStatus.VERIFIED, VerificationStatus.SKIPPED)


@dataclass
class InsightVerification:
    """Result of verifying all evidence for an insight.

    Attributes:
        insight_id: ID of the insight being verified.
        source_id: ID of the source document.
        pdf_sha256: SHA-256 of the PDF used for verification.
        evidence_results: Verification results for each piece of evidence.
        overall_status: Overall verification status.
    """

    insight_id: str
    source_id: str
    pdf_sha256: str = ""
    evidence_results: list[EvidenceVerification] = field(default_factory=list)
    overall_status: VerificationStatus = VerificationStatus.VERIFIED

    @property
    def is_valid(self) -> bool:
        """Check if all evidence is valid."""
        return all(ev.is_valid for ev in self.evidence_results)

    @property
    def verified_count(self) -> int:
        """Count of verified evidence items."""
        return sum(
            1 for ev in self.evidence_results if ev.status == VerificationStatus.VERIFIED
        )

    @property
    def failed_count(self) -> int:
        """Count of failed evidence items."""
        return sum(1 for ev in self.evidence_results if not ev.is_valid)


def _get_attr(obj: Any, key: str, default: Any = None) -> Any:
    """Get attribute from dict or object."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def verify_evidence(
    evidence: Any,
    pdf: PDFDocument,
) -> EvidenceVerification:
    """Verify a single piece of evidence against a PDF.

    Args:
        evidence: The evidence to verify (dict or Evidence object).
        pdf: PDFDocument with extracted text.

    Returns:
        EvidenceVerification with results.
    """
    evidence_id = _get_attr(evidence, "id", "unknown")
    location = _get_attr(evidence, "location")
    expected_page = _get_attr(location, "page") if location else None

    result = EvidenceVerification(
        evidence_id=evidence_id,
        status=VerificationStatus.VERIFIED,
        expected_page=expected_page,
    )

    # Check quote if present
    quote = _get_attr(evidence, "quote")
    if quote:
        quote_text = _get_attr(quote, "exact", "")
        hint_page = expected_page

        found_pages = pdf.find_quote(quote_text, page=hint_page)

        if not found_pages:
            result.quote_status = VerificationStatus.NOT_FOUND
            result.status = VerificationStatus.NOT_FOUND
            result.message = f"Quote not found in PDF: '{quote_text[:50]}...'"
        elif hint_page and hint_page not in found_pages:
            result.quote_status = VerificationStatus.WRONG_PAGE
            result.quote_found_pages = found_pages
            result.status = VerificationStatus.WRONG_PAGE
            result.message = (
                f"Quote found on page(s) {found_pages}, expected page {hint_page}"
            )
        else:
            result.quote_status = VerificationStatus.VERIFIED
            result.quote_found_pages = found_pages
            result.message = f"Quote verified on page(s) {found_pages}"

    # Figure/table verification - skip for now
    elif _get_attr(evidence, "figure"):
        figure = _get_attr(evidence, "figure")
        label = _get_attr(figure, "label", "unknown")
        result.status = VerificationStatus.SKIPPED
        result.message = f"Figure verification not yet implemented: {label}"

    elif _get_attr(evidence, "table"):
        table = _get_attr(evidence, "table")
        label = _get_attr(table, "label", "unknown")
        result.status = VerificationStatus.SKIPPED
        result.message = f"Table verification not yet implemented: {label}"

    return result


def verify_insight(
    insight: Any,
    cache_dir: Path | None = None,
) -> InsightVerification:
    """Verify all evidence for an insight.

    Downloads the source PDF (if arXiv) and verifies each piece of evidence.

    Args:
        insight: The insight to verify (dict or Insight object).
        cache_dir: Directory to cache PDFs.

    Returns:
        InsightVerification with results for all evidence.
    """
    insight_id = _get_attr(insight, "id", "unknown")
    sources = _get_attr(insight, "sources", [])
    evidence_list = _get_attr(insight, "evidence", [])

    # Get the first arXiv source (we verify against primary source)
    arxiv_sources = [s for s in sources if _get_attr(s, "type") == "arxiv"]

    if not arxiv_sources:
        first_source_id = _get_attr(sources[0], "id", "unknown") if sources else "unknown"
        return InsightVerification(
            insight_id=insight_id,
            source_id=first_source_id,
            overall_status=VerificationStatus.SKIPPED,
            evidence_results=[
                EvidenceVerification(
                    evidence_id=_get_attr(ev, "id", "unknown"),
                    status=VerificationStatus.SKIPPED,
                    message="Only arXiv sources are currently supported for verification",
                )
                for ev in evidence_list
            ],
        )

    source = arxiv_sources[0]
    source_id = _get_attr(source, "id", "unknown")

    try:
        # Download and extract PDF
        pdf_path = get_arxiv_pdf(source, cache_dir=cache_dir)
        pdf = extract_text_from_pdf(pdf_path)
    except Exception as e:
        return InsightVerification(
            insight_id=insight_id,
            source_id=source_id,
            overall_status=VerificationStatus.ERROR,
            evidence_results=[
                EvidenceVerification(
                    evidence_id=_get_attr(ev, "id", "unknown"),
                    status=VerificationStatus.ERROR,
                    message=f"Failed to download/extract PDF: {e}",
                )
                for ev in evidence_list
            ],
        )

    # Verify each piece of evidence
    evidence_results = []
    for ev in evidence_list:
        # Only verify evidence that references this source
        ev_source_ref = _get_attr(ev, "source_ref", "")
        if ev_source_ref == source_id:
            result = verify_evidence(ev, pdf)
        else:
            result = EvidenceVerification(
                evidence_id=_get_attr(ev, "id", "unknown"),
                status=VerificationStatus.SKIPPED,
                message=f"Evidence references different source: {ev_source_ref}",
            )
        evidence_results.append(result)

    # Determine overall status
    if any(r.status == VerificationStatus.ERROR for r in evidence_results):
        overall = VerificationStatus.ERROR
    elif any(r.status == VerificationStatus.NOT_FOUND for r in evidence_results):
        overall = VerificationStatus.NOT_FOUND
    elif any(r.status == VerificationStatus.WRONG_PAGE for r in evidence_results):
        overall = VerificationStatus.WRONG_PAGE
    elif all(r.status == VerificationStatus.SKIPPED for r in evidence_results):
        overall = VerificationStatus.SKIPPED
    else:
        overall = VerificationStatus.VERIFIED

    return InsightVerification(
        insight_id=insight_id,
        source_id=source_id,
        pdf_sha256=pdf.sha256,
        evidence_results=evidence_results,
        overall_status=overall,
    )
