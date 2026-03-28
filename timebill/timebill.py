"""TimeBill CLI entry point."""

import sys


def main():
    """Main entry point for the TimeBill application."""
    if len(sys.argv) > 1 and sys.argv[1] == "agent":
        print("TimeBill agent starting...")
        print("Passive project detection enabled.")
        print("Press Ctrl+C to stop.")
        # TODO: Start agent loop in future iteration
    else:
        print("Usage: python -m timebill agent")
        sys.exit(1)


if __name__ == "__main__":
    main()
