# TimeBill

Automatic time-tracking application that detects what project you're working on from terminal activity, IDE usage, and browser interaction.

## Features
- **Passive Project Detection** - Infers active project from window titles, IDE status, browser tabs
- **Idle-Based Time Accounting** - Tracks active time, stops after configurable idle period
- **Local Storage** - Persists data in SQLite database locally

## Tech Stack
- Python 3.11+
- SQLite (bundled)
- pytest for testing

## Quick Start
```bash
./init.sh        # Set up and start
python -m timebill agent   # Run the agent
```

## Project Structure
```
timebill/
├── timebill.py          # Entry point (CLI)
├── agent/
│   ├── __init__.py
│   ├── detection.py     # Project detection
│   ├── accounting.py    # Time accounting
│   └── storage.py       # Agent storage
├── data/
│   ├── models.py        # Data models
│   └── storage.py       # SQLite wrapper + JSON fallback
└── tests/
    ├── test_detection.py
    ├── test_accounting.py
    └── test_storage.py
```

## Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `TIMEBILL_DB_PATH` | SQLite database path | `./data/timebill.db` |
| `TIMEBILL_LOG_LEVEL` | Log verbosity | `INFO` |
| `TIMEBILL_IDLE_SECONDS` | Idle timeout | `300` |
| `TIMEBILL_PROJECT_DETECTION` | Detection patterns | `""` |
