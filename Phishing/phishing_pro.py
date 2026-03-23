#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║   PHISHING AWARENESS SIMULATOR  —  Professional Edition  v3.0   ║
║   Pure stdlib · Python 3.9+  ·  No pip installs needed          ║
╚══════════════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk
import platform, random, time, math
from dataclasses import dataclass, field
from typing import Optional, Callable

# ═══════════════════════════════════════════════════════════════════
#  DESIGN SYSTEM
# ═══════════════════════════════════════════════════════════════════

_OS = platform.system()

# System font cascade
_UI_PREF   = {"Darwin": "SF Pro Display", "Windows": "Segoe UI",    "Linux": "Ubuntu"         }
_MONO_PREF = {"Darwin": "Menlo",          "Windows": "Consolas",    "Linux": "Ubuntu Mono"    }
UI_F   = _UI_PREF.get(_OS, "Helvetica")
MONO_F = _MONO_PREF.get(_OS, "Courier New")

def f(size=12, weight="normal", family=None): return (family or UI_F,   size, weight)
def m(size=12, weight="normal"):              return (MONO_F, size, weight)

# ── Palette ──────────────────────────────────────────────────────
BG      = "#07080f"
S0      = "#0b1120"   # surface base
S1      = "#0f1929"   # surface raised
S2      = "#141e30"   # surface elevated
S3      = "#1a2640"   # surface overlay
BD      = "#1e2f47"   # border subtle
BD2     = "#2a3f5c"   # border strong

# Brand
BLUE    = "#3b82f6";  BLUE_L  = "#60a5fa"
CYAN    = "#06b6d4";  CYAN_L  = "#22d3ee"

# Semantic
GREEN   = "#10b981";  GREEN_L = "#34d399"
RED     = "#ef4444";  RED_L   = "#f87171"
AMBER   = "#f59e0b";  AMBER_L = "#fcd34d"
PURPLE  = "#8b5cf6"

# Text
TXT     = "#dde6f0"   # primary text
TXT2    = "#7090b0"   # secondary
TXT3    = "#3d5570"   # muted
WHITE   = "#ffffff"

# Difficulty mapping
DC      = {"easy": GREEN, "medium": AMBER, "hard": RED}
DC_DIM  = {"easy": "#0d4a35", "medium": "#4a3a10", "hard": "#4a1a1a"}

# Spacing (multiples of 4)
P = 16   # base padding
G = 8    # base gap

# ═══════════════════════════════════════════════════════════════════
#  LOW-LEVEL DRAWING UTILITIES
# ═══════════════════════════════════════════════════════════════════

def rrect(cv, x1, y1, x2, y2, r=10, **kw):
    """Draw a smooth rounded rectangle on a Canvas."""
    r = min(r, (x2-x1)//2, (y2-y1)//2)
    pts = [
        x1+r, y1,   x2-r, y1,
        x2,   y1,   x2,   y1+r,
        x2,   y2-r, x2,   y2,
        x2-r, y2,   x1+r, y2,
        x1,   y2,   x1,   y2-r,
        x1,   y1+r, x1,   y1,
    ]
    return cv.create_polygon(pts, smooth=True, **kw)


def lerp_color(c1, c2, t):
    """Linearly interpolate between two hex colors."""
    r1,g1,b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
    r2,g2,b2 = int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16)
    r = int(r1 + (r2-r1)*t); g = int(g1 + (g2-g1)*t); b = int(b1 + (b2-b1)*t)
    return f"#{r:02x}{g:02x}{b:02x}"


def ease_out(t):
    return 1 - (1-t)**3


def tween(widget, getter, setter, start, end, ms=400, on_done=None):
    """Generic value tweener."""
    t0 = time.time()
    def step():
        try:
            if not widget.winfo_exists():
                return
        except tk.TclError:
            return
        p = min((time.time()-t0)*1000/ms, 1.0)
        v = start + (end-start)*ease_out(p)
        try:
            setter(v)
        except tk.TclError:
            return
        if p < 1.0:
            widget.after(14, step)
        elif on_done:
            on_done()
    widget.after(1, step)


# ═══════════════════════════════════════════════════════════════════
#  CUSTOM WIDGETS
# ═══════════════════════════════════════════════════════════════════

class RoundedButton(tk.Canvas):
    """A fully custom rounded button with hover/press glow states."""

    def __init__(self, parent, text="", command=None, width=180, height=44,
                 color=BLUE, radius=8, font_spec=None, icon="", bg=BG, **kw):
        super().__init__(parent, width=width, height=height,
                         bg=bg, highlightthickness=0, cursor="hand2", **kw)
        self.command   = command
        self._text     = text
        self._icon     = icon
        self._color    = color
        self._radius   = radius
        self._w        = width
        self._h        = height
        self._font     = font_spec or f(11, "bold")
        self._state    = "normal"   # normal | hover | press | disabled
        self._anim_t   = 0.0
        self._ready    = False

        self.after(0, self._init_draw)
        self.bind("<Enter>",    lambda e: self._set_state("hover"))
        self.bind("<Leave>",    lambda e: self._set_state("normal"))
        self.bind("<Button-1>", lambda e: self._set_state("press"))
        self.bind("<ButtonRelease-1>", self._click)

    def _init_draw(self):
        self._ready = True
        self._draw()

    def _set_state(self, s):
        if self._state == "disabled": return
        self._state = s
        self._draw()

    def _click(self, e):
        if self._state == "disabled": return
        self._set_state("hover")
        if self.command:
            self.after(60, self.command)

    def _draw(self):
        if not self._ready:
            return
        try:
            self.delete("all")
        except tk.TclError:
            return
        w, h, r = self._w, self._h, self._radius
        c = self._color

        # Background fill
        alpha = {"normal": 0.08, "hover": 0.18, "press": 0.28, "disabled": 0.03}[self._state]
        fill  = lerp_color(BG, c, alpha + 0.06)
        stroke_a = {"normal": 0.55, "hover": 1.0, "press": 1.0, "disabled": 0.2}[self._state]
        stroke = lerp_color(S0, c, stroke_a)

        # Outer glow rings on hover/press
        if self._state in ("hover", "press"):
            glow_a = 0.12 if self._state == "hover" else 0.22
            for i in range(3, 0, -1):
                gc = lerp_color(BG, c, glow_a * (4-i)/3)
                rrect(self, i*2, i*2, w-i*2, h-i*2, r, fill=gc, outline="")

        rrect(self, 2, 2, w-2, h-2, r, fill=fill, outline=stroke, width=1)

        # Label
        lbl = f"{self._icon}  {self._text}" if self._icon else self._text
        txt_col = WHITE if self._state != "disabled" else TXT3
        self.create_text(w//2, h//2, text=lbl, fill=txt_col, font=self._font)

    def set_disabled(self, d=True):
        self._state = "disabled" if d else "normal"
        self.config(cursor="" if d else "hand2")
        self._draw()


class CircleProgress(tk.Canvas):
    """Animated circular progress ring with center label."""

    def __init__(self, parent, size=120, thickness=7, color=BLUE, bg=S0, **kw):
        super().__init__(parent, width=size, height=size,
                         bg=bg, highlightthickness=0, **kw)
        self._size  = size
        self._thick = thickness
        self._color = color
        self._value = 0.0
        self._label = ""
        self._sub   = ""
        self.after(0, lambda: self._draw(0.0))

    def animate_to(self, pct, label="", sub=""):
        self._label = label
        self._sub   = sub
        start = self._value
        tween(self, None, lambda v: self._update(v), start, pct, ms=600)

    def _update(self, v):
        self._value = v
        self._draw(v)

    def _draw(self, v):
        try:
            self.delete("all")
        except tk.TclError:
            return
        s, t = self._size, self._thick
        p = t + 2
        # Track
        self.create_arc(p, p, s-p, s-p, start=90, extent=360,
                        outline=BD, width=t, style="arc")
        # Fill
        if v > 0.5:
            ext = -min(v/100*360, 359.9)
            self.create_arc(p, p, s-p, s-p, start=90, extent=ext,
                            outline=self._color, width=t, style="arc")
        # Center text
        if self._label:
            self.create_text(s//2, s//2 - 6, text=self._label,
                             fill=WHITE, font=f(16, "bold"))
        if self._sub:
            self.create_text(s//2, s//2 + 12, text=self._sub,
                             fill=TXT2, font=f(9))


class Badge(tk.Label):
    """A small inline pill/badge label."""
    PRESETS = {
        "easy":   (GREEN,  DC_DIM["easy"]),
        "medium": (AMBER,  DC_DIM["medium"]),
        "hard":   (RED,    DC_DIM["hard"]),
        "phish":  (RED,    "#3a0d0d"),
        "legit":  (GREEN,  "#0a3020"),
        "email":  (BLUE_L, "#101a30"),
        "sms":    (CYAN_L, "#08202a"),
    }
    def __init__(self, parent, text, preset=None, fg=None, bg_c=None, **kw):
        if preset and preset in self.PRESETS:
            fg, bg_c = self.PRESETS[preset]
        super().__init__(parent, text=text,
                         fg=fg or TXT, bg=bg_c or S2,
                         font=f(9, "bold"),
                         padx=8, pady=3, **kw)


class Separator(tk.Frame):
    def __init__(self, parent, orient="h", **kw):
        if orient == "h":
            super().__init__(parent, bg=BD, height=1, **kw)
        else:
            super().__init__(parent, bg=BD, width=1, **kw)


class ScrollableFrame(tk.Frame):
    """A vertically scrollable container."""
    def __init__(self, parent, bg=BG, **kw):
        super().__init__(parent, bg=bg, **kw)
        self._cv = tk.Canvas(self, bg=bg, highlightthickness=0)
        self._sb = tk.Scrollbar(self, orient="vertical",
                                command=self._cv.yview,
                                bg=S1, troughcolor=S0,
                                activebackground=BD2, width=6)
        self._cv.configure(yscrollcommand=self._sb.set)
        self._sb.pack(side="right", fill="y")
        self._cv.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self._cv, bg=bg)
        self._win  = self._cv.create_window((0,0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>",
                        lambda e: self._cv.configure(scrollregion=self._cv.bbox("all")))
        self._cv.bind("<Configure>",
                      lambda e: self._cv.itemconfig(self._win, width=e.width))
        self._cv.bind_all("<MouseWheel>",
                          lambda e: self._cv.yview_scroll(-1*(1 if e.delta>0 else -1), "units"))

    def scroll_top(self): self._cv.yview_moveto(0)
    def scroll_bot(self): self._cv.after(100, lambda: self._cv.yview_moveto(1))


class ToastManager:
    """Slide-in toast notifications from top-right."""
    def __init__(self, root):
        self.root = root
        self._queue = []
        self._active = False

    def show(self, msg, color=GREEN, duration=2200):
        self._queue.append((msg, color, duration))
        if not self._active:
            self._next()

    def _next(self):
        if not self._queue: self._active = False; return
        self._active = True
        msg, color, dur = self._queue.pop(0)
        self._display(msg, color, dur)

    def _display(self, msg, color, dur):
        rw = self.root.winfo_width()
        w, h = 280, 48
        x0 = rw + w
        y0 = 80

        top = tk.Toplevel(self.root)
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        try: top.attributes("-alpha", 0.0)
        except: pass

        cv = tk.Canvas(top, width=w, height=h, bg=BG, highlightthickness=0)
        cv.pack()
        rrect(cv, 1, 1, w-1, h-1, 8, fill=S2, outline=color, width=1)
        cv.create_text(w//2, h//2, text=msg, fill=WHITE, font=f(11, "bold"))

        def place(px):
            rx = self.root.winfo_rootx()
            ry = self.root.winfo_rooty()
            top.geometry(f"{w}x{h}+{rx+rw-px-10}+{ry+y0}")

        def slide_in():
            tween(cv, None, lambda v: (place(int(v)),
                                       top.attributes("-alpha", min(v/w, 1.0))),
                  0, w, ms=300, on_done=lambda: self.root.after(dur, slide_out))

        def slide_out():
            tween(cv, None, lambda v: (place(int(v)),
                                       top.attributes("-alpha", max(v/w, 0.0))),
                  w, 0, ms=250, on_done=lambda: (top.destroy(), self._next()))

        top.after(10, slide_in)


# ═══════════════════════════════════════════════════════════════════
#  DATA MODEL
# ═══════════════════════════════════════════════════════════════════

@dataclass
class RedFlag:
    cat:  str
    desc: str

@dataclass
class Scenario:
    id:         int
    title:      str
    msg_type:   str       # "email" | "sms"
    is_phish:   bool
    difficulty: str       # "easy" | "medium" | "hard"
    sender:     str
    subject:    Optional[str]
    body:       str
    url:        Optional[str]
    red_flags:  list
    explanation:str
    tip:        str

@dataclass
class Session:
    score:       int   = 0
    total:       int   = 0
    correct:     int   = 0
    streak:      int   = 0
    best_streak: int   = 0
    hints:       int   = 0
    start_time:  float = field(default_factory=time.time)
    results:     list  = field(default_factory=list)

PTS = {"easy": 10, "medium": 20, "hard": 30}

SCENARIOS = [
    Scenario(1,"PayPal Account Suspended","email",True,"easy",
        "security-alert@paypa1.com","⚠️ URGENT: Your account has been compromised!",
        "Dear Valued Customer,\n\nWe detected SUSPICIOUS ACTIVITY on your account. "
        "It will be PERMANENTLY SUSPENDED in 24 hours unless you verify immediately.\n\n"
        "Secure your account NOW — click the link below.\n\nPayPal Security Team",
        "http://paypa1-secure-login.xyz/verify?token=abc123",
        [RedFlag("Typosquatted Domain","paypa1.com — '1' replaces 'l' in 'paypal'"),
         RedFlag("Urgency + Threat","24-hour deadline and threats of permanent closure"),
         RedFlag("Generic Greeting","'Dear Valued Customer' — PayPal always uses your name"),
         RedFlag("Suspicious URL","paypa1-secure-login.xyz is not a PayPal domain")],
        "Classic typosquatting attack. The '1' for 'l' swap is only spotted on careful inspection. "
        "Legitimate PayPal emails always address you by name and never threaten immediate suspension.",
        "Hover every link before clicking. Verify the domain character by character."),

    Scenario(2,"Chase Bank Statement","email",False,"easy",
        "statements@chase.com","Your October 2025 statement is ready",
        "Hi Alex,\n\nYour Chase checking account statement for October 2025 is now available.\n\n"
        "To view it, sign in at chase.com or open the Chase mobile app. For your security, "
        "we never include direct login links in emails.\n\n"
        "Questions? Call 1-800-935-9935 or visit chase.com/support.\n\nChase Customer Service",
        None,[],
        "Legitimate bank notification. It uses your real name, explicitly avoids login links, "
        "comes from the verified @chase.com domain, and provides multiple verifiable contacts.",
        "Legitimate banks tell you they won't include login links. That transparency is a trust signal."),

    Scenario(3,"USPS Redelivery Fee","sms",True,"easy",
        "+1-555-019-2847",None,
        "[USPS] Package #7392018 could not be delivered.\n"
        "A $0.30 redelivery fee is required to reschedule.\n\n"
        "Pay now or your package will be returned:\n"
        "http://usps-redelivery.com/pay?id=739201\n\nExpires in 12 hours.",
        "http://usps-redelivery.com/pay?id=739201",
        [RedFlag("Fake Domain","usps-redelivery.com is not usps.com"),
         RedFlag("Smishing","USPS never requests payment via SMS"),
         RedFlag("Micro-Payment Trick","$0.30 feels trivial — designed to skip your skepticism"),
         RedFlag("Expiry Pressure","12-hour window creates urgency")],
        "Smishing (SMS phishing). The tiny fee is intentional — it seems too small to question. "
        "Once on the fake site they capture your full card details for much larger charges.",
        "Never click links in unexpected SMS. Navigate to usps.com directly in your browser."),

    Scenario(4,"IT Security Patch Notice","email",True,"medium",
        "it-support@company-helpdesk.net","[URGENT] Mandatory Patch — Action Required Today",
        "Hello,\n\nA critical zero-day vulnerability (CVE-2025-4821) was found on your workstation. "
        "You MUST install the patch before 5 PM today or your network access will be revoked.\n\n"
        "Download:\n    https://company-helpdesk.net/patches/urgent/install.exe\n\nIT Security Team",
        "https://company-helpdesk.net/patches/urgent/install.exe",
        [RedFlag("External Domain","company-helpdesk.net ≠ your company's IT domain"),
         RedFlag(".exe from Email","IT never asks you to download executables via email"),
         RedFlag("Fake CVE","Real patches come through WSUS/Jamf/Intune — never email links"),
         RedFlag("No Ticket ID","Legitimate IT requests include a ticket number like INC-4821")],
        "Spear-phishing impersonating IT. Your real IT team patches via automated tools, "
        "never by emailing an .exe link. The CVE reference adds false credibility.",
        "Verify all IT patch requests by calling the helpdesk at the number on your company intranet."),

    Scenario(5,"LinkedIn Connection","email",False,"medium",
        "messages-noreply@linkedin.com","Sarah Chen wants to connect on LinkedIn",
        "Hi there,\n\nSarah Chen (Senior PM at Acme Corp) wants to connect with you.\n\n"
        "To respond, sign in to linkedin.com.\n\nThe LinkedIn Team\n\n"
        "─────────────────────────────────────\n"
        "Unsubscribe · Help · Privacy Policy\nLinkedIn Corporation, 1000 W Maude Ave, Sunnyvale CA",
        None,[],
        "Legitimate LinkedIn notification. Official @linkedin.com sender, no embedded login link, "
        "real physical address, and legally required unsubscribe/privacy options.",
        "Legitimate commercial emails must include a physical address and unsubscribe link by law."),

    Scenario(6,"CEO Wire Transfer","email",True,"medium",
        "j.morrison@acmecorp-hq.co","Confidential — Urgent Wire Transfer Needed",
        "Hi,\n\nI need you to wire $47,500 to a new vendor today. Deal is closing — time-sensitive.\n"
        "I'm in back-to-back board meetings and can't take calls. Keep this confidential for now.\n\n"
        "Beneficiary: Global Trade Solutions LLC\nBank: First National · Account: 7734882100982\n\n"
        "Thanks,\nJames Morrison, CEO",
        None,
        [RedFlag("Domain Lookalike","acmecorp-hq.co ≠ acmecorp.com — deliberately similar"),
         RedFlag("BEC Attack","CEO impersonation to authorize a fraudulent wire transfer"),
         RedFlag("Secrecy Demand","'Keep confidential' prevents you consulting colleagues"),
         RedFlag("Unavailability Excuse","'In meetings' stops you calling to verify"),
         RedFlag("No PO/Invoice","All legitimate vendor payments have documented paper trails")],
        "Business Email Compromise — the most financially damaging cybercrime. The attacker "
        "registered a lookalike domain and combined urgency, secrecy, and CEO authority. "
        "One phone call using a known number would expose this immediately.",
        "Mandate out-of-band phone verification for ALL wire transfers. No exceptions."),

    Scenario(7,"GitHub Login Alert","email",True,"hard",
        "noreply@github-security.com","[GitHub] Sign-in from Moscow, Russia",
        "Hi there,\n\nWe detected a sign-in to your GitHub account from an unrecognized device.\n\n"
        "    Location:   Moscow, Russia\n    Device:     Windows 10 · Chrome 118\n"
        "    IP:         185.220.101.47\n    Time:       Nov 3, 2025 · 03:14 UTC\n\n"
        "If this wasn't you, secure your account now:\n"
        "    https://github-security.com/secure?token=eyJhbGc...\n\nThis link expires in 30 minutes.",
        "https://github-security.com/secure?token=eyJhbGc...",
        [RedFlag("Wrong Sender Domain","github-security.com ≠ github.com (GitHub only uses @github.com)"),
         RedFlag("Fear Engineering","Moscow location triggers panic, bypassing critical thinking"),
         RedFlag("JWT Token Harvesting","Token in URL captures your session credentials"),
         RedFlag("30-Min Expiry","Short window prevents calm verification")],
        "Extremely convincing phishing — the ONLY giveaway is the sender domain. GitHub exclusively "
        "emails from @github.com, never github-security.com. Fear of a foreign login makes people "
        "click without reading the URL.",
        "When you receive any scary security alert, navigate DIRECTLY to the site — never via the link."),

    Scenario(8,"AWS Cost Anomaly","email",False,"hard",
        "aws-cost-management@amazon.com","[AWS] Cost anomaly — Account 123456789012",
        "Hello,\n\nAWS Cost Anomaly Detection found unusual spending in your account.\n\n"
        "    Account ID:  123456789012\n    Service:     Amazon EC2\n"
        "    Anomaly:     $234.50 above expected\n    Period:      Nov 1–3, 2025\n\n"
        "To investigate, sign in to aws.amazon.com → Billing → Cost Anomaly Detection.\n\n"
        "AWS Cost Management · 410 Terry Ave N, Seattle WA 98109",
        None,[],
        "Legitimate AWS alert. Signals: official @amazon.com domain, your actual 12-digit account ID, "
        "no embedded action link (directs you to navigate manually), and AWS's verified physical address.",
        "Cloud alerts always include your account ID. Missing account ID = treat it as suspicious."),

    Scenario(9,"DocuSign NDA Request","email",True,"hard",
        "dse@docusign.net","Please DocuSign: Mutual NDA — Review and Sign",
        "Your signature is requested.\n\n"
        "    Document:  Mutual Non-Disclosure Agreement\n"
        "    From:      contracts@globalpartners-llc.com\n    Expires:   48 hours\n\n"
        "REVIEW & SIGN:\n    https://app.docusign.net/sign?envelopeId=f3a9bc12...\n\n"
        "Do Not Share This Email — it contains your unique authentication token.\n\n"
        "DocuSign Electronic Signature · 221 Main St, SF CA 94105",
        "https://app.docusign.net/sign?envelopeId=f3a9bc12...",
        [RedFlag("Wrong TLD","docusign.net ≠ docusign.com — DocuSign exclusively uses .com"),
         RedFlag("Unexpected Document","No prior context about this NDA"),
         RedFlag("'Do Not Share' Warning","Stops you asking a colleague who might spot the fraud"),
         RedFlag("48-Hour Expiry","Pressure to sign before you verify")],
        "DocuSign ONLY sends from @docusign.com. The .net TLD is the tell. This steals credentials "
        "via a fake document viewer. The 'Do Not Share' line cleverly prevents peer review.",
        "Check TLDs carefully — .net, .co, .org versions of trusted brands are common attack vectors."),

    Scenario(10,"Slack DM from Colleague","email",True,"hard",
        "no-reply@slack-notifications.com","Jordan Rivera sent you a message on Slack",
        'Jordan Rivera sent you a direct message:\n\n'
        '    "Hey! Can you review the mockup I shared? It\'s for\n'
        '     tomorrow\'s presentation. Figma kept breaking so I\n'
        '     exported it here: https://figma-share.net/d/mockup-v3\n\n'
        '     Need your feedback before EOD — thanks!"\n\n'
        "Reply in Slack: https://slack-notifications.com/open?msg=...",
        "https://figma-share.net/d/mockup-v3",
        [RedFlag("Fake Slack Domain","slack-notifications.com ≠ slack.com"),
         RedFlag("Fake Figma Domain","figma-share.net ≠ figma.com — two lookalike domains"),
         RedFlag("Dual-Brand Spoofing","Simultaneously impersonates Slack AND Figma"),
         RedFlag("Social Engineering","Uses a real colleague's name to lower your guard"),
         RedFlag("'Figma Broke' Excuse","Explains away the suspicious non-Figma URL")],
        "Two impersonations in one email. Both slack-notifications.com and figma-share.net are fakes. "
        "The colleague's name may have been harvested from LinkedIn. The 'Figma broke' excuse is "
        "engineered to make the off-brand URL feel legitimate.",
        "In multi-brand emails, verify EVERY domain independently. Real Slack only emails from @slack.com."),
]


# ═══════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════

class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Phishing Awareness Simulator")
        self._center(1080, 740)
        self.minsize(900, 660)
        self.configure(bg=BG)
        self.resizable(True, True)

        self.session = Session()
        self.queue:   list[Scenario] = []
        self.idx      = 0
        self.answered = False
        self.hint_on  = False
        self._mode    = tk.StringVar(value="full")

        self.toasts = ToastManager(self)
        self._build()
        self._show("intro")

        # Global keyboard shortcuts (active during game)
        self.bind("<Key-1>", lambda e: self._kb_answer(True))
        self.bind("<Key-2>", lambda e: self._kb_answer(False))
        self.bind("<Key-h>", lambda e: self._kb_hint())
        self.bind("<Return>", lambda e: self._kb_next())
        self.bind("<Escape>", lambda e: self._kb_escape())

    def _center(self, w, h):
        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    # ── Scaffold ───────────────────────────────────────────────────
    def _build(self):
        self._build_topbar()
        self.pages = tk.Frame(self, bg=BG)
        self.pages.pack(fill="both", expand=True)

        self.pg_intro   = tk.Frame(self.pages, bg=BG)
        self.pg_game    = tk.Frame(self.pages, bg=BG)
        self.pg_results = tk.Frame(self.pages, bg=BG)
        for pg in (self.pg_intro, self.pg_game, self.pg_results):
            pg.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._build_intro()
        self._build_game()
        self._build_results_shell()

    def _show(self, page):
        {"intro": self.pg_intro, "game": self.pg_game,
         "results": self.pg_results}[page].lift()
        self.current_page = page

    # ── Top Bar ────────────────────────────────────────────────────
    def _build_topbar(self):
        bar = tk.Frame(self, bg=S0, height=52)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        Separator(bar).pack(fill="x", side="bottom")

        tk.Label(bar, text="⬡", bg=S0, fg=BLUE, font=f(18, "bold")).pack(side="left", padx=(18,4))
        tk.Label(bar, text="PhishGuard", bg=S0, fg=WHITE, font=f(14, "bold")).pack(side="left")
        tk.Label(bar, text="Awareness Simulator", bg=S0, fg=TXT3, font=f(10)).pack(side="left", padx=(4,0), pady=3)

        # Right side – live stats (shown during game)
        self._tb_right = tk.Frame(bar, bg=S0)
        self._tb_right.pack(side="right", padx=16)

        def stat_chip(parent, var_name, icon, color):
            f2 = tk.Frame(parent, bg=S1, highlightbackground=BD,
                          highlightthickness=1)
            f2.pack(side="right", padx=4, pady=10)
            lbl = tk.Label(f2, text=f"{icon}  —", bg=S1, fg=color, font=f(10,"bold"),
                           padx=12, pady=3)
            lbl.pack()
            setattr(self, var_name, lbl)

        stat_chip(self._tb_right, "_tb_streak", "🔥", AMBER)
        stat_chip(self._tb_right, "_tb_score",  "◈",  BLUE_L)
        self._tb_right.pack_forget()

    def _tb_show(self): self._tb_right.pack(side="right", padx=16)
    def _tb_hide(self): self._tb_right.pack_forget()
    def _tb_update(self):
        self._tb_score.config(text=f"◈  {self.session.score} pts")
        self._tb_streak.config(text=f"🔥  {self.session.streak}")

    # ═══════════════════════════════════════════════════════════════
    #  INTRO SCREEN
    # ═══════════════════════════════════════════════════════════════
    def _build_intro(self):
        pg = self.pg_intro
        wrap = tk.Frame(pg, bg=BG)
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        # Animated orb (canvas)
        self._orb = tk.Canvas(wrap, width=110, height=110, bg=BG, highlightthickness=0)
        self._orb.pack(pady=(0, 8))
        self._orb_t = 0.0
        self._draw_orb()

        tk.Label(wrap, text="Phishing Awareness Simulator",
                 bg=BG, fg=WHITE, font=f(26, "bold")).pack()
        tk.Label(wrap, text="Test your ability to identify real-world cyber threats",
                 bg=BG, fg=TXT2, font=f(12)).pack(pady=(4, 28))

        # ── Mode grid ──────────────────────────────────────────────
        grid = tk.Frame(wrap, bg=BG)
        grid.pack(pady=(0, 24))
        self._mode_cards = {}
        modes = [
            ("full",   "📋", "Full Training",  "All 10 scenarios · Mixed difficulty"),
            ("quick",  "⚡", "Quick Quiz",     "5 random · Fast 5-min session"),
            ("hard",   "🔥", "Hard Mode",      "Expert scenarios only"),
            ("easy",   "🟢", "Easy Start",     "Beginner-friendly · Learn the basics"),
        ]
        for col, (mid, icon, title, desc) in enumerate(modes):
            card = self._mode_card(grid, mid, icon, title, desc)
            card.grid(row=0, column=col, padx=6, sticky="nsew")
        self._mode_select("full")

        # ── Feature strip ──────────────────────────────────────────
        strip = tk.Frame(wrap, bg=S0, highlightbackground=BD, highlightthickness=1)
        strip.pack(fill="x", pady=(0, 28), ipadx=12, ipady=10)
        for icon, lbl in [("🎯","10 Scenarios"), ("🚩","Red Flag Analysis"),
                          ("📊","Score & Streaks"), ("💡","Security Tips"), ("⌨","Keyboard Shortcuts")]:
            fc = tk.Frame(strip, bg=S0)
            fc.pack(side="left", expand=True, padx=8)
            tk.Label(fc, text=icon, bg=S0, font=f(16)).pack()
            tk.Label(fc, text=lbl, bg=S0, fg=TXT2, font=f(9)).pack()

        # ── Start button ───────────────────────────────────────────
        self._start_btn = RoundedButton(wrap, "Begin Training", self._start_game,
                                        width=240, height=52, color=BLUE,
                                        font_spec=f(13, "bold"), icon="▶", bg=BG)
        self._start_btn.pack()
        tk.Label(wrap, text="Press  Enter  to start", bg=BG, fg=TXT3, font=f(9)).pack(pady=(6,0))

        # Animate orb
        self._animate_orb()

    def _mode_card(self, parent, mid, icon, title, desc):
        card = tk.Frame(parent, bg=S1, highlightthickness=1,
                        highlightbackground=BD, cursor="hand2", width=182, height=88)
        card.pack_propagate(False)
        tk.Label(card, text=f"{icon}  {title}", bg=S1, fg=WHITE,
                 font=f(11, "bold"), anchor="w").pack(fill="x", padx=14, pady=(14, 2))
        tk.Label(card, text=desc, bg=S1, fg=TXT2, font=f(9), anchor="w",
                 wraplength=160, justify="left").pack(fill="x", padx=14)
        for w in [card] + list(card.winfo_children()):
            w.bind("<Button-1>", lambda e, m=mid: self._mode_select(m))
        self._mode_cards[mid] = card
        return card

    def _mode_select(self, mid):
        self._mode.set(mid)
        for m, c in self._mode_cards.items():
            sel = (m == mid)
            c.config(bg=S2 if sel else S1,
                     highlightbackground=BLUE if sel else BD)
            for w in c.winfo_children():
                w.config(bg=S2 if sel else S1,
                         fg=(WHITE if sel else (WHITE if w.cget("font") == str(f(11,"bold")) else TXT2)))

    def _draw_orb(self):
        try:
            cv = self._orb
            cv.delete("all")
        except tk.TclError:
            return
        cx, cy = 55, 55
        t = self._orb_t
        # outer glow pulse
        r = 42 + math.sin(t)*4
        glow_rings = [(r+16,"#050d1a"), (r+10,"#070f20"), (r+4,"#091424")]
        for gr, gc in glow_rings:
            cv.create_oval(cx-gr, cy-gr, cx+gr, cy+gr, fill=gc, outline="")
        # rotating arc
        cv.create_oval(cx-r, cy-r, cx+r, cy+r,
                       outline=BD2, width=2, fill=S1)
        start = int((t * 60) % 360)
        cv.create_arc(cx-r, cy-r, cx+r, cy+r,
                      start=start, extent=200,
                      outline=BLUE, width=3, style="arc")
        cv.create_arc(cx-r, cy-r, cx+r, cy+r,
                      start=start+210, extent=100,
                      outline=lerp_color(BLUE, CYAN, 0.5), width=2, style="arc")
        # inner icon
        cv.create_text(cx, cy, text="🎣", font=f(22))

    def _animate_orb(self):
        try:
            if not self._orb.winfo_exists():
                return
        except tk.TclError:
            return
        self._orb_t += 0.035
        self._draw_orb()
        self._orb_anim = self.after(20, self._animate_orb)

    # ═══════════════════════════════════════════════════════════════
    #  GAME SCREEN
    # ═══════════════════════════════════════════════════════════════
    def _build_game(self):
        pg = self.pg_game
        pg.columnconfigure(1, weight=1)
        pg.rowconfigure(0, weight=1)

        # Left sidebar
        self._sb = tk.Frame(pg, bg=S0, width=220)
        self._sb.grid(row=0, column=0, sticky="nsew")
        self._sb.pack_propagate(False)
        Separator(pg, orient="v").grid(row=0, column=0, sticky="nse")
        self._build_sidebar()

        # Right main area
        self._main = tk.Frame(pg, bg=BG)
        self._main.grid(row=0, column=1, sticky="nsew")
        self._build_main()

    # ── Sidebar ────────────────────────────────────────────────────
    def _build_sidebar(self):
        sb = self._sb

        # Header
        hdr = tk.Frame(sb, bg=S0)
        hdr.pack(fill="x", padx=0, pady=0)
        tk.Label(hdr, text="SESSION STATS", bg=S0, fg=TXT3,
                 font=f(9, "bold"), padx=16, pady=14).pack(anchor="w")
        Separator(hdr).pack(fill="x")

        # Progress ring
        ring_wrap = tk.Frame(sb, bg=S0)
        ring_wrap.pack(pady=20)
        self._ring = CircleProgress(ring_wrap, size=116, thickness=8, color=BLUE, bg=S0)
        self._ring.pack()

        Separator(sb).pack(fill="x", padx=16, pady=4)

        # Stats
        def stat(label, attr, color, big=False):
            f2 = tk.Frame(sb, bg=S0)
            f2.pack(fill="x", padx=16, pady=5)
            tk.Label(f2, text=label, bg=S0, fg=TXT3, font=f(8, "bold")).pack(anchor="w")
            lbl = tk.Label(f2, text="—", bg=S0, fg=color,
                           font=f(22 if big else 16, "bold"))
            lbl.pack(anchor="w")
            setattr(self, attr, lbl)

        stat("SCORE",       "_s_score",      BLUE_L, big=True)
        stat("CORRECT",     "_s_correct",    GREEN)
        stat("ACCURACY",    "_s_acc",        TXT)

        Separator(sb).pack(fill="x", padx=16, pady=4)
        stat("🔥 STREAK",    "_s_streak",     AMBER)
        stat("BEST STREAK", "_s_best",        TXT2)

        Separator(sb).pack(fill="x", padx=16, pady=8)

        # Difficulty mini-bars
        tk.Label(sb, text="BY DIFFICULTY", bg=S0, fg=TXT3,
                 font=f(8, "bold"), padx=16).pack(anchor="w", pady=(0, 6))
        self._diff_bars = {}
        for d, color in [("Easy", GREEN), ("Medium", AMBER), ("Hard", RED)]:
            row = tk.Frame(sb, bg=S0)
            row.pack(fill="x", padx=16, pady=2)
            tk.Label(row, text=d, bg=S0, fg=color, font=f(9), width=7, anchor="w").pack(side="left")
            bg_bar = tk.Frame(row, bg=BD, height=5)
            bg_bar.pack(side="left", fill="x", expand=True, pady=2)
            fill = tk.Frame(bg_bar, bg=color, height=5)
            fill.place(relx=0, rely=0, relheight=1, relwidth=0)
            cnt = tk.Label(row, text="0/0", bg=S0, fg=TXT3, font=f(8), width=4)
            cnt.pack(side="right")
            self._diff_bars[d.lower()] = (fill, cnt)

        # Hint button
        Separator(sb).pack(fill="x", padx=16, pady=10)
        self._hint_btn = RoundedButton(sb, "Show Hint", self._use_hint,
                                       width=188, height=38,
                                       color=AMBER, icon="💡",
                                       font_spec=f(10, "bold"), bg=S0)
        self._hint_btn.pack(pady=(0, 6))
        self._hint_cost = tk.Label(sb, text="Reduces points by 5", bg=S0, fg=TXT3, font=f(8))
        self._hint_cost.pack()

        # Keyboard shortcuts legend
        Separator(sb).pack(fill="x", padx=16, pady=10)
        tk.Label(sb, text="SHORTCUTS", bg=S0, fg=TXT3, font=f(8, "bold"), padx=16).pack(anchor="w")
        for key, action in [("[1]","Phishing"), ("[2]","Legitimate"),
                            ("[H]","Hint"), ("[↵]","Next"), ("[Esc]","Quit game")]:
            row = tk.Frame(sb, bg=S0)
            row.pack(fill="x", padx=16, pady=1)
            tk.Label(row, text=key, bg=S0, fg=BLUE_L, font=f(9, "bold"), width=5, anchor="w").pack(side="left")
            tk.Label(row, text=action, bg=S0, fg=TXT2, font=f(9)).pack(side="left")

    # ── Main area ──────────────────────────────────────────────────
    def _build_main(self):
        ma = self._main
        ma.rowconfigure(1, weight=1)
        ma.columnconfigure(0, weight=1)

        # Info bar
        self._infobar = tk.Frame(ma, bg=S1, height=46)
        self._infobar.grid(row=0, column=0, sticky="ew")
        self._infobar.pack_propagate(False)
        Separator(self._infobar, orient="h").pack(fill="x", side="bottom")
        self._ib_left  = tk.Frame(self._infobar, bg=S1)
        self._ib_left.pack(side="left",  padx=16, pady=8)
        self._ib_right = tk.Frame(self._infobar, bg=S1)
        self._ib_right.pack(side="right", padx=16, pady=8)
        self._ib_title = tk.Label(self._ib_left, text="", bg=S1, fg=WHITE, font=f(12,"bold"))
        self._ib_title.pack(side="left", padx=(0,10))

        # Scrollable message + feedback
        self._scroll = ScrollableFrame(ma, bg=BG)
        self._scroll.grid(row=1, column=0, sticky="nsew")

        # Answer control bar (fixed at bottom)
        self._ctrl = tk.Frame(ma, bg=S0, height=80)
        self._ctrl.grid(row=2, column=0, sticky="ew")
        self._ctrl.pack_propagate(False)
        Separator(self._ctrl, orient="h").pack(fill="x", side="top")
        self._build_controls()

    def _build_controls(self):
        ctrl = self._ctrl
        inner = tk.Frame(ctrl, bg=S0)
        inner.pack(expand=True)

        tk.Label(inner, text="Is this message  PHISHING  or  LEGITIMATE ?",
                 bg=S0, fg=TXT2, font=f(10)).pack(pady=(8,8))

        btn_row = tk.Frame(inner, bg=S0)
        btn_row.pack()
        self._phish_btn = RoundedButton(btn_row, "Phishing", lambda: self._answer(True),
                                        width=200, height=44, color=RED, icon="🎣",
                                        font_spec=f(11,"bold"), bg=S0)
        self._phish_btn.pack(side="left", padx=10)
        self._legit_btn = RoundedButton(btn_row, "Legitimate", lambda: self._answer(False),
                                        width=200, height=44, color=GREEN, icon="✅",
                                        font_spec=f(11,"bold"), bg=S0)
        self._legit_btn.pack(side="left", padx=10)

    # ─── GAME FLOW ───────────────────────────────────────────────────

    def _start_game(self):
        mode = self._mode.get()
        pool = list(SCENARIOS)
        if   mode == "quick": q = random.sample(pool, 5)
        elif mode == "hard":  q = [s for s in pool if s.difficulty == "hard"]
        elif mode == "easy":  q = [s for s in pool if s.difficulty == "easy"]
        else:                 q = random.sample(pool, len(pool))

        self.queue   = q
        self.idx     = 0
        self.session = Session()

        # Stop intro animation
        if hasattr(self, "_orb_anim"):
            self.after_cancel(self._orb_anim)

        self._tb_show()
        self._show("game")
        self._load()

    def _load(self):
        self.answered  = False
        self.hint_on   = False
        self._hint_btn.set_disabled(False)

        inner = self._scroll.inner
        for w in inner.winfo_children(): w.destroy()

        s   = self.queue[self.idx]
        tot = len(self.queue)

        # Info bar
        for w in self._ib_left.winfo_children()[1:]: w.destroy()
        for w in self._ib_right.winfo_children(): w.destroy()
        self._ib_title.config(text=s.title)
        Badge(self._ib_left,  s.msg_type.upper(), preset=s.msg_type).pack(side="left")
        Badge(self._ib_right, s.difficulty.upper(), preset=s.difficulty).pack(side="left", padx=4)
        tk.Label(self._ib_right, text=f"{self.idx+1} / {tot}",
                 bg=S1, fg=TXT2, font=f(9)).pack(side="left", padx=8)

        # Ring
        pct = (self.idx / tot) * 100
        self._ring.animate_to(pct, f"{self.idx}/{tot}", "done")

        # Render
        if s.msg_type == "email":  self._render_email(s, inner)
        else:                      self._render_sms(s, inner)

        # Hint placeholder
        self._hint_area = tk.Frame(inner, bg=BG)
        self._hint_area.pack(fill="x", padx=P, pady=(0, 4))

        # Feedback placeholder
        self._fb_area = tk.Frame(inner, bg=BG)
        self._fb_area.pack(fill="x", padx=P, pady=(0, P))

        # Show answer buttons
        self._phish_btn.set_disabled(False)
        self._legit_btn.set_disabled(False)
        self._ctrl.grid()

        self._update_stats()
        self._scroll.scroll_top()

    def _render_email(self, s: Scenario, parent):
        # ── Email chrome ────────────────────────────────────────────
        wrap = tk.Frame(parent, bg=BG)
        wrap.pack(fill="x", padx=P, pady=(P, G))

        # Window chrome bar
        chrome = tk.Frame(wrap, bg="#0e1d30", height=34)
        chrome.pack(fill="x")
        chrome.pack_propagate(False)
        dot_row = tk.Frame(chrome, bg="#0e1d30")
        dot_row.pack(side="left", padx=12, pady=10)
        for c_col in ("#ff5f57","#febc2e","#28c840"):
            tk.Label(dot_row, text="⬤", bg="#0e1d30", fg=c_col, font=f(9)).pack(side="left", padx=2)
        tk.Label(chrome, text="INBOX", bg="#0e1d30", fg=TXT3, font=f(9, "bold")).pack(side="right", padx=16)

        # Header fields
        hdr = tk.Frame(wrap, bg=S1, highlightbackground=BD, highlightthickness=1)
        hdr.pack(fill="x")

        for lbl_text, val, val_fg in [("FROM",    s.sender,           AMBER),
                                       ("SUBJECT", s.subject or "(no subject)", WHITE)]:
            row = tk.Frame(hdr, bg=S1)
            row.pack(fill="x", padx=16, pady=6)
            tk.Label(row, text=lbl_text, bg=S1, fg=TXT3, font=f(9,"bold"),
                     width=8, anchor="e").pack(side="left")
            tk.Label(row, text=val, bg=S1, fg=val_fg, font=m(11,"bold"),
                     anchor="w", justify="left", wraplength=700).pack(side="left", padx=10)
            if lbl_text == "FROM":
                Separator(hdr).pack(fill="x", padx=16)

        # Body
        body_f = tk.Frame(wrap, bg=S0, highlightbackground=BD, highlightthickness=1)
        body_f.pack(fill="x")
        body_txt = tk.Text(body_f, bg=S0, fg=TXT, font=m(11),
                           wrap="word", relief="flat", padx=20, pady=16,
                           state="normal", cursor="arrow", height=10,
                           selectbackground=S2, insertbackground=S0)
        body_txt.pack(fill="x")
        body_txt.insert("1.0", s.body)
        if s.url:
            body_txt.insert("end", "\n\n")
            body_txt.insert("end", s.url, "link")
            body_txt.tag_configure("link", foreground=BLUE_L, underline=True)
        body_txt.config(state="disabled")

    def _render_sms(self, s: Scenario, parent):
        wrap = tk.Frame(parent, bg=BG)
        wrap.pack(fill="x", padx=P, pady=(P, G))

        # SMS chrome
        chrome = tk.Frame(wrap, bg="#0e1d30", height=38)
        chrome.pack(fill="x")
        chrome.pack_propagate(False)
        tk.Label(chrome, text="◀  Messages", bg="#0e1d30", fg=BLUE_L,
                 font=f(10,"bold")).pack(side="left", padx=14, pady=10)
        tk.Label(chrome, text="📱 Text Message", bg="#0e1d30", fg=TXT3,
                 font=f(9)).pack(side="right", padx=14)

        # Sender bar
        sender_bar = tk.Frame(wrap, bg=S1, highlightbackground=BD, highlightthickness=1)
        sender_bar.pack(fill="x")
        tk.Label(sender_bar, text=s.sender, bg=S1, fg=AMBER,
                 font=m(11,"bold"), padx=16, pady=10).pack(anchor="w")

        # Bubble
        bbl_area = tk.Frame(wrap, bg=S0, highlightbackground=BD, highlightthickness=1)
        bbl_area.pack(fill="x")
        tk.Label(bbl_area, text="Today · Received", bg=S0, fg=TXT3,
                 font=f(9)).pack(pady=(12,6))

        bbl = tk.Frame(bbl_area, bg=S2, highlightbackground=BD2, highlightthickness=1)
        bbl.pack(anchor="w", padx=20, pady=(0,16), ipadx=16, ipady=12)
        body_lbl = tk.Label(bbl, text=s.body, bg=S2, fg=TXT, font=m(11),
                            justify="left", anchor="w", wraplength=560)
        body_lbl.pack()
        if s.url:
            tk.Label(bbl_area, text=s.url, bg=S0, fg=BLUE_L, font=m(10),
                     wraplength=600).pack(anchor="w", padx=20, pady=(0,12))

    # ── Answer logic ───────────────────────────────────────────────
    def _answer(self, is_phish: bool):
        if self.answered: return
        self.answered = True
        self._phish_btn.set_disabled(True)
        self._legit_btn.set_disabled(True)
        self._ctrl.grid_remove()

        s = self.queue[self.idx]
        correct = (is_phish == s.is_phish)
        pts = 0

        self.session.total += 1
        if correct:
            self.session.correct += 1
            pts = max(0, PTS[s.difficulty] - (5 if self.hint_on else 0))
            self.session.score += pts
            self.session.streak += 1
            self.session.best_streak = max(self.session.best_streak, self.session.streak)
            self.toasts.show(f"✓  Correct!  +{pts} pts", GREEN, 2000)
            if self.session.streak >= 3:
                self.toasts.show(f"🔥  {self.session.streak}× Streak!", AMBER, 2000)
        else:
            self.session.streak = 0
            self.toasts.show("✗  Incorrect", RED, 2000)

        self.session.hints += (1 if self.hint_on else 0)
        self.session.results.append({
            "title": s.title, "diff": s.difficulty,
            "is_phish": s.is_phish, "correct": correct, "pts": pts, "hint": self.hint_on
        })

        self._update_stats()
        self._render_feedback(s, correct, pts)
        self._scroll.scroll_bot()

    def _use_hint(self):
        if self.hint_on or self.answered: return
        self.hint_on = True
        self._hint_btn.set_disabled(True)

        s = self.queue[self.idx]
        for w in self._hint_area.winfo_children(): w.destroy()

        if s.is_phish and s.red_flags:
            rf = s.red_flags[0]
            txt = f"💡  {rf.cat}  —  {rf.desc}"
        else:
            txt = "💡  Notice what this email is NOT doing — no login link, no threats."

        hint_wrap = tk.Frame(self._hint_area, bg=DC_DIM["medium"],
                             highlightbackground=AMBER, highlightthickness=1)
        hint_wrap.pack(fill="x")
        tk.Label(hint_wrap, text=txt, bg=DC_DIM["medium"], fg=AMBER_L,
                 font=f(10), wraplength=720, justify="left",
                 padx=14, pady=10).pack(anchor="w")

    def _render_feedback(self, s: Scenario, correct: bool, pts: int):
        for w in self._fb_area.winfo_children(): w.destroy()
        parent = self._fb_area

        color  = GREEN if correct else RED
        icon   = "✓" if correct else "✗"
        label  = "Correct!" if correct else "Incorrect"
        truth  = ("🎣  Phishing" if s.is_phish else "✅  Legitimate")
        t_col  = RED if s.is_phish else GREEN

        # ── Result header card ──────────────────────────────────────
        hcard = tk.Frame(parent, bg=S1, highlightbackground=color, highlightthickness=2)
        hcard.pack(fill="x", pady=(G, 2))
        hrow = tk.Frame(hcard, bg=S1)
        hrow.pack(fill="x", padx=P, pady=14)

        tk.Label(hrow, text=icon, bg=S1, fg=color,
                 font=f(24,"bold"), width=2).pack(side="left")
        tk.Label(hrow, text=label, bg=S1, fg=color,
                 font=f(16,"bold")).pack(side="left", padx=(4,16))
        tk.Label(hrow, text="This was:", bg=S1, fg=TXT2,
                 font=f(10)).pack(side="left")
        tk.Label(hrow, text=truth, bg=S1, fg=t_col,
                 font=f(12,"bold")).pack(side="left", padx=8)
        pts_txt = f"+{pts} pts" if pts else ("+0 pts  (hint used)" if self.hint_on else "+0 pts")
        tk.Label(hrow, text=pts_txt, bg=S1,
                 fg=GREEN if pts > 0 else TXT3,
                 font=f(13,"bold")).pack(side="right")

        # ── Red flags ──────────────────────────────────────────────
        if s.is_phish and s.red_flags:
            rf_card = tk.Frame(parent, bg=S1, highlightbackground=BD, highlightthickness=1)
            rf_card.pack(fill="x", pady=2)
            tk.Label(rf_card, text="🚩  RED FLAGS", bg=S1, fg=RED,
                     font=f(10,"bold"), padx=P, pady=10).pack(anchor="w")
            Separator(rf_card).pack(fill="x")
            for i, rf in enumerate(s.red_flags):
                row = tk.Frame(rf_card, bg=(S2 if i%2==0 else S1))
                row.pack(fill="x")
                tk.Label(row, text=f"  {i+1}", bg=row.cget("bg"), fg=RED,
                         font=f(10,"bold"), width=4).pack(side="left", pady=8)
                inner = tk.Frame(row, bg=row.cget("bg"))
                inner.pack(side="left", fill="x", expand=True, pady=8, padx=4)
                tk.Label(inner, text=rf.cat, bg=row.cget("bg"), fg=WHITE,
                         font=f(10,"bold"), anchor="w").pack(anchor="w")
                tk.Label(inner, text=rf.desc, bg=row.cget("bg"), fg=TXT2,
                         font=f(9), anchor="w", wraplength=620).pack(anchor="w")

        # ── Explanation ─────────────────────────────────────────────
        exp_card = tk.Frame(parent, bg=S1, highlightbackground=BD, highlightthickness=1)
        exp_card.pack(fill="x", pady=2)
        tk.Label(exp_card, text="📖  EXPLANATION", bg=S1, fg=CYAN_L,
                 font=f(10,"bold"), padx=P, pady=10).pack(anchor="w")
        Separator(exp_card).pack(fill="x")
        tk.Label(exp_card, text=s.explanation, bg=S1, fg=TXT,
                 font=f(11), wraplength=720, justify="left",
                 padx=P, pady=12).pack(anchor="w")

        # ── Pro tip ─────────────────────────────────────────────────
        tip_card = tk.Frame(parent, bg=DC_DIM["easy"],
                            highlightbackground=GREEN, highlightthickness=1)
        tip_card.pack(fill="x", pady=2)
        tk.Label(tip_card, text=f"💡  PRO TIP  —  {s.tip}", bg=DC_DIM["easy"],
                 fg=GREEN_L, font=f(10), wraplength=720, justify="left",
                 padx=P, pady=12).pack(anchor="w")

        # ── Next button ─────────────────────────────────────────────
        tot    = len(self.queue)
        is_last = (self.idx + 1 >= tot)
        lbl    = "View Results" if is_last else "Next Scenario"
        btn    = RoundedButton(parent, lbl, self._next,
                               width=220, height=44, color=BLUE,
                               icon="📊" if is_last else "▶",
                               font_spec=f(11,"bold"), bg=BG)
        btn.pack(pady=(12, 4))
        tk.Label(parent, text="or press  Enter", bg=BG, fg=TXT3, font=f(9)).pack()

    def _next(self):
        self.idx += 1
        if self.idx >= len(self.queue):
            self._show_results()
        else:
            self._load()
            self._scroll.scroll_top()

    def _update_stats(self):
        s = self.session
        pct = round(s.correct/s.total*100) if s.total else 0
        self._s_score.config(text=str(s.score))
        self._s_correct.config(text=f"{s.correct} / {s.total}")
        self._s_acc.config(text=f"{pct}%" if s.total else "—")
        self._s_streak.config(text=str(s.streak))
        self._s_best.config(text=str(s.best_streak))
        self._tb_update()

        # Difficulty bars
        diff_cnt = {"easy":[0,0],"medium":[0,0],"hard":[0,0]}
        for r in s.results:
            diff_cnt[r["diff"]][1] += 1
            if r["correct"]: diff_cnt[r["diff"]][0] += 1
        for d, (fill, cnt) in self._diff_bars.items():
            c_num, t_num = diff_cnt[d]
            fill.place(relwidth=(c_num/t_num if t_num else 0))
            cnt.config(text=f"{c_num}/{t_num}")

    # ── Keyboard bindings ───────────────────────────────────────────
    def _kb_answer(self, v):
        if self.current_page == "game" and not self.answered:
            self._answer(v)
    def _kb_hint(self):
        if self.current_page == "game" and not self.hint_on and not self.answered:
            self._use_hint()
    def _kb_next(self):
        if self.current_page == "intro": self._start_game()
        elif self.current_page == "game" and self.answered: self._next()
    def _kb_escape(self):
        if self.current_page in ("game","results"): self._go_home()

    # ═══════════════════════════════════════════════════════════════
    #  RESULTS SCREEN
    # ═══════════════════════════════════════════════════════════════
    def _build_results_shell(self):
        """Shell only — content is rendered dynamically."""
        self._results_scroll = ScrollableFrame(self.pg_results, bg=BG)
        self._results_scroll.pack(fill="both", expand=True)

    def _show_results(self):
        # Re-render results every time
        inner = self._results_scroll.inner
        for w in inner.winfo_children(): w.destroy()
        self._tb_hide()
        self._render_results(inner)
        self._show("results")
        self._results_scroll.scroll_top()

    def _render_results(self, parent):
        s    = self.session
        tot  = s.total
        pct  = round(s.correct/tot*100) if tot else 0
        mins = int((time.time()-s.start_time)//60)
        secs = int((time.time()-s.start_time) % 60)

        if   pct >= 90: grade,gc,gl = "A+", GREEN,   "Security Expert"
        elif pct >= 75: grade,gc,gl = "B",  BLUE_L,  "Security Aware"
        elif pct >= 60: grade,gc,gl = "C",  AMBER,   "Developing Skills"
        elif pct >= 40: grade,gc,gl = "D",  "#f97316","Needs Improvement"
        else:           grade,gc,gl = "F",  RED,     "High Risk"

        # ── Hero banner ─────────────────────────────────────────────
        hero = tk.Frame(parent, bg=S1)
        hero.pack(fill="x")
        Separator(hero, orient="h").pack(fill="x", side="bottom")

        hero_inner = tk.Frame(hero, bg=S1)
        hero_inner.pack(expand=True, pady=28)

        grade_cv = tk.Canvas(hero_inner, width=130, height=130, bg=S1, highlightthickness=0)
        grade_cv.pack(side="left", padx=(0, 24))
        rrect(grade_cv, 4, 4, 126, 126, 16, fill=lerp_color(S1, gc, 0.08), outline=gc, width=2)
        grade_cv.create_text(65, 58, text=grade, fill=gc, font=f(48,"bold"))
        grade_cv.create_text(65, 104, text=gl, fill=gc, font=f(10,"bold"))

        info = tk.Frame(hero_inner, bg=S1)
        info.pack(side="left")
        tk.Label(info, text="Training Complete", bg=S1, fg=WHITE, font=f(22,"bold")).pack(anchor="w")
        tk.Label(info, text=f"Completed in  {mins}m {secs}s  ·  {tot} scenarios",
                 bg=S1, fg=TXT2, font=f(11)).pack(anchor="w", pady=(4,16))
        tk.Label(info, text=f"You scored  {s.score}  points",
                 bg=S1, fg=gc, font=f(18,"bold")).pack(anchor="w")

        # ── Metric grid ─────────────────────────────────────────────
        grid = tk.Frame(parent, bg=BG)
        grid.pack(fill="x", pady=(G,0))
        metrics = [
            (str(s.score),        "Total Points",   BLUE_L),
            (f"{s.correct}/{tot}","Correct Answers",GREEN),
            (f"{pct}%",           "Accuracy",       AMBER),
            (str(s.best_streak),  "Best Streak",    PURPLE),
        ]
        for col,(val,lbl,mc) in enumerate(metrics):
            grid.columnconfigure(col, weight=1)
            card = tk.Frame(grid, bg=S0, highlightbackground=BD, highlightthickness=1)
            card.grid(row=0, column=col, sticky="ew", padx=1, pady=1)
            tk.Label(card, text=val, bg=S0, fg=mc, font=f(28,"bold")).pack(pady=(18,2))
            tk.Label(card, text=lbl, bg=S0, fg=TXT2, font=f(9)).pack(pady=(0,18))

        # ── Accuracy bar ─────────────────────────────────────────────
        acc_sec = tk.Frame(parent, bg=BG)
        acc_sec.pack(fill="x", padx=P*2, pady=(P, G))
        Separator(parent).pack(fill="x")

        tk.Label(acc_sec, text="ACCURACY BREAKDOWN", bg=BG, fg=TXT3,
                 font=f(9,"bold")).pack(anchor="w", pady=(P,G))
        bar_outer = tk.Frame(acc_sec, bg=BD, height=14)
        bar_outer.pack(fill="x")
        bar_outer.pack_propagate(False)
        if tot > 0:
            c_ratio = s.correct / tot
            w_ratio = 1 - c_ratio
            if c_ratio > 0:
                tk.Frame(bar_outer, bg=GREEN).place(relx=0, rely=0, relwidth=c_ratio, relheight=1)
            if w_ratio > 0:
                tk.Frame(bar_outer, bg=RED).place(relx=c_ratio, rely=0, relwidth=w_ratio, relheight=1)
        row = tk.Frame(acc_sec, bg=BG)
        row.pack(anchor="w", pady=G)
        for clr, txt in [(GREEN, f"■  {s.correct} Correct"), (RED, f"■  {tot-s.correct} Incorrect"),
                         (AMBER, f"■  {s.hints} Hints Used")]:
            tk.Label(row, text=txt, bg=BG, fg=clr, font=f(9)).pack(side="left", padx=(0,16))

        Separator(parent).pack(fill="x")

        # ── Scenario breakdown ──────────────────────────────────────
        bd_wrap = tk.Frame(parent, bg=BG)
        bd_wrap.pack(fill="x", padx=P*2, pady=P)
        tk.Label(bd_wrap, text="SCENARIO BREAKDOWN", bg=BG, fg=TXT3,
                 font=f(9,"bold")).pack(anchor="w", pady=(0, G))

        # Column headers
        hrow = tk.Frame(bd_wrap, bg=S0)
        hrow.pack(fill="x")
        hrow.columnconfigure(1, weight=1)
        for col,(t,w,a) in enumerate([("#","4",  "center"), ("Scenario","1","w"),
                                       ("Type","6","center"), ("Diff","7","center"),
                                       ("Result","7","center"), ("Points","7","e")]):
            tk.Label(hrow, text=t, bg=S0, fg=TXT3, font=f(8,"bold"),
                     width=int(w) if w.isdigit() else 1, anchor=a).grid(
                         row=0, column=col, padx=4 if col==0 else 2, pady=6,
                         sticky="ew" if col==1 else "")
        hrow.columnconfigure(1, weight=1)

        Separator(bd_wrap).pack(fill="x")

        for i, r in enumerate(s.results):
            row = tk.Frame(bd_wrap, bg=S1 if i%2==0 else S0)
            row.pack(fill="x")
            row.columnconfigure(1, weight=1)

            ri_bg = row.cget("bg")
            c_fg  = GREEN if r["correct"] else RED
            c_sym = "✓" if r["correct"] else "✗"
            d_col = DC.get(r["diff"], TXT2)

            tk.Label(row, text=str(i+1), bg=ri_bg, fg=TXT3,
                     font=f(9), width=4, anchor="center").grid(row=0, column=0, padx=4, pady=8)
            tk.Label(row, text=r["title"], bg=ri_bg, fg=TXT,
                     font=f(10), anchor="w").grid(row=0, column=1, padx=2, pady=8, sticky="ew")
            tk.Label(row, text="PHISH" if r["is_phish"] else "LEGIT",
                     bg=ri_bg, fg=RED if r["is_phish"] else GREEN,
                     font=f(8,"bold"), width=6, anchor="center").grid(row=0, column=2, padx=2)
            tk.Label(row, text=r["diff"][:3].upper(), bg=ri_bg, fg=d_col,
                     font=f(8,"bold"), width=7, anchor="center").grid(row=0, column=3, padx=2)
            tk.Label(row, text=c_sym, bg=ri_bg, fg=c_fg,
                     font=f(12,"bold"), width=7, anchor="center").grid(row=0, column=4, padx=2)
            tk.Label(row, text=f"+{r['pts']}", bg=ri_bg,
                     fg=GREEN if r["pts"]>0 else TXT3,
                     font=f(10,"bold"), width=7, anchor="e").grid(row=0, column=5, padx=8)

        Separator(parent).pack(fill="x")

        # ── Key takeaways ───────────────────────────────────────────
        tips_wrap = tk.Frame(parent, bg=BG)
        tips_wrap.pack(fill="x", padx=P*2, pady=P)
        tk.Label(tips_wrap, text="KEY TAKEAWAYS", bg=BG, fg=TXT3,
                 font=f(9,"bold")).pack(anchor="w", pady=(0, G))
        tips_card = tk.Frame(tips_wrap, bg=S0, highlightbackground=BD, highlightthickness=1)
        tips_card.pack(fill="x")

        takeaways = [
            ("🔍", "Check sender domains character by character — attackers exploit single-character swaps."),
            ("🔗", "Never click links in emails. Navigate directly to the official website."),
            ("⚡", "Urgency and threats are social engineering tools. Pause and verify before acting."),
            ("📞", "Verify all wire transfers by calling the requestor using a known, trusted number."),
            ("🌐", "Examine TLDs carefully — .net, .co, .org variants impersonate .com brands."),
            ("🤝", "Multi-brand emails fake multiple companies at once. Verify every domain independently."),
            ("📢", "Report every suspicious message to your IT security team — even if you're unsure."),
        ]
        for i, (icon, tip) in enumerate(takeaways):
            r = tk.Frame(tips_card, bg=(S1 if i%2==0 else S0))
            r.pack(fill="x")
            tk.Label(r, text=icon, bg=r.cget("bg"), font=f(12),
                     width=3).pack(side="left", padx=(P, 4), pady=10)
            tk.Label(r, text=tip, bg=r.cget("bg"), fg=TXT2, font=f(10),
                     wraplength=720, justify="left", anchor="w").pack(side="left", padx=4, pady=10)

        # ── Actions ─────────────────────────────────────────────────
        btn_row = tk.Frame(parent, bg=BG)
        btn_row.pack(pady=P*2)
        RoundedButton(btn_row, "Train Again", self._go_home,
                      width=200, height=46, color=BLUE, icon="↺",
                      font_spec=f(11,"bold"), bg=BG).pack(side="left", padx=8)
        RoundedButton(btn_row, "Quit", self.quit,
                      width=150, height=46, color=RED, icon="✕",
                      font_spec=f(11,"bold"), bg=BG).pack(side="left", padx=8)

    def _go_home(self):
        self._tb_hide()
        self._show("intro")
        self._orb_t = 0.0
        self._animate_orb()


# ═══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = App()
    app.mainloop()
