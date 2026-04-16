

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

TimeBill automatically logs billable hours by monitoring your active windows, IDE status, and browser tabs, then stores the data locally so you can generate invoices without manual entry. It's ideal for freelancers, consultants, and agencies who bill by the hour.

```
$ python -m timebill agent
[INFO] Started agent. Monitoring active windows.
[INFO] Detected project: API Development (browser: Chrome)
[INFO] Idle threshold: 300s
```

Freelancers and consultants manually log billable hours using spreadsheets or forms, which is tedious, error‑prone, and often forgotten until invoicing time. This leads to lost revenue and administrative overhead that takes away from actual client work.

| Feature | Description |
|---|---|
| Passive Project Detection | Infers the active project from foreground window title, IDE status bar, or browser tab name without user input. |
| Idle‑Based Time Accounting | Starts tracking when the user becomes active and stops after a configurable period of inactivity (default 5 minutes). |
| Local Encrypted Storage | Persists project‑to‑seconds mappings in a SQLite database (`timebill.db`) encrypted with AES‑256 using a machine‑specific key. |
| Cross‑Platform Minimal UI | Provides a system‑tray / menu‑bar icon that opens a simple settings dialog; no web front‑end or Electron wrapper. |
| Offline‑Only Operation | All processing (focus detection, idle timing, storage, encryption) runs locally; no internet connectivity required. |
| Configurable Idle Timeout | Adjust the period of inactivity before tracking stops via the `TIMEBILL_IDLE_SECONDS` environment variable. |
| Project‑Keyword Detection | Optionally supply a comma‑separated list of keywords or regex patterns via `TIMEBILL_PROJECT_DETECTION` to refine project inference. |
| SQLite/JSON Fallback | Stores data in SQLite by default; can fall back to in‑memory JSON if the database file cannot be created. |

**Quick Start**

1. Clone the repository:  
   `git clone https://github.com/yourusername/TimeBill.git`
2. Navigate to the project directory:  
   `cd TimeBill`
3. Install the package in development mode:  
   `pip install -e .`
4. Run the agent:  
   `python -m timebill agent`  
   (Optional: set environment variables such as `TIMEBILL_IDLE_SECONDS=200` before the command.)

**Examples**

**Detecting project from IDE**  
Command:  
`$ python -m timebill agent`  
Output:  
```
[INFO] Started agent. Monitoring active windows.
[INFO] Detected project: Web Development (IDE: VS Code)
[INFO] Tracking started for project Web Development at 2025-09-16 10:12:03
```

**Using custom project keywords**  
Command:  
`$ TIMEBILL_PROJECT_DETECTION="react,node" python -m timebill agent`  
Output:  
```
[INFO] Started agent. Monitoring active windows.
[INFO] Detected project: Frontend Refactor (browser: Firefox - React devtools)
[INFO] Tracking started for project Frontend Refactor at 2025-09-16 10:15:42
```

**Viewing logged time via SQLite**  
Command:  
`$ sqlite3 data/timebill.db "SELECT p.name AS project, SUM(t.duration_ms)/60000.0 AS minutes FROM TimeEntry t JOIN Project p ON t.project_name = p.name GROUP BY p.name;"`  
Output:  
```
project            | minutes
-------------------|--------
Web Development    | 125.5
Frontend Refactor  |  78.0
API Development    | 210.3
```

**File Structure**

```
TimeBill/
  agent/               # Core detection, accounting, storage logic
    __init__.py
    detection.py
    accounting.py
    storage.py
  data/                # Data models, encryption, persistence
    __init__.py
    models.py
    storage.py
    encryption.py
  assets/              # Visual assets
    infographic.png
  tests/               # Unit test suite
    test_accounting.py
    test_detection.py
    test_encryption.py
    test_storage.py
  timebill.py          # CLI entry point
  README.md
  .gitignore
```

**Tech Stack**

| Technology | Purpose |
|---|---|
| Python 3.11+ | Core language and runtime |
| SQLite | Local persistent storage (or in‑memory JSON fallback) |
| AES‑256 (via libsodium‑linked primitives) | Encryption of stored data |
| pytest | Test framework |
| setuptools | Packaging and distribution |

**Contributing**

Fork the repository, make your changes, run the test suite with `pytest`, and submit a pull request. Please keep changes focused and well‑tested.

**License**

MIT

**Author**

Matthew Snow -- [M2AI](https://m2ai.co) | [@m2ai-portfolio](https://github.com/m2ai-portfolio)