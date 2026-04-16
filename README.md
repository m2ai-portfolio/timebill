

<p align="center">
  <img src="assets/infographic.png" alt="TimeBill" width="800">
</p>

<h3 align="center">Automatic time tracking app that detects what project you're working on from your terminal, IDE, and browser activity.</h3>

<p align="center">
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#features">Features</a> &bull;
  <a href="#examples">Examples</a> &bull;
  <a href="#contributing">Contributing</a>
</p>

## What is this?
TimeBill is a locally‑run, offline time‑tracker that watches your active window, IDE status, and browser tabs to infer the project you’re billing for and records the duration automatically. It’s aimed at freelancers, consultants, and contractors who need accurate billable hours without manual logs.

Example:
```bash
$ python -m timebill agent
[INFO] Started TimeBill agent
[INFO] Detected project: Vim Editing
[INFO] Tracking started at 1628450123000
```

## Problem
Freelancers and consultants manually log billable hours using spreadsheets or forms, which is tedious, error‑prone, and often forgotten until invoicing time. This leads to lost revenue and administrative overhead that takes away from actual client work.

## Features
| Feature | Description |
|---|---|
| Passive Project Detection | Infers the active project from window titles, IDE status bars, or browser tab names without user input. |
| Idle‑Based Time Accounting | Starts tracking on user activity and stops after a configurable period of inactivity (default 5 min). |
| Local Encrypted Storage | Saves project‑to‑second mappings in a SQLite file encrypted with AES‑256 using a machine‑specific key. |
| Cross‑Platform Offline Operation | Pure Python 3.11+ code runs on Windows, macOS, and Linux with no network calls. |
| Minimal System‑Tray UI | Provides a tiny icon that opens a settings dialog and shows current session time on hover. |
| Configurable Detection Rules | Allows custom keywords or regex patterns via `TIMEBILL_PROJECT_DETECTION` to refine project inference. |

## Quick Start
1. Clone the repository:  
   ```bash
   git clone https://github.com/yourname/TimeBill.git
   cd TimeBill
   ```
2. Ensure Python 3.11+ is installed (no external dependencies required).  
3. Run the agent:  
   ```bash
   $ python -m timebill agent
   [INFO] Started TimeBill agent
   [INFO] Detected project: Default
   ```
4. Optionally set environment variables (e.g., `TIMEBILL_IDLE_SECONDS=120`) before step 3.

## Examples
**Basic tracking with IDE**  
```bash
$ python -m timebill agent
[INFO] Started TimeBill agent
[INFO] Detected project: Vim Editing
[INFO] Tracking started at 1628450123000
# Switch to a VSCode window titled “MyApp – src/main.py”
[INFO] Detected project: MyApp Development
[INFO] Tracking switched to MyApp Development at 1628450500000
```

**Idle detection stops tracking**  
```bash
$ export TIMEBILL_IDLE_SECONDS=60
$ python -m timebill agent
[INFO] Started TimeBill agent
[INFO] Detected project: Browser Research
[INFO] Tracking started at 1628451000000
# No mouse or keyboard input for 70 seconds
[INFO] Idle threshold reached – stopping accrual for Browser Research
[INFO] Session elapsed: 00:01:10
```

**Exporting data after shutdown**  
```bash
$ python -m timebill agent &
# Work for a few minutes, then press Ctrl+C
[INFO] Received shutdown signal
[INFO] Exporting data to ./data/timebill.db
[INFO] Shutdown complete
$ sqlite3 ./data/timebill.db "SELECT name FROM Project;"
Vim Editing
MyApp Development
Browser Research
$ sqlite3 ./data/timebill.db "SELECT project_name, duration_ms FROM TimeEntry;"
Vim Editing|120000
MyApp Development|300000
Browser Research|90000
```

## File Structure
```
TimeBill/
├── agent/               # Core detection and accounting logic
│   ├── detection.py
│   ├── accounting.py
│   └── __init__.py
├── data/                # Models, storage, encryption helpers
│   ├── models.py
│   ├── storage.py
│   └── encryption.py
├── tests/               # Unit test suite
│   ├── test_detection.py
│   ├── test_accounting.py
│   ├── test_storage.py
│   └── test_encryption.py
├── assets/              # Icons and graphics
│   └── infographic.png
├── timebill.py          # CLI entry point (python -m timebill agent)
├── README.md
└── .gitignore
```

## Tech Stack
| Technology | Purpose |
|---|---|
| Python 3.11+ | Core language and runtime |
| SQLite (built‑in) | Persistent storage of projects and time entries |
| hashlib / secrets | AES‑256 key derivation and encryption (OS UUID) |
| pytest | Running unit tests |
| setuptools (optional) | Packaging and distribution |

## Contributing
Fork the repo, make changes, run `pytest` locally, then submit a pull request. Please keep new features to a single iteration and update tests accordingly.

## License
MIT

## Author
Matthew Snow -- [M2AI](https://m2ai.co) | [@m2ai-portfolio](https://github.com/m2ai-portfolio)