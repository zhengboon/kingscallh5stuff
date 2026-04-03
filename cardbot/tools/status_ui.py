"""Local web UI for CardBot runtime status heartbeats."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


HTML_PAGE = """<!DOCTYPE html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <title>CardBot Status</title>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <style>
    :root {
      --bg: #0f172a;
      --panel: #1e293b;
      --text: #e2e8f0;
      --muted: #94a3b8;
      --ok: #16a34a;
      --warn: #d97706;
      --stop: #b91c1c;
      --line: #334155;
    }
    body {
      margin: 0;
      font-family: Segoe UI, Tahoma, sans-serif;
      background: radial-gradient(circle at 20% 10%, #1f2937, var(--bg));
      color: var(--text);
      min-height: 100vh;
    }
    .wrap {
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
    }
    h1 { margin: 0 0 6px 0; font-size: 28px; }
    .sub { color: var(--muted); margin-bottom: 18px; }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
      margin-bottom: 14px;
    }
    .row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
    }
    .row input, .row select {
      background: #0b1220;
      color: var(--text);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px 10px;
      font-size: 14px;
    }
    .row input[type=\"text\"] { min-width: 420px; }
    .row input[type=\"number\"] { width: 90px; }
    .btn {
      background: #0b1220;
      border: 1px solid var(--line);
      color: var(--text);
      border-radius: 8px;
      padding: 8px 12px;
      font-size: 13px;
      cursor: pointer;
    }
    .btn.primary { border-color: #22c55e; }
    .btn.warn { border-color: #f59e0b; }
    .msg {
      margin-top: 8px;
      font-size: 13px;
      color: #bfdbfe;
    }
    .summary {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-bottom: 16px;
    }
    .pill {
      background: #0b1220;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 8px 14px;
      font-size: 13px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 12px;
    }
    .card {
      background: var(--panel);
      border-radius: 14px;
      padding: 14px;
      border: 1px solid var(--line);
      box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);
    }
    .top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }
    .title { font-size: 18px; font-weight: 600; }
    .badge {
      border-radius: 999px;
      padding: 4px 10px;
      font-size: 12px;
      font-weight: 700;
      color: white;
    }
    .running { background: var(--ok); }
    .stale { background: var(--warn); }
    .stopped { background: var(--stop); }
    .kv { font-size: 13px; line-height: 1.7; color: #dbeafe; }
    .label { color: var(--muted); }
    pre {
      white-space: pre-wrap;
      font-size: 12px;
      background: #0b1220;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px;
      margin-top: 8px;
      max-height: 120px;
      overflow: auto;
    }
    .board {
      margin-top: 10px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: #0b1220;
    }
    .board-header {
      display: flex;
      justify-content: space-between;
      color: var(--ok);
      font-weight: 600;
      font-size: 13px;
      margin-bottom: 8px;
    }
    .lane-row {
      display: flex;
      justify-content: space-between;
      margin-bottom: 6px;
    }
    .lane-slot {
      flex: 1;
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 6px;
      padding: 6px;
      margin: 0 4px;
      font-size: 11px;
      text-align: center;
      min-height: 40px;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }
    .lane-slot.empty { opacity: 0.3; }
    .lane-slot.enemy { border-color: var(--warn); color: var(--warn); }
    .lane-slot.player { border-color: var(--text); color: var(--text); }
    .slot-title { font-weight: bold; margin-bottom: 2px; }
    .slot-stats { display: flex; justify-content: center; gap: 6px; }
    .btn.feedback { border-color: #3b82f6; color: #60a5fa; margin-top: 10px; width: 100%; }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <h1>CardBot Runtime Dashboard</h1>
    <div class=\"sub\">Auto-refresh every second</div>

    <div class=\"panel\">
      <div class=\"row\">
        <input id=\"targetUrl\" type=\"text\" value=\"https://www.xstargame.com/game/server/game/id/4\" />
        <input id=\"count\" type=\"number\" min=\"1\" max=\"12\" value=\"4\" />
        <select id=\"browser\">
          <option value=\"ie\" selected>Internet Explorer (native)</option>
          <option value=\"edge\">Microsoft Edge</option>
          <option value=\"chrome\">Google Chrome</option>
          <option value=\"default\">System Default</option>
        </select>
        <button class=\"btn primary\" onclick=\"launchBrowsers()\">Launch Windows</button>
        <button class=\"btn warn\" onclick=\"stopBrowsers()\">Stop Launched Browsers</button>
      </div>
      <div id=\"launchMsg\" class=\"msg\">Ready</div>
    </div>

    <div class=\"summary\" id=\"summary\"></div>
    <div class=\"grid\" id=\"grid\"></div>
  </div>
  <script>
    function fmtTime(ts) {
      if (!ts) return '-';
      return new Date(ts * 1000).toLocaleTimeString();
    }

    function statusClass(status) {
      if (status === 'RUNNING') return 'running';
      if (status === 'STALE') return 'stale';
      return 'stopped';
    }

    async function submitFeedback(instId) {
      const btn = document.getElementById('fb-btn-' + instId);
      const stateRaw = btn.getAttribute('data-state');
      if (!stateRaw) return;
      const notes = prompt("What is incorrect with Instance " + instId + "? (e.g., enemy lane 2 is empty but bot sees enemy)");
      if (!notes) return;
      
      try {
        const payload = JSON.parse(stateRaw);
        const res = await fetch('/api/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
             instance_id: instId,
             notes: notes,
             state: payload
          })
        });
        const data = await res.json();
        if (res.ok) alert("Feedback submitted! Logged to " + data.file);
        else alert("Failed to submit feedback: " + data.error);
      } catch (err) {
        alert("Error: " + err);
      }
    }

    async function launchBrowsers() {
      const url = document.getElementById('targetUrl').value.trim();
      const count = Number(document.getElementById('count').value || 4);
      const browser = document.getElementById('browser').value;
      const msg = document.getElementById('launchMsg');

      try {
        const res = await fetch('/api/launch-browsers', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url, count, browser }),
        });
        const data = await res.json();
        if (!res.ok) {
          msg.textContent = `Launch failed: ${data.error || 'unknown error'}`;
          return;
        }
        msg.textContent = `Launched ${data.launched} window(s) using ${data.browser}.`;
      } catch (err) {
        msg.textContent = `Launch request failed: ${String(err)}`;
      }
    }

    async function stopBrowsers() {
      const msg = document.getElementById('launchMsg');
      try {
        const res = await fetch('/api/stop-browsers', { method: 'POST' });
        const data = await res.json();
        if (!res.ok) {
          msg.textContent = `Stop failed: ${data.error || 'unknown error'}`;
          return;
        }
        msg.textContent = `Stopped ${data.stopped} launched browser process(es).`;
      } catch (err) {
        msg.textContent = `Stop request failed: ${String(err)}`;
      }
    }

    function render(data) {
      const summary = document.getElementById('summary');
      const grid = document.getElementById('grid');
      summary.innerHTML = '';
      grid.innerHTML = '';

      const totals = data.summary || {};
      const pills = [
        `Running: ${totals.running || 0}`,
        `Stale: ${totals.stale || 0}`,
        `Stopped: ${totals.stopped || 0}`,
        `Total: ${totals.total || 0}`,
        `Updated: ${new Date().toLocaleTimeString()}`,
      ];
      pills.forEach(text => {
        const el = document.createElement('div');
        el.className = 'pill';
        el.textContent = text;
        summary.appendChild(el);
      });

      (data.instances || []).forEach(inst => {
        const card = document.createElement('div');
        card.className = 'card';
        const stateData = inst.state || {};
        const lastAction = inst.last_action ? JSON.stringify(inst.last_action) : '-';
        const err = inst.last_error ? String(inst.last_error) : '-';
        const safeStateStr = JSON.stringify(stateData).replace(/"/g, '&quot;');
        
        let boardHtml = '';
        if (stateData.lanes && stateData.lanes.length > 0) {
           const pHP = stateData.player_hp ? (stateData.player_hp.player || 0) : 0;
           const eHP = stateData.player_hp ? (stateData.player_hp.enemy || 0) : 0;
           
           boardHtml += '<div class="board">';
           boardHtml += '<div class="board-header"><span>E: ' + eHP + ' HP</span> <span style="text-align:right">P: ' + pHP + ' HP</span></div>';
           
           stateData.lanes.forEach(lane => {
              boardHtml += '<div class="lane-row">';
              // Enemy Slot
              if (lane.enemy && lane.enemy.alive) {
                 const atk = lane.enemy.atk !== undefined ? lane.enemy.atk : lane.enemy.base_atk;
                 boardHtml += '<div class="lane-slot enemy"><div class="slot-title">' + (lane.enemy.name || lane.enemy.card_id) + '</div><div class="slot-stats"><span>A: ' + atk + '</span><span>H: ' + lane.enemy.hp + '</span><span>⏱ ' + lane.enemy.countdown + '</span></div></div>';
              } else {
                 boardHtml += '<div class="lane-slot empty">Empty</div>';
              }
              // Lane Label
              boardHtml += '<div style="display:flex;align-items:center;font-size:10px;color:#94a3b8;margin:0 4px;">L' + lane.index + '</div>';
              // Player Slot
              if (lane.player && lane.player.alive) {
                 const atk = lane.player.atk !== undefined ? lane.player.atk : lane.player.base_atk;
                 boardHtml += '<div class="lane-slot player"><div class="slot-title">' + (lane.player.name || lane.player.card_id) + '</div><div class="slot-stats"><span>A: ' + atk + '</span><span>H: ' + lane.player.hp + '</span><span>⏱ ' + lane.player.countdown + '</span></div></div>';
              } else {
                 boardHtml += '<div class="lane-slot empty">Empty</div>';
              }
              boardHtml += '</div>';
           });
           boardHtml += '</div>';
        }

        card.innerHTML = `
          <div class="top">
            <div class="title">Instance ${inst.instance_id}</div>
            <div class="badge ${statusClass(inst.health)}">${inst.health}</div>
          </div>
          <div class="kv"><span class="label">PID:</span> ${inst.pid || '-'}</div>
          <div class="kv"><span class="label">Mode:</span> ${inst.mode || '-'}</div>
          <div class="kv"><span class="label">FPS:</span> ${inst.fps || 0}</div>
          <div class="kv"><span class="label">Frames:</span> ${inst.frame_count || 0}</div>
          <div class="kv"><span class="label">My Turn:</span> ${inst.my_turn ? 'yes' : 'no'}</div>
          <div class="kv"><span class="label">Last Beat:</span> ${fmtTime(inst.updated_at)} (${inst.age_sec.toFixed(1)}s ago)</div>
          <div class="kv"><span class="label">Last Action:</span></div>
          <pre>${lastAction}</pre>
          <div class="kv"><span class="label">Last Error:</span></div>
          <pre>${err}</pre>
          ${boardHtml}
          <button id="fb-btn-${inst.instance_id}" class="btn feedback" data-state="${safeStateStr}" onclick="submitFeedback(${inst.instance_id})">Leave Feedback</button>
        `;
        grid.appendChild(card);
      });
    }

    async function tick() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        render(data);
      } catch (err) {
        console.error(err);
      }
    }

    tick();
    setInterval(tick, 1000);
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(description="CardBot runtime dashboard")
    parser.add_argument("--status-dir", type=str, default="cardbot/data/runtime_status")
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--stale-seconds",
        type=float,
        default=3.0,
        help="Heartbeat age threshold used for stale detection",
    )
    return parser.parse_args()


def _read_status_files(status_dir: Path) -> list[dict[str, Any]]:
    instances: list[dict[str, Any]] = []
    if not status_dir.exists():
        return instances

    for file_path in sorted(status_dir.glob("instance_*.json")):
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            instances.append(payload)

    instances.sort(key=lambda item: int(item.get("instance_id", 0)))
    return instances


def _normalize_health(instances: list[dict[str, Any]], stale_seconds: float) -> dict[str, Any]:
    now = time.time()

    running = 0
    stale = 0
    stopped = 0

    normalized: list[dict[str, Any]] = []
    for item in instances:
        updated_at = float(item.get("updated_at", 0.0) or 0.0)
        age_sec = max(0.0, now - updated_at)

        is_running = bool(item.get("running", False))
        if is_running and age_sec <= stale_seconds:
            health = "RUNNING"
            running += 1
        elif is_running:
            health = "STALE"
            stale += 1
        else:
            health = "STOPPED"
            stopped += 1

        patched = dict(item)
        patched["age_sec"] = round(age_sec, 2)
        patched["health"] = health
        normalized.append(patched)

    return {
        "instances": normalized,
        "summary": {
            "running": running,
            "stale": stale,
            "stopped": stopped,
            "total": len(normalized),
        },
    }


def _resolve_browser_executable(browser: str) -> str | None:
    browser_name = browser.lower().strip()

    if browser_name == "ie":
        candidates = [
            os.path.join(os.environ.get("ProgramFiles", r"C:\\Program Files"), "Internet Explorer", "iexplore.exe"),
            os.path.join(
                os.environ.get("ProgramFiles(x86)", r"C:\\Program Files (x86)"),
                "Internet Explorer",
                "iexplore.exe",
            ),
            shutil.which("iexplore.exe"),
        ]
    elif browser_name == "edge":
        candidates = [
            shutil.which("msedge.exe"),
            os.path.join(
                os.environ.get("ProgramFiles(x86)", r"C:\\Program Files (x86)"),
                "Microsoft",
                "Edge",
                "Application",
                "msedge.exe",
            ),
            os.path.join(
                os.environ.get("ProgramFiles", r"C:\\Program Files"),
                "Microsoft",
                "Edge",
                "Application",
                "msedge.exe",
            ),
        ]
    elif browser_name == "chrome":
        candidates = [
            shutil.which("chrome.exe"),
            os.path.join(
                os.environ.get("ProgramFiles", r"C:\\Program Files"),
                "Google",
                "Chrome",
                "Application",
                "chrome.exe",
            ),
            os.path.join(
                os.environ.get("ProgramFiles(x86)", r"C:\\Program Files (x86)"),
                "Google",
                "Chrome",
                "Application",
                "chrome.exe",
            ),
        ]
    else:
        return None

    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def _launch_browser_windows(
    url: str, 
    count: int, 
    browser: str, 
    isolate_profiles: bool = False,
    accounts: list[str] | None = None
) -> tuple[list[int], str]:
    if os.name != "nt":
        raise RuntimeError("Native browser launching is only supported on Windows hosts.")

    if browser == "default":
        launched: list[int] = []
        for _ in range(count):
            os.startfile(url)  # type: ignore[attr-defined]
        return launched, "default"

    browser_exe = _resolve_browser_executable(browser)
    if browser_exe is None:
        if browser == "ie":
            raise RuntimeError("Internet Explorer executable not found. Install/enable IE mode or use Edge.")
        raise RuntimeError(f"Browser executable not found for: {browser}")

    launched_pids: list[int] = []
    for i in range(count):
        args = [browser_exe]
        if browser in {"edge", "chrome"}:
            args.append("--new-window")
            if isolate_profiles:
                profile_dir = Path("cardbot/data/browser_profiles") / f"instance_{i}"
                profile_dir.mkdir(parents=True, exist_ok=True)
                args.append(f"--user-data-dir={profile_dir.absolute()}")
                
                if accounts and i < len(accounts):
                    from cardbot.tools.autologin_manager import generate_autologin_extension
                    ext_path = generate_autologin_extension(i, accounts[i])
                    if ext_path:
                        args.append(f"--load-extension={ext_path}")
        args.append(url)

        proc = subprocess.Popen(args)
        if proc.pid is not None:
            launched_pids.append(int(proc.pid))

    return launched_pids, browser


class StatusHandler(BaseHTTPRequestHandler):
    """HTTP handler serving static UI and status JSON."""

    status_dir: Path
    stale_seconds: float
    launched_browser_pids: set[int]

    def log_message(self, format: str, *args: object) -> None:
        """Reduce console noise; keep handler quiet by default."""
        return

    def _send_json(self, payload: dict[str, Any], status_code: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            return {}
        raw = self.rfile.read(content_length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self._send_html(HTML_PAGE)
            return

        if parsed.path == "/api/status":
            records = _read_status_files(self.status_dir)
            payload = _normalize_health(records, stale_seconds=self.stale_seconds)
            self._send_json(payload)
            return

        self._send_json({"error": "not found"}, status_code=404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)

        if parsed.path == "/api/launch-browsers":
            payload = self._read_json_body()
            url = str(payload.get("url", "")).strip()
            browser = str(payload.get("browser", "ie")).strip().lower()

            try:
                count = int(payload.get("count", 4))
            except (TypeError, ValueError):
                count = 4

            if not url.startswith(("http://", "https://")):
                self._send_json({"error": "URL must start with http:// or https://"}, status_code=400)
                return

            if count <= 0 or count > 12:
                self._send_json({"error": "Count must be between 1 and 12"}, status_code=400)
                return

            try:
                launched_pids, launched_browser = _launch_browser_windows(
                    url=url, count=count, browser=browser, isolate_profiles=False
                )
            except Exception as exc:
                self._send_json({"error": str(exc)}, status_code=500)
                return

            for pid in launched_pids:
                type(self).launched_browser_pids.add(pid)

            self._send_json(
                {
                    "ok": True,
                    "launched": count,
                    "browser": launched_browser,
                    "pids": launched_pids,
                }
            )
            return

        if parsed.path == "/api/stop-browsers":
            stopped = 0
            still_running: set[int] = set()
            for pid in type(self).launched_browser_pids:
                try:
                    os.kill(pid, 9)
                    stopped += 1
                except OSError:
                    still_running.add(pid)

            type(self).launched_browser_pids = still_running
            self._send_json({"ok": True, "stopped": stopped})
            return

        if parsed.path == "/api/feedback":
            payload = self._read_json_body()
            instance_id = payload.get("instance_id", "unknown")
            feedback_dir = type(self).status_dir.parent / "feedback"
            feedback_dir.mkdir(parents=True, exist_ok=True)
            
            ts = time.strftime("%Y%m%d_%H%M%S")
            filename = f"human_feedback_{ts}_{instance_id}.jsonl"
            file_path = feedback_dir / filename
            
            with file_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(payload, separators=(",", ":")) + "\n")
                
            self._send_json({"ok": True, "file": str(file_path.absolute())})
            return

        self._send_json({"error": "not found"}, status_code=404)


def main() -> None:
    """Run the status web dashboard server."""
    args = parse_args()

    status_dir = Path(args.status_dir)

    StatusHandler.status_dir = status_dir
    StatusHandler.stale_seconds = float(args.stale_seconds)
    StatusHandler.launched_browser_pids = set()

    server = ThreadingHTTPServer((args.host, args.port), StatusHandler)
    print(f"[STATUS-UI] Serving http://{args.host}:{args.port} status_dir={status_dir}")
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
