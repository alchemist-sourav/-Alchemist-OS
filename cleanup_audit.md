# Alchemist OS RC1 Cleanup Audit Report

## KEEP
* `backend/core/`, `backend/memory/`, `backend/planner/`, `backend/executor/`, `backend/tools/`, `backend/vision/`, `backend/voice/`, `backend/main.py`
  - Reason: Core backend subsystem logic required for Alchemist OS.
* `frontend/`
  - Reason: Main UI and client components.
* `data/memory.db`, `data/calendar.json`, `data/notes.txt`
  - Reason: Active data files necessary for system state persistence.
* `docs/`, `scripts/`, `requirements.txt`, `README.md`, `LICENSE`, `.gitignore`
  - Reason: Standard repository documentation and tooling.
* `backend/tests/test_computer_control.py`, `backend/tests/test_experience_system.py`, `backend/tests/test_file_agent.py`, `backend/tests/test_operator_mode.py`, `backend/tests/test_screenshot.py`, `backend/tests/test_system.py`, `backend/tests/test_wake_word.py`
  - Reason: Active unit tests for core modules.
* `backend/tests/stability_test.py`
  - Reason: Core stability testing suite.
* `backend/tests/stress_test.py`
  - Reason: Core stress testing suite.

## MOVE
* `backend/tests/stability_test.py`
  - Target: `tests/stability/stability_test.py`
* `backend/tests/stress_test.py`
  - Target: `tests/stress/stress_test.py`
* Remaining active tests in `backend/tests/` (except the ones listed in MERGE or DELETE)
  - Target: `tests/unit/` (or `tests/integration/`)

## MERGE
* `backend/tests/test_agent_executor.py`
  - Merge Target: `tests/unit/test_executor.py`
  - Reason: Both tests target the executor workflow.
* `backend/tests/test_vision_agent.py`
  - Merge Target: `tests/unit/test_vision.py`
  - Reason: Both tests target the vision analysis subsystem.
* `backend/requirements.txt`
  - Merge Target: root `requirements.txt`
  - Reason: Duplicate dependency file.

## DELETE
* `backend/test_phase1.py`
  - Reason: Abandoned experimental console script.
* `backend/test_final.py`
  - Reason: Abandoned experimental console script.
* `backend/tests/run_audit.py`
  - Reason: Experimental test script that uses hardcoded prompt tests.
* `data/response.mp3`, `data/response.wav`
  - Reason: Temporary TTS/voice testing output files.
* `logs/*` (e.g., `actions.log`, `errors.log`, `system.log`)
  - Reason: Old log debris from previous executions.
* `screenshots/*`
  - Reason: Redundant test screenshots from previous runs.
* `__pycache__/`, `.pytest_cache/`, `*.pyc`
  - Reason: Standard Python compilation and cache debris.
* `stability_report.md` (root) and `stability_test_audit.md` (root)
  - Reason: Temporary reports generated during debugging, should not be committed.
