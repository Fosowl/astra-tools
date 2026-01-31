"""Evidence verification for ASP insights.

Provides functionality to verify that evidence (quotes, figures, tables)
actually exists in the referenced source documents.

Requires optional dependencies: pip install asp[verify]
"""

from asp.verification.cache import VerificationCache, VerificationCacheEntry
from asp.verification.core import (
    EvidenceVerification,
    InsightVerification,
    VerificationStatus,
    verify_all_insights,
    verify_evidence,
    verify_insight,
)
from asp.verification.pdf import (
    PDFDocument,
    extract_text_from_pdf,
)

__all__ = [
    # Verification
    "EvidenceVerification",
    "InsightVerification",
    "VerificationStatus",
    "verify_evidence",
    "verify_insight",
    "verify_all_insights",
    # Cache
    "VerificationCache",
    "VerificationCacheEntry",
    # PDF utilities
    "PDFDocument",
    "extract_text_from_pdf",
]
