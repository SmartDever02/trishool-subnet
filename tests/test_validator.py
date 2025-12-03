"""
Tests for validator functionality using pytest.

Tests for validator's ability to process submissions without Platform API.
"""
import pytest
import asyncio
import time
from neurons.validator import Validator
from alignet.models.submission import SubmissionStatus
from tests.conftest import (
    sample_seed_instruction,
    sample_models,
    sample_auditor,
    sample_judge,
)


@pytest.fixture
def validator():
    """Fixture providing Validator instance."""
    return Validator()


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_validator_initialization(validator):
    """Test validator initialization."""
    assert validator is not None
    assert hasattr(validator, "sandbox_manager")
    assert hasattr(validator, "api_client")
    assert hasattr(validator, "active_submissions")


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_fake_submission_creation(
    validator,
    sample_seed_instruction,
    sample_models,
    sample_auditor,
    sample_judge,
):
    """Test creating a fake submission."""
    submission = await validator.fake_submission(
        miner_id="test_miner_001",
        seed=sample_seed_instruction,
        models=sample_models,
        auditor=sample_auditor,
        judge=sample_judge,
        max_turns=5,
    )

    assert submission is not None
    assert submission.submission_id is not None
    assert submission.run_id is not None
    assert submission.seed_instruction == sample_seed_instruction
    assert submission.models == sample_models
    assert submission.auditor == sample_auditor
    assert submission.judge == sample_judge
    assert submission.max_turns == 5
    assert submission.submission_id in validator.active_submissions


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_fake_submission_with_defaults(validator):
    """Test creating fake submission with default values."""
    submission = await validator.fake_submission()

    assert submission is not None
    assert submission.submission_id is not None
    assert submission.run_id is not None
    assert len(submission.seed_instruction) > 0
    assert len(submission.models) > 0


@pytest.mark.unit
def test_validator_status(validator):
    """Test getting validator status."""
    status = validator.get_validator_status()

    assert isinstance(status, dict)
    assert "active_submissions" in status
    assert "processed_submissions" in status
    assert "pending_scores" in status
    assert "active_sandboxes" in status
    assert "max_concurrent_sandboxes" in status
    assert isinstance(status["active_submissions"], int)
    assert isinstance(status["processed_submissions"], int)


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_submission_status_tracking(
    validator,
    sample_seed_instruction,
    sample_models,
    sample_auditor,
    sample_judge,
):
    """Test that submission status is tracked correctly."""
    submission = await validator.fake_submission(
        miner_id="test_miner_tracking",
        seed=sample_seed_instruction,
        models=sample_models,
        auditor=sample_auditor,
        judge=sample_judge,
        max_turns=5,
    )

    # Check initial status
    assert submission.submission_id in validator.active_submissions
    active_submission = validator.active_submissions[submission.submission_id]
    assert active_submission.status in [
        SubmissionStatus.SUBMITTED,
        SubmissionStatus.VALIDATING,
        SubmissionStatus.EVALUATING,
    ]

    # Wait a bit for processing
    await asyncio.sleep(2)

    # Check if still active or moved to processed
    assert (
        submission.submission_id in validator.active_submissions
        or submission.submission_id in validator.processed_submissions
    )

