# TimeBill - Automatic Time Tracker

Automatic time-tracking application for freelancers, consultants, and contractors who bill by the hour.

## Overview
TimeBill detects what project you're working on from terminal activity, IDE usage, and browser interaction. It runs locally on your machine, requires no internet connectivity, and stores data in a local SQLite database.

## Tech Stack
- Python 3.11+
- SQLite (bundled)
- Standard library only (no third-party packages)
- Cross-platform (Windows, macOS, Linux)

## Features
1. **Passive Project Detection** - Infers active project from window titles, IDE, and browser tabs
2. **Idle-Based Time Accounting** - Tracks time automatically, stops on inactivity
3. **Local Encrypted Storage** - Persists data in encrypted SQLite database

## Quick Start
```bash
chmod +x init.sh
./init.sh
```

## Usage
```bash
python -m timebill agent
```

## Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `TIMEBILL_DB_PATH` | SQLite database path | `./data/timebill.db` |
| `TIMEBILL_LOG_LEVEL` | Logging verbosity | `INFO` |
| `TIMEBILL_IDLE_SECONDS` | Idle timeout in seconds | `300` |
| `TIMEBILL_PROJECT_DETECTION` | Project detection patterns | `""` |

## File Structure
```
timebill/
├── timebill.py          # entry point (CLI)
├── agent/
│   ├── __init__.py
│   ├── detection.py     # window title detection
│   ├── accounting.py    # time tracking
│   └── storage.py       # high-level storage ops
├── data/
│   ├── models.py        # data models
│   └── storage.py       # SQLite wrapper
├── tests/
│   └── ...
└── README.md
```
