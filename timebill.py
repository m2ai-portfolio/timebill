#!/usr/bin/env python3
"""TimeBill - Automatic time-tracking application.

Entry point for the TimeBill CLI.
"""

import sys
import time
import os
from agent.accounting import TimeAccountant
from data.storage import Storage
from data.models import Project


def run_agent_demo():
    """Run agent in demo/simulation mode to demonstrate idle-based time accounting."""
    print("=" * 60)
    print("TimeBill Agent - Idle-Based Time Accounting Demo")
    print("=" * 60)

    # Get configuration from environment
    idle_seconds = int(os.environ.get('TIMEBILL_IDLE_SECONDS', '300'))
    db_path = os.environ.get('TIMEBILL_DB_PATH', './data/timebill.db')

    print(f"\nConfiguration:")
    print(f"  Idle threshold: {idle_seconds} seconds")
    print(f"  Database path: {db_path}")
    print()

    # Initialize storage and accountant
    storage = Storage(db_path=db_path)
    accountant = TimeAccountant(idle_threshold_seconds=idle_seconds)

    print("Initializing storage...")
    print(f"  Using {'JSON fallback' if storage.use_json_fallback else 'SQLite'} storage")
    print()

    # Simulate a work session
    print("Simulating work session...")
    print("-" * 60)

    # Scenario 1: User starts working on project A
    print("\n[T+0s] User opens 'Visual Studio Code - ProjectAlpha/main.py'")
    accountant.on_activity("ProjectAlpha")
    time.sleep(0.1)  # Small delay for demonstration

    # Simulate work for 2 seconds
    print("[T+2s] User continues working on ProjectAlpha...")
    time.sleep(2)
    accountant.on_activity("ProjectAlpha")

    # Check current entry
    current = accountant.get_current_entry()
    print(f"  Current entry: {current.project_name if current else 'None'}")

    # Scenario 2: User switches to project B
    print("\n[T+4s] User switches to 'vim - ~/projects/timebill/agent/accounting.py'")
    time.sleep(2)
    accountant.on_activity("timebill")

    # Check entries
    completed = accountant.get_all_entries()
    print(f"  Completed entries: {len(completed)}")
    if completed:
        last_entry = completed[-1]
        print(f"    Last entry: {last_entry.project_name}, duration: {last_entry.duration_ms}ms")

    # Scenario 3: Continue working
    print("\n[T+6s] User continues working on timebill...")
    time.sleep(2)
    accountant.on_activity("timebill")

    # Scenario 4: Simulate short idle (less than threshold)
    # For demo purposes, we'll use a very short idle threshold
    print("\n[T+8s] User takes a short break (1 second)...")
    time.sleep(1)

    # Check if idle was detected (should not be for 1 second)
    was_idle = accountant.check_idle()
    print(f"  Idle detected: {was_idle} (threshold is {idle_seconds}s)")

    # Scenario 5: User returns to work
    print("\n[T+9s] User returns and continues on timebill...")
    accountant.on_activity("timebill")

    # Scenario 6: Final stop
    print("\n[T+10s] Stopping agent and finalizing entries...")
    accountant.stop()

    # Display results
    print("\n" + "=" * 60)
    print("Final Results")
    print("=" * 60)

    all_entries = accountant.get_all_entries()
    print(f"\nTotal completed entries: {len(all_entries)}")
    print()

    total_duration_ms = 0
    for i, entry in enumerate(all_entries, 1):
        duration_sec = entry.duration_ms / 1000
        total_duration_ms += entry.duration_ms
        print(f"Entry #{i}:")
        print(f"  Project: {entry.project_name}")
        print(f"  Duration: {entry.duration_ms}ms ({duration_sec:.2f}s)")
        print(f"  Start: {entry.start_ts}")
        print(f"  End: {entry.end_ts}")
        print()

        # Save to storage
        # First ensure project exists
        project = Project(name=entry.project_name)
        storage.save_project(project)
        # Then save time entry
        storage.save_time_entry(entry)

    total_duration_sec = total_duration_ms / 1000
    print(f"Total tracked time: {total_duration_ms}ms ({total_duration_sec:.2f}s)")

    # Verify storage
    print("\n" + "-" * 60)
    print("Verifying storage...")
    stored_projects = storage.get_projects()
    stored_entries = storage.get_time_entries()

    print(f"  Stored projects: {len(stored_projects)}")
    for proj in stored_projects:
        print(f"    - {proj.name}")

    print(f"  Stored time entries: {len(stored_entries)}")

    # Close storage
    storage.close()

    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


def main():
    """Main entry point for TimeBill."""
    if len(sys.argv) > 1 and sys.argv[1] == 'agent':
        run_agent_demo()
    else:
        print("TimeBill - Automatic Time Tracking")
        print()
        print("Usage:")
        print("  python timebill.py agent    # Run agent demo")
        print()
        print("Project detection module loaded successfully.")
        print("Run 'python -m pytest tests/' to run tests.")


if __name__ == '__main__':
    main()
