#!/usr/bin/env python3
"""CLI for ECG Axis Calculator."""
import argparse
import json
import sys

from ecg_axis import quick_axis, calculate_axis, calculate_axis_from_leads, process_csv


def _cmd_audit(args):
    """Run supervisor audit on a task payload."""
    from agents.supervisor import SystemSupervisor
    from agents.models import SystemTaskPayload
    from agents.base import PHIGuard

    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id=args.task_id,
        target_identifier=args.target_id or "CLI-TARGET",
        primary_metric=args.primary_metric,
        secondary_metric=args.secondary_metric,
        status_descriptor=args.status_descriptor,
        is_critical_flag=args.is_critical,
    )
    # Zero-PHI validation
    PHIGuard.assert_no_phi(payload.task_id)
    PHIGuard.assert_no_phi(payload.target_identifier)
    PHIGuard.assert_no_phi(payload.status_descriptor)

    dossier = supervisor.process_task(payload)
    print(json.dumps(dossier.to_dict(), indent=2, default=str))
    return 0


def _cmd_chat(args):
    """Query the supervisory chat system."""
    from agents.supervisor import SystemSupervisor

    supervisor = SystemSupervisor(model_provider="mock")
    query = " ".join(args.query_text)
    response = supervisor.query_supervisory_chat(query)
    print(json.dumps({"response": response}, indent=2))
    return 0


def _cmd_verify_audit(args):
    """Verify the cryptographic audit trail integrity."""
    from agents.base import AuditLogger

    verified = AuditLogger.verify_integrity()
    trail_len = len(AuditLogger.get_trail())
    print(json.dumps({"audit_verified": verified, "trail_length": trail_len}, indent=2))
    return 0


def _cmd_serve(args):
    """Start the FastAPI server."""
    try:
        import uvicorn
        from agents.api import app
    except ImportError as e:
        print(f"Error: Missing dependency for serve command: {e}", file=sys.stderr)
        return 1

    uvicorn.run(app, host=args.host, port=args.port)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="ecg-axis-calculator",
        description="ECG Axis Calculator — QRS axis from limb lead amplitudes",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Quick axis (I + aVF)
    quick = subparsers.add_parser("quick", help="Quick axis from leads I and aVF")
    quick.add_argument("--lead-i", type=float, required=True, help="Net QRS amplitude in lead I (R - S, mV)")
    quick.add_argument("--lead-avf", type=float, required=True, help="Net QRS amplitude in lead aVF (R - S, mV)")

    # Precise axis from two leads
    precise = subparsers.add_parser("precise", help="Precise axis from any two leads")
    precise.add_argument("--lead1-name", required=True, help="First lead name (I, II, III, aVR, aVL, aVF)")
    precise.add_argument("--lead1-net", type=float, required=True, help="Net QRS amplitude of first lead")
    precise.add_argument("--lead2-name", required=True, help="Second lead name")
    precise.add_argument("--lead2-net", type=float, required=True, help="Net QRS amplitude of second lead")

    # Multi-lead axis
    multi = subparsers.add_parser("multi", help="Axis from multiple leads (JSON)")
    multi.add_argument("--leads", required=True, help='JSON dict of lead:amplitude, e.g. \'{"I":0.5,"aVF":0.3}\'')

    # Batch processing
    batch = subparsers.add_parser("batch", help="Batch process CSV file")
    batch.add_argument("-i", "--input", required=True, help="Input CSV path")
    batch.add_argument("-o", "--output", default="results.csv", help="Output CSV path")

    # Audit command
    audit = subparsers.add_parser("audit", help="Run supervisor audit on a task payload")
    audit.add_argument("--task-id", required=True, help="Unique task identifier")
    audit.add_argument("--target-id", default="CLI-TARGET", help="Target identifier")
    audit.add_argument("--primary-metric", type=float, default=10.0, help="Primary measurement value")
    audit.add_argument("--secondary-metric", type=float, default=0.0, help="Secondary measurement value")
    audit.add_argument("--status-descriptor", default="NOMINAL", help="Status descriptor")
    audit.add_argument("--is-critical", action="store_true", help="Flag as critical priority")

    # Chat command
    chat = subparsers.add_parser("chat", help="Query the supervisory chat system")
    chat.add_argument("query_text", nargs="+", help="Query text to send")

    # Verify audit command
    verify_audit = subparsers.add_parser("verify-audit", help="Verify audit trail integrity")

    # Serve command
    serve = subparsers.add_parser("serve", help="Start FastAPI server")
    serve.add_argument("--host", default="0.0.0.0", help="Host to bind")
    serve.add_argument("--port", type=int, default=8000, help="Port to bind")

    args = parser.parse_args(argv)

    if args.command == "quick":
        result = quick_axis(args.lead_i, args.lead_avf)
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "precise":
        result = calculate_axis(args.lead1_name, args.lead1_net, args.lead2_name, args.lead2_net)
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "multi":
        leads = json.loads(args.leads)
        result = calculate_axis_from_leads(leads)
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "batch":
        results = process_csv(args.input, args.output)
        print(f"Processed {len(results)} records -> {args.output}")
        return 0

    if args.command == "audit":
        return _cmd_audit(args)

    if args.command == "chat":
        return _cmd_chat(args)

    if args.command == "verify-audit":
        return _cmd_verify_audit(args)

    if args.command == "serve":
        return _cmd_serve(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
