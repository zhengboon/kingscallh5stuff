CardBot (Kings Call H5) - Progress Report and Roadmap
Updated: 2026-03-10

==================================================
1) What is implemented now
==================================================

Core architecture (modular):
- capture/: MSS-based screen capture
- vision/: lane detection, card presence detection, turn detection, OCR helper, template matching, debug overlay
- engine/: deterministic game model with lanes, creatures, abilities, modifiers, event bus, and resolver
- environment/: Gymnasium RL environment wrapper around the deterministic engine
- agents/: heuristic and random policies
- controller/: input controller placeholder + session logger
- main.py: end-to-end loop (capture -> vision -> state sync -> agent -> optional action)
- run_multi.py: multi-instance launcher for tiled browser setups

Gameplay/engine support currently includes:
- 2/3/4 lanes
- turn lifecycle (start/end)
- creature stats and countdown
- shared abilities/triggers
- modifiers and stacking
- healing, max HP changes, damage growth
- creature death cleanup
- event dispatch hooks:
  on_turn_start, on_turn_end, on_summon, on_hit, on_damage_taken, on_heal, on_death

Observation and control modes:
- observe: watch + log only
- assist: watch + suggest actions (no execution)
- autoplay: watch + execute actions through controller mapping

Session logging:
- JSONL logs are written under cardbot/data/sessions/
- includes metadata, sampled frame detections, state summaries, and turn events

==================================================
2) Improvements added in this update
==================================================

A) Vision profile system (new)
- New file: cardbot/vision/profile.py
- Supports loading/saving JSON profiles for:
  - lane_coords
  - turn_roi
  - turn_threshold
  - card_match_threshold
  - card_edge_ratio_threshold
- main.py now supports:
  --vision-profile <path>
  --save-vision-profile <path>
- Safety behavior:
  if profile lane count does not match --lanes, bot falls back to auto lane layout.

B) Multi-instance launcher hardened
- run_multi.py now supports:
  --vision-profile <path-with-{instance_id}-optional>
  --launch-delay <seconds>
- Better supervision:
  - if one worker exits with non-zero code, launcher terminates other workers
  - on shutdown, waits and force-kills stuck workers

C) Session analysis utility (new)
- New script: cardbot/tools/session_summary.py
- Summarizes one or many JSONL session logs:
  - frames
  - turn events
  - suggestions
  - executed actions
  - my_turn frame count
  - card presence ratio

D) Calibration template (new)
- New file: cardbot/data/vision_profile.template.json
- Starter structure for manual ROI tuning.

E) Runtime heartbeat + dashboard integration (new)
- New file: cardbot/controller/runtime_status.py
- main.py now writes live heartbeat JSON per instance:
  cardbot/data/runtime_status/instance_<id>.json
- Dashboard reads these files and marks each instance as:
  RUNNING / STALE / STOPPED

F) Dashboard native browser launcher (new)
- status_ui includes launch controls for:
  - Internet Explorer (native)
  - Edge
  - Chrome
  - default browser
- Supports launching multiple game windows from URL and stopping launched browser processes.

G) Observation-to-scenario workflow (new)
- Observe logs now store reconstructable engine snapshots (per sampled frame).
- New script: cardbot/tools/session_to_scenarios.py
  - extracts unique snapshots from session logs into one scenario JSON file.
- New script: cardbot/tools/scenario_runner.py
  - loads one exported scenario into RLEnv for quick testing.
- RLEnv reset now supports:
  reset(options={"state_snapshot": ...})

==================================================
3) How to run (current)
==================================================

Single instance:
1. source .venv/bin/activate
2. python -m cardbot.main --mode observe --agent heuristic --target-fps 30 --debug-window

Single instance with profile:
- python -m cardbot.main --mode assist --vision-profile cardbot/data/vision_profile.template.json

Save detected layout into a profile file:
- python -m cardbot.main --mode observe --save-vision-profile cardbot/data/my_profile.json --max-frames 30

4 instances (2x2 tiled browser):
- python -m cardbot.run_multi --instances 4 --rows 2 --cols 2 --mode observe --target-fps 30

4 instances with per-instance profiles:
- python -m cardbot.run_multi \
    --instances 4 --rows 2 --cols 2 \
    --mode assist \
    --vision-profile cardbot/data/profiles/instance_{instance_id}.json

Summarize logs:
- python -m cardbot.tools.session_summary cardbot/data/sessions

Observe and export reconstructable scenarios:
1. Record an observe session with denser sampling:
   python -m cardbot.main --mode observe --agent heuristic --target-fps 30 --log-fps 10 --debug-window
2. Convert session logs into reusable scenarios:
   python -m cardbot.tools.session_to_scenarios cardbot/data/sessions --output cardbot/data/scenarios/observed_scenarios.json --my-turn-only --max-scenarios 300
3. Load one scenario into the RL env:
   python -m cardbot.tools.scenario_runner cardbot/data/scenarios/observed_scenarios.json --index 0
4. Optional one-step check from that scenario:
   python -m cardbot.tools.scenario_runner cardbot/data/scenarios/observed_scenarios.json --index 0 --action 0

Runtime status UI (new):
- Start dashboard:
  python -m cardbot.tools.status_ui --status-dir cardbot/data/runtime_status --host 127.0.0.1 --port 8765
- Open:
  http://127.0.0.1:8765
- Bot instances publish heartbeat files to:
  cardbot/data/runtime_status/instance_<id>.json
- Dashboard also supports browser launch controls:
  - Launch 4 game windows directly from the UI
  - Browser choices include Internet Explorer (native), Edge, Chrome, or default browser
  - Stop button can terminate browser processes launched by the dashboard

Stop recording and inspect latest session:
- Stop all active observers (Windows PowerShell):
  Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -like '*cardbot.main*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
- Summarize all session logs:
  python -m cardbot.tools.session_summary cardbot/data/sessions

Train a baseline RL policy (tabular Q-learning):
- Quick smoke run:
  .venv/bin/python -m cardbot.tools.train_q --episodes 100 --print-every 20 --save-path cardbot/data/models/q_table_smoke.pkl
- Longer run:
  .venv/bin/python -m cardbot.tools.train_q --episodes 5000 --print-every 200 --save-path cardbot/data/models/q_table_v1.pkl
- Tuned example:
  .venv/bin/python -m cardbot.tools.train_q --episodes 10000 --alpha 0.08 --gamma 0.995 --epsilon-decay 0.999 --print-every 250 --save-path cardbot/data/models/q_table_v2.pkl

Notes:
- Output model files are pickle artifacts containing:
  - q_table (state_key -> Q-values)
  - meta (training config + summary metrics)
- Training currently uses the deterministic internal engine (not live browser frames).

==================================================
4) Known gaps / limitations
==================================================

- Input execution is still placeholder logging (no OS-level click injection yet).
- Vision still uses heuristic card presence; card identity classification is not complete.
- OCR pipeline exists, but HP/countdown ROIs are not fully integrated into state sync.
- Turn indicator template pipeline is prepared, but profile/template calibration per UI skin is still needed.
- State sync from vision is currently approximate and should be upgraded for production-grade autonomy.
- Observe mode does not train/update a model yet; it logs data and suggestions only.
- Observe mode can now export replayable snapshots, but true card identity/OCR quality still limits fidelity.
- RL training is offline against the deterministic simulator; online/live adaptation from browser play is not integrated yet.

==================================================
5) Future plan (recommended order)
==================================================

Phase 1: Browser-instance calibration and control hardening
- Add per-instance calibration capture tool (point-and-click ROI selection)
- Add robust browser-window anchoring checks before acting
- Add real input backend for controlled click/drag execution

Phase 2: Perception quality upgrades
- Add card identity matching bank and confidence gating
- Add OCR ROI mapping for HP/countdown and sanity filters
- Add temporal smoothing and state reconciliation to reduce false positives

Phase 3: Data and learning loop
- Convert session JSONL into training datasets
- Add imitation learning baseline from observe/assist traces
- Expand RL reward shaping and curriculum scenarios

Phase 4: Production automation safety
- Add action validation layer against mirrored engine state
- Add fail-safe guardrails (pause on uncertainty/conflict)
- Add metrics dashboard for FPS, detection confidence, and action success rates

==================================================
6) Practical next step for Kings Call H5
==================================================

- Collect 4 profile files (one per tiled browser instance):
  cardbot/data/profiles/instance_0.json ... instance_3.json
- Run in assist mode first, verify suggestions match your gameplay.
- Only move to autoplay after profile and lane/turn detection are stable.
