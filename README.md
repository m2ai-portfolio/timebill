

# TimeBill  
  

## Overview  
TimeBill is an automatic time‑tracking application that detects what project you're working on from terminal activity, IDE usage, and browser interaction. It runs locally on the developer’s machine, requires no internet connectivity, and stores data exclusively in a local SQLite database (`timebill.db`) or in‑memory JSON structures. The tool is intended for freelancers, consultants, agencies, and contractors who bill by the hour and need an effortless way to capture billable time without manual spreadsheets or forms.

## Problem Statement  
Freelancers and consultants currently log billable hours manually using spreadsheets or forms—a process that is tedious, error‑prone, and often forgotten until invoicing time, leading to lost revenue and avoidable administrative overhead.

## Features  
- Passive project detection from window titles, IDE status bars, and browser tabs  
- Idle‑based time accounting (stops after configurable inactivity)  
- Local, encrypted storage (SQLite or in‑memory JSON)  
- Zero external API calls – fully offline operation  
- Minimal system‑tray / menu‑bar UI with tooltip display  
- Automatic start/stop of time entries based on user focus  

## Tech Stack  
- **Language:** Python 3.11+  
- **Testing:** pytest  
- **Dependency Management:** pip (standard library only)  
- **Build Tool:** setuptools (optional)  
- **Database:** SQLite (bundled with the app) or in‑memory JSON  
- **OS:** Cross‑platform (Windows, macOS, Linux) – pure Python, no native extensions  

## Quick Start / Installation  
1. Clone the repository: `git clone <repo-url>`  
2. Create a virtual environment: `python -m venv .venv`  
3. Activate the environment:  
   - Windows: `.venv\Scripts\activate`  
   - macOS/Linux: `source .venv/bin/activate`  
4. Install dependencies: `pip install -r requirements.txt`  
5. Run the agent: `python -m timebill agent`  
6. (Optional) Build with setuptools: `python setup.py sdist bdist_wheel`  

## Usage  
- Start tracking automatically when you focus on a known project (e.g., a VS Code window titled “Website Redesign”).  
- Switching to a browser tab showing “GitHub – acme/api” continues accruing time for the associated project.  
- After five minutes of no keyboard or mouse activity, tracking stops and a tray tooltip shows the elapsed session time.  
- Quitting the program exports a valid SQLite file `timebill.db` containing at least one `Project` row and zero or more `TimeEntry` rows.  
- Restarting the agent with the same environment variables yields identical project‑name mappings and monotonic timestamps.  

## Architecture  
```
[User] <--(idle detection)--> [Agent Core] <--(local storage)--> [SQLite/JSON DB]
```
- The **Agent Core** runs in a single process, sampling OS‑level focus events, IDE plugin hooks, and browser‑tab change events every second.  
- When idle time exceeds the configured threshold, the agent stops accruing time for the current project.  
- All data (project mapping, accumulated seconds) is written locally to the SQLite database or held in‑memory as JSON; no external calls are made.  
- The UI is a minimal system‑tray / menu‑bar icon that opens a simple settings dialog; no web front‑end or Electron wrapper is used.  

## License  
MIT License  

---  
*All processing (focus detection, idle timing, storage, encryption) is performed locally; the tool works entirely offline.*  
*Target – a working minimum viable product (MVP) after exactly five build iterations.*  
*Priority – “works correctly” (success criteria satisfied) over “feature complete.”*  
*Length – total markdown kept between 300‑600 lines; shorter preferred.*  
*Data – only SQLite `.db` files **or** in‑memory JSON; no multiple storage back‑ends.*  
*Architecture – no separate servers, workers, message queues, or micro‑services; everything runs in a single process.*  
*Features – every feature specific to the *TimeBill* idea; no generic features such as “Error Handling” or “Logging”.*  
*Testing – every test step a concrete CLI command with exact, verifiable stdout; vague steps forbidden.*  
*If external APIs were needed – a local alternative (mocked data, local analysis, file‑based) would be used instead.*