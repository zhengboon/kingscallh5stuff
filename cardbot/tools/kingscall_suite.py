"""Unified data capture suite and dashboard for KingsCall H5.

Features a multi-tab tkinter interface for:
- Launching game clients
- Live session recording (screenshots/logs)
- Browsing decoded game data tables
- Viewing recorded session stats
- Monitoring multi-instance runtime health
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any

# Import status_ui
try:
    from cardbot.tools.status_ui import _launch_browser_windows, _read_status_files, _normalize_health
except ImportError as exc:
    print(f"Warning: Failed to import status_ui: {exc}")
    _launch_browser_windows = None
    _read_status_files = None
    _normalize_health = None

# Import session_recorder
try:
    from cardbot.tools.session_recorder import SessionRecorder
except ImportError as exc:
    print(f"Warning: Failed to import session_recorder: {exc}")
    SessionRecorder = None

# Import session_summary
try:
    from cardbot.tools.session_summary import iter_logs, summarize_file
except ImportError as exc:
    print(f"Warning: Failed to import session_summary: {exc}")
    iter_logs = None
    summarize_file = None

# Import input_controller
try:
    from cardbot.controller.input_controller import InputController
except ImportError as exc:
    print(f"Warning: Failed to import input_controller: {exc}")
    InputController = None


class KingsCallSuite(tk.Tk):
    """Main application window for the data capture suite."""

    def __init__(self) -> None:
        super().__init__()
        self.title("KingsCall H5 Data Capture Suite")
        self.geometry("1100x750")
        self.configure(bg="#0f172a")

        self._setup_styles()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self._init_launcher_tab()
        self._init_capture_tab()
        self._init_data_browser_tab()
        self._init_session_viewer_tab()
        self._init_status_tab()

        # State for live capture
        self.recorder: SessionRecorder | None = None
        self.launched_pids: set[int] = set()
        
        # Periodic refresh
        self.after(1000, self._tick)

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        
        # Dark theme colors
        bg_color = "#0f172a"
        panel_color = "#1e293b"
        text_color = "#e2e8f0"
        accent_color = "#3b82f6"
        
        style.configure(".", background=bg_color, foreground=text_color, troughcolor=panel_color)
        style.configure("TNotebook", background=bg_color, borderwidth=0)
        style.configure("TNotebook.Tab", background=panel_color, foreground=text_color, padding=[10, 5], font=("Segoe UI", 10))
        style.map("TNotebook.Tab", background=[("selected", accent_color)])
        
        style.configure("TFrame", background=bg_color)
        style.configure("Panel.TFrame", background=panel_color, borderwidth=1, relief="solid")
        
        style.configure("TLabel", background=bg_color, foreground=text_color, font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), padding=(0, 10))
        
        style.configure("TButton", background="#334155", foreground=text_color, font=("Segoe UI", 10), padding=5)
        style.map("TButton", background=[("active", accent_color)])
        
        style.configure("Primary.TButton", background=accent_color)
        style.configure("Danger.TButton", background="#ef4444")
        style.configure("Warning.TButton", background="#facc15", foreground="#1e293b")
        
        style.configure("Treeview", background=panel_color, foreground=text_color, fieldbackground=panel_color, borderwidth=0)
        style.map("Treeview", background=[("selected", accent_color)])
        style.configure("Treeview.Heading", background="#334155", foreground=text_color, font=("Segoe UI", 9, "bold"))

    # --- Tab 1: Game Launcher ---
    def _init_launcher_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=" Game Launcher ")
        
        ttk.Label(tab, text="Launch Game Clients", style="Header.TLabel").pack(anchor=tk.W, padx=20, pady=(10, 0))
        
        panel = ttk.Frame(tab, style="Panel.TFrame", padding=20)
        panel.pack(fill=tk.X, padx=20, pady=10)
        
        # URL
        ttk.Label(panel, text="Target URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar(value="https://www.xstargame.com/game/server/game/id/4")
        ttk.Entry(panel, textvariable=self.url_var, width=60).grid(row=0, column=1, columnspan=3, sticky=tk.W, padx=10, pady=5)
        
        # Browser & Count
        ttk.Label(panel, text="Browser:").grid(row=1, column=0, sticky=tk.W, pady=10)
        self.browser_var = tk.StringVar(value="chrome")
        browsers = [("Internet Explorer (Native)", "ie"), ("Edge", "edge"), ("Chrome", "chrome"), ("Default", "default")]
        cb = ttk.Combobox(panel, textvariable=self.browser_var, values=[b[0] for b in browsers], state="readonly", width=30)
        cb.grid(row=1, column=1, sticky=tk.W, padx=10, pady=10)
        cb.set("Chrome")
        
        ttk.Label(panel, text="Instances:").grid(row=1, column=2, sticky=tk.W, padx=(20, 0))
        self.count_var = tk.IntVar(value=1)
        ttk.Spinbox(panel, from_=1, to=12, textvariable=self.count_var, width=5).grid(row=1, column=3, sticky=tk.W, padx=10)
        
        self.isolate_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(panel, text="Create Isolated Profiles", variable=self.isolate_var).grid(row=1, column=4, sticky=tk.W, padx=15)
        
        # Accounts
        ttk.Label(panel, text="Accounts (user:pass, line matches instance):").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.accounts_txt = tk.Text(panel, height=4, width=40)
        self.accounts_txt.grid(row=2, column=1, columnspan=3, sticky=tk.W, pady=(10, 0), padx=10)
        acc_file = Path("cardbot/data/accounts.txt")
        if acc_file.exists():
            self.accounts_txt.insert("1.0", acc_file.read_text(encoding="utf-8"))
        
        acc_btn_frame = ttk.Frame(panel, style="Panel.TFrame")
        acc_btn_frame.grid(row=2, column=4, sticky=tk.W, padx=10)
        ttk.Button(acc_btn_frame, text="Save Backup", command=self._backup_accounts).pack(pady=2)
        ttk.Button(acc_btn_frame, text="Load Backup", command=self._restore_accounts).pack(pady=2)
        ttk.Button(acc_btn_frame, text="Macro Login (3s)", style="Warning.TButton", command=self._do_macro_login).pack(pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(panel, style="Panel.TFrame")
        btn_frame.grid(row=3, column=0, columnspan=5, sticky=tk.W, pady=20)
        
        ttk.Button(btn_frame, text="Launch Windows", style="Primary.TButton", command=self._do_launch).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Stop Launched Windows", style="Danger.TButton", command=self._do_stop_browsers).pack(side=tk.LEFT, padx=5)
        
        self.launch_status_var = tk.StringVar(value="Ready.")
        ttk.Label(panel, textvariable=self.launch_status_var).grid(row=3, column=0, columnspan=4, sticky=tk.W)

    def _get_browser_code(self) -> str:
        # Match display text to internal code
        bmap = {"Internet Explorer (Native)": "ie", "Edge": "edge", "Chrome": "chrome"}
        return bmap.get(self.browser_var.get(), "default")

    def _do_launch(self) -> None:
        if _launch_browser_windows is None:
            messagebox.showerror("Error", "launch logic not imported.")
            return

        # Save accounts to disk
        raw_accs = self.accounts_txt.get("1.0", tk.END).strip()
        acc_path = Path("cardbot/data/accounts.txt")
        acc_path.parent.mkdir(parents=True, exist_ok=True)
        acc_path.write_text(raw_accs, encoding="utf-8")
        
        accounts = [l.strip() for l in raw_accs.splitlines() if l.strip()]

        try:
            pids, browser = _launch_browser_windows(
                url=self.url_var.get(), 
                count=self.count_var.get(), 
                browser=self._get_browser_code(),
                isolate_profiles=self.isolate_var.get(),
                accounts=accounts
            )
            self.launched_pids.update(pids)
            self.launch_status_var.set(f"Successfully launched {len(pids)} windows using {browser}.")
        except Exception as exc:
            self.launch_status_var.set(f"Launch failed: {exc}")

    def _backup_accounts(self) -> None:
        raw = self.accounts_txt.get("1.0", tk.END).strip()
        if not raw: return
        Path("cardbot/data/accounts_backup.txt").write_text(raw, encoding="utf-8")
        messagebox.showinfo("Backup", "Accounts backed up to cardbot/data/accounts_backup.txt")

    def _restore_accounts(self) -> None:
        bp = Path("cardbot/data/accounts_backup.txt")
        if not bp.exists():
            messagebox.showwarning("Restore", "No backup file found.")
            return
        self.accounts_txt.delete("1.0", tk.END)
        self.accounts_txt.insert("1.0", bp.read_text(encoding="utf-8"))

    def _do_macro_login(self) -> None:
        """Fallback: types credentials into currently focused window after a delay."""
        if InputController is None:
            messagebox.showerror("Error", "InputController module not found.")
            return

        raw = self.accounts_txt.get("1.0", tk.END).strip()
        accounts = [l.strip() for l in raw.splitlines() if l.strip()]
        if not accounts:
            messagebox.showwarning("Macro", "No accounts entered.")
            return
        
        # Use first account as default for macro
        user_pass = accounts[0]
        if ":" not in user_pass:
            messagebox.showwarning("Macro", "First account is not in user:pass format.")
            return
        user, pw = user_pass.split(":", 1)

        def run_macro():
            ctrl = InputController()
            ctrl.type_text(user)
            ctrl.type_tab()
            ctrl.type_text(pw)
            ctrl.type_enter()
            self.launch_status_var.set("Macro login complete.")

        self.launch_status_var.set("Macro starting in 3 seconds... FOCUS YOUR BROWSER NOW!")
        self.after(3000, run_macro)

    def _do_stop_browsers(self) -> None:
        stopped = 0
        still_running = set()
        for pid in self.launched_pids:
            try:
                os.kill(pid, 9)
                stopped += 1
            except OSError:
                still_running.add(pid)
        self.launched_pids = still_running
        self.launch_status_var.set(f"Stopped {stopped} launched processes.")

    # --- Tab 2: Live Data Capture ---
    def _init_capture_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=" Live Data Capture ")
        
        ttk.Label(tab, text="Session Recorder (Screenshots & Logs)", style="Header.TLabel").pack(anchor=tk.W, padx=20, pady=(10, 0))
        
        ctrl_frame = ttk.Frame(tab, style="Panel.TFrame", padding=15)
        ctrl_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.btn_start_cap = ttk.Button(ctrl_frame, text="Start Recording", style="Primary.TButton", command=self._toggle_capture)
        self.btn_start_cap.pack(side=tk.LEFT, padx=5)
        
        self.cap_status_var = tk.StringVar(value="Idle. Press Start to record screen frames.")
        ttk.Label(ctrl_frame, textvariable=self.cap_status_var).pack(side=tk.LEFT, padx=15)
        
        # Log viewer
        log_frame = ttk.Frame(tab, padding=20)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.capture_log_txt = tk.Text(log_frame, bg="#1e293b", fg="#e2e8f0", font=("Consolas", 10), state=tk.DISABLED)
        scroll = ttk.Scrollbar(log_frame, command=self.capture_log_txt.yview)
        self.capture_log_txt.configure(yscrollcommand=scroll.set)
        
        self.capture_log_txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _toggle_capture(self) -> None:
        if SessionRecorder is None:
            messagebox.showerror("Error", "SessionRecorder module not found.")
            return

        if self.recorder and self.recorder.is_running:
            # STOP
            summary = self.recorder.stop()
            self.btn_start_cap.config(text="Start Recording", style="Primary.TButton")
            self.cap_status_var.set(f"Saved session to {summary.get('session_dir')} ({summary.get('frames_captured')} frames).")
            self.recorder = None
        else:
            # START
            self.recorder = SessionRecorder(interval=2.0)
            try:
                out_dir = self.recorder.start()
                self.btn_start_cap.config(text="Stop Recording", style="Danger.TButton")
                self.cap_status_var.set(f"Recording to {out_dir}...")
                
                self.capture_log_txt.config(state=tk.NORMAL)
                self.capture_log_txt.delete(1.0, tk.END)
                self.capture_log_txt.config(state=tk.DISABLED)
            except Exception as e:
                messagebox.showerror("Recorder Error", str(e))
                self.recorder = None

    def _update_capture_logs(self) -> None:
        if not self.recorder:
            return
        
        lines = self.recorder.log_lines
        if not lines:
            return
            
        self.capture_log_txt.config(state=tk.NORMAL)
        self.capture_log_txt.delete(1.0, tk.END)
        self.capture_log_txt.insert(tk.END, "\n".join(lines[-50:])) # show last 50 lines
        self.capture_log_txt.see(tk.END)
        self.capture_log_txt.config(state=tk.DISABLED)
        
        if self.recorder.is_running:
            self.cap_status_var.set(f"Recording... {self.recorder.frame_count} frames captured.")

    # --- Tab 3: APK Data Browser ---
    def _init_data_browser_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=" APK Data Browser ")
        
        top = ttk.Frame(tab)
        top.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left: Table list
        left = ttk.Frame(top, width=250)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left.pack_propagate(False)
        
        ttk.Label(left, text="Game Tables", style="Header.TLabel").pack(anchor=tk.W)
        
        self.table_list = tk.Listbox(left, bg="#1e293b", fg="#e2e8f0", font=("Segoe UI", 10), selectbackground="#3b82f6", borderwidth=0)
        self.table_list.pack(fill=tk.BOTH, expand=True)
        self.table_list.bind("<<ListboxSelect>>", self._on_table_select)
        
        # Right: Data View
        right = ttk.Frame(top)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(right, text="Table Contents", style="Header.TLabel").pack(anchor=tk.W)
        
        # Treeview for records
        scroll_y = ttk.Scrollbar(right)
        scroll_x = ttk.Scrollbar(right, orient=tk.HORIZONTAL)
        self.data_tree = ttk.Treeview(right, yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set, selectmode="browse")
        scroll_y.config(command=self.data_tree.yview)
        scroll_x.config(command=self.data_tree.xview)
        
        self.data_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load tables
        self.table_data_path = Path("analysis/kingscall_data_pack/raw")
        if self.table_data_path.exists():
            for f in sorted(self.table_data_path.glob("*.json")):
                self.table_list.insert(tk.END, f.stem)

    def _on_table_select(self, event: Any) -> None:
        sel = self.table_list.curselection()
        if not sel:
            return
        
        t_name = self.table_list.get(sel[0])
        fpath = self.table_data_path / f"{t_name}.json"
        
        try:
            data = json.loads(fpath.read_text("utf-8"))
            self._populate_tree(data)
        except Exception as e:
            messagebox.showerror("Parse Error", str(e))

    def _populate_tree(self, data: list[dict[str, Any]] | dict[str, Any]) -> None:
        self.data_tree.delete(*self.data_tree.get_children())
        self.data_tree["columns"] = ()
        
        if isinstance(data, dict):
            # Convert dict to list of KV
            data = [{"key": k, "value": v} for k, v in data.items()]
            
        if not data or not isinstance(data, list) or not isinstance(data[0], dict):
            # Just show raw JSON
            self.data_tree["columns"] = ("Content",)
            self.data_tree.heading("Content", text="Content")
            self.data_tree.column("Content", width=800)
            self.data_tree.insert("", "end", values=(json.dumps(data, ensure_ascii=False)[:1000],))
            return
            
        # Get headers from first few items
        headers = set()
        for item in data[:10]:
            headers.update(item.keys())
        cols = sorted(list(headers))
        
        self.data_tree["columns"] = cols
        self.data_tree["show"] = "headings"
        for c in cols:
            self.data_tree.heading(c, text=c)
            self.data_tree.column(c, width=max(100, min(800 // len(cols), 250)))
            
        for i, row in enumerate(data[:1000]): # Cap at 1000 rows for performance
            vals = [str(row.get(c, "")) for c in cols]
            self.data_tree.insert("", "end", values=vals)

    # --- Tab 4: Session Viewer ---
    def _init_session_viewer_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=" Session Viewer ")
        
        ttk.Label(tab, text="Parse & Summarize JSONL Sessions", style="Header.TLabel").pack(anchor=tk.W, padx=20, pady=(10, 0))
        
        ctrl_frame = ttk.Frame(tab, style="Panel.TFrame", padding=15)
        ctrl_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(ctrl_frame, text="Load / Refresh Sessions", style="Primary.TButton", command=self._load_sessions).pack(side=tk.LEFT)
        
        self.sess_txt = tk.Text(tab, bg="#1e293b", fg="#e2e8f0", font=("Consolas", 10))
        self.sess_txt.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
    def _load_sessions(self) -> None:
        if iter_logs is None or summarize_file is None:
            self.sess_txt.insert(tk.END, "cardbot.tools.session_summary not imported.\n")
            return
            
        sdir = Path("cardbot/data/sessions")
        if not sdir.exists():
            self.sess_txt.delete(1.0, tk.END)
            self.sess_txt.insert(tk.END, f"Directory not found: {sdir}\n")
            return
            
        logs = list(iter_logs(sdir))
        if not logs:
            self.sess_txt.delete(1.0, tk.END)
            self.sess_txt.insert(tk.END, "No session logs found.\n")
            return
            
        lines = []
        for file_path in logs:
            summary = summarize_file(file_path)
            lines.append(json.dumps(summary, indent=2))
        
        report = "\n\n".join(lines)
        
        self.sess_txt.delete(1.0, tk.END)
        self.sess_txt.insert(tk.END, report)

    # --- Tab 5: Status Dashboard ---
    def _init_status_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=" Runtime Status ")
        
        ttk.Label(tab, text="Per-Instance Health Dashboard", style="Header.TLabel").pack(anchor=tk.W, padx=20, pady=(10, 0))
        
        self.status_container = ttk.Frame(tab)
        self.status_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.cards: list[ttk.Frame] = []

    def _refresh_status(self) -> None:
        if _read_status_files is None:
            return
            
        st_dir = Path("cardbot/data/runtime_status")
        records = _read_status_files(st_dir)
        payload = _normalize_health(records, stale_seconds=3.0)
        
        # Clear old
        for widget in self.status_container.winfo_children():
            widget.destroy()
            
        instances = payload.get("instances", [])
        if not instances:
            ttk.Label(self.status_container, text="No runtime status files found. Launch bot instances to see them here.").pack()
            return

        # Build grid
        for i, inst in enumerate(instances):
            card = ttk.Frame(self.status_container, style="Panel.TFrame", padding=15)
            card.grid(row=i // 2, column=i % 2, padx=10, pady=10, sticky="nsew")
            self.status_container.columnconfigure(i % 2, weight=1)
            
            top = ttk.Frame(card, style="Panel.TFrame")
            top.pack(fill=tk.X, pady=(0, 10))
            
            ttk.Label(top, text=f"Instance {inst.get('instance_id', '?')}", font=("Segoe UI", 12, "bold"), background="#1e293b").pack(side=tk.LEFT)
            
            health = inst.get("health", "UNKNOWN")
            color = "#16a34a" if health == "RUNNING" else "#d97706" if health == "STALE" else "#b91c1c"
            l = tk.Label(top, text=f" {health} ", bg=color, fg="white", font=("Segoe UI", 9, "bold"))
            l.pack(side=tk.RIGHT)
            
            ttk.Label(card, text=f"PID: {inst.get('pid', '-')}", background="#1e293b").pack(anchor=tk.W)
            ttk.Label(card, text=f"FPS: {inst.get('fps', 0):.1f}", background="#1e293b").pack(anchor=tk.W)
            ttk.Label(card, text=f"Frames: {inst.get('frame_count', 0)}", background="#1e293b").pack(anchor=tk.W)
            try:
                dt = time.strftime('%H:%M:%S', time.localtime(inst.get('updated_at', 0)))
            except:
                dt = "-"
            ttk.Label(card, text=f"Last Beat: {dt} ({inst.get('age_sec', 0)}s ago)", background="#1e293b").pack(anchor=tk.W)

    # --- Main Loop ---
    def _tick(self) -> None:
        if self.notebook.index("current") == 4: # Status tab
            self._refresh_status()
        elif self.notebook.index("current") == 1: # Capture tab
            self._update_capture_logs()
            
        self.after(1000, self._tick)


def main() -> None:
    app = KingsCallSuite()
    app.mainloop()


if __name__ == "__main__":
    main()
