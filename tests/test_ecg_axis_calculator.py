"""
Automated Pytest Test Suite for Ecg Axis Calculator.
Domain: Cardiology & Intensive Care Systems
Standard: AHA/ACC Guidelines / Surviving Sepsis Campaign
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import PHIGuard, AuditLogger, SecurityException
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0


def test_cli_audit_command():
    """Test the audit CLI command with various parameters."""
    # Basic audit
    assert main(["audit", "--task-id", "TEST-AUDIT-01"]) == 0

    # Audit with critical flag
    assert main(["audit", "--task-id", "TEST-AUDIT-02", "--is-critical"]) == 0

    # Audit with custom metrics
    assert main([
        "audit",
        "--task-id", "TEST-AUDIT-03",
        "--primary-metric", "25.5",
        "--secondary-metric", "10.0",
        "--status-descriptor", "NOMINAL"
    ]) == 0


def test_cli_chat_command():
    """Test the chat CLI command."""
    assert main(["chat", "What", "is", "normal", "axis?"]) == 0
    assert main(["chat", "Explain", "left", "axis", "deviation"]) == 0


def test_cli_verify_audit_command():
    """Test the verify-audit CLI command."""
    assert main(["verify-audit"]) == 0


def test_cli_quick_command():
    """Test the quick axis CLI command."""
    assert main(["quick", "--lead-i", "0.5", "--lead-avf", "0.3"]) == 0


def test_cli_precise_command():
    """Test the precise axis CLI command."""
    assert main([
        "precise",
        "--lead1-name", "I",
        "--lead1-net", "0.5",
        "--lead2-name", "aVF",
        "--lead2-net", "0.3"
    ]) == 0


def test_cli_multi_command():
    """Test the multi-lead CLI command."""
    assert main(["multi", "--leads", '{"I": 0.5, "aVF": 0.3}']) == 0


def test_cli_batch_command(tmp_path):
    """Test the batch CSV processing CLI command."""
    import csv

    # Create a temporary input CSV
    input_csv = tmp_path / "test_input.csv"
    output_csv = tmp_path / "test_output.csv"

    with open(input_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["lead_i_net", "lead_avf_net"])
        writer.writerow(["0.5", "0.3"])
        writer.writerow(["-0.2", "0.8"])

    assert main(["batch", "-i", str(input_csv), "-o", str(output_csv)]) == 0
    assert output_csv.exists()


def test_cli_batch_command_file_not_found():
    """Test batch command with non-existent input file."""
    with pytest.raises(FileNotFoundError):
        main(["batch", "-i", "/nonexistent/path/input.csv"])


def test_cli_batch_command_path_traversal():
    """Test batch command rejects path traversal attempts."""
    with pytest.raises(ValueError):
        main(["batch", "-i", "../../../etc/passwd"])


def test_audit_trail_integrity():
    """Test that audit trail maintains integrity after multiple operations."""
    from agents.base import AuditTrail

    trail = AuditTrail(secret_key="test-key-for-integrity")

    # Log multiple entries
    trail.log("test", "tester", "TEST_EVENT", {"data": "value1"})
    trail.log("test", "tester", "TEST_EVENT", {"data": "value2"})
    trail.log("test", "tester", "TEST_EVENT", {"data": "value3"})

    # Verify integrity
    assert trail.verify_integrity() is True
    assert len(trail.get_trail()) == 3


def test_phi_guard_redaction():
    """Test PHI redaction functionality."""
    text_with_phi = "Patient MRN-12345678 has appointment tomorrow"
    redacted = PHIGuard.redact_phi(text_with_phi)
    assert "MRN-12345678" not in redacted
    assert "[REDACTED_IDENTIFIER]" in redacted
