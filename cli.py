#!/usr/bin/env python3
"""CLI for ECG Axis Calculator."""
import argparse
import json
import sys

from ecg_axis import quick_axis, calculate_axis, calculate_axis_from_leads, process_csv


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

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
