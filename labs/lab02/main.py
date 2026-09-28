import argparse

from labs.lab02.task1 import (
    Admin,
    User,
    UserAccount,
)
from labs.lab02.task2 import (
    create_report,
    load_certificates,
    print_summary,
    save_report,
)


def run_demo():
    """Run Task 1 demonstration."""
    print("=" * 60)
    print("LAB 02 - TASK 1 DEMO")
    print("=" * 60)

    user = User(
        "demyan",
        "demyan@example.com",
        "SecurePassword123!",
    )

    account = UserAccount(user)

    print("\n1. USER")
    print(user)

    print("\n2. LOGIN")
    result = account.login(
        "demyan",
        "SecurePassword123!",
        "192.168.1.100",
    )
    print("Successful login:", result)
    print("Authenticated:", account.is_authenticated())

    print("\n3. WRONG PASSWORD")
    result = account.login(
        "demyan",
        "WrongPassword123!",
        "192.168.1.100",
    )
    print("Login result:", result)

    print("\n4. CHANGE EMAIL")
    account["email"] = "new@example.com"
    print("New email:", account["user"].email)

    print("\n5. ADMIN")
    admin = Admin(
        "admin",
        "admin@example.com",
        "AdminPassword123!",
        permissions={"read", "write"},
    )

    print(admin)
    print("Has read:", admin.has_permission("read"))
    print("Has delete:", admin.has_permission("delete"))

    admin.grant_permission("delete")
    print(
        "After grant delete:",
        admin.has_permission("delete"),
    )

    admin.revoke_permission("write")
    print(
        "After revoke write:",
        admin.has_permission("write"),
    )

    print("\n6. PASSWORD PROTECTION")

    try:
        account["password"]
    except KeyError as error:
        print("Password access denied:", error)

    print("\n7. LOGOUT")
    account.logout()
    print("Authenticated:", account.is_authenticated())

    print("\n8. AUDIT LOG")
    account["audit_log"].show_all()


def run_analyze(args):
    """Run Task 2 certificate analysis."""
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


def build_parser():
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Cybersecurity Python Labs - Lab 02"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # demo
    subparsers.add_parser(
        "demo",
        help="Run Task 1 OOP demonstration",
    )

    # analyze
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze SSL/TLS certificates",
    )

    analyze_parser.add_argument(
        "--certs-data",
        required=True,
        help="Path to certificates JSON file",
    )

    analyze_parser.add_argument(
        "--days-warning",
        type=int,
        default=30,
        help=(
            "Warn about certificates expiring "
            "within this number of days"
        ),
    )

    analyze_parser.add_argument(
        "--output-report",
        required=True,
        help="Path to output report",
    )

    analyze_parser.add_argument(
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

    try:
        if args.command == "demo":
            run_demo()

        elif args.command == "analyze":
            run_analyze(args)

    except (
        FileNotFoundError,
        ValueError,
        KeyError,
    ) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()