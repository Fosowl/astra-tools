"""Tests for validation modules."""

from pathlib import Path

from asp.helpers import load_yaml
from asp.validation.schema import (
    is_valid_analysis,
    is_valid_universe,
    validate_analysis_schema,
    validate_universe_schema,
)
from asp.validation.semantic import (
    SemanticError,
    validate_analysis,
    validate_analysis_file,
    validate_universe,
    validate_universe_file,
)


class TestSchemaValidation:
    """Tests for JSON schema validation."""

    def test_valid_minimal_analysis(self, minimal_analysis_path: Path):
        errors = validate_analysis_schema(minimal_analysis_path)
        assert errors == []
        assert is_valid_analysis(minimal_analysis_path)

    def test_valid_full_analysis(self, full_analysis_path: Path):
        errors = validate_analysis_schema(full_analysis_path)
        assert errors == []

    def test_valid_universe(self, baseline_universe_path: Path):
        errors = validate_universe_schema(baseline_universe_path)
        assert errors == []
        assert is_valid_universe(baseline_universe_path)

    def test_missing_version(self, invalid_dir: Path):
        errors = validate_analysis_file(invalid_dir / "missing_version.yaml")
        assert any(e.code == "MISSING_ROOT_FIELD" and "version" in e.message for e in errors)

    def test_invalid_input_type(self, invalid_dir: Path):
        errors = validate_analysis_schema(invalid_dir / "invalid_input_type.yaml")
        assert len(errors) > 0

    def test_invalid_output_type(self, invalid_dir: Path):
        errors = validate_analysis_schema(invalid_dir / "invalid_output_type.yaml")
        assert len(errors) > 0

    def test_invalid_decision_type(self, invalid_dir: Path):
        errors = validate_analysis_schema(invalid_dir / "invalid_decision_type.yaml")
        assert len(errors) > 0


class TestSemanticValidation:
    """Tests for semantic validation."""

    def test_valid_analysis(self, full_analysis_path: Path):
        data = load_yaml(full_analysis_path)
        errors = validate_analysis(data)
        assert errors == []

    def test_valid_analysis_file(self, full_analysis_path: Path):
        errors = validate_analysis_file(full_analysis_path)
        assert errors == []

    def test_duplicate_input_ids(self, invalid_dir: Path):
        errors = validate_analysis_file(invalid_dir / "duplicate_input_ids.yaml")
        assert any(e.code == "DUPLICATE_INPUT" for e in errors)

    def test_duplicate_output_ids(self, invalid_dir: Path):
        errors = validate_analysis_file(invalid_dir / "duplicate_output_ids.yaml")
        assert any(e.code == "DUPLICATE_OUTPUT" for e in errors)

    def test_invalid_insight_ref(self, invalid_dir: Path):
        errors = validate_analysis_file(invalid_dir / "invalid_insight_ref.yaml")
        assert any(e.code == "INVALID_INSIGHT_REF" for e in errors)

    def test_invalid_constraint_ref(self, invalid_dir: Path):
        errors = validate_analysis_file(invalid_dir / "invalid_constraint_ref.yaml")
        assert any(e.code == "INVALID_CONSTRAINT_REF" for e in errors)


class TestUniverseValidation:
    """Tests for universe validation."""

    def test_valid_universe(self, full_analysis_path: Path, baseline_universe_path: Path):
        errors = validate_universe_file(baseline_universe_path, full_analysis_path)
        assert errors == []

    def test_valid_svm_universe(self, full_analysis_path: Path, svm_universe_path: Path):
        # SVM requires standard preprocessing, which is set
        errors = validate_universe_file(svm_universe_path, full_analysis_path)
        assert errors == []

    def test_missing_decision(self, full_analysis_path: Path, invalid_dir: Path):
        errors = validate_universe_file(
            invalid_dir / "universe_missing_decision.yaml",
            full_analysis_path,
        )
        assert any(e.code == "MISSING_DECISION" for e in errors)

    def test_invalid_option(self, full_analysis_path: Path, invalid_dir: Path):
        errors = validate_universe_file(
            invalid_dir / "universe_invalid_option.yaml",
            full_analysis_path,
        )
        assert any(e.code == "UNKNOWN_OPTION" for e in errors)

    def test_incompatible_options(self, full_analysis_path: Path, invalid_dir: Path):
        errors = validate_universe_file(
            invalid_dir / "universe_incompatible.yaml",
            full_analysis_path,
        )
        assert any(e.code == "INCOMPATIBLE_OPTIONS" for e in errors)

    def test_missing_required_option(self, full_analysis_path: Path, invalid_dir: Path):
        errors = validate_universe_file(
            invalid_dir / "universe_missing_required.yaml",
            full_analysis_path,
        )
        assert any(e.code == "MISSING_REQUIRED_OPTION" for e in errors)


class TestNestedAnalysisValidation:
    """Tests for nested analysis semantic validation."""

    def test_valid_nested_analysis(self, valid_dir: Path):
        errors = validate_analysis_file(valid_dir / "nested.yaml")
        assert errors == []

    def test_valid_nested_universe(self, valid_dir: Path):
        analysis_data = load_yaml(valid_dir / "nested.yaml")
        universe_data = load_yaml(valid_dir / "nested_universe.yaml")
        errors = validate_universe(universe_data, analysis_data)
        assert errors == []

    def test_missing_analysis_decision_in_universe(self, valid_dir: Path, invalid_dir: Path):
        analysis_data = load_yaml(valid_dir / "nested.yaml")
        universe_data = load_yaml(invalid_dir / "universe_missing_analysis_decision.yaml")
        errors = validate_universe(universe_data, analysis_data)
        assert any(e.code == "MISSING_DECISION" for e in errors)


class TestSubAnalysisRequirements:
    """Tests for sub-analysis required fields and parent_decisions."""

    def test_sub_missing_outputs(self, invalid_dir: Path):
        errors = validate_analysis_file(invalid_dir / "sub_missing_outputs.yaml")
        assert any(e.code == "MISSING_SUB_FIELD" and "outputs" in e.message for e in errors)

    def test_invalid_parent_decision(self, invalid_dir: Path):
        errors = validate_analysis_file(invalid_dir / "invalid_parent_decision.yaml")
        assert any(e.code == "INVALID_PARENT_DECISION" for e in errors)

    def test_cross_level_constraint_in_analysis(self, valid_dir: Path):
        """parent_decisions allows constraints referencing parent decisions."""
        errors = validate_analysis_file(valid_dir / "nested.yaml")
        assert errors == []

    def test_cross_level_incompatible_universe(self, valid_dir: Path, invalid_dir: Path):
        """Universe violates cross-level incompatible_with constraint."""
        analysis_data = load_yaml(valid_dir / "nested.yaml")
        universe_data = load_yaml(invalid_dir / "universe_cross_level_incompatible.yaml")
        errors = validate_universe(universe_data, analysis_data)
        assert any(e.code == "INCOMPATIBLE_OPTIONS" for e in errors)


class TestRecipeValidation:
    """Tests for recipe semantic validation."""

    def test_valid_recipes(self, valid_dir: Path):
        errors = validate_analysis_file(valid_dir / "full.yaml")
        assert errors == []

    def test_orphan_recipe_output(self, invalid_dir: Path):
        errors = validate_analysis_file(invalid_dir / "recipe_orphan_output.yaml")
        assert any(e.code == "ORPHAN_RECIPE_OUTPUT" for e in errors)

    def test_duplicate_recipe_output(self, invalid_dir: Path):
        errors = validate_analysis_file(invalid_dir / "recipe_duplicate_output.yaml")
        assert any(e.code == "DUPLICATE_RECIPE_OUTPUT" for e in errors)

    def test_invalid_recipe_dependency(self, invalid_dir: Path):
        errors = validate_analysis_file(invalid_dir / "recipe_invalid_dep.yaml")
        assert any(e.code == "INVALID_RECIPE_DEP" for e in errors)

    def test_recipe_cycle(self, invalid_dir: Path):
        errors = validate_analysis_file(invalid_dir / "recipe_cycle.yaml")
        assert any(e.code == "RECIPE_CYCLE" for e in errors)

    def test_nested_recipes(self, valid_dir: Path):
        errors = validate_analysis_file(valid_dir / "nested.yaml")
        assert errors == []


class TestDecisionGroupValidation:
    """Tests for decision group validation."""

    def test_valid_decision_groups(self, valid_dir: Path):
        errors = validate_analysis_file(valid_dir / "full_v2.yaml")
        assert errors == []

    def test_ungrouped_decision(self, invalid_dir: Path):
        errors = validate_analysis_file(invalid_dir / "decision_group_missing_decision.yaml")
        assert any(e.code == "UNGROUPED_DECISION" for e in errors)

    def test_duplicate_group_decision(self, invalid_dir: Path):
        errors = validate_analysis_file(invalid_dir / "decision_group_duplicate.yaml")
        assert any(e.code == "DUPLICATE_GROUP_DECISION" for e in errors)

    def test_nonexistent_group_decision(self, invalid_dir: Path):
        errors = validate_analysis_file(invalid_dir / "decision_group_nonexistent.yaml")
        assert any(e.code == "INVALID_GROUP_DECISION" for e in errors)


class TestConditionalDecisionValidation:
    """Tests for conditional decision (when) validation."""

    def test_valid_when(self, valid_dir: Path):
        errors = validate_analysis_file(valid_dir / "full_v2.yaml")
        assert errors == []

    def test_invalid_when_ref(self, invalid_dir: Path):
        errors = validate_analysis_file(invalid_dir / "invalid_when_ref.yaml")
        assert any(e.code == "INVALID_WHEN_REF" for e in errors)


class TestExcludedOptionValidation:
    """Tests for excluded option validation."""

    def test_excluded_no_reason(self, invalid_dir: Path):
        errors = validate_analysis_file(invalid_dir / "excluded_no_reason.yaml")
        assert any(e.code == "MISSING_EXCLUDED_REASON" for e in errors)

    def test_excluded_default(self, invalid_dir: Path):
        errors = validate_analysis_file(invalid_dir / "excluded_default.yaml")
        assert any(e.code == "EXCLUDED_DEFAULT" for e in errors)

    def test_orphan_excluded_reason(self, invalid_dir: Path):
        errors = validate_analysis_file(invalid_dir / "orphan_excluded_reason.yaml")
        assert any(e.code == "ORPHAN_EXCLUDED_REASON" for e in errors)


class TestUniverseNewFeaturesValidation:
    """Tests for universe validation with conditional decisions and excluded options."""

    def test_excluded_option_in_universe(self, invalid_dir: Path, valid_dir: Path):
        analysis_data = load_yaml(valid_dir / "full_v2.yaml")
        universe_data = load_yaml(invalid_dir / "universe_excluded_option.yaml")
        errors = validate_universe(universe_data, analysis_data)
        assert any(e.code == "EXCLUDED_OPTION_SELECTED" for e in errors)

    def test_inactive_decision_in_universe(self, invalid_dir: Path, valid_dir: Path):
        analysis_data = load_yaml(valid_dir / "full_v2.yaml")
        universe_data = load_yaml(invalid_dir / "universe_inactive_decision.yaml")
        errors = validate_universe(universe_data, analysis_data)
        assert any(e.code == "INACTIVE_DECISION" for e in errors)


class TestSemanticError:
    """Tests for SemanticError class."""

    def test_error_str_with_path(self):
        error = SemanticError("TEST_CODE", "Test message", "some.path")
        assert "[TEST_CODE]" in str(error)
        assert "some.path" in str(error)
        assert "Test message" in str(error)

    def test_error_str_without_path(self):
        error = SemanticError("TEST_CODE", "Test message")
        assert "[TEST_CODE]" in str(error)
        assert "Test message" in str(error)
