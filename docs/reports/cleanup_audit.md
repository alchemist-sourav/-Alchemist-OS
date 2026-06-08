# Repository Cleanup Audit

This audit analyzes the entire Alchemist OS repository to identify ephemeral files, generated reports, and cache folders that should be moved or deleted before the final RC1 tag.

## KEEP

* `backend/` (Core source code)
* `frontend/` (UI assets)
* `data/memory.db`, `data/calendar.json`, `data/notes.txt` (Active data stores)
* `tests/` (Unit, stability, and stress test suites)
* `docs/` (Architecture, installation, deployment, and troubleshooting guides)
* `scripts/` (Utility scripts)
* `.gitignore`, `.env`, `.env.example`, `requirements.txt`, `README.md`, `Alchemist.spec`
  - **Reason:** Core project infrastructure, source code, and active runtime files essential to Alchemist OS.

## MOVE

* `RC1_CHECKLIST.md` -> `docs/RC1_CHECKLIST.md`
* `ALCHEMIST_RC1_REPORT.md` -> `docs/ALCHEMIST_RC1_REPORT.md`
  - **Reason:** These are important milestone documents but should not clutter the repository root. Moving them to the `docs/` directory maintains repository hygiene.

## MERGE

* **None.**
  - **Reason:** The test suites and backend modules are highly modular and properly segregated. No duplicate functionality or test overlaps remain.

---

## DELETE (High-Confidence Candidates)

The following files are identified as highly confident candidates for deletion. They consist of temporary artifacts, regenerated caches, and old outputs from previous testing phases.

### 1. Generated Reports
* `cleanup_report.md`
* `code_quality_report.md`
* `error_handling_report.md`
* `performance_report.md`
* `rc1_validation_report.md`
* `security_report.md`
* `stability_report.md`
* `logs/stability_report.md`
  - **Reason:** Ephemeral snapshot reports generated during the RC1 Hardening phase. They have served their purpose and are now obsolete.

### 2. Temporary Scripts
* `measure_perf.py`
  - **Reason:** A one-off script created exclusively to run benchmarks for the `performance_report.md`. It is no longer needed.

### 3. Old Screenshots
* `screenshots/screenshot_full_20260607_120400.png`
* `screenshots/screenshot_full_20260607_122905.png`
* `screenshots/screenshot_full_20260607_123233.png`
* `screenshots/screenshot_full_20260607_123912.png`
* `screenshots/screenshot_full_20260607_125409.png`
* `screenshots/screenshot_full_20260607_130917.png`
* `screenshots/screenshot_full_20260607_132419.png`
  - **Reason:** Leftover active-window captures from previous Vision Agent operations and performance tests. They consume unnecessary disk space.

### 4. Old Logs
* `logs/actions.log`
* `logs/errors.log`
* `logs/system.log`
  - **Reason:** Ephemeral runtime logs generated during prior testing and daemon executions.

### 5. Cache Folders
* `.pytest_cache/`
* `backend/__pycache__/`
* `tests/__pycache__/` (and nested `__pycache__` inside `unit/`, `stability/`, `stress/`)
  - **Reason:** Standard Python and Pytest bytecode cache directories. Safe to delete.

### 6. Duplicate Test Files / Abandoned Prototypes
* **None.**
  - **Reason:** All duplicate test files and abandoned prototypes were successfully purged prior to the RC1 branch cut.

### 7. Unused Imports / Dead Code
* **None.**
  - **Reason:** The `backend/` was completely scrubbed of unused imports and dead code during the Code Quality hardening step. 

### 8. Duplicate Databases
* **None.**
  - **Reason:** Only the primary `memory.db` exists in the `data/` directory.
