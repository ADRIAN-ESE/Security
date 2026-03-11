"""app.py — Main GUI application (Tkinter dark theme)."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import collections
import datetime

import collectors
import scanner as net_scanner
import history as hist
import exporters

# ── Palette ──────────────────────────────────────────────────────────────────
BG      = "#0d1117"
BG2     = "#161b22"
BG3     = "#21262d"
ACCENT  = "#00d68f"
ACCENT2 = "#388bfd"
TEXT    = "#e6edf3"
DIM     = "#8b949e"
RED     = "#f85149"
YELLOW  = "#d29922"
BORDER  = "#30363d"

FONT_MONO  = ("Courier New", 10)
FONT_MONO_S= ("Courier New", 9)
FONT_MONO_L= ("Courier New", 12, "bold")
FONT_HEAD  = ("Courier New", 11, "bold")


def _apply_theme(root: tk.Tk):
    s = ttk.Style(root)
    s.theme_use("clam")

    s.configure(".",              background=BG,  foreground=TEXT, font=FONT_MONO)
    s.configure("TFrame",         background=BG)
    s.configure("TLabelframe",    background=BG,  foreground=ACCENT, bordercolor=BORDER)
    s.configure("TLabelframe.Label", background=BG, foreground=ACCENT, font=FONT_HEAD)
    s.configure("TLabel",         background=BG,  foreground=TEXT)
    s.configure("Dim.TLabel",     background=BG,  foreground=DIM,  font=FONT_MONO_S)
    s.configure("Accent.TLabel",  background=BG,  foreground=ACCENT)
    s.configure("Red.TLabel",     background=BG,  foreground=RED)

    s.configure("TButton",
        background=BG3, foreground=TEXT, bordercolor=BORDER,
        focuscolor=BG3, relief="flat", font=FONT_MONO,
    )
    s.map("TButton",
        background=[("active", ACCENT2), ("pressed", ACCENT)],
        foreground=[("active", TEXT)],
    )
    s.configure("Accent.TButton",
        background=ACCENT, foreground="#000000", font=FONT_HEAD,
    )
    s.map("Accent.TButton", background=[("active", "#00ff9f")])

    s.configure("Red.TButton",
        background=RED, foreground=TEXT, font=FONT_MONO,
    )
    s.map("Red.TButton", background=[("active", "#ff6b63")])

    s.configure("TNotebook",        background=BG,  bordercolor=BORDER, tabmargins=[2,2,2,0])
    s.configure("TNotebook.Tab",
        background=BG2, foreground=DIM, font=FONT_MONO,
        padding=[14, 6],
    )
    s.map("TNotebook.Tab",
        background=[("selected", BG)],
        foreground=[("selected", ACCENT)],
    )

    s.configure("Treeview",
        background=BG2, foreground=TEXT, fieldbackground=BG2,
        rowheight=22, font=FONT_MONO_S,
    )
    s.configure("Treeview.Heading",
        background=BG3, foreground=ACCENT, font=FONT_HEAD, relief="flat",
    )
    s.map("Treeview", background=[("selected", ACCENT2)], foreground=[("selected", TEXT)])

    s.configure("TEntry",
        fieldbackground=BG2, foreground=TEXT, insertcolor=TEXT,
        bordercolor=BORDER, relief="flat",
    )
    s.configure("TScrollbar",
        background=BG3, troughcolor=BG, bordercolor=BORDER, arrowcolor=DIM,
    )
    s.configure("TProgressbar",
        background=ACCENT, troughcolor=BG2, bordercolor=BORDER,
    )
    s.configure("TSeparator", background=BORDER)
    s.configure("TCombobox",
        fieldbackground=BG2, foreground=TEXT, selectbackground=BG3,
        background=BG2,
    )


# ── Helpers ──────────────────────────────────────────────────────────────────

def _scrollable_tree(parent, columns, col_cfg, height=12):
    """Return (frame, tree) with auto scrollbars."""
    frame = ttk.Frame(parent)
    tree  = ttk.Treeview(frame, columns=columns, show="headings", height=height)
    vsb   = ttk.Scrollbar(frame, orient="vertical",   command=tree.yview)
    hsb   = ttk.Scrollbar(frame, orient="horizontal",  command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid( row=0, column=1, sticky="ns")
    hsb.grid( row=1, column=0, sticky="ew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    for col, (heading, width, anchor) in col_cfg.items():
        tree.heading(col, text=heading)
        tree.column(col, width=width, anchor=anchor, minwidth=40)
    return frame, tree


def _tag_row(tree, item, tags):
    tree.item(item, tags=tags)


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 1 — Dashboard
# ─────────────────────────────────────────────────────────────────────────────

class DashboardTab(ttk.Frame):
    HISTORY = 60  # seconds of live data

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self._cpu_history = collections.deque([0.0]*self.HISTORY, maxlen=self.HISTORY)
        self._ram_history = collections.deque([0.0]*self.HISTORY, maxlen=self.HISTORY)
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=1)

        # ── Top bar
        top = ttk.Frame(self)
        top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(12,4))
        ttk.Label(top, text="SYSTEM DASHBOARD", font=FONT_MONO_L, foreground=ACCENT).pack(side="left")
        self.ts_label = ttk.Label(top, text="", style="Dim.TLabel")
        self.ts_label.pack(side="right")

        # ── Info panes (left)
        left = ttk.Frame(self)
        left.grid(row=1, column=0, sticky="nsew", padx=(12,4), pady=4)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(3, weight=1)

        self._sys_tree_frame, self._sys_tree = _scrollable_tree(left,
            columns=("field","value"),
            col_cfg={"field":("Field",180,"w"), "value":("Value",320,"w")},
            height=8,
        )
        self._sys_tree_frame.grid(row=0, column=0, sticky="nsew", pady=(0,4))

        self._disk_frame, self._disk_tree = _scrollable_tree(left,
            columns=("device","mount","total","used","free","pct"),
            col_cfg={
                "device":("Device",130,"w"), "mount":("Mount",110,"w"),
                "total":("Total GB",70,"e"),  "used":("Used GB",70,"e"),
                "free":("Free GB",70,"e"),    "pct":("Usage %",70,"e"),
            },
            height=5,
        )
        ttk.Label(left, text="DISK PARTITIONS", foreground=ACCENT2, font=FONT_HEAD).grid(row=1, column=0, sticky="w", pady=(6,2))
        self._disk_frame.grid(row=2, column=0, sticky="nsew")

        self._net_frame, self._net_tree = _scrollable_tree(left,
            columns=("iface","status","mac","ip"),
            col_cfg={
                "iface":("Interface",100,"w"), "status":("Status",54,"center"),
                "mac":("MAC",140,"w"),         "ip":("IPs",240,"w"),
            },
            height=5,
        )
        ttk.Label(left, text="NETWORK INTERFACES", foreground=ACCENT2, font=FONT_HEAD).grid(row=3, column=0, sticky="sw", pady=(6,2))
        self._net_frame.grid(row=4, column=0, sticky="nsew")
        left.rowconfigure(4, weight=1)

        # ── Charts (right)
        right = ttk.Frame(self)
        right.grid(row=1, column=1, sticky="nsew", padx=(4,12), pady=4)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        right.rowconfigure(3, weight=1)

        ttk.Label(right, text="CPU USAGE (live)", foreground=ACCENT2, font=FONT_HEAD).grid(row=0, column=0, sticky="w")
        self._cpu_canvas = _SparkCanvas(right, self._cpu_history, ACCENT, "CPU %")
        self._cpu_canvas.grid(row=1, column=0, sticky="nsew", pady=(0,8))

        ttk.Label(right, text="RAM USAGE (live)", foreground=ACCENT2, font=FONT_HEAD).grid(row=2, column=0, sticky="w")
        self._ram_canvas = _SparkCanvas(right, self._ram_history, ACCENT2, "RAM %")
        self._ram_canvas.grid(row=3, column=0, sticky="nsew")

        # ── Metric badges
        badge_frame = ttk.Frame(right)
        badge_frame.grid(row=4, column=0, sticky="ew", pady=(8,0))
        for i in range(4):
            badge_frame.columnconfigure(i, weight=1)

        self._badge_cpu = _Badge(badge_frame, "CPU",  "—", ACCENT)
        self._badge_ram = _Badge(badge_frame, "RAM",  "—", ACCENT2)
        self._badge_ip  = _Badge(badge_frame, "IP",   "—", YELLOW)
        self._badge_loc = _Badge(badge_frame, "LOC",  "—", DIM)
        self._badge_cpu.grid(row=0, column=0, padx=2, sticky="ew")
        self._badge_ram.grid(row=0, column=1, padx=2, sticky="ew")
        self._badge_ip.grid( row=0, column=2, padx=2, sticky="ew")
        self._badge_loc.grid(row=0, column=3, padx=2, sticky="ew")

    # ── Public API called by App ─────────────────────────────────────────────

    def populate(self, report):
        s   = report.system
        cpu = report.cpu
        mem = report.memory
        geo = report.geo
        self.ts_label.config(text=f"Last scan: {report.generated_at}")

        # System tree
        self._sys_tree.delete(*self._sys_tree.get_children())
        rows = [
            ("Hostname",    s.hostname),
            ("OS",          f"{s.os_name} {s.os_release}"),
            ("Architecture",f"{s.architecture} / {s.machine}"),
            ("Processor",   (s.processor or "N/A")[:60]),
            ("Python",      s.python_version),
            ("User",        s.current_user),
            ("MAC Address", s.mac_address),
            ("Boot Time",   s.boot_time),
            ("CPU Cores",   f"{cpu.physical_cores}P / {cpu.logical_cores}L"),
            ("Max Freq",    f"{cpu.max_freq_mhz} MHz"),
        ]
        for field, val in rows:
            self._sys_tree.insert("", "end", values=(field, val))

        # Disk tree
        self._disk_tree.delete(*self._disk_tree.get_children())
        for d in report.disks:
            color = "warn" if d.percent_used > 85 else ""
            iid = self._disk_tree.insert("", "end", values=(
                d.device, d.mountpoint, d.total_gb, d.used_gb, d.free_gb, f"{d.percent_used}%"
            ))
            if color:
                self._disk_tree.item(iid, tags=("warn",))
        self._disk_tree.tag_configure("warn", foreground=RED)

        # Net tree
        self._net_tree.delete(*self._net_tree.get_children())
        for iface in report.interfaces:
            ips = " | ".join(iface.ip_addresses)
            iid = self._net_tree.insert("", "end", values=(
                iface.name,
                "UP" if iface.is_up else "DOWN",
                iface.mac_address or "—",
                ips or "—",
            ))
            tag = "up" if iface.is_up else "down"
            self._net_tree.item(iid, tags=(tag,))
        self._net_tree.tag_configure("up",   foreground=ACCENT)
        self._net_tree.tag_configure("down", foreground=RED)

        # Badges
        self._badge_cpu.set_value(f"{cpu.usage_percent}%")
        self._badge_ram.set_value(f"{mem.percent_used}%")
        self._badge_ip.set_value(geo.public_ip or "N/A")
        loc = f"{geo.city}, {geo.country_code}" if geo.city else "N/A"
        self._badge_loc.set_value(loc)

    def tick(self):
        """Called every second to update live charts."""
        try:
            import psutil
            self._cpu_history.append(psutil.cpu_percent())
            vm = psutil.virtual_memory()
            self._ram_history.append(vm.percent)
            self._badge_cpu.set_value(f"{self._cpu_history[-1]:.0f}%")
            self._badge_ram.set_value(f"{self._ram_history[-1]:.0f}%")
            self._cpu_canvas.redraw()
            self._ram_canvas.redraw()
        except Exception:
            pass


# ── Spark-line canvas ─────────────────────────────────────────────────────────

class _SparkCanvas(tk.Canvas):
    def __init__(self, master, data, color, label):
        super().__init__(master, bg=BG2, highlightthickness=0, height=90)
        self.data  = data
        self.color = color
        self.label = label
        self.bind("<Configure>", lambda e: self.redraw())

    def redraw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10:
            return
        pad = 8

        # Grid lines
        for pct in [25, 50, 75, 100]:
            y = h - pad - (pct / 100) * (h - pad*2)
            self.create_line(pad, y, w-pad, y, fill=BG3, dash=(2,4))
            self.create_text(pad+2, y-1, text=f"{pct}%", anchor="sw",
                             fill=DIM, font=("Courier New", 7))

        # Spark fill
        data = list(self.data)
        n = len(data)
        if n < 2:
            return
        dx = (w - pad*2) / (n - 1)
        pts = []
        for i, v in enumerate(data):
            x = pad + i * dx
            y = h - pad - (min(max(v,0),100) / 100) * (h - pad*2)
            pts.append((x, y))

        # Fill polygon
        poly = [pad, h-pad] + [c for p in pts for c in p] + [w-pad, h-pad]
        fill_color = _hex_darken(self.color, 0.25)
        self.create_polygon(poly, fill=fill_color, outline="")

        # Line
        flat = [c for p in pts for c in p]
        self.create_line(flat, fill=self.color, width=2, smooth=True)

        # Latest dot + value
        lx, ly = pts[-1]
        lv = data[-1]
        self.create_oval(lx-4, ly-4, lx+4, ly+4, fill=self.color, outline=BG2)
        self.create_text(w-pad-2, pad, text=f"{lv:.0f}%",
                         anchor="ne", fill=self.color, font=FONT_HEAD)
        self.create_text(pad+2, pad, text=self.label,
                         anchor="nw", fill=DIM, font=("Courier New", 8))


def _hex_darken(hex_color: str, alpha: float) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2],16), int(hex_color[2:4],16), int(hex_color[4:6],16)
    r2 = int(r * alpha + int(BG2[1:3],16) * (1-alpha))
    g2 = int(g * alpha + int(BG2[3:5],16) * (1-alpha))
    b2 = int(b * alpha + int(BG2[5:7],16) * (1-alpha))
    return f"#{r2:02x}{g2:02x}{b2:02x}"


# ── Metric badge ─────────────────────────────────────────────────────────────

class _Badge(ttk.Frame):
    def __init__(self, master, label, value, color):
        super().__init__(master, style="TFrame")
        self.config(relief="flat")
        inner = tk.Frame(self, bg=BG2, bd=0)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        tk.Label(inner, text=label, bg=BG2, fg=color,
                 font=("Courier New", 7, "bold")).pack(pady=(4,0))
        self._val = tk.Label(inner, text=value, bg=BG2, fg=TEXT,
                              font=("Courier New", 10, "bold"))
        self._val.pack(pady=(0,4))

    def set_value(self, v):
        self._val.config(text=str(v))


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 2 — Network Scanner
# ─────────────────────────────────────────────────────────────────────────────

class ScannerTab(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app       = app
        self._stop     = [False]
        self._scanning = False
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        ttk.Label(self, text="NETWORK SCANNER", font=FONT_MONO_L, foreground=ACCENT
                  ).grid(row=0, column=0, sticky="w", padx=12, pady=(12,4))

        # ── Controls
        ctrl = ttk.LabelFrame(self, text="Scan Configuration", padding=10)
        ctrl.grid(row=1, column=0, sticky="ew", padx=12, pady=4)
        ctrl.columnconfigure(1, weight=1)
        ctrl.columnconfigure(4, weight=1)

        ttk.Label(ctrl, text="Subnet:").grid(row=0, column=0, sticky="e", padx=(0,6))
        self._subnet_var = tk.StringVar(value=net_scanner.get_local_subnet())
        ttk.Entry(ctrl, textvariable=self._subnet_var, width=20).grid(row=0, column=1, sticky="w")

        ttk.Label(ctrl, text="Custom ports (comma-sep):").grid(row=0, column=2, sticky="e", padx=(12,6))
        self._ports_var = tk.StringVar(value="")
        ttk.Entry(ctrl, textvariable=self._ports_var, width=28).grid(row=0, column=3, sticky="w")

        btn_frame = ttk.Frame(ctrl)
        btn_frame.grid(row=0, column=4, sticky="e", padx=(12,0))
        self._scan_btn = ttk.Button(btn_frame, text="▶ Ping Sweep", style="Accent.TButton",
                                     command=self._start_ping)
        self._scan_btn.pack(side="left", padx=2)
        self._stop_btn = ttk.Button(btn_frame, text="■ Stop", style="Red.TButton",
                                     command=self._stop_scan, state="disabled")
        self._stop_btn.pack(side="left", padx=2)

        # ── Progress
        prog_row = ttk.Frame(self)
        prog_row.grid(row=2, column=0, sticky="ew", padx=12, pady=(0,4))
        prog_row.columnconfigure(0, weight=1)
        self._progress = ttk.Progressbar(prog_row, mode="determinate")
        self._progress.grid(row=0, column=0, sticky="ew")
        self._status_var = tk.StringVar(value="Ready.")
        ttk.Label(prog_row, textvariable=self._status_var, style="Dim.TLabel"
                  ).grid(row=1, column=0, sticky="w")

        # ── Host results
        hosts_lf = ttk.LabelFrame(self, text="Discovered Hosts", padding=4)
        hosts_lf.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0,4))
        hosts_lf.columnconfigure(0, weight=1)
        hosts_lf.rowconfigure(0, weight=1)
        self.rowconfigure(3, weight=2)

        hf, self._host_tree = _scrollable_tree(hosts_lf,
            columns=("ip","status","hostname","ms"),
            col_cfg={
                "ip":("IP Address",130,"w"), "status":("Status",70,"center"),
                "hostname":("Hostname",200,"w"), "ms":("Response ms",90,"e"),
            },
            height=10,
        )
        hf.pack(fill="both", expand=True)
        self._host_tree.bind("<<TreeviewSelect>>", self._on_host_select)

        scan_port_btn = ttk.Button(hosts_lf, text="⚡ Scan Ports on Selected Host",
                                    command=self._start_portscan)
        scan_port_btn.pack(pady=(4,0))

        # ── Port results
        ports_lf = ttk.LabelFrame(self, text="Open Ports", padding=4)
        ports_lf.grid(row=4, column=0, sticky="nsew", padx=12, pady=(0,12))
        ports_lf.columnconfigure(0, weight=1)
        ports_lf.rowconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

        pf, self._port_tree = _scrollable_tree(ports_lf,
            columns=("port","service","risk"),
            col_cfg={
                "port":("Port",80,"e"), "service":("Service",140,"w"),
                "risk":("Note",300,"w"),
            },
            height=6,
        )
        pf.pack(fill="both", expand=True)

        self._host_tree.tag_configure("alive", foreground=ACCENT)
        self._host_tree.tag_configure("dead",  foreground=BG3)
        self._port_tree.tag_configure("risk",  foreground=YELLOW)

    # ── Ping sweep ────────────────────────────────────────────────────────────

    def _start_ping(self):
        if self._scanning:
            return
        subnet = self._subnet_var.get().strip()
        self._host_tree.delete(*self._host_tree.get_children())
        self._port_tree.delete(*self._port_tree.get_children())
        self._stop[0] = False
        self._scanning = True
        self._scan_btn.config(state="disabled")
        self._stop_btn.config(state="normal")
        threading.Thread(target=self._ping_worker, args=(subnet,), daemon=True).start()

    def _ping_worker(self, subnet):
        try:
            hosts = net_scanner.ping_sweep(
                subnet,
                progress_cb=self._ping_progress,
                stop_flag=self._stop,
            )
            self.after(0, self._ping_done, hosts)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Scan Error", str(e)))
            self.after(0, self._scan_finished)

    def _ping_progress(self, done, total, ip):
        pct = int(done / total * 100)
        self.after(0, lambda: self._progress.config(value=pct))
        self.after(0, lambda: self._status_var.set(f"Scanning {ip}… {done}/{total}"))

    def _ping_done(self, hosts):
        alive = [h for h in hosts if h.is_alive]
        for h in hosts:
            tag = "alive" if h.is_alive else "dead"
            self._host_tree.insert("", "end", tags=(tag,), values=(
                h.ip,
                "ALIVE" if h.is_alive else "—",
                h.hostname or "—",
                f"{h.response_ms}" if h.is_alive else "—",
            ))
        self._status_var.set(f"Done. {len(alive)}/{len(hosts)} hosts alive.")
        self._progress.config(value=100)
        self._scan_finished()

    def _stop_scan(self):
        self._stop[0] = True
        self._status_var.set("Stopping…")

    def _scan_finished(self):
        self._scanning = False
        self._scan_btn.config(state="normal")
        self._stop_btn.config(state="disabled")

    # ── Port scan ─────────────────────────────────────────────────────────────

    RISK_NOTES = {
        21: "FTP — unencrypted; prefer SFTP",
        22: "SSH — ensure key auth, disable root",
        23: "Telnet — plaintext; disable immediately",
        3389: "RDP — frequent brute-force target",
        445: "SMB — common ransomware vector",
        3306: "MySQL — should not be public-facing",
        6379: "Redis — often left unauthenticated",
        27017: "MongoDB — often left unauthenticated",
        5900: "VNC — use strong passwords + tunneling",
    }

    def _on_host_select(self, _event=None):
        pass  # could pre-populate IP field

    def _start_portscan(self):
        sel = self._host_tree.selection()
        if not sel:
            messagebox.showinfo("Select Host", "Please select a host from the list first.")
            return
        ip = self._host_tree.item(sel[0])["values"][0]
        self._port_tree.delete(*self._port_tree.get_children())

        custom = self._ports_var.get().strip()
        if custom:
            try:
                ports = [int(p.strip()) for p in custom.split(",") if p.strip()]
            except ValueError:
                messagebox.showerror("Invalid ports", "Enter comma-separated integers.")
                return
        else:
            ports = list(net_scanner.COMMON_PORTS.keys())

        self._status_var.set(f"Scanning ports on {ip}…")
        self._scanning = True
        self._scan_btn.config(state="disabled")
        self._stop_btn.config(state="normal")
        threading.Thread(target=self._port_worker, args=(ip, ports), daemon=True).start()

    def _port_worker(self, ip, ports):
        try:
            open_ports = net_scanner.scan_ports(
                ip, ports,
                progress_cb=lambda d,t,p: self.after(
                    0, lambda: (self._progress.config(value=int(d/t*100)),
                                self._status_var.set(f"Port {p}… {d}/{t}"))
                ),
                stop_flag=self._stop,
            )
            self.after(0, self._port_done, ip, open_ports)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Port Scan Error", str(e)))
            self.after(0, self._scan_finished)

    def _port_done(self, ip, open_ports):
        for port, service in open_ports:
            note = self.RISK_NOTES.get(port, "")
            iid = self._port_tree.insert("", "end", values=(port, service, note))
            if note:
                self._port_tree.item(iid, tags=("risk",))
        self._status_var.set(f"{len(open_ports)} open port(s) found on {ip}.")
        self._progress.config(value=100)
        self._scan_finished()


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 3 — Geolocation & Map
# ─────────────────────────────────────────────────────────────────────────────

class GeoTab(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self._map_widget = None
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text="GEOLOCATION & MAP", font=FONT_MONO_L, foreground=ACCENT
                  ).grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(12,4))

        # ── Info panel (left)
        info_lf = ttk.LabelFrame(self, text="IP Intelligence", padding=8)
        info_lf.grid(row=1, column=0, sticky="nsew", padx=(12,4), pady=4)
        info_lf.columnconfigure(0, weight=1)

        fframe, self._geo_tree = _scrollable_tree(info_lf,
            columns=("field","value"),
            col_cfg={"field":("Field",140,"w"), "value":("Value",200,"w")},
            height=18,
        )
        fframe.pack(fill="both", expand=True)

        # Threat badges
        badge_row = ttk.Frame(info_lf)
        badge_row.pack(fill="x", pady=(8,0))
        badge_row.columnconfigure(0, weight=1)
        badge_row.columnconfigure(1, weight=1)
        self._proxy_badge = tk.Label(badge_row, text="PROXY: —", bg=BG3, fg=DIM,
                                      font=FONT_HEAD, padx=8, pady=4)
        self._proxy_badge.grid(row=0, column=0, sticky="ew", padx=(0,2))
        self._host_badge  = tk.Label(badge_row, text="HOSTING: —", bg=BG3, fg=DIM,
                                      font=FONT_HEAD, padx=8, pady=4)
        self._host_badge.grid(row=0, column=1, sticky="ew", padx=(2,0))

        # ── Map panel (right)
        map_lf = ttk.LabelFrame(self, text="Map", padding=4)
        map_lf.grid(row=1, column=1, sticky="nsew", padx=(4,12), pady=4)
        map_lf.columnconfigure(0, weight=1)
        map_lf.rowconfigure(0, weight=1)

        self._map_container = map_lf
        self._map_placeholder = tk.Label(
            map_lf, text="Map will appear here after scan.\n\n(Requires: pip install tkintermapview)",
            bg=BG2, fg=DIM, font=FONT_MONO, justify="center",
        )
        self._map_placeholder.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

    def populate(self, report):
        g = report.geo
        self._geo_tree.delete(*self._geo_tree.get_children())
        rows = [
            ("Public IP",    g.public_ip or g.error or "N/A"),
            ("Country",      f"{g.country} ({g.country_code})"),
            ("Region",       g.region),
            ("City",         g.city),
            ("ZIP Code",     g.zip_code),
            ("Latitude",     str(g.latitude)),
            ("Longitude",    str(g.longitude)),
            ("Timezone",     g.timezone),
            ("ISP",          g.isp),
            ("Organization", g.org),
            ("ASN",          g.asn),
        ]
        for field, val in rows:
            self._geo_tree.insert("", "end", values=(field, val or "—"))

        # Threat badges
        if g.is_proxy:
            self._proxy_badge.config(text="⚠ PROXY / VPN", bg=RED, fg=TEXT)
        else:
            self._proxy_badge.config(text="✓ No Proxy",    bg=BG3, fg=ACCENT)
        if g.is_hosting:
            self._host_badge.config(text="⚠ HOSTING / DC", bg=YELLOW, fg="#000")
        else:
            self._host_badge.config(text="✓ No Hosting",   bg=BG3, fg=ACCENT)

        # Map
        self._try_show_map(g.latitude, g.longitude, g.city, g.country)

    def _try_show_map(self, lat, lon, city, country):
        if not lat and not lon:
            return
        try:
            import tkintermapview
            if self._map_widget is None:
                self._map_placeholder.grid_forget()
                self._map_widget = tkintermapview.TkinterMapView(
                    self._map_container, width=500, height=380, corner_radius=0
                )
                self._map_widget.grid(row=0, column=0, sticky="nsew")
            self._map_widget.set_position(lat, lon)
            self._map_widget.set_zoom(10)
            label = f"{city}, {country}" if city else f"{lat}, {lon}"
            self._map_widget.set_marker(lat, lon, text=label)
        except ImportError:
            self._map_placeholder.config(
                text=f"Map not available\n(pip install tkintermapview)\n\nCoordinates:\nLat {lat}\nLon {lon}"
            )
        except Exception as e:
            self._map_placeholder.config(text=f"Map error:\n{e}")


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 4 — History & Comparison
# ─────────────────────────────────────────────────────────────────────────────

class HistoryTab(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self._history = []
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(3, weight=2)

        ttk.Label(self, text="SCAN HISTORY & COMPARISON", font=FONT_MONO_L, foreground=ACCENT
                  ).grid(row=0, column=0, sticky="w", padx=12, pady=(12,4))

        # ── History list
        hist_lf = ttk.LabelFrame(self, text="Saved Scans", padding=4)
        hist_lf.grid(row=1, column=0, sticky="nsew", padx=12, pady=4)
        hist_lf.columnconfigure(0, weight=1)
        hist_lf.rowconfigure(0, weight=1)

        hf, self._hist_tree = _scrollable_tree(hist_lf,
            columns=("ts","hostname","ip","city","country"),
            col_cfg={
                "ts":("Timestamp",160,"w"),  "hostname":("Hostname",130,"w"),
                "ip":("Public IP",120,"w"),  "city":("City",100,"w"),
                "country":("Country",80,"w"),
            },
            height=6,
        )
        hf.grid(row=0, column=0, sticky="nsew")

        btn_row = ttk.Frame(hist_lf)
        btn_row.grid(row=1, column=0, sticky="ew", pady=(6,0))
        ttk.Button(btn_row, text="🔃 Refresh",        command=self.refresh).pack(side="left",  padx=2)
        ttk.Button(btn_row, text="⚖ Compare Selected (2)", command=self._compare).pack(side="left", padx=2)
        ttk.Button(btn_row, text="🗑 Delete Selected", command=self._delete).pack(side="left",  padx=2)
        ttk.Button(btn_row, text="🗑 Clear All",       command=self._clear_all, style="Red.TButton").pack(side="right", padx=2)

        # ── Diff panel
        diff_lf = ttk.LabelFrame(self, text="Comparison (changed fields highlighted)", padding=4)
        diff_lf.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0,12))
        diff_lf.columnconfigure(0, weight=1)
        diff_lf.rowconfigure(0, weight=1)

        df, self._diff_tree = _scrollable_tree(diff_lf,
            columns=("field","scan_a","scan_b"),
            col_cfg={
                "field":("Field",220,"w"),
                "scan_a":("Scan A (older)",260,"w"),
                "scan_b":("Scan B (newer)",260,"w"),
            },
            height=12,
        )
        df.pack(fill="both", expand=True)
        self._diff_tree.tag_configure("changed",   foreground=YELLOW)
        self._diff_tree.tag_configure("unchanged", foreground=DIM)

    def refresh(self):
        self._history = hist.load_history()
        self._hist_tree.delete(*self._hist_tree.get_children())
        for rpt in self._history:
            s = rpt.get("system", {})
            g = rpt.get("geo", {})
            self._hist_tree.insert("", "end", values=(
                rpt.get("generated_at",""),
                s.get("hostname",""),
                g.get("public_ip",""),
                g.get("city",""),
                g.get("country",""),
            ))

    def _compare(self):
        sel = self._hist_tree.selection()
        if len(sel) != 2:
            messagebox.showinfo("Select Two", "Hold Ctrl and select exactly 2 scans.")
            return
        idx_a = self._hist_tree.index(sel[0])
        idx_b = self._hist_tree.index(sel[1])
        if idx_a > idx_b:
            idx_a, idx_b = idx_b, idx_a
        rpt_a = self._history[idx_a]
        rpt_b = self._history[idx_b]
        diffs = hist.compare_reports(rpt_a, rpt_b)
        self._diff_tree.delete(*self._diff_tree.get_children())
        for d in diffs:
            tag = "changed" if d["changed"] else "unchanged"
            self._diff_tree.insert("", "end", tags=(tag,), values=(
                d["field"], d["old"], d["new"]
            ))

    def _delete(self):
        sel = self._hist_tree.selection()
        if not sel:
            return
        for item in reversed(sel):
            idx = self._hist_tree.index(item)
            hist.delete_scan(idx)
        self.refresh()

    def _clear_all(self):
        if messagebox.askyesno("Clear History", "Delete all saved scans?"):
            hist.clear_history()
            self.refresh()
            self._diff_tree.delete(*self._diff_tree.get_children())


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────────────────────────────────────

class SysInfoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SysInfo & Geolocation Extractor")
        self.geometry("1100x760")
        self.minsize(900, 600)
        self.configure(bg=BG)
        _apply_theme(self)

        self._report     = None
        self._report_dict= None
        self._scanning   = False
        self._live_job   = None

        self._build_header()
        self._build_tabs()
        self._build_status_bar()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._start_live_refresh()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = tk.Frame(self, bg=BG2, bd=0)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⚙  SYSINFO & GEOLOCATION EXTRACTOR",
                  bg=BG2, fg=ACCENT, font=("Courier New", 14, "bold"),
                  padx=14, pady=8).pack(side="left")

        btn_row = tk.Frame(hdr, bg=BG2)
        btn_row.pack(side="right", padx=10)

        tk.Button(btn_row, text="▶ Run Full Scan", bg=ACCENT, fg="#000000",
                   font=FONT_HEAD, relief="flat", padx=12, pady=4,
                   cursor="hand2", command=self._run_scan).pack(side="left", padx=4)

        export_menu_btn = tk.Menubutton(
            btn_row, text="⬇ Export ▾", bg=BG3, fg=TEXT,
            font=FONT_MONO, relief="flat", padx=10, pady=4, cursor="hand2",
        )
        export_menu = tk.Menu(export_menu_btn, tearoff=0, bg=BG3, fg=TEXT,
                               activebackground=ACCENT2, activeforeground=TEXT,
                               font=FONT_MONO)
        export_menu.add_command(label="Export HTML",  command=lambda: self._export("html"))
        export_menu.add_command(label="Export CSV",   command=lambda: self._export("csv"))
        export_menu.add_command(label="Export PDF",   command=lambda: self._export("pdf"))
        export_menu_btn["menu"] = export_menu
        export_menu_btn.pack(side="left", padx=4)

        tk.Frame(hdr, bg=BORDER, width=1).pack(side="right", fill="y", pady=4, padx=4)

    def _build_tabs(self):
        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True, padx=0, pady=0)

        self._dash    = DashboardTab(self._nb, self)
        self._scanner = ScannerTab(self._nb, self)
        self._geo     = GeoTab(self._nb, self)
        self._history = HistoryTab(self._nb, self)

        self._nb.add(self._dash,    text="  📊 Dashboard  ")
        self._nb.add(self._scanner, text="  🔍 Scanner  ")
        self._nb.add(self._geo,     text="  🌍 Geo / Map  ")
        self._nb.add(self._history, text="  📋 History  ")

    def _build_status_bar(self):
        sb = tk.Frame(self, bg=BG3, height=24)
        sb.pack(fill="x", side="bottom")
        self._status_var = tk.StringVar(value="Ready — click ▶ Run Full Scan to begin.")
        tk.Label(sb, textvariable=self._status_var, bg=BG3, fg=DIM,
                  font=("Courier New", 9), padx=8).pack(side="left")
        self._scan_indicator = tk.Label(sb, text="●", bg=BG3, fg=BG3,
                                         font=("Courier New", 12))
        self._scan_indicator.pack(side="right", padx=8)

    # ── Scan ─────────────────────────────────────────────────────────────────

    def _run_scan(self):
        if self._scanning:
            return
        self._scanning = True
        self._scan_indicator.config(fg=YELLOW)
        self._status_var.set("Scanning… collecting system info & geolocation…")
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        try:
            report      = collectors.build_report()
            report_dict = collectors.report_to_dict(report)
            hist.save_scan(report_dict)
            self.after(0, self._scan_done, report, report_dict)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Scan Error", str(e)))
            self.after(0, self._scan_finish)

    def _scan_done(self, report, report_dict):
        self._report      = report
        self._report_dict = report_dict
        self._dash.populate(report)
        self._geo.populate(report)
        self._history.refresh()
        self._status_var.set(f"Scan complete — {report.generated_at}  |  "
                              f"IP: {report.geo.public_ip}  |  {report.geo.city}, {report.geo.country}")
        self._scan_finish()

    def _scan_finish(self):
        self._scanning = False
        self._scan_indicator.config(fg=ACCENT)

    # ── Live refresh ──────────────────────────────────────────────────────────

    def _start_live_refresh(self):
        self._dash.tick()
        self._live_job = self.after(1000, self._start_live_refresh)

    # ── Export ───────────────────────────────────────────────────────────────

    def _export(self, fmt: str):
        if not self._report_dict:
            messagebox.showinfo("No Data", "Run a scan first.")
            return
        ts    = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        exts  = {"html": ".html", "csv": ".csv", "pdf": ".pdf"}
        types = {
            "html": [("HTML files","*.html")],
            "csv":  [("CSV files","*.csv")],
            "pdf":  [("PDF files","*.pdf")],
        }
        path = filedialog.asksaveasfilename(
            defaultextension=exts[fmt],
            filetypes=types[fmt],
            initialfile=f"sysinfo_report_{ts}{exts[fmt]}",
        )
        if not path:
            return
        try:
            if fmt == "html":
                exporters.export_html(self._report_dict, path)
            elif fmt == "csv":
                exporters.export_csv(self._report_dict, path)
            elif fmt == "pdf":
                exporters.export_pdf(self._report_dict, path)
            self._status_var.set(f"Exported {fmt.upper()} → {path}")
            messagebox.showinfo("Export Successful", f"Report saved to:\n{path}")
        except ImportError as e:
            messagebox.showerror("Missing Library", str(e))
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    # ── Close ─────────────────────────────────────────────────────────────────

    def _on_close(self):
        if self._live_job:
            self.after_cancel(self._live_job)
        self.destroy()
