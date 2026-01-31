"""Integration tests for evidence verification using a real arXiv paper.

Uses arXiv:1603.01599 "High Resolution Weak Lensing Mass-Mapping Combining
Shear and Flexion" by Lanusse et al.

These tests require network access and optional dependencies:
    pip install httpx pypdf

Run with: pytest tests/test_evidence_verification.py -v
"""

import shutil
import tempfile
from pathlib import Path

import pytest

# Check for optional dependencies
httpx = pytest.importorskip("httpx", reason="httpx required: pip install httpx")
pypdf = pytest.importorskip("pypdf", reason="pypdf required: pip install pypdf")

# Mark all tests as requiring network and verify deps
pytestmark = [
    pytest.mark.network,
    pytest.mark.slow,
]


# Test paper details
ARXIV_ID = "1603.01599"
DOI = f"10.48550/arXiv.{ARXIV_ID}"
VERSION = 1  # Use a specific version for reproducibility

# Real quote from the paper abstract
VALID_QUOTE = (
    "Including flexion allows us to supplement the shear on small scales "
    "in order to increase the sensitivity to substructures and the overall "
    "resolution of the convergence map."
)

# A fabricated quote that doesn't exist in the paper
FAKE_QUOTE = (
    "This paper proves that deep learning is always better than "
    "traditional methods for all scientific applications."
)


@pytest.fixture(scope="module")
def temp_cache_dir():
    """Create a temporary cache directory for tests."""
    cache_dir = Path(tempfile.mkdtemp(prefix="asp_test_cache_"))
    yield cache_dir
    # Cleanup after all tests in module
    shutil.rmtree(cache_dir, ignore_errors=True)


@pytest.fixture(scope="module")
def paper_cache(temp_cache_dir):
    """Create a paper cache using temp directory."""
    from asp.papers.cache import PaperCache

    return PaperCache(cache_dir=temp_cache_dir / "papers")


@pytest.fixture(scope="module")
def verification_cache(temp_cache_dir):
    """Create a verification cache using temp directory."""
    from asp.verification.cache import VerificationCache

    return VerificationCache(cache_dir=temp_cache_dir / "verification")


@pytest.fixture(scope="module")
def downloaded_paper(paper_cache):
    """Download the test paper once for all tests."""
    from asp.papers.download import download_paper

    # Check if already in cache
    if paper_cache.has(DOI, VERSION):
        return paper_cache.get(DOI, VERSION)

    # Download the paper
    result = download_paper(DOI, VERSION)
    assert result.success, f"Failed to download paper: {result.error}"
    assert result.content is not None

    # Add to cache
    paper = paper_cache.add(
        doi=DOI,
        pdf_content=result.content,
        version=VERSION,
        source_url=result.url,
    )
    return paper


class TestPaperDownload:
    """Tests for paper downloading and caching."""

    def test_download_arxiv_paper(self, downloaded_paper):
        """Test that we can download an arXiv paper."""
        assert downloaded_paper is not None
        assert downloaded_paper.pdf_path.exists()
        assert downloaded_paper.metadata.doi == DOI
        assert downloaded_paper.metadata.version == VERSION
        assert len(downloaded_paper.metadata.sha256) == 64  # SHA-256 hex

    def test_paper_is_cached(self, paper_cache, downloaded_paper):
        """Test that downloaded paper is in cache."""
        assert paper_cache.has(DOI, VERSION)
        cached = paper_cache.get(DOI, VERSION)
        assert cached is not None
        assert cached.pdf_path == downloaded_paper.pdf_path

    def test_cache_returns_same_path(self, paper_cache):
        """Test that cache returns consistent paths."""
        path1 = paper_cache.get_path(DOI, VERSION)
        path2 = paper_cache.get_path(DOI, VERSION)
        assert path1 == path2


class TestPDFExtraction:
    """Tests for PDF text extraction."""

    def test_extract_text_from_pdf(self, downloaded_paper):
        """Test that we can extract text from the PDF."""
        from asp.verification.pdf import extract_text_from_pdf

        pdf = extract_text_from_pdf(downloaded_paper.pdf_path)
        assert pdf.num_pages > 0
        assert len(pdf.pages) == pdf.num_pages
        assert pdf.sha256 == downloaded_paper.metadata.sha256

    def test_find_valid_quote(self, downloaded_paper):
        """Test that we can find a real quote in the paper."""
        from asp.verification.pdf import extract_text_from_pdf

        pdf = extract_text_from_pdf(downloaded_paper.pdf_path)
        found_pages = pdf.find_quote(VALID_QUOTE)
        assert len(found_pages) > 0, f"Quote not found in paper: {VALID_QUOTE[:50]}..."

    def test_fake_quote_not_found(self, downloaded_paper):
        """Test that a fake quote is not found."""
        from asp.verification.pdf import extract_text_from_pdf

        pdf = extract_text_from_pdf(downloaded_paper.pdf_path)
        found_pages = pdf.find_quote(FAKE_QUOTE)
        assert len(found_pages) == 0, "Fake quote should not be found"


class TestEvidenceVerification:
    """Tests for evidence verification."""

    def test_verify_valid_evidence(self, paper_cache, verification_cache):
        """Test verification of valid evidence succeeds."""
        from asp.verification.core import VerificationStatus, verify_insight

        insight = {
            "id": "test_insight",
            "claim": "Flexion improves weak lensing mass mapping",
            "evidence": [
                {
                    "id": "ev1",
                    "doi": DOI,
                    "version": VERSION,
                    "quote": {
                        "type": "TextQuoteSelector",
                        "exact": VALID_QUOTE,
                    },
                }
            ],
        }

        result = verify_insight(insight, paper_cache, verification_cache)
        assert result.is_valid
        assert result.overall_status in (
            VerificationStatus.VERIFIED,
            VerificationStatus.CACHED,
        )
        assert len(result.evidence_results) == 1
        assert result.evidence_results[0].status in (
            VerificationStatus.VERIFIED,
            VerificationStatus.CACHED,
        )

    def test_verify_fake_evidence_fails(self, paper_cache, verification_cache):
        """Test verification of fake evidence fails."""
        from asp.verification.core import VerificationStatus, verify_insight

        insight = {
            "id": "fake_insight",
            "claim": "A fabricated claim",
            "evidence": [
                {
                    "id": "ev_fake",
                    "doi": DOI,
                    "version": VERSION,
                    "quote": {
                        "type": "TextQuoteSelector",
                        "exact": FAKE_QUOTE,
                    },
                }
            ],
        }

        result = verify_insight(insight, paper_cache, verification_cache)
        assert not result.is_valid
        assert result.overall_status == VerificationStatus.NOT_FOUND
        assert result.evidence_results[0].status == VerificationStatus.NOT_FOUND

    def test_verification_caching(self, paper_cache, verification_cache):
        """Test that verification results are cached."""
        from asp.verification.core import verify_insight

        insight = {
            "id": "cached_insight",
            "claim": "Testing cache",
            "evidence": [
                {
                    "id": "ev_cached",
                    "doi": DOI,
                    "version": VERSION,
                    "quote": {
                        "type": "TextQuoteSelector",
                        "exact": VALID_QUOTE,
                    },
                }
            ],
        }

        # First verification - should verify
        result1 = verify_insight(insight, paper_cache, verification_cache)
        assert result1.is_valid

        # Second verification - should come from cache
        result2 = verify_insight(insight, paper_cache, verification_cache)
        assert result2.is_valid
        assert result2.evidence_results[0].from_cache

    def test_missing_paper_error(self, verification_cache, temp_cache_dir):
        """Test error when paper is not in cache."""
        from asp.papers.cache import PaperCache
        from asp.verification.core import VerificationStatus, verify_insight

        # Use empty cache
        empty_cache = PaperCache(cache_dir=temp_cache_dir / "empty_papers")

        insight = {
            "id": "missing_paper_insight",
            "claim": "Test",
            "evidence": [
                {
                    "id": "ev_missing",
                    "doi": "10.48550/arXiv.9999.99999",  # Non-existent
                    "quote": {"type": "TextQuoteSelector", "exact": "test"},
                }
            ],
        }

        result = verify_insight(insight, empty_cache, verification_cache)
        assert not result.is_valid
        assert result.overall_status == VerificationStatus.ERROR
        assert "not in cache" in result.evidence_results[0].message


class TestFullValidationWorkflow:
    """Integration tests for the full validation workflow."""

    def test_validate_analysis_with_insights(self, paper_cache, temp_cache_dir):
        """Test validating an analysis file with insights and evidence."""
        from asp.helpers import load_yaml, save_yaml
        from asp.validation.schema import validate_analysis_schema
        from asp.validation.semantic import validate_analysis
        from asp.verification.cache import VerificationCache
        from asp.verification.core import verify_all_insights

        # Create a test analysis file
        analysis = {
            "version": "1.0",
            "analysis": {
                "name": "Test Analysis",
                "problem": "Test the evidence verification system",
                "inputs": [{"id": "data", "type": "data"}],
                "outputs": [{"id": "result", "type": "metric", "dtype": "float"}],
            },
            "insights": {
                "flexion_insight": {
                    "id": "flexion_insight",
                    "claim": "Flexion improves weak lensing resolution",
                    "created_at": "2024-01-01T00:00:00Z",
                    "evidence": [
                        {
                            "id": "ev1",
                            "doi": DOI,
                            "version": VERSION,
                            "quote": {
                                "type": "TextQuoteSelector",
                                "exact": VALID_QUOTE,
                            },
                        }
                    ],
                }
            },
            "chunks": {
                "main": {
                    "decisions": {
                        "method": {
                            "label": "Method",
                            "type": "method",
                            "default": "flexion",
                            "options": {
                                "flexion": {
                                    "label": "Use flexion",
                                    "insights": ["flexion_insight"],
                                },
                                "shear_only": {
                                    "label": "Shear only",
                                },
                            },
                        }
                    }
                }
            },
        }

        # Save to temp file
        analysis_path = temp_cache_dir / "test_analysis.yaml"
        save_yaml(analysis, analysis_path)

        # Stage 1: Schema validation
        schema_errors = validate_analysis_schema(analysis_path)
        assert schema_errors == [], f"Schema errors: {schema_errors}"

        # Stage 2: Semantic validation
        data = load_yaml(analysis_path)
        semantic_errors = validate_analysis(data)
        assert semantic_errors == [], f"Semantic errors: {semantic_errors}"

        # Stage 3: Evidence verification
        verification_cache = VerificationCache(cache_dir=temp_cache_dir / "verification")
        results = verify_all_insights(data["insights"], paper_cache, verification_cache)

        assert "flexion_insight" in results
        assert results["flexion_insight"].is_valid
