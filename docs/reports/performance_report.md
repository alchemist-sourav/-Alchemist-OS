# Alchemist OS Performance Benchmarks

**Date:** 2026-06-07
**Phase:** RC1 Hardening - Step 5

## Benchmarks Executed

A specialized testing script (`measure_perf.py`) was isolated from the `pytest` harness to profile precise subsystem wall-clock durations and idle memory. 

### 1. Cold Startup & Idle Memory
- **Idle Memory Footprint:** `59.86 MB`
  - *Analysis:* Exceptional overhead. The daemon remains incredibly lightweight prior to Playwright/Vision instantiation.

### 2. Playwright Browser Launch
- **Launch Duration:** `1.76s`
  - *Analysis:* Fast. Playwright Chromium launches and fully connects to a target site within ~1.7s natively from Python.

### 3. Vision Acquisition
- **Screenshot Duration:** `0.16s`
  - *Analysis:* Ultra-low latency for native screen grabs via PIL. Negligible impact on the main loop.

### 4. Planner LLM Latency
- **Planning Loop:** `0.45s`
  - *Analysis:* Powered by Groq API, the LLM JSON reflection parsing and networking roundtrip took less than half a second.

## Conclusion
The system successfully scales down to minimal footprint constraints. Subsystem delays remain below the threshold required to feel "instantaneous" to the user, paving the way for real-time Operator behavior.
