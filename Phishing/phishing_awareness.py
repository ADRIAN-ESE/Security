#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║         PHISHING AWARENESS SIMULATION TOOL               ║
║              Security Training Platform                  ║
╚══════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import random
import textwrap
from datetime import datetime

# ─── ANSI Color Codes ─────────────────────────────────────
class Colors:
    RED     = '\033[91m'
    GREEN   = '\033[92m'
    YELLOW  = '\033[93m'
    BLUE    = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN    = '\033[96m'
    WHITE   = '\033[97m'
    BOLD    = '\033[1m'
    DIM     = '\033[2m'
    RESET   = '\033[0m'
    BG_RED  = '\033[41m'
    BG_GREEN= '\033[42m'
    BG_BLUE = '\033[44m'

C = Colors  # shorthand

# ─── Scenario Database ────────────────────────────────────
SCENARIOS = [
    {
        "id": 1,
        "type": "email",
        "is_phishing": True,
        "difficulty": "Easy",
        "scenario": {
            "from":    "security@paypa1.com",
            "subject": "⚠️ URGENT: Your account has been suspended!",
            "body": """Dear Valued Customer,

We have detected unusual activity in your PayPal account.
Your account has been TEMPORARILY SUSPENDED for your protection.

To restore access, please verify your information IMMEDIATELY:

  ➤  Click here: http://paypa1-secure-login.ru/verify

You must act within 24 HOURS or your account will be permanently
closed and all funds frozen.

Enter your:  • Full name  • SSN  • Credit card number  • Password

PayPal Security Team
© PayPal Inc. 2024"""
        },
        "red_flags": [
            "Sender domain is 'paypa1.com' (number '1' instead of letter 'l')",
            "Creates extreme urgency ('24 HOURS', 'IMMEDIATELY')",
            "Link points to a .ru domain, not paypal.com",
            "Asks for SSN and credit card — PayPal never does this",
            "Threatening language ('permanently closed', 'funds frozen')",
        ],
        "explanation": "Classic account-suspension phish. The misspelled domain (paypa1 vs paypal) is the #1 red flag. Legitimate companies never ask for SSNs or credit card numbers via email.",
        "tip": "Always hover over links before clicking. Check the FULL domain carefully.",
    },
    {
        "id": 2,
        "type": "email",
        "is_phishing": False,
        "difficulty": "Easy",
        "scenario": {
            "from":    "noreply@github.com",
            "subject": "Your GitHub account: new sign-in from Chrome on Windows",
            "body": """Hi there,

We noticed a new sign-in to your GitHub account.

  Device:    Chrome on Windows 11
  Location:  New York, NY, USA
  Time:      December 5, 2024 at 2:34 PM EST

If this was you, no action is needed.

If you don't recognize this sign-in, please secure your account:
  https://github.com/settings/security

You're receiving this email because security alerts are enabled
for your account.

GitHub Security
github.com"""
        },
        "red_flags": [],
        "explanation": "This is a LEGITIMATE security notification. Note: real sender domain (github.com), no urgent threats, no requests for credentials, clean link pointing to actual github.com, and informational tone.",
        "tip": "Legitimate security emails inform — they don't threaten or demand immediate action.",
    },
    {
        "id": 3,
        "type": "email",
        "is_phishing": True,
        "difficulty": "Medium",
        "scenario": {
            "from":    "hr-department@your-company-benefits.net",
            "subject": "Action Required: Open Enrollment Closes Tomorrow",
            "body": """Dear Employee,

This is a reminder from Human Resources that Open Enrollment
for 2025 benefits CLOSES TOMORROW at 5:00 PM.

You have NOT yet completed your enrollment selections.
Failure to enroll will result in loss of ALL benefits.

Complete your enrollment now:
  http://benefits-portal.your-company-benefits.net/login

You will need:
  • Employee ID
  • Current password
  • SSN (last 4 digits)
  • Date of birth

Questions? Reply to this email or call 1-800-555-0199.

HR Benefits Team"""
        },
        "red_flags": [
            "Sender is 'your-company-benefits.net' — not your actual company domain",
            "Pressure tactic: 'CLOSES TOMORROW', 'loss of ALL benefits'",
            "Asking for SSN and date of birth is unusual for internal HR",
            "Generic greeting 'Dear Employee' instead of your name",
            "Link goes to a third-party domain, not your company intranet",
        ],
        "explanation": "Spear-phishing targeting employees. HR emails come from your company's official domain. When in doubt, call HR directly using the number from the company directory — not the one in the email.",
        "tip": "Verify unexpected HR requests directly with your HR department using known contact info.",
    },
    {
        "id": 4,
        "type": "sms",
        "is_phishing": True,
        "difficulty": "Medium",
        "scenario": {
            "from":    "+1 (855) 203-4471",
            "subject": "SMS Message",
            "body": """USPS ALERT: Package #9400111899223397 could not be delivered.
Update your delivery address:
usps-redelivery-portal.com/track?id=9400111899

Reply STOP to unsubscribe."""
        },
        "red_flags": [
            "USPS texts come from 5-digit short codes, not 10-digit phone numbers",
            "Domain is 'usps-redelivery-portal.com' — NOT usps.com",
            "USPS does not send unsolicited texts unless you opt-in via Informed Delivery",
            "Fake tracking number to make it look legitimate",
        ],
        "explanation": "SMS phishing ('smishing') impersonating USPS. The real USPS website is usps.com. Any delivery notification link should go to that domain only.",
        "tip": "Go directly to the official carrier website and enter your tracking number manually.",
    },
    {
        "id": 5,
        "type": "email",
        "is_phishing": False,
        "difficulty": "Medium",
        "scenario": {
            "from":    "billing@netflix.com",
            "subject": "Your Netflix receipt - December 2024",
            "body": """Hi Alex,

Thanks for being a Netflix member.

Here's your receipt for this month:

  Plan:        Standard with ads
  Amount:      $6.99
  Date:        December 1, 2024
  Method:      Visa ending in 4242

Your next billing date is January 1, 2025.

To manage your account, visit netflix.com/account

Questions about your bill?
  help.netflix.com/billing

Netflix, Inc.
100 Winchester Circle
Los Gatos, CA 95032"""
        },
        "red_flags": [],
        "explanation": "This is a LEGITIMATE billing receipt. Key indicators: real sender domain, personalized greeting with your name, specific billing details you'd recognize, no requests for action or credentials, and links go only to netflix.com subdomains.",
        "tip": "Billing receipts are safe — but never click 'update payment' links in emails. Go directly to the website instead.",
    },
    {
        "id": 6,
        "type": "email",
        "is_phishing": True,
        "difficulty": "Hard",
        "scenario": {
            "from":    "docusign@docusign-notifications.com",
            "subject": "Action Required: Review and Sign Document",
            "body": """DocuSign Electronic Signature

  ┌─────────────────────────────────────────┐
  │  Sarah Johnson has sent you a document  │
  │  to review and sign.                    │
  └─────────────────────────────────────────┘

  Document:  NDA_Agreement_Final_v3.pdf
  Sender:    sarah.johnson@legalpartners.com
  Expires:   December 10, 2024

  [REVIEW DOCUMENT]
  https://docusign-notifications.com/d/sign?token=8f3k2

This message was sent to you by DocuSign.
docusign.com | privacy | contact"""
        },
        "red_flags": [
            "Sender domain: 'docusign-notifications.com' — NOT docusign.com",
            "Review link goes to 'docusign-notifications.com', not docusign.com",
            "Real DocuSign links look like: docusign.net/Signing/...",
            "Plausible context (NDA) designed to reduce suspicion",
        ],
        "explanation": "Advanced phishing mimicking DocuSign's exact email format. This is hard because the design is convincing. The only giveaway is the domain. Real DocuSign emails ALWAYS link to docusign.net or docusign.com.",
        "tip": "For DocuSign specifically: log into your DocuSign account directly to find pending documents instead of clicking email links.",
    },
    {
        "id": 7,
        "type": "email",
        "is_phishing": True,
        "difficulty": "Hard",
        "scenario": {
            "from":    "it-support@microsoft-helpdesk.com",
            "subject": "Re: Your IT Support Ticket #TK-48821",
            "body": """Hi,

Following up on your recent IT support request regarding
slow login times (Ticket #TK-48821).

Our engineers have identified the issue and need you to
install a small diagnostic tool to complete the fix.

Please download and run:
  https://microsoftsupport.blob.core.windows.net/tools/diag.exe

File: DiagnosticTool_v2.exe  (2.4 MB)
SHA256: a1b2c3d4e5f6...

This is safe and digitally signed by Microsoft.
The tool will run for ~2 minutes and fix your login issue.

IT Help Desk | Ext. 4400"""
        },
        "red_flags": [
            "Sender is 'microsoft-helpdesk.com' — not your company or microsoft.com",
            "Asking you to download and RUN an .exe file is a major red flag",
            "Fake ticket number to establish false context",
            "Providing a fake SHA256 hash to falsely imply legitimacy",
            "URL uses 'blob.core.windows.net' — real but can host anything (including malware)",
        ],
        "explanation": "Sophisticated attack using a fake IT ticket. The blob.core.windows.net URL is actually a real Microsoft Azure storage URL — attackers can upload malware there. Never run executables sent via email, even if they seem signed.",
        "tip": "IT will NEVER ask you to download tools via email. Call your IT department directly to verify any such requests.",
    },
    {
        "id": 8,
        "type": "email",
        "is_phishing": False,
        "difficulty": "Hard",
        "scenario": {
            "from":    "security-noreply@amazon.com",
            "subject": "We changed your Amazon password",
            "body": """Hello,

Your Amazon password was recently changed.

  Date:      December 6, 2024 at 9:15 AM PST
  Browser:   Firefox 121 on macOS
  Location:  Seattle, WA

If you made this change, you can disregard this message.

If you did NOT make this change, please secure your account
immediately at:
  https://www.amazon.com/gp/help/customer/security

Do not reply to this email. To contact us, visit amazon.com/help

Amazon.com Security"""
        },
        "red_flags": [],
        "explanation": "LEGITIMATE Amazon security email. Despite the alarming subject, all indicators check out: official sender (amazon.com), specific device/time details, security link goes to amazon.com, no credential requests, and a calm tone.",
        "tip": "Even legitimate-looking emails can be scary. Stay calm, verify the sender domain, and go directly to the website rather than clicking links if unsure.",
    },
]

# ─── Display Utilities ────────────────────────────────────
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def slow_print(text, delay=0.02):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def banner():
    print(f"""
{C.CYAN}{C.BOLD}
 ██████╗ ██╗  ██╗██╗███████╗██╗  ██╗
 ██╔══██╗██║  ██║██║██╔════╝██║  ██║
 ██████╔╝███████║██║███████╗███████║
 ██╔═══╝ ██╔══██║██║╚════██║██╔══██║
 ██║     ██║  ██║██║███████║██║  ██║
 ╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝
{C.RESET}
{C.WHITE}  ╔══════════════════════════════════════════╗
  ║   A W A R E N E S S   T R A I N I N G   ║
  ║          Phishing Simulation v1.0        ║
  ╚══════════════════════════════════════════╝{C.RESET}
""")

def divider(char='─', width=54, color=C.DIM):
    print(f"{color}{char * width}{C.RESET}")

def section_header(title, color=C.CYAN):
    divider()
    print(f"{color}{C.BOLD}  {title}{C.RESET}")
    divider()

def render_email(scenario):
    """Render an email or SMS in a terminal-friendly format."""
    msg = scenario["scenario"]
    msg_type = scenario["type"].upper()
    diff = scenario["difficulty"]

    diff_colors = {"Easy": C.GREEN, "Medium": C.YELLOW, "Hard": C.RED}
    dc = diff_colors.get(diff, C.WHITE)

    print(f"\n{C.BOLD}{C.BG_BLUE}  {'─'*50}  {C.RESET}")
    print(f"{C.BOLD}{C.BLUE}  📧 {msg_type} MESSAGE  {C.DIM}[Difficulty: {dc}{diff}{C.RESET}{C.DIM}]{C.RESET}")
    print(f"{C.BOLD}{C.BG_BLUE}  {'─'*50}  {C.RESET}\n")

    print(f"  {C.DIM}From:   {C.RESET}{C.WHITE}{msg['from']}{C.RESET}")
    print(f"  {C.DIM}To:     {C.RESET}{C.WHITE}you@example.com{C.RESET}")
    print(f"  {C.DIM}Subj:   {C.RESET}{C.WHITE}{C.BOLD}{msg['subject']}{C.RESET}")
    print(f"  {C.DIM}Date:   {C.RESET}{C.WHITE}{datetime.now().strftime('%B %d, %Y %I:%M %p')}{C.RESET}")
    divider('┄')

    # Wrap and indent body
    for line in msg["body"].splitlines():
        wrapped = textwrap.fill(line, width=56) if len(line) > 56 else line
        for wl in (wrapped.splitlines() if wrapped else [""]):
            print(f"  {C.WHITE}{wl}{C.RESET}")
    print()
    divider('─')

def show_result(scenario, user_answer):
    """Show whether the user was correct and explain why."""
    correct = (user_answer == scenario["is_phishing"])

    if correct:
        print(f"\n  {C.BG_GREEN}{C.BOLD} ✓  CORRECT! {C.RESET}\n")
    else:
        print(f"\n  {C.BG_RED}{C.BOLD} ✗  INCORRECT {C.RESET}\n")

    verdict = "PHISHING" if scenario["is_phishing"] else "LEGITIMATE"
    vcolor  = C.RED if scenario["is_phishing"] else C.GREEN

    print(f"  This message was: {vcolor}{C.BOLD}{verdict}{C.RESET}\n")

    # Explanation
    section_header("📖  EXPLANATION", C.MAGENTA)
    wrapped = textwrap.fill(scenario["explanation"], width=52)
    for line in wrapped.splitlines():
        print(f"  {C.WHITE}{line}{C.RESET}")
    print()

    # Red flags (only for phishing)
    if scenario["is_phishing"] and scenario["red_flags"]:
        section_header("🚩  RED FLAGS IDENTIFIED", C.RED)
        for flag in scenario["red_flags"]:
            wrapped_flag = textwrap.fill(f"• {flag}", width=50, subsequent_indent="  ")
            print(f"  {C.YELLOW}{wrapped_flag}{C.RESET}")
        print()

    # Tip
    section_header("💡  SECURITY TIP", C.CYAN)
    wrapped_tip = textwrap.fill(scenario["tip"], width=52)
    for line in wrapped_tip.splitlines():
        print(f"  {C.CYAN}{line}{C.RESET}")
    print()

    return correct

def prompt_answer():
    """Get a validated answer from the user."""
    while True:
        print(f"\n  {C.BOLD}Is this message PHISHING or LEGITIMATE?{C.RESET}")
        print(f"  {C.RED}[P]{C.RESET} Phishing    {C.GREEN}[L]{C.RESET} Legitimate    {C.DIM}[Q]{C.RESET} Quit")
        print()
        choice = input(f"  {C.BOLD}Your answer: {C.RESET}").strip().upper()
        if choice == 'Q':
            return 'QUIT'
        elif choice == 'P':
            return True
        elif choice == 'L':
            return False
        else:
            print(f"  {C.YELLOW}  Please enter P, L, or Q.{C.RESET}")

def show_final_report(results, total_time):
    """Display a detailed end-of-session report."""
    clear()
    banner()

    correct    = sum(1 for r in results if r["correct"])
    total      = len(results)
    score_pct  = int((correct / total) * 100) if total > 0 else 0

    # Score color
    if score_pct >= 80:
        sc = C.GREEN
        grade = "EXCELLENT"
        medal = "🏆"
    elif score_pct >= 60:
        sc = C.YELLOW
        grade = "GOOD"
        medal = "🥈"
    else:
        sc = C.RED
        grade = "NEEDS IMPROVEMENT"
        medal = "📚"

    section_header("📊  SESSION REPORT", C.CYAN)
    print(f"  {medal} Final Grade:   {sc}{C.BOLD}{grade}{C.RESET}")
    print(f"  Score:          {sc}{C.BOLD}{correct}/{total}  ({score_pct}%){C.RESET}")
    print(f"  Time Taken:     {C.WHITE}{int(total_time)}s{C.RESET}")
    print()

    # Per-question breakdown
    section_header("📋  QUESTION BREAKDOWN", C.BLUE)
    for i, r in enumerate(results, 1):
        icon   = "✓" if r["correct"] else "✗"
        ic     = C.GREEN if r["correct"] else C.RED
        ptype  = "🎣 PHISH" if r["is_phishing"] else "✅ LEGIT"
        tc     = C.RED if r["is_phishing"] else C.GREEN
        diff   = r["difficulty"]
        dc_map = {"Easy": C.GREEN, "Medium": C.YELLOW, "Hard": C.RED}
        dc     = dc_map.get(diff, C.WHITE)
        print(f"  {ic}{C.BOLD}{icon}{C.RESET}  Q{i:02d}  {tc}{ptype}{C.RESET}  {C.DIM}[{dc}{diff}{C.RESET}{C.DIM}]{C.RESET}")
    print()

    # Insights
    section_header("🔍  KEY INSIGHTS", C.MAGENTA)
    phish_q   = [r for r in results if r["is_phishing"]]
    legit_q   = [r for r in results if not r["is_phishing"]]
    phish_acc = int(sum(1 for r in phish_q if r["correct"]) / len(phish_q) * 100) if phish_q else 0
    legit_acc = int(sum(1 for r in legit_q if r["correct"]) / len(legit_q) * 100) if legit_q else 0

    print(f"  Phishing Detection:  {C.RED if phish_acc < 60 else C.GREEN}{phish_acc}%{C.RESET}")
    print(f"  Legitimate ID Rate:  {C.RED if legit_acc < 60 else C.GREEN}{legit_acc}%{C.RESET}")

    if legit_acc < phish_acc:
        print(f"\n  {C.YELLOW}⚠  You tend toward false positives — be careful{C.RESET}")
        print(f"  {C.YELLOW}   not to flag legitimate emails as phishing.{C.RESET}")
    elif phish_acc < legit_acc:
        print(f"\n  {C.YELLOW}⚠  You missed some phishing attempts. Review{C.RESET}")
        print(f"  {C.YELLOW}   sender domains and link URLs carefully.{C.RESET}")
    else:
        print(f"\n  {C.GREEN}✓  Balanced detection — great job!{C.RESET}")

    print()
    section_header("📌  TOP SECURITY REMINDERS", C.CYAN)
    tips = [
        "Always check the FULL sender domain, not just the display name",
        "Hover over links — does the URL match what you expect?",
        "Urgency + threats + credential requests = phishing",
        "When in doubt, go directly to the website — don't click links",
        "Call to verify: use official numbers, not ones in the email",
    ]
    for tip in tips:
        wrapped = textwrap.fill(f"• {tip}", width=50, subsequent_indent="  ")
        print(f"  {C.CYAN}{wrapped}{C.RESET}")
    print()

def choose_mode():
    """Let the user pick a quiz mode."""
    section_header("🎮  SELECT MODE", C.CYAN)
    print(f"  {C.BOLD}[1]{C.RESET}  Full Training  {C.DIM}(all 8 scenarios){C.RESET}")
    print(f"  {C.BOLD}[2]{C.RESET}  Quick Quiz     {C.DIM}(random 4 scenarios){C.RESET}")
    print(f"  {C.BOLD}[3]{C.RESET}  Hard Mode      {C.DIM}(hard difficulty only){C.RESET}")
    print(f"  {C.BOLD}[Q]{C.RESET}  Quit")
    print()
    while True:
        choice = input(f"  {C.BOLD}Select mode: {C.RESET}").strip().upper()
        if choice == '1':
            return list(SCENARIOS)
        elif choice == '2':
            return random.sample(SCENARIOS, 4)
        elif choice == '3':
            return [s for s in SCENARIOS if s["difficulty"] == "Hard"]
        elif choice == 'Q':
            return None
        print(f"  {C.YELLOW}  Please enter 1, 2, 3, or Q.{C.RESET}")

def run_quiz(scenarios):
    """Main quiz loop."""
    results    = []
    start_time = time.time()
    total      = len(scenarios)

    for idx, scenario in enumerate(scenarios, 1):
        clear()
        print(f"\n{C.DIM}  Question {idx} of {total}  {'▓' * idx}{'░' * (total - idx)}{C.RESET}\n")

        render_email(scenario)
        answer = prompt_answer()

        if answer == 'QUIT':
            print(f"\n  {C.YELLOW}Quiz ended early. No report generated.{C.RESET}\n")
            return None

        correct = show_result(scenario, answer)
        results.append({
            "correct":     correct,
            "is_phishing": scenario["is_phishing"],
            "difficulty":  scenario["difficulty"],
        })

        if idx < total:
            input(f"\n  {C.DIM}Press ENTER for the next scenario...{C.RESET}")

    elapsed = time.time() - start_time
    return results, elapsed

def main():
    clear()
    banner()

    slow_print(f"  {C.WHITE}Welcome to the Phishing Awareness Simulation Tool.{C.RESET}", 0.03)
    slow_print(f"  {C.DIM}You'll be shown real-world email and SMS scenarios.{C.RESET}", 0.025)
    slow_print(f"  {C.DIM}Identify which are phishing attempts — and learn why.{C.RESET}", 0.025)
    print()
    input(f"  {C.DIM}Press ENTER to begin...{C.RESET}")
    clear()
    banner()

    scenarios = choose_mode()
    if scenarios is None:
        print(f"\n  {C.CYAN}Stay vigilant! Goodbye.{C.RESET}\n")
        sys.exit(0)

    outcome = run_quiz(scenarios)
    if outcome is None:
        sys.exit(0)

    results, elapsed = outcome
    show_final_report(results, elapsed)

    print()
    input(f"  {C.DIM}Press ENTER to exit...{C.RESET}")
    print(f"\n  {C.CYAN}Stay safe online! 🛡️{C.RESET}\n")

if __name__ == "__main__":
    main()
