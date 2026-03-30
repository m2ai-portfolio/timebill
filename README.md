

# TimeBill  
![Python >=3.11](https://img.shields.io/badge/python-3.11%2B-blue)  
![License MIT](https://img.shields.io/badge/license-MIT-green)


## Overview  
TimeBill is an automatic time‑tracking application that infers the project you're working on from terminal activity, IDE focus, and browser‑tab changes. It runs entirely on the developer’s machine, stores data locally in a SQLite database (or in‑memory JSON), and requires no internet connection. Target users are freelancers, consultants, agencies, and contractors who bill by the hour and need a hands‑free way to capture billable time.

## Problem Statement  
Freelancers and consultants currently log billable hours manually with spreadsheets or forms—a tedious, error‑prone process that is often delayed until invoicing, resulting in lost revenue and unnecessary admin overhead.

## Features  
- **Passive Project Detection** – Infers the active project from window titles, IDE status bars, or browser tab names without user input.  
- **Idle‑Based Time Accounting** – Starts tracking on user activity and stops accruing time after a configurable period of inactivity.  
- **Local, Encrypted Storage** – Persists project‑to‑seconds mappings in SQLite (AES‑256 encrypted with a machine‑specific key) or holds them in‑memory JSON; all work is offline.  
- **Minimal System‑Tray / Menu‑Bar UI** – Provides a simple icon for start/stop and settings; no Electron or web front‑end.  
- **Cross‑Platform, Pure Python** – Works on Windows, macOS, and Linux using only the standard library and a few optional native‑accessibility helpers.

## Tech Stack  
- **Language:** Python 3.11+  
- **Testing:** pytest  
- **Packaging:** setuptools (optional)  
- **Database:** SQLite (bundled) + SQLAlchemy‑lite wrapper or plain sqlite3 module; in‑memory JSON fallback  
- **Security:** libsodium‑based AES‑256 (via `pynacl` or pure‑python fallback) for local encryption  
- **OS Interaction:**  
  - Windows: `ctypes` + Win32 accessibility APIs  
  - macOS: `pyobjc` / `Quartz` for window title access  
  - Linux: `dbus` + `Xorg`/`wnck` or `gtk` for active window detection  
- **Build / CI:** None required beyond running the test suite

## Quick Start / Installation  

1. **Clone the repository**  
   ```bash
   git clone <repo‑url>
   cd <repo‑dir>
   ```

2. **Ensure Python 3.11+ is installed**  
   ```bash
   python --version   # should show 3.11 or higher
   ```

3. **(Optional) Install in development mode**  
   ```bash
   pip install -e .
   ```
   *The project has no third‑party runtime dependencies beyond the standard library; the step mainly makes the `timebill` module importable.*

4. **Run the agent**  
   ```bash
   python -m timebill agent
   ```
   The agent will appear as a tray/menu‑bar icon and begin tracking automatically. Press `Ctrl+C` in the terminal to stop it.

## Usage  

- **Start tracking** – Launch the agent as shown above; it begins accruing time as soon as you interact with an IDE, terminal, or browser.  
- **Change idle timeout** – Set the environment variable before launching:  
  ```bash
  export TIMEBILL_IDLE_SECONDS=600   # 10 minutes
  python -m timebill agent
  ```
- **Specify storage location** – Override the default SQLite path:  
  ```bash
  export TIMEBILL_DB_PATH=$HOME/.timebill/timebill.db
  python -m timebill agent
  ```
- **View a quick summary** – After stopping the agent, a report is printed to stdout showing total seconds per project:  
  ```
  Total tracked time:
    Website Redesign: 7200s
    API Development: 3600s
  ```
- **Run the test suite** – Verify the core logic:  
  ```bash
  pytest -q
  ```

## Architecture  

```
[User] <--(focus/idle events)--> [Agent Core] <--(local storage)--> [Encrypted SQLite/JSON]
```

- **Agent Core** (single process) consists of three cooperating modules:  
  - `detection.py` – Receives OS focus events, determines the active project name.  
  - `accounting.py` – Starts/stops timers based on idle thresholds, accumulates `duration_ms`.  
  - `storage.py` – Writes `Project` and `TimeEntry` records to SQLite (AES‑256 encrypted) or holds them in‑memory JSON.  
- A thin **system‑tray / menu‑bar** layer (built with `tkinter` or `rumps`/`pystray` depending on platform) provides start/stop controls and a settings dialog.  
- All components run in‑process; no external services, message queues, or network calls are involved, guaranteeing offline operation.  
- Data model follows the Pydantic definitions in `data/models.py` (`Project`, `TimeEntry`).  

## License  

MIT License  

Copyright (c) 2025 TimeBill Contributors  

Permission is hereby granted, free of charge, to any person obtaining a copy… (see the full `LICENSE` file for details).