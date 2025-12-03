"""
Tests for sandbox execution using pytest.

Tests for Petri sandbox evaluation functionality.
"""
import pytest
import json
import os
import time
import threading
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

from alignet.models.submission import MinerSubmission, SubmissionStatus
from alignet.validator.sandbox.sandbox_management import SandboxManager
from alignet.validator.petri_commit_checker import PetriCommitChecker
from tests.conftest import (
    sample_seed_instruction,
    sample_models,
    sample_auditor,
    sample_judge,
    env_vars,
)


def load_config_from_file(config_path: str) -> Dict[str, Any]:
    """
    Load PetriConfig from JSON file.

    Args:
        config_path: Path to config.json file

    Returns:
        Dictionary containing PetriConfig fields

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return config


def build_test_submission(
    *,
    miner_id: str,
    run_id: str,
    seed_instruction: str,
    models: list,
    auditor: str,
    judge: str,
    max_turns: int,
    output_dir: str = "./outputs",
    temp_dir: str = "./temp",
    cleanup: bool = False,
    json_output: Optional[str] = None,
    verbose: bool = True,
    parallel: bool = True,
) -> MinerSubmission:
    """
    Create a MinerSubmission populated with PetriConfig fields for testing.

    Args:
        miner_id: Miner identifier
        run_id: Run ID for Petri evaluation
        seed_instruction: Seed instruction text
        models: List of target models
        auditor: Auditor model
        judge: Judge model
        max_turns: Maximum conversation turns
        output_dir: Output directory (default: "./outputs")
        temp_dir: Temp directory (default: "./temp")
        cleanup: Cleanup flag (default: False)
        json_output: JSON output filename (default: None, will use output.json)
        verbose: Verbose logging (default: True)
        parallel: Run in parallel (default: True)
    """
    if json_output is None:
        json_output = "output.json"

    return MinerSubmission(
        submission_id=f"{miner_id}_{int(time.time())}",
        miner_id=miner_id,
        version="1.0.0",
        run_id=run_id,
        seed_instruction=seed_instruction,
        models=models,
        auditor=auditor,
        judge=judge,
        max_turns=max_turns,
        output_dir=output_dir,
        temp_dir=temp_dir,
        cleanup=cleanup,
        json_output=json_output,
        verbose=verbose,
        parallel=parallel,
        metadata={
            "test_submission": True,
            "source": "tests/test_sandbox.py",
        },
    )


@pytest.fixture
def sandbox_manager():
    """Fixture providing SandboxManager instance."""
    return SandboxManager()


@pytest.fixture
def test_submission(
    sample_seed_instruction,
    sample_models,
    sample_auditor,
    sample_judge,
):
    """Fixture providing a test MinerSubmission."""
    run_id = f"test_run_{int(time.time())}"
    return build_test_submission(
        miner_id="test_miner_001",
        run_id=run_id,
        seed_instruction=sample_seed_instruction,
        models=sample_models,
        auditor=sample_auditor,
        judge=sample_judge,
        max_turns=5,
    )


@pytest.mark.unit
def test_build_submission(
    sample_seed_instruction,
    sample_models,
    sample_auditor,
    sample_judge,
):
    """Test building a submission with test data."""
    submission = build_test_submission(
        miner_id="test_miner",
        run_id="test_run_123",
        seed_instruction=sample_seed_instruction,
        models=sample_models,
        auditor=sample_auditor,
        judge=sample_judge,
        max_turns=5,
    )

    assert submission.submission_id is not None
    assert submission.run_id == "test_run_123"
    assert submission.seed_instruction == sample_seed_instruction
    assert submission.models == sample_models
    assert submission.auditor == sample_auditor
    assert submission.judge == sample_judge
    assert submission.max_turns == 5
    assert submission.status == SubmissionStatus.SUBMITTED


@pytest.mark.unit
def test_submission_to_petri_config(test_submission):
    """Test converting submission to PetriConfig dictionary."""
    petri_config = test_submission.to_petri_config_dict()

    assert isinstance(petri_config, dict)
    assert "run_id" in petri_config
    assert "seed_instruction" in petri_config
    assert "models" in petri_config
    assert petri_config["run_id"] == test_submission.run_id
    assert petri_config["seed_instruction"] == test_submission.seed_instruction


@pytest.mark.unit
def test_submission_status_transition(test_submission):
    """Test submission status transitions."""
    assert test_submission.status == SubmissionStatus.SUBMITTED

    test_submission.update_status(SubmissionStatus.EVALUATING)
    assert test_submission.status == SubmissionStatus.EVALUATING

    test_submission.update_status(SubmissionStatus.EVALUATION_COMPLETED)
    assert test_submission.status == SubmissionStatus.EVALUATION_COMPLETED


@pytest.mark.unit
def test_load_config_from_file():
    """Test loading config from JSON file."""
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        config = load_config_from_file(str(config_path))
        assert isinstance(config, dict)
        # Check for expected config keys if they exist
        if "run_id" in config:
            assert isinstance(config["run_id"], str)
    else:
        pytest.skip(f"Config file not found: {config_path}")


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_sandbox_creation(sandbox_manager, test_submission, env_vars):
    """Test creating a sandbox for evaluation."""
    petri_config = test_submission.to_petri_config_dict()

    sandbox_result = {"completed": False, "output_json": None, "error": None}

    def on_finish(result):
        sandbox_result["completed"] = True
        sandbox_result["output_json"] = result.get("output_json")
        sandbox_result["error"] = result.get("error")

    sandbox_id = sandbox_manager.create_sandbox(
        petri_config=petri_config,
        env_vars=env_vars,
        on_finish=on_finish,
        timeout=600,
    )

    assert sandbox_id is not None
    assert sandbox_id in sandbox_manager.sandboxes

    # Cleanup
    try:
        sandbox_manager.cleanup_sandbox(sandbox_id)
    except Exception:
        pass  # Ignore cleanup errors in test


@pytest.mark.integration
@pytest.mark.slow
def test_sandbox_manager_initialization():
    """Test SandboxManager initialization."""
    manager = SandboxManager()
    assert manager is not None
    assert hasattr(manager, "sandboxes")
    assert isinstance(manager.sandboxes, dict)


@pytest.mark.unit
def test_submission_metadata(test_submission):
    """Test submission metadata."""
    assert test_submission.metadata is not None
    assert test_submission.metadata.get("test_submission") is True
    assert test_submission.metadata.get("source") == "tests/test_sandbox.py"

