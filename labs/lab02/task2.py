import argparse
import csv
import json
import logging
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


logger = logging.getLogger(__name__)


def load_certificates(path):
    """Load certificates from a JSON file."""
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Certificates file not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        certificates = json.load(file)

    if not isinstance(certificates, list):
        raise ValueError(
            "Certificates data must be a list"
        )

    return certificates


def parse_date(date_string):
    """Convert YYYY-MM-DD string to a datetime object."""
    return datetime.strptime(
        date_string,
        "%Y-%m-%d",
    ).replace(tzinfo=timezone.utc)


def calculate_days_left(valid_to):
    """Calculate the number of days until certificate expiration."""
    expiration_date = parse_date(valid_to)
    current_date = datetime.now(timezone.utc)

    difference = expiration_date - current_date

    return difference.days


def is_weak_signature(signature_algorithm):
    """Check whether a certificate uses a weak signature algorithm."""
    pattern = r"(?i)\b(?:sha1|md5)\b"

    return re.search(
        pattern,
        signature_algorithm,
    ) is not None


def analyze_certificates(
    certificates,
    days_warning,
):
    """Analyze certificate expiration and security."""
    analyzed = []

    for certificate in certificates:
        domain = certificate["domain"]
        issuer = certificate["issuer"]
        valid_to = certificate["validTo"]
        signature_algorithm = certificate[
            "signatureAlgorithm"
        ]

        days_left = calculate_days_left(valid_to)

        weak_signature = is_weak_signature(
            signature_algorithm
        )

        expired = days_left < 0
        expiring_soon = (
            0 <= days_left <= days_warning
        )

        if expired:
            logger.warning(
                "Certificate expired: %s",
                domain,
            )
        elif expiring_soon:
            logger.warning(
                "Certificate expires soon: %s "
                "(%d days left)",
                domain,
                days_left,
            )

        if weak_signature:
            logger.warning(
                "Weak signature algorithm: %s (%s)",
                domain,
                signature_algorithm,
            )

        analyzed.append(
            {
                "domain": domain,
                "issuer": issuer,
                "validFrom": certificate["validFrom"],
                "validTo": valid_to,
                "keyLength": certificate["keyLength"],
                "signatureAlgorithm": (
                    signature_algorithm
                ),
                "daysLeft": days_left,
                "expired": expired,
                "expiringSoon": expiring_soon,
                "weakSignature": weak_signature,
            }
        )

    return analyzed


def count_issuers(certificates):
    """Count certificates grouped by issuer."""
    issuers = Counter(
        certificate["issuer"]
        for certificate in certificates
    )

    return issuers


def create_report(
    certificates,
    days_warning,
):
    """Create the complete analysis report."""
    analyzed = analyze_certificates(
        certificates,
        days_warning,
    )

    issuer_counts = count_issuers(
        certificates
    )

    expired_count = sum(
        certificate["expired"]
        for certificate in analyzed
    )

    expiring_soon_count = sum(
        certificate["expiringSoon"]
        for certificate in analyzed
    )

    weak_signature_count = sum(
        certificate["weakSignature"]
        for certificate in analyzed
    )

    return {
        "summary": {
            "totalCertificates": len(analyzed),
            "expiredCertificates": expired_count,
            "expiringSoon": expiring_soon_count,
            "weakSignatureCertificates": (
                weak_signature_count
            ),
            "daysWarning": days_warning,
        },
        "issuerStatistics": dict(
            issuer_counts
        ),
        "certificates": analyzed,
    }


def save_json_report(report, output_path):
    """Save report as JSON."""
    output_path = Path(output_path)

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False,
        )


def save_csv_report(report, output_path):
    """Save certificate report as CSV."""
    output_path = Path(output_path)

    certificates = report["certificates"]

    if not certificates:
        return

    fieldnames = [
        "domain",
        "issuer",
        "validFrom",
        "validTo",
        "keyLength",
        "signatureAlgorithm",
        "daysLeft",
        "expired",
        "expiringSoon",
        "weakSignature",
    ]

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(certificates)


def save_report(
    report,
    output_path,
    output_format,
):
    """Save report in JSON or CSV format."""
    if output_format == "json":
        save_json_report(
            report,
            output_path,
        )

    elif output_format == "csv":
        save_csv_report(
            report,
            output_path,
        )

    else:
        raise ValueError(
            f"Unsupported format: {output_format}"
        )


def print_summary(report):
    """Print a short analysis summary."""
    summary = report["summary"]

    print("\n" + "=" * 60)
    print("SSL/TLS CERTIFICATE ANALYSIS")
    print("=" * 60)

    print(
        f"Total certificates: "
        f"{summary['totalCertificates']}"
    )

    print(
        f"Expired certificates: "
        f"{summary['expiredCertificates']}"
    )

    print(
        f"Expiring soon: "
        f"{summary['expiringSoon']}"
    )

    print(
        f"Weak signature certificates: "
        f"{summary['weakSignatureCertificates']}"
    )

    print("\nIssuer statistics:")

    for issuer, count in report[
        "issuerStatistics"
    ].items():
        print(f"  {issuer}: {count}")

    print("\nCertificates:")

    for certificate in report["certificates"]:
        status = []

        if certificate["expired"]:
            status.append("EXPIRED")
        elif certificate["expiringSoon"]:
            status.append("EXPIRING SOON")

        if certificate["weakSignature"]:
            status.append("WEAK SIGNATURE")

        status_text = (
            ", ".join(status)
            if status
            else "OK"
        )

        print(
            f"  {certificate['domain']} | "
            f"{certificate['daysLeft']} days | "
            f"{status_text}"
        )


def build_parser():
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "SSL/TLS certificate expiration "
            "monitor"
        )
    )

    parser.add_argument(
        "command",
        choices=["analyze"],
        help="Command to execute",
    )

    parser.add_argument(
        "--certs-data",
        required=True,
        help="Path to certificates JSON file",
    )

    parser.add_argument(
        "--days-warning",
        type=int,
        default=30,
        help=(
            "Warn about certificates expiring "
            "within this number of days"
        ),
    )

    parser.add_argument(
        "--output-report",
        required=True,
        help="Path to output report",
    )

    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        required=True,
        help="Output report format",
    )

    return parser


def main():
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.WARNING,
        format=(
            "%(levelname)s: %(message)s"
        ),
    )

    try:
        if args.days_warning < 0:
            raise ValueError(
                "--days-warning cannot be negative"
            )

        certificates = load_certificates(
            args.certs_data
        )

        report = create_report(
            certificates,
            args.days_warning,
        )

        save_report(
            report,
            args.output_report,
            args.format,
        )

        print_summary(report)

        print(
            f"\nReport saved to: "
            f"{args.output_report}"
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        KeyError,
        ValueError,
    ) as error:
        logger.error("%s", error)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())