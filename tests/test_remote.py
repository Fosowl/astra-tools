"""Tests for HPC/remote target configuration."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from asp.cli import main
from asp.remote import (
    create_project_hpc_config,
    list_saved_targets,
    load_target_config,
    merge_permissions_into_settings,
    save_target_config,
)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def targets_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Override the targets directory to use a temp path."""
    targets = tmp_path / "targets"
    targets.mkdir()
    monkeypatch.setattr("asp.remote.get_targets_dir", lambda: targets)
    return targets


@pytest.fixture
def sample_config() -> dict:
    """A typical target config for testing."""
    return {
        "target": {
            "name": "perlmutter",
            "scheduler": "slurm",
        },
        "auth": {
            "account": "m9999",
        },
        "resource_limits": {
            "max_nodes": 4,
            "max_walltime_minutes": 120,
            "max_concurrent_jobs": 3,
            "max_node_hours_per_session": 16,
        },
        "permissions": {
            "auto_approve": ["python", "python3", "squeue", "sacct"],
            "deny": ["rm -rf /", "scancel --all"],
        },
    }


class TestTargetConfigRoundTrip:
    """Tests for saving and loading target configs."""

    def test_save_then_load(self, targets_dir: Path, sample_config: dict):
        save_target_config("perlmutter", sample_config)
        loaded = load_target_config("perlmutter")
        assert loaded is not None
        assert loaded["auth"]["account"] == "m9999"
        assert loaded["target"]["scheduler"] == "slurm"

    def test_load_nonexistent(self, targets_dir: Path):
        assert load_target_config("nonexistent") is None

    def test_list_empty(self, targets_dir: Path):
        assert list_saved_targets() == []

    def test_list_with_targets(self, targets_dir: Path, sample_config: dict):
        save_target_config("perlmutter", sample_config)
        save_target_config("other", {"target": {"name": "other"}})
        targets = list_saved_targets()
        assert targets == ["other", "perlmutter"]


class TestMergePermissions:
    """Tests for merging target permissions into settings."""

    def test_adds_auto_approve(self):
        settings: dict = {"permissions": {"allow": ["Edit"]}}
        config = {
            "permissions": {
                "auto_approve": ["python", "squeue"],
                "deny": [],
            }
        }
        merge_permissions_into_settings(settings, config)
        allow = settings["permissions"]["allow"]
        assert "Bash(python:*)" in allow
        assert "Bash(squeue:*)" in allow
        assert "Edit" in allow  # preserved

    def test_adds_deny_patterns(self):
        settings: dict = {"permissions": {"allow": []}}
        config = {
            "permissions": {
                "auto_approve": [],
                "deny": ["rm -rf /", "scancel --all"],
            }
        }
        merge_permissions_into_settings(settings, config)
        deny = settings["permissions"]["deny"]
        assert "Bash(rm -rf /)" in deny
        assert "Bash(scancel --all)" in deny

    def test_no_duplicates(self):
        settings: dict = {"permissions": {"allow": ["Bash(python:*)"]}}
        config = {"permissions": {"auto_approve": ["python"], "deny": []}}
        merge_permissions_into_settings(settings, config)
        assert settings["permissions"]["allow"].count("Bash(python:*)") == 1

    def test_creates_permissions_key(self):
        settings: dict = {}
        config = {"permissions": {"auto_approve": ["python"], "deny": []}}
        merge_permissions_into_settings(settings, config)
        assert "permissions" in settings
        assert "Bash(python:*)" in settings["permissions"]["allow"]


class TestCreateProjectHpcConfig:
    """Tests for creating project-level HPC configs."""

    def test_creates_subset(self, sample_config: dict):
        project = create_project_hpc_config(sample_config)
        assert "target" in project
        assert "auth" in project
        assert "compute" in project
        assert "resource_limits" in project
        assert "permissions" not in project

    def test_applies_overrides(self, sample_config: dict):
        overrides = {"resource_limits": {"max_nodes": 8}}
        project = create_project_hpc_config(sample_config, overrides=overrides)
        assert project["resource_limits"]["max_nodes"] == 8
        # Other limits preserved
        assert project["resource_limits"]["max_walltime_minutes"] == 120

    def test_includes_notes(self):
        config = {
            "target": {"name": "test"},
            "auth": {},
            "compute": {},
            "resource_limits": {},
            "notes": "Use debug QOS for development.",
        }
        project = create_project_hpc_config(config)
        assert project["notes"] == "Use debug QOS for development."

    def test_excludes_notes_when_empty(self, sample_config: dict):
        project = create_project_hpc_config(sample_config)
        assert "notes" not in project


class TestDefaultPermissions:
    """Tests for _default_permissions_for_scheduler."""

    def test_slurm_defaults(self):
        from asp.cli import _default_permissions_for_scheduler

        perms = _default_permissions_for_scheduler("slurm")
        assert "squeue" in perms["auto_approve"]
        assert "sacct" in perms["auto_approve"]
        assert "python" in perms["auto_approve"]
        assert "scancel --all" in perms["deny"]

    def test_pbs_defaults(self):
        from asp.cli import _default_permissions_for_scheduler

        perms = _default_permissions_for_scheduler("pbs")
        assert "qstat" in perms["auto_approve"]
        assert "qdel all" in perms["deny"]

    def test_sge_defaults(self):
        from asp.cli import _default_permissions_for_scheduler

        perms = _default_permissions_for_scheduler("sge")
        assert "qstat" in perms["auto_approve"]
        assert "qhost" in perms["auto_approve"]


class TestRemoteCLI:
    """Tests for the remote CLI commands."""

    def test_remote_setup_list_empty(self, runner: CliRunner, targets_dir: Path):
        result = runner.invoke(main, ["remote", "setup", "--list"])
        assert result.exit_code == 0
        assert "No saved targets" in result.output

    def test_remote_setup_list_with_targets(
        self, runner: CliRunner, targets_dir: Path, sample_config: dict
    ):
        save_target_config("perlmutter", sample_config)
        result = runner.invoke(main, ["remote", "setup", "--list"])
        assert result.exit_code == 0
        assert "perlmutter" in result.output

    def test_remote_setup_no_name(self, runner: CliRunner, targets_dir: Path):
        result = runner.invoke(main, ["remote", "setup"])
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_remote_setup_interactive(self, runner: CliRunner, targets_dir: Path):
        # Input: scheduler, account, 4x resource limits (accept defaults), no customize, no notes, confirm
        result = runner.invoke(
            main,
            ["remote", "setup", "test-cluster"],
            input="slurm\nm1234\n4\n120\n3\n16\nN\n\ny\n",
        )
        assert result.exit_code == 0
        assert "Saved" in result.output
        config = load_target_config("test-cluster")
        assert config is not None
        assert config["target"]["scheduler"] == "slurm"
        assert config["auth"]["account"] == "m1234"

    def test_remote_show_nonexistent(self, runner: CliRunner, targets_dir: Path):
        result = runner.invoke(main, ["remote", "show", "nonexistent"])
        assert result.exit_code == 1
        assert "No saved target" in result.output

    def test_remote_show_saved(
        self, runner: CliRunner, targets_dir: Path, sample_config: dict
    ):
        save_target_config("perlmutter", sample_config)
        result = runner.invoke(main, ["remote", "show", "perlmutter"])
        assert result.exit_code == 0
        assert "m9999" in result.output


class TestInitWithTarget:
    """Tests for asp init --target."""

    def test_init_unknown_target_errors(
        self, runner: CliRunner, tmp_path: Path, targets_dir: Path
    ):
        result = runner.invoke(
            main, ["init", str(tmp_path / "test-proj"), "--target", "fake-cluster"]
        )
        assert result.exit_code == 1
        assert "No saved target" in result.output

    def test_init_saved_target(
        self, runner: CliRunner, tmp_path: Path, targets_dir: Path, sample_config: dict
    ):
        save_target_config("perlmutter", sample_config)
        project_dir = tmp_path / "test-proj"
        result = runner.invoke(
            main,
            ["init", str(project_dir), "--target", "perlmutter", "--no-git", "--no-venv"],
        )
        assert result.exit_code == 0
        assert "Using saved target" in result.output
        assert (project_dir / ".claude" / "hpc.yaml").exists()

        # Verify settings.json has HPC hooks
        import json

        settings = json.loads((project_dir / ".claude" / "settings.json").read_text())
        assert "PreToolUse" in settings["hooks"]

        # Verify .gitignore has HPC entries
        gitignore = (project_dir / ".gitignore").read_text()
        assert "hpc.yaml" in gitignore

    def test_init_target_with_notes(
        self, runner: CliRunner, tmp_path: Path, targets_dir: Path
    ):
        config = {
            "target": {"name": "test", "scheduler": "slurm"},
            "auth": {"account": "m1234"},
            "resource_limits": {"max_nodes": 4},
            "permissions": {"auto_approve": ["python"], "deny": []},
            "notes": "Always use debug QOS for development runs.",
        }
        save_target_config("test-cluster", config)
        project_dir = tmp_path / "test-proj"
        result = runner.invoke(
            main,
            ["init", str(project_dir), "--target", "test-cluster", "--no-git", "--no-venv"],
        )
        assert result.exit_code == 0

        # Verify CLAUDE.md has notes section
        claude_md = (project_dir / "CLAUDE.md").read_text()
        assert "Compute Notes" in claude_md
        assert "debug QOS" in claude_md

        # Verify hpc.yaml has notes
        import yaml

        hpc = yaml.safe_load((project_dir / ".claude" / "hpc.yaml").read_text())
        assert hpc["notes"] == "Always use debug QOS for development runs."

    def test_init_without_target_unchanged(self, runner: CliRunner, tmp_path: Path):
        """Verify that init without --target works exactly as before."""
        project_dir = tmp_path / "test-proj"
        result = runner.invoke(
            main,
            ["init", str(project_dir), "--no-git", "--no-venv"],
        )
        assert result.exit_code == 0
        assert not (project_dir / ".claude" / "hpc.yaml").exists()
