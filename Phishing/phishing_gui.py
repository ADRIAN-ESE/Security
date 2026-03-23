#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║     PHISHING AWARENESS SIMULATOR  —  GUI Edition  v2.0  ║
║          Built with Python tkinter (stdlib only)         ║
╚══════════════════════════════════════════════════════════╝
Run: python3 phishing_gui.py
Requires: Python 3.9+ (tkinter is included in standard library)
"""

import tkinter as tk
from tkinter import ttk, font as tkfont
import random
import math
import time
import threading
from dataclasses import dataclass, field
from typing import Optional

# ══════════════════════════════════════════════════════════════
#  THEME  — Cybersecurity dark palette
# ══════════════════════════════════════════════════════════════
TH = {
    "bg":          "#080c14",
    "surface":     "#0d1520",
    "surface2":    "#111d2e",
    "border":      "#1a2d44",
    "accent":      "#00d4ff",
    "accent2":     "#ff3860",
    "accent3":     "#00ff88",
    "warn":        "#ffb020",
    "text":        "#c8dff5",
    "text_dim":    "#4a6480",
    "text_muted":  "#2a3d52",
    "easy":        "#00ff88",
    "medium":      "#ffb020",
    "hard":        "#ff3860",
    "white":       "#ffffff",
    "email_bg":    "#060a11",
    "toolbar":     "#0d1824",
}

FONTS = {
    "mono":        ("Courier New",  10, "normal"),
    "mono_b":      ("Courier New",  10, "bold"),
    "mono_lg":     ("Courier New",  13, "normal"),
    "mono_sm":     ("Courier New",   9, "normal"),
    "title":       ("Courier New",  22, "bold"),
    "heading":     ("Courier New",  14, "bold"),
    "subhead":     ("Courier New",  11, "bold"),
    "body":        ("Courier New",  11, "normal"),
    "tiny":        ("Courier New",   8, "normal"),
    "score_big":   ("Courier New",  32, "bold"),
    "grade":       ("Courier New",  64, "bold"),
}


# ══════════════════════════════════════════════════════════════
#  DATA MODELS
# ══════════════════════════════════════════════════════════════
@dataclass
class RedFlag:
    category: str
    description: str

@dataclass
class Scenario:
    id: int
    title: str
    msg_type: str        # "email" | "sms" | "call"
    is_phishing: bool
    difficulty: str      # "easy" | "medium" | "hard"
    sender: str
    subject: Optional[str]
    body: str
    url: Optional[str]
    red_flags: list
    explanation: str
    tip: str

@dataclass
class SessionStats:
    score: int = 0
    total: int = 0
    correct: int = 0
    streak: int = 0
    best_streak: int = 0
    hint_count: int = 0
    results: list = field(default_factory=list)
    start_time: float = field(default_factory=time.time)


# ══════════════════════════════════════════════════════════════
#  SCENARIO DATABASE  (10 rich scenarios)
# ══════════════════════════════════════════════════════════════
SCENARIOS = [
    Scenario(
        id=1, title="PayPal Account Suspended", msg_type="email",
        is_phishing=True, difficulty="easy",
        sender="security-alert@paypa1.com",
        subject="⚠️ URGENT: Your account has been compromised!",
        body=(
            "Dear Valued Customer,\n\n"
            "We have detected SUSPICIOUS ACTIVITY on your PayPal account.\n"
            "Your account will be PERMANENTLY SUSPENDED in 24 hours unless\n"
            "you verify your identity immediately.\n\n"
            "Click the link below to secure your account NOW:\n\n"
            "    http://paypa1-secure-login.xyz/verify?token=abc123\n\n"
            "Do NOT ignore this message. Failure to act will result in\n"
            "permanent account closure and loss of all funds.\n\n"
            "PayPal Security Team\n"
            "© 2025 PayPal Inc. All rights reserved."
        ),
        url="http://paypa1-secure-login.xyz/verify?token=abc123",
        red_flags=[
            RedFlag("Typosquatted Domain", "paypa1.com — the letter 'l' is replaced by '1'"),
            RedFlag("Urgency Tactics", "Artificial 24-hour deadline to force quick action"),
            RedFlag("Threatening Language", "Threats of permanent closure and fund loss"),
            RedFlag("Suspicious URL", "paypa1-secure-login.xyz is not PayPal's real domain"),
            RedFlag("Generic Greeting", "'Dear Valued Customer' — real PayPal uses your name"),
            RedFlag("ALL CAPS Manipulation", "CAPS words are classic social engineering"),
        ],
        explanation=(
            "Classic PayPal phishing. The attacker replaced 'l' with '1' in the domain "
            "(typosquatting). Legitimate companies never threaten account suspension via email "
            "and always address you by your registered name. Hover any link before clicking — "
            "the URL would reveal the fake domain immediately."
        ),
        tip="Always hover over links to preview the real URL. Check every character of the domain."
    ),

    Scenario(
        id=2, title="Chase Bank Statement", msg_type="email",
        is_phishing=False, difficulty="easy",
        sender="statements@chase.com",
        subject="Your October 2025 statement is ready",
        body=(
            "Hi Alex,\n\n"
            "Your Chase checking account statement for October 2025\n"
            "is now available to view online.\n\n"
            "To view your statement, please sign in to chase.com\n"
            "or open the Chase mobile app. For your security, we\n"
            "never include direct login links in our emails.\n\n"
            "If you have questions, you can:\n"
            "  • Call us at 1-800-935-9935\n"
            "  • Visit chase.com/support\n"
            "  • Visit any Chase branch\n\n"
            "Chase Customer Service\n"
            "© 2025 JPMorgan Chase & Co."
        ),
        url=None,
        red_flags=[],
        explanation=(
            "Legitimate bank email. Notice: it addresses you by your real name, explicitly "
            "states it does NOT include login links, uses the verified @chase.com domain, "
            "and provides multiple verifiable contact methods. Real banks never embed "
            "clickable login buttons in notification emails."
        ),
        tip="Legitimate banks explicitly tell you they won't include login links. That transparency is the trust signal."
    ),

    Scenario(
        id=3, title="USPS Redelivery Fee", msg_type="sms",
        is_phishing=True, difficulty="easy",
        sender="+1-555-019-2847",
        subject=None,
        body=(
            "[USPS] Your package #7392018 could not be delivered.\n\n"
            "A small $0.30 redelivery fee is required to reschedule.\n"
            "Pay now to avoid return to sender:\n\n"
            "    http://usps-redelivery.com/pay?id=739201\n\n"
            "This link expires in 12 hours."
        ),
        url="http://usps-redelivery.com/pay?id=739201",
        red_flags=[
            RedFlag("Fake Domain", "usps-redelivery.com — the real site is usps.com only"),
            RedFlag("Smishing Attack", "USPS never requests payment via SMS text message"),
            RedFlag("Micro-Payment Trick", "$0.30 fee feels trivial, bypassing your skepticism"),
            RedFlag("Unknown Phone Number", "USPS uses official shortcodes, not random mobile numbers"),
            RedFlag("Expiry Pressure", "'Expires in 12 hours' creates artificial urgency"),
        ],
        explanation=(
            "This is 'smishing' — SMS phishing. USPS never charges redelivery fees via text. "
            "The tiny $0.30 amount is deliberate: it feels too small to worry about, so you "
            "click without scrutinizing the URL. Once on the fake site, they capture your "
            "card details for much larger fraudulent charges."
        ),
        tip="If you're unsure about a delivery, open your browser and navigate to usps.com directly — never via a link."
    ),

    Scenario(
        id=4, title="IT Security Patch Notice", msg_type="email",
        is_phishing=True, difficulty="medium",
        sender="it-support@company-helpdesk.net",
        subject="[URGENT] Mandatory Security Update — Action Required Today",
        body=(
            "Hello,\n\n"
            "Our security team has identified that your workstation is\n"
            "missing a critical patch (CVE-2025-4821) that addresses a\n"
            "zero-day remote code execution vulnerability.\n\n"
            "You MUST install this update before 5:00 PM today to maintain\n"
            "access to the corporate network. Systems without the patch\n"
            "will be automatically quarantined.\n\n"
            "Download and run the patch now:\n\n"
            "    https://company-helpdesk.net/patches/urgent/install.exe\n\n"
            "Ticket #: Auto-generated\n"
            "IT Security & Compliance Team"
        ),
        url="https://company-helpdesk.net/patches/urgent/install.exe",
        red_flags=[
            RedFlag("External Domain", "company-helpdesk.net ≠ your company's actual IT domain"),
            RedFlag("Executable Download", "Asking you to run an .exe file from an email link"),
            RedFlag("Vague CVE Reference", "Real patches come through WSUS/Jamf, not email links"),
            RedFlag("Network Quarantine Threat", "Fear of losing network access pressures quick action"),
            RedFlag("No Real Ticket Number", "'Auto-generated' — real tickets have specific IDs like INC-2847"),
        ],
        explanation=(
            "Spear-phishing disguised as internal IT. The domain company-helpdesk.net looks "
            "plausible but is external. Your real IT department patches via automated tools "
            "(WSUS, Jamf, Intune) — never by asking you to download and run an .exe manually. "
            "The fake CVE number and threat of quarantine are social engineering triggers."
        ),
        tip="Verify all IT requests by calling the helpdesk using the number from your company intranet — not the email."
    ),

    Scenario(
        id=5, title="LinkedIn Invitation", msg_type="email",
        is_phishing=False, difficulty="medium",
        sender="messages-noreply@linkedin.com",
        subject="Sarah Chen wants to connect on LinkedIn",
        body=(
            "Hi there,\n\n"
            "Sarah Chen (Senior Product Manager at Acme Corp)\n"
            "wants to connect with you on LinkedIn.\n\n"
            "To view Sarah's profile and respond to her invitation,\n"
            "please sign in to linkedin.com.\n\n"
            "The LinkedIn Team\n\n"
            "─────────────────────────────────────────\n"
            "Unsubscribe  ·  Help Center  ·  Privacy Policy\n"
            "LinkedIn Corporation\n"
            "1000 W Maude Ave, Sunnyvale, CA 94085"
        ),
        url=None,
        red_flags=[],
        explanation=(
            "Legitimate LinkedIn notification. Signals: official messages-noreply@linkedin.com "
            "sender, no embedded login link (directs to linkedin.com to sign in), includes "
            "LinkedIn's real physical address, and provides unsubscribe/privacy options as "
            "required by CAN-SPAM and GDPR regulations."
        ),
        tip="Legitimate commercial emails are legally required to include a physical address and unsubscribe option."
    ),

    Scenario(
        id=6, title="CEO Wire Transfer Request", msg_type="email",
        is_phishing=True, difficulty="medium",
        sender="j.morrison@acmecorp-hq.co",
        subject="Confidential — Urgent Wire Transfer Needed",
        body=(
            "Hi,\n\n"
            "I need you to process a wire transfer of $47,500 to our\n"
            "new vendor today. We're closing a critical deal and this\n"
            "is extremely time-sensitive.\n\n"
            "I'm currently in back-to-back board meetings and can't\n"
            "take calls. Please handle this urgently and keep it\n"
            "confidential until I can debrief the team tomorrow.\n\n"
            "Beneficiary: Global Trade Solutions LLC\n"
            "Bank: First National Bank\n"
            "Account: 7734882100982\n"
            "Routing: 021000021\n\n"
            "Thanks for handling this.\n\n"
            "James Morrison\n"
            "Chief Executive Officer"
        ),
        url=None,
        red_flags=[
            RedFlag("Domain Impersonation", "acmecorp-hq.co ≠ your real company domain (acmecorp.com)"),
            RedFlag("Business Email Compromise", "Impersonates CEO to authorize fraudulent transfer"),
            RedFlag("Secrecy Demand", "'Keep it confidential' prevents you from asking colleagues"),
            RedFlag("Convenient Unavailability", "'In board meetings' blocks phone verification"),
            RedFlag("No Purchase Order", "All legitimate vendor payments have an invoice and PO number"),
            RedFlag("Urgency + Large Amount", "Pressure to act fast before thinking critically"),
        ],
        explanation=(
            "Business Email Compromise (BEC) — one of the most costly cybercrimes globally. "
            "The attacker registered a lookalike domain (acmecorp-hq.co) and impersonates the CEO. "
            "The combination of urgency, secrecy, and the CEO being 'unavailable' is a textbook BEC pattern. "
            "Always verify wire transfers by calling the requestor using a known number."
        ),
        tip="Implement a mandatory out-of-band verification call for all wire transfers. One call can save everything."
    ),

    Scenario(
        id=7, title="GitHub Unauthorized Login Alert", msg_type="email",
        is_phishing=True, difficulty="hard",
        sender="noreply@github-security.com",
        subject="[GitHub] Suspicious sign-in from Moscow, Russia",
        body=(
            "Hi there,\n\n"
            "We detected a sign-in to your GitHub account from an\n"
            "unrecognized location and device.\n\n"
            "    Location:   Moscow, Russia\n"
            "    Device:     Windows 10, Chrome 118.0\n"
            "    IP Address: 185.220.101.47\n"
            "    Time:       Nov 3, 2025 at 03:14 UTC\n\n"
            "If this was you, no action is needed.\n\n"
            "If this was NOT you, your account may be compromised.\n"
            "Secure your account immediately:\n\n"
            "    https://github-security.com/secure?token=eyJhbGc...\n\n"
            "This link expires in 30 minutes.\n\n"
            "GitHub Security Team"
        ),
        url="https://github-security.com/secure?token=eyJhbGc...",
        red_flags=[
            RedFlag("Wrong Sender Domain", "github-security.com ≠ github.com (GitHub only uses @github.com)"),
            RedFlag("Fear Engineering", "Foreign location (Moscow) triggers panic to bypass critical thinking"),
            RedFlag("Token URL", "JWT token in URL harvests your session if clicked"),
            RedFlag("30-Minute Expiry", "Short window prevents you from calmly verifying"),
            RedFlag("Highly Polished", "Designed to look identical to real GitHub security alerts"),
        ],
        explanation=(
            "Extremely convincing phishing — the ONLY giveaway is the sender domain. "
            "GitHub ONLY sends email from @github.com, never from @github-security.com or any variant. "
            "The Moscow location is chosen specifically to trigger fear. When panicked, people click "
            "without checking domains. If you get a real GitHub alert, go directly to github.com."
        ),
        tip="Domain-check every security email. github-security.com is NOT github.com. Bookmark real sites."
    ),

    Scenario(
        id=8, title="AWS Cost Anomaly Alert", msg_type="email",
        is_phishing=False, difficulty="hard",
        sender="aws-cost-management@amazon.com",
        subject="[AWS] Cost anomaly detected — Account 123456789012",
        body=(
            "Hello,\n\n"
            "AWS Cost Anomaly Detection has identified unusual spending\n"
            "in your AWS account.\n\n"
            "Account ID:   123456789012\n"
            "Service:      Amazon EC2\n"
            "Anomaly:      $234.50 above expected spend\n"
            "Period:       Nov 1–3, 2025\n"
            "Monitor:      Monthly EC2 Budget Monitor\n\n"
            "To investigate this anomaly, sign in to the AWS Console\n"
            "at aws.amazon.com and navigate to:\n"
            "Billing > Cost Management > Cost Anomaly Detection\n\n"
            "AWS Cost Management\n"
            "Amazon Web Services, Inc.\n"
            "410 Terry Ave N, Seattle, WA 98109"
        ),
        url=None,
        red_flags=[],
        explanation=(
            "Legitimate AWS notification. Key trust signals: official @amazon.com sender, "
            "includes your specific 12-digit AWS Account ID (not a generic greeting), "
            "explicitly directs you to navigate manually to aws.amazon.com (no clickable link), "
            "and includes AWS's verified physical address."
        ),
        tip="Cloud providers always include your account ID in alerts. No account ID = suspicious."
    ),

    Scenario(
        id=9, title="DocuSign NDA for Signature", msg_type="email",
        is_phishing=True, difficulty="hard",
        sender="dse@docusign.net",
        subject="Please DocuSign: Mutual NDA — Review and Sign",
        body=(
            "Your signature has been requested on a document.\n\n"
            "    Document Title:  Mutual Non-Disclosure Agreement\n"
            "    Requested by:    contracts@globalpartners-llc.com\n"
            "    Expires:         48 hours from receipt\n\n"
            "REVIEW AND SIGN DOCUMENT:\n"
            "    https://app.docusign.net/sign?envelopeId=f3a9bc12...\n\n"
            "Do Not Share This Email — it contains your unique\n"
            "authentication code for document access.\n\n"
            "DocuSign Electronic Signature Service\n"
            "© 2025 DocuSign Inc. All rights reserved.\n"
            "221 Main Street, Suite 1000, San Francisco, CA 94105"
        ),
        url="https://app.docusign.net/sign?envelopeId=f3a9bc12...",
        red_flags=[
            RedFlag("Wrong TLD", "docusign.net ≠ docusign.com — DocuSign uses .com exclusively"),
            RedFlag("Unexpected Document", "No prior context about this NDA or the sender company"),
            RedFlag("'Do Not Share' Warning", "Discourages forwarding to a colleague who might spot it"),
            RedFlag("48-Hour Expiry Pressure", "Urgency to sign without verifying the request"),
            RedFlag("Unknown Requester", "globalpartners-llc.com — not a verified business contact"),
        ],
        explanation=(
            "DocuSign ONLY sends from @docusign.com — never .net or other TLDs. "
            "This is a credential-harvesting attack via a fake document signing page. "
            "The 'Do Not Share' warning cleverly discourages you from asking a colleague. "
            "Always verify unexpected signature requests directly with the supposed sender."
        ),
        tip="Check TLDs very carefully — attackers buy .net, .co, .org variants of every major brand."
    ),

    Scenario(
        id=10, title="Slack Message from Colleague", msg_type="email",
        is_phishing=True, difficulty="hard",
        sender="no-reply@slack-notifications.com",
        subject="Jordan Rivera sent you a direct message on Slack",
        body=(
            "Jordan Rivera sent you a new direct message:\n\n"
            '    "Hey! Quick favor — can you review the mockup I\n'
            "     shared for tomorrow's presentation? The Figma\n"
            "     link kept breaking so I exported it separately:\n\n"
            "         https://figma-share.net/d/mockup-final-v3\n\n"
            '     Lmk what you think before EOD, thanks!"\n\n'
            "─────────────────────────────────────────────────\n"
            "Reply in Slack: https://slack-notifications.com/open?msg=...\n\n"
            "Slack Technologies · 500 Howard St · San Francisco, CA"
        ),
        url="https://figma-share.net/d/mockup-final-v3",
        red_flags=[
            RedFlag("Fake Slack Domain", "slack-notifications.com ≠ slack.com (Slack emails @slack.com)"),
            RedFlag("Fake Figma Domain", "figma-share.net ≠ figma.com — lookalike domain"),
            RedFlag("Dual Brand Spoofing", "Simultaneously impersonates Slack AND Figma"),
            RedFlag("Known Name Used", "Colleague's real name harvested from LinkedIn/social media"),
            RedFlag("Convenient Excuse", "'Figma kept breaking' explains the suspicious non-Figma link"),
            RedFlag("EOD Urgency", "'Before EOD' creates time pressure without seeming alarming"),
        ],
        explanation=(
            "Sophisticated dual-brand impersonation attack. Both slack-notifications.com and "
            "figma-share.net are fake domains. The attacker uses a real colleague's name (harvested "
            "from LinkedIn) to make this feel completely routine. The 'Figma was broken' excuse "
            "is engineered to explain away the suspicious link. Verify each domain independently."
        ),
        tip="In multi-brand emails, verify EVERY domain. A real Slack DM notification comes from @slack.com only."
    ),
]

POINTS = {"easy": 10, "medium": 20, "hard": 30}
DIFF_COLORS = {"easy": TH["easy"], "medium": TH["medium"], "hard": TH["hard"]}


# ══════════════════════════════════════════════════════════════
#  CUSTOM WIDGETS
# ══════════════════════════════════════════════════════════════

class AnimatedCounter:
    """Smoothly animates a number counting up."""
    def __init__(self, widget, attr, start, end, duration_ms=600, fmt="{}", callback=None):
        self.widget = widget
        self.attr = attr
        self.start = start
        self.end = end
        self.duration_ms = duration_ms
        self.fmt = fmt
        self.callback = callback
        self._step()

    def _step(self):
        now = time.time()
        if not hasattr(self, '_start_time'):
            self._start_time = now
        elapsed = (now - self._start_time) * 1000
        progress = min(elapsed / self.duration_ms, 1.0)
        # ease-out cubic
        t = 1 - (1 - progress) ** 3
        value = int(self.start + (self.end - self.start) * t)
        try:
            self.widget.config(**{self.attr: self.fmt.format(value)})
        except tk.TclError:
            return
        if progress < 1.0:
            self.widget.after(16, self._step)
        elif self.callback:
            self.callback()


class GlowButton(tk.Canvas):
    """A custom button with hover glow animation."""
    def __init__(self, parent, text, command, width=200, height=48,
                 color=TH["accent"], text_color=TH["accent"],
                 bg_color=TH["surface"], font=FONTS["subhead"], **kw):
        super().__init__(parent, width=width, height=height,
                         bg=TH["bg"], highlightthickness=0, cursor="hand2", **kw)
        self.text = text
        self.command = command
        self.width = width
        self.height = height
        self.color = color
        self.text_color = text_color
        self.bg_color = bg_color
        self.font_spec = font
        self._hover = False
        self._draw()
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _draw(self):
        self.delete("all")
        w, h = self.width, self.height
        alpha = 0.15 if self._hover else 0.06
        # border glow layers
        if self._hover:
            for i in range(4, 0, -1):
                shade = self._shade(self.color, 0.06 * i)
                self.create_rectangle(i, i, w-i, h-i, outline=shade, width=1)
        self.create_rectangle(2, 2, w-2, h-2,
                              outline=self.color,
                              fill=self._blend(self.bg_color, self.color, alpha),
                              width=1)
        self.create_text(w//2, h//2, text=self.text,
                         fill=TH["white"] if self._hover else self.text_color,
                         font=self.font_spec)

    def _blend(self, hex1, hex2, ratio):
        r1,g1,b1 = int(hex1[1:3],16), int(hex1[3:5],16), int(hex1[5:7],16)
        r2,g2,b2 = int(hex2[1:3],16), int(hex2[3:5],16), int(hex2[5:7],16)
        r = int(r1 + (r2-r1)*ratio)
        g = int(g1 + (g2-g1)*ratio)
        b = int(b1 + (b2-b1)*ratio)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _shade(self, hex_color, opacity):
        r,g,b = int(hex_color[1:3],16), int(hex_color[3:5],16), int(hex_color[5:7],16)
        r = min(255, int(r * opacity + 8 * (1-opacity)))
        g = min(255, int(g * opacity + 12 * (1-opacity)))
        b = min(255, int(b * opacity + 20 * (1-opacity)))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _on_enter(self, e):
        self._hover = True
        self._draw()

    def _on_leave(self, e):
        self._hover = False
        self._draw()

    def _on_click(self, e):
        self._draw()
        self.after(80, self.command)


class CircularProgress(tk.Canvas):
    """Animated circular progress ring."""
    def __init__(self, parent, size=120, thickness=8,
                 fg=TH["accent"], bg_ring=TH["border"], **kw):
        super().__init__(parent, width=size, height=size,
                         bg=TH["bg"], highlightthickness=0, **kw)
        self.size = size
        self.thickness = thickness
        self.fg = fg
        self.bg_ring = bg_ring
        self._value = 0
        self._draw(0)

    def set_value(self, pct, animate=True):
        if animate:
            self._animate_to(pct)
        else:
            self._value = pct
            self._draw(pct)

    def _animate_to(self, target):
        start = self._value
        start_t = time.time()
        def step():
            elapsed = (time.time() - start_t) * 1000
            progress = min(elapsed / 700, 1.0)
            t = 1 - (1 - progress) ** 3
            val = start + (target - start) * t
            self._value = val
            self._draw(val)
            if progress < 1.0:
                self.after(16, step)
        self.after(1, step)

    def _draw(self, pct):
        self.delete("all")
        s = self.size
        pad = self.thickness
        x0, y0, x1, y1 = pad, pad, s-pad, s-pad
        self.create_arc(x0, y0, x1, y1, start=90, extent=360,
                        outline=self.bg_ring, width=self.thickness, style="arc")
        if pct > 0:
            extent = -min(pct / 100 * 360, 359.9)
            self.create_arc(x0, y0, x1, y1, start=90, extent=extent,
                            outline=self.fg, width=self.thickness, style="arc")

    def set_text(self, text, color=TH["text"]):
        self.create_text(self.size//2, self.size//2,
                         text=text, fill=color, font=FONTS["subhead"])


class SegmentBar(tk.Canvas):
    """A multi-segment accuracy bar showing correct/wrong per difficulty."""
    def __init__(self, parent, width=400, height=20, **kw):
        super().__init__(parent, width=width, height=height,
                         bg=TH["surface"], highlightthickness=0, **kw)
        self.w = width
        self.h = height

    def draw(self, segments):
        """segments: list of (ratio, color)"""
        self.delete("all")
        x = 0
        for ratio, color in segments:
            w = int(ratio * self.w)
            if w > 0:
                self.create_rectangle(x, 0, x+w, self.h, fill=color, outline="")
            x += w
        if x < self.w:
            self.create_rectangle(x, 0, self.w, self.h, fill=TH["border"], outline="")


class ScanlineCanvas(tk.Canvas):
    """Background canvas with animated scanlines and grid."""
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=TH["bg"], highlightthickness=0, **kw)
        self._scan_y = 0
        self._after_id = None
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, e=None):
        self.after(50, self._draw_grid)

    def _draw_grid(self):
        self.delete("grid")
        w = self.winfo_width()
        h = self.winfo_height()
        spacing = 40
        for x in range(0, w, spacing):
            self.create_line(x, 0, x, h, fill="#0d1a2a", width=1, tags="grid")
        for y in range(0, h, spacing):
            self.create_line(0, y, w, y, fill="#0d1a2a", width=1, tags="grid")
        self.tag_lower("grid")


# ══════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════════════

class PhishingSimulator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Phishing Awareness Simulator  v2.0")
        self.geometry("1000x760")
        self.minsize(800, 640)
        self.configure(bg=TH["bg"])
        self.resizable(True, True)

        # Try to set app icon color via title bar
        try:
            self.tk.call('wm', 'iconphoto', self._w, tk.PhotoImage(width=1, height=1))
        except Exception:
            pass

        self.session = SessionStats()
        self.current_scenario_idx = 0
        self.scenario_queue: list[Scenario] = []
        self.hint_used_this_round = False
        self.answered_this_round = False
        self.selected_mode = tk.StringVar(value="full")

        self._build_ui()
        self._show_intro()

    # ── Layout ──────────────────────────────────────────────────
    def _build_ui(self):
        """One root frame that swaps child frames."""
        self.root_frame = tk.Frame(self, bg=TH["bg"])
        self.root_frame.pack(fill="both", expand=True)

        # Header strip (always visible)
        self._build_header()

        # Main content area
        self.content = tk.Frame(self.root_frame, bg=TH["bg"])
        self.content.pack(fill="both", expand=True, padx=0, pady=0)

        # Frames for each screen
        self.frame_intro   = tk.Frame(self.content, bg=TH["bg"])
        self.frame_game    = tk.Frame(self.content, bg=TH["bg"])
        self.frame_results = tk.Frame(self.content, bg=TH["bg"])

        for f in (self.frame_intro, self.frame_game, self.frame_results):
            f.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._build_intro()
        self._build_game()
        self._build_results()

    def _build_header(self):
        hdr = tk.Frame(self.root_frame, bg=TH["surface"], height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        inner = tk.Frame(hdr, bg=TH["surface"])
        inner.pack(fill="both", expand=True, padx=20)

        # Logo / title
        tk.Label(inner, text="⚠  PHISHING AWARENESS SIMULATOR",
                 bg=TH["surface"], fg=TH["accent"],
                 font=FONTS["heading"]).pack(side="left", pady=12)

        tk.Label(inner, text="v2.0",
                 bg=TH["surface"], fg=TH["text_dim"],
                 font=FONTS["tiny"]).pack(side="left", padx=8, pady=16)

        # Live score chips (hidden until game starts)
        self.hdr_score_frame = tk.Frame(inner, bg=TH["surface"])
        self.hdr_score_frame.pack(side="right", pady=8)

        self.hdr_score_lbl = self._chip(self.hdr_score_frame, "0 pts", TH["accent"])
        self.hdr_score_lbl.pack(side="right", padx=4)
        self.hdr_streak_lbl = self._chip(self.hdr_score_frame, "0🔥", TH["warn"])
        self.hdr_streak_lbl.pack(side="right", padx=4)
        self.hdr_score_frame.pack_forget()

        # Thin border line
        tk.Frame(self.root_frame, bg=TH["border"], height=1).pack(fill="x")

    def _chip(self, parent, text, fg):
        f = tk.Frame(parent, bg=TH["surface2"],
                     highlightbackground=TH["border"], highlightthickness=1)
        lbl = tk.Label(f, text=text, bg=TH["surface2"], fg=fg, font=FONTS["mono_sm"],
                       padx=10, pady=4)
        lbl.pack()
        f.lbl = lbl
        return f

    # ── INTRO SCREEN ─────────────────────────────────────────────
    def _build_intro(self):
        f = self.frame_intro

        # Centered content wrapper
        wrap = tk.Frame(f, bg=TH["bg"])
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        # Hero icon (animated with canvas)
        self.hero_canvas = tk.Canvas(wrap, width=100, height=100,
                                     bg=TH["bg"], highlightthickness=0)
        self.hero_canvas.pack(pady=(0, 10))
        self._draw_hero_icon()

        tk.Label(wrap, text="Can You Spot the Phish?",
                 bg=TH["bg"], fg=TH["white"],
                 font=("Courier New", 24, "bold")).pack()

        tk.Label(wrap, text="Cybersecurity Awareness Training  ·  10 Real-World Scenarios",
                 bg=TH["bg"], fg=TH["text_dim"],
                 font=FONTS["mono_sm"]).pack(pady=(4, 24))

        # Mode selection
        modes_frame = tk.Frame(wrap, bg=TH["bg"])
        modes_frame.pack(pady=(0, 24))

        modes = [
            ("full",   "📋  Full Training",    "All 10 scenarios · All difficulties"),
            ("quick",  "⚡  Quick Quiz",       "5 random scenarios · Mixed"),
            ("hard",   "🔥  Hard Mode",        "Expert scenarios only"),
            ("easy",   "🟢  Easy Start",       "Easy scenarios only · Beginner"),
        ]

        self.mode_buttons = []
        row = tk.Frame(modes_frame, bg=TH["bg"])
        row.pack()
        for i, (mode_id, label, desc) in enumerate(modes):
            card = self._mode_card(row, mode_id, label, desc)
            card.grid(row=0, column=i, padx=6)
            self.mode_buttons.append((mode_id, card))

        self._update_mode_selection()

        # Feature highlights
        feats = tk.Frame(wrap, bg=TH["surface"],
                         highlightbackground=TH["border"], highlightthickness=1)
        feats.pack(pady=(0, 28), ipadx=20, ipady=12)

        feat_row = tk.Frame(feats, bg=TH["surface"])
        feat_row.pack()

        for icon, label in [("🎯","Realistic Scenarios"), ("🚩","Red Flag Analysis"),
                             ("📊","Detailed Scoring"), ("💡","Pro Security Tips")]:
            fc = tk.Frame(feat_row, bg=TH["surface"])
            fc.pack(side="left", padx=16)
            tk.Label(fc, text=icon, bg=TH["surface"], font=("Courier New", 18)).pack()
            tk.Label(fc, text=label, bg=TH["surface"], fg=TH["text_dim"],
                     font=FONTS["tiny"]).pack()

        # Start button
        self.start_btn = GlowButton(wrap, "▶  BEGIN TRAINING", self._start_game,
                                    width=260, height=52, color=TH["accent"],
                                    font=("Courier New", 12, "bold"))
        self.start_btn.pack()

        # Animate hero icon
        self._animate_hero()

    def _draw_hero_icon(self, offset=0):
        c = self.hero_canvas
        c.delete("all")
        y_off = int(math.sin(offset) * 6)
        # Glow rings
        for r, alpha in [(44, "#0a1e30"), (38, "#0d2540"), (32, "#0f2d4a")]:
            c.create_oval(50-r, 50+y_off-r, 50+r, 50+y_off+r, fill=alpha, outline="")
        c.create_oval(18, 18+y_off, 82, 82+y_off, fill=TH["surface2"], outline=TH["accent"], width=2)
        c.create_text(50, 50+y_off, text="🎣", font=("", 28))

    def _animate_hero(self):
        self._hero_t = getattr(self, '_hero_t', 0) + 0.06
        self._draw_hero_icon(self._hero_t)
        self._hero_after = self.after(40, self._animate_hero)

    def _mode_card(self, parent, mode_id, label, desc):
        card = tk.Frame(parent, bg=TH["surface2"], cursor="hand2",
                        highlightthickness=1)
        tk.Label(card, text=label, bg=TH["surface2"], fg=TH["text"],
                 font=FONTS["subhead"], padx=16, pady=8).pack()
        tk.Label(card, text=desc, bg=TH["surface2"], fg=TH["text_dim"],
                 font=FONTS["tiny"], padx=12).pack(pady=(0, 8))
        card.bind("<Button-1>", lambda e, m=mode_id: self._select_mode(m))
        for w in card.winfo_children():
            w.bind("<Button-1>", lambda e, m=mode_id: self._select_mode(m))
        return card

    def _select_mode(self, mode_id):
        self.selected_mode.set(mode_id)
        self._update_mode_selection()

    def _update_mode_selection(self):
        mode = self.selected_mode.get()
        for mode_id, card in self.mode_buttons:
            selected = (mode_id == mode)
            card.config(
                highlightbackground=TH["accent"] if selected else TH["border"],
                bg=TH["surface"] if selected else TH["surface2"]
            )
            for w in card.winfo_children():
                w.config(bg=TH["surface"] if selected else TH["surface2"],
                         fg=TH["white"] if selected else (TH["text"] if isinstance(w, tk.Label) and w.cget('font') == str(FONTS["subhead"]) else TH["text_dim"]))

    # ── GAME SCREEN ──────────────────────────────────────────────
    def _build_game(self):
        f = self.frame_game

        # ── Left sidebar: stats
        self.sidebar = tk.Frame(f, bg=TH["surface"], width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        # ── Right: scenario + controls
        self.main_area = tk.Frame(f, bg=TH["bg"])
        self.main_area.pack(side="left", fill="both", expand=True)
        self._build_main_area()

    def _build_sidebar(self):
        sb = self.sidebar
        tk.Frame(sb, bg=TH["border"], height=1).pack(fill="x")

        # Progress ring
        ring_frame = tk.Frame(sb, bg=TH["surface"])
        ring_frame.pack(pady=20)
        self.progress_ring = CircularProgress(ring_frame, size=110, thickness=7)
        self.progress_ring.pack()
        self.progress_text = tk.Label(ring_frame, text="0 / 0",
                                      bg=TH["surface"], fg=TH["text_dim"],
                                      font=FONTS["tiny"])
        self.progress_text.pack(pady=(4, 0))

        tk.Frame(sb, bg=TH["border"], height=1).pack(fill="x", padx=16)

        # Score display
        self._sb_stat(sb, "SCORE", "score_big_lbl", "0", TH["accent"], FONTS["score_big"])
        self._sb_stat(sb, "CORRECT", "correct_lbl", "0 / 0", TH["accent3"], FONTS["heading"])
        self._sb_stat(sb, "ACCURACY", "accuracy_lbl", "—", TH["text"], FONTS["heading"])

        tk.Frame(sb, bg=TH["border"], height=1).pack(fill="x", padx=16, pady=4)

        self._sb_stat(sb, "🔥 STREAK", "streak_lbl", "0", TH["warn"], FONTS["heading"])
        self._sb_stat(sb, "BEST STREAK", "best_streak_lbl", "0", TH["text_dim"], FONTS["mono_b"])

        tk.Frame(sb, bg=TH["border"], height=1).pack(fill="x", padx=16, pady=8)

        # Difficulty breakdown mini-chart
        tk.Label(sb, text="DIFFICULTY CHART", bg=TH["surface"],
                 fg=TH["text_muted"], font=FONTS["tiny"]).pack(padx=16)

        self.diff_bars = {}
        for diff, color in [("easy", TH["easy"]), ("medium", TH["medium"]), ("hard", TH["hard"])]:
            row = tk.Frame(sb, bg=TH["surface"])
            row.pack(fill="x", padx=16, pady=2)
            tk.Label(row, text=diff.upper()[:3], bg=TH["surface"], fg=color,
                     font=FONTS["tiny"], width=4, anchor="w").pack(side="left")
            bar_bg = tk.Frame(row, bg=TH["border"], height=6)
            bar_bg.pack(side="left", fill="x", expand=True, pady=2)
            bar = tk.Frame(bar_bg, bg=color, height=6)
            bar.place(relx=0, rely=0, relheight=1, relwidth=0)
            self.diff_bars[diff] = (bar, bar_bg)
            tk.Label(row, text="0/0", bg=TH["surface"], fg=TH["text_muted"],
                     font=FONTS["tiny"], width=5).pack(side="right")
            self.diff_bars[diff] = (bar, bar_bg, row.winfo_children()[-1])

        # Hint button
        self.hint_btn = GlowButton(sb, "💡  SHOW HINT", self._use_hint,
                                   width=168, height=36,
                                   color=TH["warn"], font=FONTS["mono_sm"])
        self.hint_btn.pack(pady=20)
        self.hint_cost_lbl = tk.Label(sb, text="Costs 5 points",
                                      bg=TH["surface"], fg=TH["text_muted"],
                                      font=FONTS["tiny"])
        self.hint_cost_lbl.pack()

    def _sb_stat(self, parent, label, attr_name, initial, color, font_spec):
        frame = tk.Frame(parent, bg=TH["surface"])
        frame.pack(fill="x", padx=16, pady=6)
        tk.Label(frame, text=label, bg=TH["surface"], fg=TH["text_muted"],
                 font=FONTS["tiny"]).pack(anchor="w")
        lbl = tk.Label(frame, text=initial, bg=TH["surface"], fg=color, font=font_spec)
        lbl.pack(anchor="w")
        setattr(self, attr_name, lbl)

    def _build_main_area(self):
        ma = self.main_area

        # ── Top info bar
        info_bar = tk.Frame(ma, bg=TH["surface2"], height=40)
        info_bar.pack(fill="x")
        info_bar.pack_propagate(False)

        self.scenario_title_lbl = tk.Label(info_bar, text="",
                                           bg=TH["surface2"], fg=TH["white"],
                                           font=FONTS["subhead"])
        self.scenario_title_lbl.pack(side="left", padx=16, pady=8)

        self.diff_lbl = tk.Label(info_bar, text="",
                                 bg=TH["surface2"], fg=TH["text"],
                                 font=FONTS["tiny"])
        self.diff_lbl.pack(side="right", padx=16)

        self.type_lbl = tk.Label(info_bar, text="",
                                 bg=TH["surface2"], fg=TH["text_dim"],
                                 font=FONTS["tiny"])
        self.type_lbl.pack(side="right", padx=8)

        # ── Scrollable message area
        msg_wrap = tk.Frame(ma, bg=TH["bg"])
        msg_wrap.pack(fill="both", expand=True, padx=16, pady=12)

        self.msg_canvas = tk.Canvas(msg_wrap, bg=TH["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(msg_wrap, orient="vertical",
                                 command=self.msg_canvas.yview,
                                 bg=TH["border"], troughcolor=TH["surface"])
        self.msg_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.msg_canvas.pack(side="left", fill="both", expand=True)

        self.msg_inner = tk.Frame(self.msg_canvas, bg=TH["bg"])
        self.msg_canvas_window = self.msg_canvas.create_window(
            (0, 0), window=self.msg_inner, anchor="nw")

        self.msg_inner.bind("<Configure>", self._on_msg_resize)
        self.msg_canvas.bind("<Configure>", self._on_canvas_resize)
        self.msg_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # ── Hint area
        self.hint_area = tk.Frame(ma, bg=TH["bg"])
        self.hint_area.pack(fill="x", padx=16)

        # ── Answer buttons
        self.answer_frame = tk.Frame(ma, bg=TH["bg"])
        self.answer_frame.pack(fill="x", padx=16, pady=12)

        lbl = tk.Label(self.answer_frame,
                       text="▸  Is this message PHISHING or LEGITIMATE?",
                       bg=TH["bg"], fg=TH["text_dim"], font=FONTS["mono_sm"])
        lbl.pack(pady=(0, 10))

        btn_row = tk.Frame(self.answer_frame, bg=TH["bg"])
        btn_row.pack()

        self.phish_btn = GlowButton(btn_row, "🎣  PHISHING", lambda: self._answer(True),
                                    width=220, height=52,
                                    color=TH["accent2"], font=FONTS["subhead"])
        self.phish_btn.pack(side="left", padx=8)

        self.legit_btn = GlowButton(btn_row, "✅  LEGITIMATE", lambda: self._answer(False),
                                    width=220, height=52,
                                    color=TH["accent3"], font=FONTS["subhead"])
        self.legit_btn.pack(side="left", padx=8)

        # ── Feedback area (hidden until answered)
        self.feedback_outer = tk.Frame(ma, bg=TH["bg"])
        self.feedback_outer.pack(fill="x", padx=16, pady=(0, 12))

    def _on_msg_resize(self, e):
        self.msg_canvas.configure(scrollregion=self.msg_canvas.bbox("all"))

    def _on_canvas_resize(self, e):
        self.msg_canvas.itemconfig(self.msg_canvas_window, width=e.width)

    def _on_mousewheel(self, e):
        self.msg_canvas.yview_scroll(int(-1*(e.delta/120)), "units")

    # ── RESULTS SCREEN ───────────────────────────────────────────
    def _build_results(self):
        f = self.frame_results

        # Scrollable
        canvas = tk.Canvas(f, bg=TH["bg"], highlightthickness=0)
        sb = tk.Scrollbar(f, orient="vertical", command=canvas.yview,
                          bg=TH["border"], troughcolor=TH["surface"])
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self.results_inner = tk.Frame(canvas, bg=TH["bg"])
        win = canvas.create_window((0, 0), window=self.results_inner, anchor="nw")
        self.results_inner.bind("<Configure>",
                                lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))

    # ══════════════════════════════════════════════════════════════
    #  GAME LOGIC
    # ══════════════════════════════════════════════════════════════

    def _start_game(self):
        mode = self.selected_mode.get()
        pool = list(SCENARIOS)

        if mode == "quick":
            queue = random.sample(pool, min(5, len(pool)))
        elif mode == "hard":
            queue = [s for s in pool if s.difficulty == "hard"]
        elif mode == "easy":
            queue = [s for s in pool if s.difficulty == "easy"]
        else:
            queue = random.sample(pool, len(pool))

        self.scenario_queue = queue
        self.current_scenario_idx = 0
        self.session = SessionStats()
        self.session.start_time = time.time()

        # Cancel hero animation
        if hasattr(self, '_hero_after'):
            self.after_cancel(self._hero_after)

        self.hdr_score_frame.pack(side="right", pady=8)
        self._show_game()
        self._load_scenario()

    def _show_intro(self):
        self.frame_intro.lift()

    def _show_game(self):
        self.frame_game.lift()

    def _show_results_screen(self):
        self.frame_results.lift()

    def _load_scenario(self):
        self.hint_used_this_round = False
        self.answered_this_round = False

        # Clear areas
        for w in self.msg_inner.winfo_children():
            w.destroy()
        for w in self.hint_area.winfo_children():
            w.destroy()
        for w in self.feedback_outer.winfo_children():
            w.destroy()

        # Re-enable buttons
        self.phish_btn.config(state="normal") if hasattr(self.phish_btn, 'config') else None
        self.answer_frame.pack(fill="x", padx=16, pady=12)
        self.hint_btn._hover = False
        self.hint_btn._draw()

        s = self.scenario_queue[self.current_scenario_idx]
        total = len(self.scenario_queue)
        idx = self.current_scenario_idx

        # Update info bar
        type_icons = {"email": "📧 EMAIL", "sms": "📱 SMS", "call": "📞 CALL"}
        self.scenario_title_lbl.config(text=f"#{idx+1}/{total}  ·  {s.title}")
        self.type_lbl.config(text=type_icons.get(s.msg_type, s.msg_type.upper()))
        diff_color = DIFF_COLORS[s.difficulty]
        self.diff_lbl.config(text=f"▲ {s.difficulty.upper()}", fg=diff_color)

        # Render message
        if s.msg_type == "email":
            self._render_email(s)
        else:
            self._render_sms(s)

        # Update progress
        pct = (idx / total) * 100
        self.progress_ring.set_value(pct)
        self.progress_text.config(text=f"{idx} / {total}")

        self._update_stats_display()
        self.msg_canvas.yview_moveto(0)

    def _render_email(self, s: Scenario):
        parent = self.msg_inner

        # Email client chrome
        toolbar = tk.Frame(parent, bg=TH["toolbar"])
        toolbar.pack(fill="x")
        for color in [("#ff5f57", 10), ("#febc2e", 10), ("#28c840", 10)]:
            tk.Label(toolbar, text="●", bg=TH["toolbar"], fg=color[0],
                     font=("Courier New", color[1])).pack(side="left", padx=(8,2), pady=6)
        tk.Label(toolbar, text="I N B O X", bg=TH["toolbar"], fg=TH["text_muted"],
                 font=FONTS["tiny"]).pack(side="right", padx=16, pady=8)

        # Email headers
        hdr_frame = tk.Frame(parent, bg=TH["email_bg"])
        hdr_frame.pack(fill="x")

        for label, value, color in [
            ("FROM", s.sender, TH["warn"]),
            ("SUBJECT", s.subject or "(no subject)", TH["white"]),
        ]:
            row = tk.Frame(hdr_frame, bg=TH["email_bg"])
            row.pack(fill="x", padx=16, pady=4)
            tk.Label(row, text=f"{label}:", bg=TH["email_bg"], fg=TH["text_muted"],
                     font=FONTS["mono_sm"], width=7, anchor="e").pack(side="left")
            tk.Label(row, text=value, bg=TH["email_bg"], fg=color,
                     font=FONTS["mono_b"], wraplength=600, anchor="w",
                     justify="left").pack(side="left", padx=8)

        # Separator
        tk.Frame(parent, bg=TH["border"], height=1).pack(fill="x")

        # Body
        body_frame = tk.Frame(parent, bg=TH["email_bg"])
        body_frame.pack(fill="x")

        body_text = tk.Text(body_frame, bg=TH["email_bg"], fg=TH["text"],
                            font=FONTS["mono_lg"], wrap="word",
                            relief="flat", padx=20, pady=16,
                            state="normal", cursor="arrow",
                            height=12, selectbackground=TH["surface2"])
        body_text.pack(fill="x")
        body_text.insert("1.0", s.body)

        # Insert URL with styling
        if s.url:
            body_text.insert("end", "\n\n")
            body_text.insert("end", s.url, "url")
            body_text.tag_configure("url", foreground=TH["accent"],
                                    underline=True)

        body_text.config(state="disabled")

    def _render_sms(self, s: Scenario):
        parent = self.msg_inner

        # SMS header bar
        hdr = tk.Frame(parent, bg=TH["toolbar"])
        hdr.pack(fill="x")
        tk.Label(hdr, text="◀", bg=TH["toolbar"], fg=TH["accent"],
                 font=FONTS["subhead"]).pack(side="left", padx=16, pady=8)
        tk.Label(hdr, text=s.sender, bg=TH["toolbar"], fg=TH["text"],
                 font=FONTS["mono_b"]).pack(side="left")
        tk.Label(hdr, text="📱 SMS / Text Message", bg=TH["toolbar"],
                 fg=TH["text_muted"], font=FONTS["tiny"]).pack(side="right", padx=16)

        # Bubble area
        bubble_area = tk.Frame(parent, bg=TH["email_bg"])
        bubble_area.pack(fill="x", padx=20, pady=16)

        # Time label
        tk.Label(bubble_area, text="Today  •  Received",
                 bg=TH["email_bg"], fg=TH["text_muted"],
                 font=FONTS["tiny"]).pack(anchor="center", pady=(0, 8))

        # Message bubble
        bubble = tk.Frame(bubble_area, bg=TH["surface"],
                          highlightbackground=TH["border"], highlightthickness=1)
        bubble.pack(anchor="w", ipadx=16, ipady=12)

        body_lbl = tk.Label(bubble, text=s.body, bg=TH["surface"], fg=TH["text"],
                            font=FONTS["mono_lg"], wraplength=500,
                            justify="left", anchor="w")
        body_lbl.pack(padx=4)

        # Link highlight
        if s.url:
            tk.Label(bubble_area, text=s.url, bg=TH["email_bg"], fg=TH["accent"],
                     font=FONTS["mono_sm"], wraplength=560).pack(anchor="w", pady=(4, 0))

    def _use_hint(self):
        if self.hint_used_this_round or self.answered_this_round:
            return
        self.hint_used_this_round = True

        s = self.scenario_queue[self.current_scenario_idx]
        hint_text = ""
        if s.is_phishing and s.red_flags:
            f = s.red_flags[0]
            hint_text = f"💡  Look carefully at:  {f.category}\n     {f.description}"
        else:
            hint_text = "💡  This one looks legitimate — check the sender domain and note what's NOT in the email."

        for w in self.hint_area.winfo_children():
            w.destroy()

        frame = tk.Frame(self.hint_area, bg=TH["surface"],
                         highlightbackground=TH["warn"], highlightthickness=1)
        frame.pack(fill="x", pady=(0, 8))
        tk.Label(frame, text=hint_text, bg=TH["surface"], fg=TH["warn"],
                 font=FONTS["mono_sm"], wraplength=700, justify="left",
                 padx=16, pady=10).pack(anchor="w")

    def _answer(self, is_phishing: bool):
        if self.answered_this_round:
            return
        self.answered_this_round = True

        s = self.scenario_queue[self.current_scenario_idx]
        correct = (is_phishing == s.is_phishing)
        pts = 0

        self.session.total += 1
        if correct:
            self.session.correct += 1
            if not self.hint_used_this_round:
                pts = POINTS[s.difficulty]
            else:
                pts = max(0, POINTS[s.difficulty] - 5)
            self.session.score += pts
            self.session.streak += 1
            self.session.best_streak = max(self.session.best_streak, self.session.streak)
        else:
            self.session.streak = 0

        self.session.hint_count += (1 if self.hint_used_this_round else 0)
        self.session.results.append({
            "title": s.title,
            "difficulty": s.difficulty,
            "is_phishing": s.is_phishing,
            "correct": correct,
            "pts": pts,
            "hint": self.hint_used_this_round,
        })

        self._update_stats_display()
        self._show_feedback(s, correct, pts)

        # Disable answer buttons
        self.answer_frame.pack_forget()

    def _show_feedback(self, s: Scenario, correct: bool, pts: int):
        for w in self.feedback_outer.winfo_children():
            w.destroy()

        fg = TH["accent3"] if correct else TH["accent2"]
        border = TH["accent3"] if correct else TH["accent2"]
        icon = "✓" if correct else "✗"
        verdict = "CORRECT!" if correct else "INCORRECT"

        # Result header
        header = tk.Frame(self.feedback_outer, bg=TH["surface"],
                          highlightbackground=border, highlightthickness=2)
        header.pack(fill="x", pady=(8, 0))

        top_row = tk.Frame(header, bg=TH["surface"])
        top_row.pack(fill="x", padx=16, pady=12)

        tk.Label(top_row, text=icon, bg=TH["surface"], fg=fg,
                 font=("Courier New", 24, "bold")).pack(side="left")
        tk.Label(top_row, text=f" {verdict}", bg=TH["surface"], fg=fg,
                 font=FONTS["heading"]).pack(side="left")

        truth = "🎣 PHISHING" if s.is_phishing else "✅ LEGITIMATE"
        truth_fg = TH["accent2"] if s.is_phishing else TH["accent3"]
        tk.Label(top_row, text=f"This was:  {truth}",
                 bg=TH["surface"], fg=truth_fg,
                 font=FONTS["subhead"]).pack(side="left", padx=24)

        pts_text = f"+{pts} pts" if pts > 0 else ("hint −5" if self.hint_used_this_round else "+0 pts")
        tk.Label(top_row, text=pts_text, bg=TH["surface"],
                 fg=TH["accent3"] if pts > 0 else TH["text_muted"],
                 font=FONTS["heading"]).pack(side="right")

        # Expandable red flags + explanation
        detail = tk.Frame(self.feedback_outer, bg=TH["surface2"],
                          highlightbackground=TH["border"], highlightthickness=1)
        detail.pack(fill="x")

        # Red Flags (only for phishing)
        if s.is_phishing and s.red_flags:
            flag_hdr = tk.Frame(detail, bg=TH["surface2"])
            flag_hdr.pack(fill="x", padx=16, pady=(12, 4))
            tk.Label(flag_hdr, text="🚩 RED FLAGS IDENTIFIED", bg=TH["surface2"],
                     fg=TH["accent2"], font=FONTS["mono_b"]).pack(anchor="w")

            for i, rf in enumerate(s.red_flags):
                flag_row = tk.Frame(detail, bg=TH["surface"],
                                    highlightbackground="#1e2d3f", highlightthickness=1)
                flag_row.pack(fill="x", padx=16, pady=2)

                num_lbl = tk.Label(flag_row, text=f" {i+1}. ", bg=TH["surface"],
                                   fg=TH["accent2"], font=FONTS["mono_b"])
                num_lbl.pack(side="left", padx=(8, 0), pady=6)

                inner = tk.Frame(flag_row, bg=TH["surface"])
                inner.pack(side="left", fill="x", expand=True, pady=6)
                tk.Label(inner, text=rf.category, bg=TH["surface"], fg=TH["white"],
                         font=FONTS["mono_b"], anchor="w").pack(anchor="w")
                tk.Label(inner, text=rf.description, bg=TH["surface"], fg=TH["text_dim"],
                         font=FONTS["mono_sm"], anchor="w", wraplength=550).pack(anchor="w")

        # Explanation
        exp_frame = tk.Frame(detail, bg=TH["surface2"])
        exp_frame.pack(fill="x", padx=16, pady=(10, 4))
        tk.Label(exp_frame, text="📖  EXPLANATION", bg=TH["surface2"],
                 fg=TH["accent"], font=FONTS["mono_b"]).pack(anchor="w")
        tk.Label(detail, text=s.explanation, bg=TH["surface2"], fg=TH["text"],
                 font=FONTS["mono_sm"], wraplength=720, justify="left",
                 padx=16).pack(anchor="w", pady=(0, 8))

        # Pro Tip
        tip_frame = tk.Frame(detail, bg=TH["surface"],
                             highlightbackground=TH["accent"], highlightthickness=1)
        tip_frame.pack(fill="x", padx=16, pady=(4, 12))
        tk.Label(tip_frame, text=f"💡  PRO TIP:  {s.tip}",
                 bg=TH["surface"], fg=TH["accent"], font=FONTS["mono_sm"],
                 wraplength=700, justify="left", padx=16, pady=10).pack(anchor="w")

        # Next button
        total = len(self.scenario_queue)
        btn_label = ("▶  NEXT SCENARIO" if self.current_scenario_idx + 1 < total
                     else "📊  VIEW RESULTS")
        next_btn = GlowButton(self.feedback_outer, btn_label, self._next,
                              width=280, height=46, color=TH["accent"],
                              font=("Courier New", 11, "bold"))
        next_btn.pack(pady=10)

        # Scroll to bottom to show feedback
        self.feedback_outer.after(100, lambda: self.msg_canvas.yview_moveto(1.0))

    def _next(self):
        self.current_scenario_idx += 1
        if self.current_scenario_idx >= len(self.scenario_queue):
            self._render_results()
            self._show_results_screen()
        else:
            self._load_scenario()
            self.msg_canvas.yview_moveto(0)

    def _update_stats_display(self):
        s = self.session
        pct_text = f"{round(s.correct/s.total*100)}%" if s.total else "—"

        self.score_big_lbl.config(text=str(s.score))
        self.correct_lbl.config(text=f"{s.correct} / {s.total}")
        self.accuracy_lbl.config(text=pct_text)
        self.streak_lbl.config(text=str(s.streak))
        self.best_streak_lbl.config(text=str(s.best_streak))

        self.hdr_score_lbl.lbl.config(text=f"{s.score} pts")
        self.hdr_streak_lbl.lbl.config(text=f"{s.streak}🔥")

        # Difficulty bars
        diff_stats = {"easy": [0, 0], "medium": [0, 0], "hard": [0, 0]}
        for r in s.results:
            d = r["difficulty"]
            diff_stats[d][1] += 1
            if r["correct"]:
                diff_stats[d][0] += 1

        total_in_diff = {d: sum(1 for sc in SCENARIOS if sc.difficulty == d) for d in diff_stats}
        for diff, (bar, bg_frame, count_lbl) in self.diff_bars.items():
            correct, total = diff_stats[diff]
            if total > 0:
                bar.place(relwidth=correct / total)
            else:
                bar.place(relwidth=0)
            count_lbl.config(text=f"{correct}/{total}")

    # ══════════════════════════════════════════════════════════════
    #  RESULTS SCREEN
    # ══════════════════════════════════════════════════════════════

    def _render_results(self):
        # Clear old results
        for w in self.results_inner.winfo_children():
            w.destroy()

        s = self.session
        total = s.total
        pct = round((s.correct / total) * 100) if total else 0
        elapsed = int(time.time() - s.start_time)
        elapsed_str = f"{elapsed//60}m {elapsed%60}s"

        # Grade
        if pct >= 90:   grade, gc, gl = "A+", TH["accent3"],  "SECURITY EXPERT"
        elif pct >= 75: grade, gc, gl = "B",  TH["accent"],   "SECURITY AWARE"
        elif pct >= 60: grade, gc, gl = "C",  TH["warn"],     "DEVELOPING SKILLS"
        elif pct >= 40: grade, gc, gl = "D",  "#ff7040",      "NEEDS IMPROVEMENT"
        else:           grade, gc, gl = "F",  TH["accent2"],  "HIGH RISK"

        content = self.results_inner

        # ── Hero grade section ──────────────────────────────────
        hero = tk.Frame(content, bg=TH["surface2"])
        hero.pack(fill="x")

        tk.Label(hero, text=grade, bg=TH["surface2"], fg=gc,
                 font=("Courier New", 72, "bold")).pack(pady=(24, 0))
        tk.Label(hero, text=gl, bg=TH["surface2"], fg=gc,
                 font=FONTS["heading"]).pack()
        tk.Label(hero, text=f"Training Complete  ·  {elapsed_str}",
                 bg=TH["surface2"], fg=TH["text_muted"],
                 font=FONTS["tiny"]).pack(pady=(4, 24))

        # ── 4 stat boxes ──────────────────────────────────────
        stats_row = tk.Frame(content, bg=TH["bg"])
        stats_row.pack(fill="x")

        for val, label, color in [
            (str(s.score),           "POINTS",       TH["accent"]),
            (f"{s.correct}/{total}", "CORRECT",      TH["accent3"]),
            (f"{pct}%",              "ACCURACY",     TH["warn"]),
            (str(s.best_streak),     "BEST STREAK",  TH["text"]),
        ]:
            box = tk.Frame(stats_row, bg=TH["surface"],
                           highlightbackground=TH["border"], highlightthickness=1)
            box.pack(side="left", fill="x", expand=True)
            tk.Label(box, text=val, bg=TH["surface"], fg=color,
                     font=("Courier New", 28, "bold")).pack(pady=(16, 0))
            tk.Label(box, text=label, bg=TH["surface"], fg=TH["text_muted"],
                     font=FONTS["tiny"]).pack(pady=(0, 16))

        # ── Accuracy bar ──────────────────────────────────────
        acc_section = tk.Frame(content, bg=TH["bg"])
        acc_section.pack(fill="x", padx=24, pady=16)
        tk.Label(acc_section, text="ACCURACY BREAKDOWN",
                 bg=TH["bg"], fg=TH["text_muted"], font=FONTS["tiny"]).pack(anchor="w")
        bar_frame = tk.Frame(acc_section, bg=TH["border"], height=18)
        bar_frame.pack(fill="x", pady=6)
        bar_frame.pack_propagate(False)

        correct_pct = s.correct / total if total else 0
        wrong_pct = 1 - correct_pct

        bar_inner = tk.Frame(bar_frame, bg=TH["border"])
        bar_inner.pack(fill="both", expand=True)

        if correct_pct > 0:
            c_bar = tk.Frame(bar_inner, bg=TH["accent3"])
            c_bar.place(relx=0, rely=0, relwidth=correct_pct, relheight=1)
        if wrong_pct > 0:
            w_bar = tk.Frame(bar_inner, bg=TH["accent2"])
            w_bar.place(relx=correct_pct, rely=0, relwidth=wrong_pct, relheight=1)

        row2 = tk.Frame(acc_section, bg=TH["bg"])
        row2.pack(anchor="w")
        tk.Label(row2, text=f"■ {s.correct} Correct", bg=TH["bg"],
                 fg=TH["accent3"], font=FONTS["mono_sm"]).pack(side="left", padx=(0, 16))
        tk.Label(row2, text=f"■ {total - s.correct} Incorrect", bg=TH["bg"],
                 fg=TH["accent2"], font=FONTS["mono_sm"]).pack(side="left")
        if s.hint_count:
            tk.Label(row2, text=f"■ {s.hint_count} Hints Used", bg=TH["bg"],
                     fg=TH["warn"], font=FONTS["mono_sm"]).pack(side="left", padx=16)

        # ── Scenario Breakdown ────────────────────────────────
        bd_frame = tk.Frame(content, bg=TH["bg"])
        bd_frame.pack(fill="x", padx=24, pady=(0, 16))

        tk.Label(bd_frame, text="SCENARIO BREAKDOWN",
                 bg=TH["bg"], fg=TH["text_muted"], font=FONTS["tiny"]).pack(anchor="w", pady=(0, 8))

        for r in s.results:
            row = tk.Frame(bd_frame, bg=TH["surface"],
                           highlightbackground=TH["border"], highlightthickness=1)
            row.pack(fill="x", pady=2)

            icon = "✓" if r["correct"] else "✗"
            icon_fg = TH["accent3"] if r["correct"] else TH["accent2"]
            tk.Label(row, text=icon, bg=TH["surface"], fg=icon_fg,
                     font=FONTS["subhead"], width=3).pack(side="left", padx=8, pady=8)

            tk.Label(row, text=r["title"], bg=TH["surface"], fg=TH["text"],
                     font=FONTS["mono_sm"], anchor="w").pack(side="left", fill="x", expand=True)

            diff_color = DIFF_COLORS[r["difficulty"]]
            tk.Label(row, text=r["difficulty"].upper()[:3],
                     bg=TH["surface"], fg=diff_color,
                     font=FONTS["tiny"], width=4).pack(side="right", padx=4)

            tag = "PHISH" if r["is_phishing"] else "LEGIT"
            tag_fg = TH["accent2"] if r["is_phishing"] else TH["accent3"]
            tk.Label(row, text=tag, bg=TH["surface"], fg=tag_fg,
                     font=FONTS["tiny"], width=6).pack(side="right", padx=8)

            pts_text = f"+{r['pts']}" if r["pts"] else "+0"
            tk.Label(row, text=pts_text, bg=TH["surface"],
                     fg=TH["accent3"] if r["pts"] > 0 else TH["text_muted"],
                     font=FONTS["mono_sm"], width=5).pack(side="right")

        # ── Key Takeaways ─────────────────────────────────────
        tips_frame = tk.Frame(content, bg=TH["surface"],
                              highlightbackground=TH["border"], highlightthickness=1)
        tips_frame.pack(fill="x", padx=24, pady=(0, 16))

        tk.Label(tips_frame, text="KEY TAKEAWAYS", bg=TH["surface"],
                 fg=TH["accent"], font=FONTS["mono_b"],
                 padx=16, pady=10).pack(anchor="w")

        takeaways = [
            "Always verify sender domains character by character — one '1' vs 'l' can fool you.",
            "Never click links in emails or SMS. Navigate directly to the official site.",
            "Urgency and threats are manipulation tactics designed to bypass critical thinking.",
            "BEC attacks impersonate executives — verify all wire transfers with a phone call.",
            "Check the TLD (.com vs .net) — attackers register lookalike domains.",
            "Multi-brand phishing impersonates multiple companies in one email. Verify each domain.",
            "Report all suspicious messages to your IT security team immediately.",
        ]

        for tip in takeaways:
            r = tk.Frame(tips_frame, bg=TH["surface"])
            r.pack(fill="x", padx=16, pady=2)
            tk.Label(r, text="›", bg=TH["surface"], fg=TH["accent"],
                     font=FONTS["mono_b"]).pack(side="left", pady=4)
            tk.Label(r, text=tip, bg=TH["surface"], fg=TH["text_dim"],
                     font=FONTS["mono_sm"], wraplength=700, justify="left",
                     anchor="w").pack(side="left", padx=8, pady=4, anchor="w")

        # ── Action buttons ────────────────────────────────────
        btn_row = tk.Frame(content, bg=TH["bg"])
        btn_row.pack(pady=24)

        GlowButton(btn_row, "↺  TRAIN AGAIN", self._restart,
                   width=220, height=48, color=TH["accent"],
                   font=FONTS["subhead"]).pack(side="left", padx=8)

        GlowButton(btn_row, "✕  QUIT", self.quit,
                   width=150, height=48, color=TH["accent2"],
                   font=FONTS["subhead"]).pack(side="left", padx=8)

    def _restart(self):
        # Cancel any running animations, reset everything
        self.hdr_score_frame.pack_forget()
        self._hero_t = 0
        self._show_intro()
        self._animate_hero()


# ══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = PhishingSimulator()
    app.mainloop()
