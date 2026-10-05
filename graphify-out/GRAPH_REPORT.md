# Graph Report - reverse_cam  (2026-10-05)

## Corpus Check
- 30 files · ~10,216 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 3, .example 1, .service 1)

## Summary
- 233 nodes · 300 edges · 23 communities (15 shown, 8 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 5 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `afc2a91c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ParkingSessionLogger
- ProximityFilter
- test_ble_link.py
- pi_config.py
- BLEManager
- setup_pi.sh
- docker-entrypoint.sh
- start_reverse_cam.sh
- test_graphify.py
- 🚀 B.L.A.S.T. Master System Prompt
- TerminalHUD
- Quick Start
- Project Findings & Discoveries
- Phases & Checklists
- Project Constitution (`gemini.md`)
- SOP: BLE Client Communication & GATT Management
- SOP: Proximity Signal Filtering & Hysteresis
- SOP: Parking Session & Analytical Cube Logging
- Progress Log
- rules/graphify.md
- workflows/graphify.md
- claude.md

## God Nodes (most connected - your core abstractions)
1. `ProximityFilter` - 16 edges
2. `BLEManager` - 11 edges
3. `ParkingSessionLogger` - 10 edges
4. `🚀 B.L.A.S.T. Master System Prompt` - 9 edges
5. `interactive_menu()` - 8 edges
6. `Phases & Checklists` - 8 edges
7. `Quick Start` - 7 edges
8. `main()` - 6 edges
9. `run_ble_handshake()` - 6 edges
10. `TerminalHUD` - 6 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `BLEManager`  [EXTRACTED]
  reverse_cam_runner.py → tools/ble_manager.py
- `main()` --calls--> `ProximityFilter`  [EXTRACTED]
  reverse_cam_runner.py → tools/proximity_filter.py
- `main()` --calls--> `TerminalHUD`  [EXTRACTED]
  reverse_cam_runner.py → tools/terminal_hud.py
- `test_median_filter()` --calls--> `ProximityFilter`  [EXTRACTED]
  tests/test_proximity_filter.py → tools/proximity_filter.py
- `test_hysteresis_boundary()` --calls--> `ProximityFilter`  [EXTRACTED]
  tests/test_proximity_filter.py → tools/proximity_filter.py

## Import Cycles
- None detected.

## Communities (23 total, 8 thin omitted)

### Community 0 - "ParkingSessionLogger"
Cohesion: 0.12
Nodes (7): main(), 4. Automotive Resiliency & Fault Tolerance: Automatic BLE Reconnect Loop with Exponential Backoff, 5. Cloud / VPS Telemetry Synchronization: Offline-First Store-and-Forward, 🔮 Phase 6: Future Roadmap & Architectural Extensions, test_session_finalize_without_readings(), test_session_lifecycle(), ParkingSessionLogger

### Community 1 - "ProximityFilter"
Cohesion: 0.16
Nodes (5): test_danger_solid_zone(), test_hysteresis_boundary(), test_median_filter(), test_stale_watchdog(), ProximityFilter

### Community 3 - "test_ble_link.py"
Cohesion: 0.16
Nodes (5): main(), run_ble_handshake(), test_ble_adapter_readiness(), test_env_configuration(), verify_env_config()

### Community 4 - "pi_config.py"
Cohesion: 0.16
Nodes (9): display_banner(), display_menu(), display_settings(), find_device(), interactive_menu(), main(), monitor_distance(), read_settings() (+1 more)

### Community 9 - "test_graphify.py"
Cohesion: 0.16
Nodes (5): main(), run_graphify_cli(), test_graphify_graph_generation(), test_graphify_html_generation(), test_open_graphify_html()

### Community 10 - "🚀 B.L.A.S.T. Master System Prompt"
Cohesion: 0.15
Nodes (12): 1. The "Data-First" Rule, 2. Self-Annealing (The Repair Loop), 3. Deliverables vs. Intermediates, 🚀 B.L.A.S.T. Master System Prompt, 📂 File Structure Reference, 🛠️ Operating Principles, 🏗️ Phase 1: B - Blueprint (Vision & Logic), ⚡ Phase 2: L - Link (Connectivity) (+4 more)

### Community 11 - "TerminalHUD"
Cohesion: 0.15
Nodes (6): 1. Goal, 2. Display Components, 3. Refresh Rate & Rendering, 4. Architectural Invariant & Self-Annealing Note (Cross-Platform Terminal Compatibility), SOP: Real-Time Terminal HUD & User Interface, TerminalHUD

### Community 12 - "Quick Start"
Cohesion: 0.15
Nodes (12): 1. Build the Docker Image, 2. Running in Simulation Mode (No Hardware Needed), 3. Running with Physical BLE on Raspberry Pi / Linux Host, 4. Running the Interactive BLE Configuration Tool, 5. Running the Test Suite Inside Docker, 6. Running Graphify Inside Docker, Architecture Overview, Docker Guide for ReverseCam (+4 more)

### Community 13 - "Project Findings & Discoveries"
Cohesion: 0.17
Nodes (11): 1. Existing System Architecture, 2. Research on Automotive Reverse Proximity Sensors (ISO 17386 / MALSO), 3. Data & Storage Considerations (OLAP Cube / VPS Ingestion), 4. Automotive Resiliency & Fault Tolerance, 5. Cloud / VPS Telemetry Synchronization, A. Automatic BLE Reconnect Loop with Exponential Backoff, A. Store-and-Forward Telemetry Architecture, Client Configuration Script (`pi_config.py`) (+3 more)

### Community 14 - "Phases & Checklists"
Cohesion: 0.20
Nodes (9): B.L.A.S.T. Task Plan: Reverse Cam Automation, 🏗️ Phase 1: B - Blueprint (Vision & Logic), ⚡ Phase 2: L - Link (Connectivity), ⚙️ Phase 3: A - Architect (The 3-Layer Build), ✨ Phase 4: S - Stylize (Refinement & UI), 🛰️ Phase 5: T - Trigger (Deployment), Phases & Checklists, Project Status: COMPLETED (All Phases Verified) (+1 more)

### Community 15 - "Project Constitution (`gemini.md`)"
Cohesion: 0.22
Nodes (8): 1. Architectural Invariants (A.N.T.), 2. Behavioral Rules (Automotive Proximity Standards: ISO 17386 / MALSO), 3. Data Schemas (JSON), 4. Maintenance Log, Project Constitution (`gemini.md`), Schema A: `ReverseCamSettings` (ESP32 GATT Settings Characteristic), Schema B: `ReverseCamTelemetry` (Real-Time Sensor Telemetry), Schema C: `ParkingSessionFact` (Cube Data Model / VPS Analytical Storage)

### Community 16 - "SOP: BLE Client Communication & GATT Management"
Cohesion: 0.33
Nodes (5): 1. Goal, 2. Inputs & Environment, 3. Operational Logic, 4. Edge Cases, SOP: BLE Client Communication & GATT Management

### Community 17 - "SOP: Proximity Signal Filtering & Hysteresis"
Cohesion: 0.33
Nodes (5): 1. Goal, 2. Inputs, 3. Algorithm & Logic, 4. Edge Cases, SOP: Proximity Signal Filtering & Hysteresis

### Community 18 - "SOP: Parking Session & Analytical Cube Logging"
Cohesion: 0.33
Nodes (5): 1. Goal, 2. Storage Architecture, 3. Operational Logic, 4. Edge Cases, SOP: Parking Session & Analytical Cube Logging

### Community 19 - "Progress Log"
Cohesion: 0.50
Nodes (3): Milestones Delivered:, Progress Log, Session: Full B.L.A.S.T. Protocol Execution Complete

## Knowledge Gaps
- **61 isolated node(s):** `setup_pi.sh script`, `docker-entrypoint.sh script`, `start_reverse_cam.sh script`, `graphify`, `🟢 Protocol 0: Initialization (Mandatory)` (+56 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 135 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ParkingSessionLogger` connect `ParkingSessionLogger` to `reverse_cam_runner.py`, `test_ble_link.py`?**
  _High betweenness centrality (0.120) - this node is a cross-community bridge._
- **Why does `BLEManager` connect `BLEManager` to `ParkingSessionLogger`, `reverse_cam_runner.py`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Why does `ProximityFilter` connect `ProximityFilter` to `ParkingSessionLogger`, `reverse_cam_runner.py`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **What connects `setup_pi.sh script`, `docker-entrypoint.sh script`, `start_reverse_cam.sh script` to the rest of the system?**
  _61 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ParkingSessionLogger` be split into smaller, more focused modules?**
  _Cohesion score 0.11695906432748537 - nodes in this community are weakly interconnected._
- **Should `BLEManager` be split into smaller, more focused modules?**
  _Cohesion score 0.13970588235294118 - nodes in this community are weakly interconnected._