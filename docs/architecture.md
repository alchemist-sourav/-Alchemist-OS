# Alchemist OS Architecture

Alchemist OS is designed as an agentic operating system. The architecture is broken into highly decoupled subsystems that communicate via a central Planner loop and a WebSocket broadcast system.

## 1. The Core Loop
The primary entrypoint (`backend/main.py`) initializes a persistent WebSocket connection to the frontend UI and spins up a background Wake Word daemon. 

## 2. Planner (`planner/planner.py`)
The `TaskPlanner` intercepts natural language queries. Powered by Groq LLMs, it parses the query, matches the user's intent to available registered tools, and constructs a JSON sequence of actions.

## 3. Executor (`executor/executor.py`)
The `AgentExecutor` executes the JSON steps asynchronously. It parses `step_results` mapping, resolving cross-step dynamic variable injections (e.g., passing output from step 1 into the arguments of step 2).

## 4. Tools Registry (`tools/registry.py`)
A generalized abstraction layer. Tools (like `file_agent`, `browser_agent`, `system`) register themselves with a function signature and a JSON schema. The executor pulls directly from this registry.

## 5. Vision System (`vision/analyzer.py` & `vision/screen.py`)
Built on PIL and LLM Vision capabilities. The `screen.py` acquires active desktop dimensions or application boundaries, captures the pixel state, and `analyzer.py` queries the LLM for spatial understanding of UI elements.

## 6. Voice & Wake Word (`voice/wake_word.py` & `voice/engine.py`)
A continuous threaded background loop using `speech_recognition`. On detecting "Alchemist", the state switches to `listening`, and subsequent audio buffers are forwarded to the Planner.

## 7. Memory (`memory/database.py`)
A local SQLite instance storing long-term preferences, user history, and pending background tasks. No external database servers are required.
