"""Evidence verification for ASP insights.

Provides functionality to verify that evidence (quotes, figures, tables)
actually exists in the referenced source documents.

Requires optional dependencies: pip install asp[verify]
"""

from asp.verification.core import (
    EvidenceVerification,
    InsightVerification,
    VerificationStatus,
    verify_evidence,
    verify_insight,
)
from asp.verification.pdf import (
    PDFDocument,
    extract_text_from_pdf,
    get_arxiv_pdf,
)

__all__ = [
    # Verification
    "EvidenceVerification",
    "InsightVerification",
    "VerificationStatus",
    "verify_evidence",
    "verify_insight",
    # PDF utilities
    "PDFDocument",
    "extract_text_from_pdf",
    "get_arxiv_pdf",
]
