"""TimeBill CLI entry point."""

import sys
import os


def main():
    """Main entry point for the TimeBill application."""
    if len(sys.argv) > 1 and sys.argv[1] == "agent":
        idle_seconds = int(os.environ.get('TIMEBILL_IDLE_SECONDS', '300'))
        print("TimeBill agent starting...")
        print("Passive project detection enabled.")
        print(f"Idle-based time tracking enabled (idle threshold: {idle_seconds}s).")
        print("Press Ctrl+C to stop.")
        # TODO: Start agent loop in future iteration
    else:
        print("Usage: python -m timebill agent")
        sys.exit(1)


if __name__ == "__main__":
    main()
