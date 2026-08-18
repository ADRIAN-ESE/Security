# Login

A single repository containing **three separate, self-contained implementations** of the same authentication system — registration, login, sessions, password reset, and login-history tracking — written three different ways:

1. **Django** (`login_systems/django_login`) — a full Django 5 project with a custom user model
2. **Flask** (`login_systems/flask_login`) — a single-file Flask 3 app using SQLAlchemy
3. **Tkinter** (`login_systems/tkinter_login`) — an offline desktop GUI app using raw `sqlite3`

They don't depend on each other — pick whichever one matches what you're trying to learn or build on, and ignore the rest. This document explains what each one does internally, how to install and run every part of the project, and how to take each one to production.

---

## Table of contents

1. [Overview](#overview)
2. [Repository layout](#repository-layout)
3. [How each system works](#how-each-system-works)
   - [Django app internals](#31-django-app-internals)
   - [Flask app internals](#32-flask-app-internals)
   - [Tkinter app internals](#33-tkinter-app-internals)
4. [Comparing the three approaches](#comparing-the-three-approaches)
5. [Prerequisites](#prerequisites)
6. [Installation](#installation)
7. [Running and using each system](#running-and-using-each-system)
8. [Environment variables](#environment-variables)
9. [Testing the password-reset flow locally](#testing-the-password-reset-flow-locally)
10. [Deployment](#deployment)
11. [Security review](#security-review)
12. [Troubleshooting](#troubleshooting)
13. [Suggested improvements](#suggested-improvements)
14. [License](#license)

---

## Overview

All three implementations solve the same problem — "let a user create an account, log in, stay logged in, see their login history, and reset a forgotten password" — but each one shows a different way of solving it:

- Django gives you an ORM, migrations, an admin panel, and a batteries-included auth framework, at the cost of more moving parts and "magic" you have to learn.
- Flask gives you explicit control over every request, every database query, and every line of HTML, at the cost of having to wire up things (like session handling and email) yourself.
- Tkinter shows that "login system" doesn't have to mean "website" at all — it's a normal desktop program with its own local database and no network dependency.

Reading all three side by side is a good way to see which parts of a login system are universal (password hashing, token-based resets, tracking login attempts) and which parts are specific to the framework you chose (URL routing, template engines, session cookies vs. desktop widgets).

---

## Repository layout

```
Login/
└── login_systems/
    ├── requirements.txt              # pip dependencies shared by django_login and flask_login
    │
    ├── django_login/
    │   ├── manage.py                 # Django's command-line entry point
    │   ├── db.sqlite3                 # SQLite database file (created by migrations)
    │   ├── login_system/              # the Django "project" (global config)
    │   │   ├── settings.py            # apps, middleware, database, auth, email config
    │   │   ├── urls.py                # top-level URL routing
    │   │   ├── wsgi.py                # entry point for production WSGI servers (gunicorn, etc.)
    │   │   └── asgi.py                # entry point for async servers (Daphne, Uvicorn, etc.)
    │   ├── accounts/                  # the Django "app" that owns authentication
    │   │   ├── models.py              # custom User + LoginHistory models
    │   │   ├── forms.py               # registration / login / password-reset forms
    │   │   ├── views.py               # request handlers (register, login, logout, dashboard)
    │   │   ├── urls.py                # /accounts/... routes
    │   │   ├── admin.py                # registers models with the Django admin site
    │   │   └── migrations/            # database schema history
    │   ├── templates/                 # base.html + accounts/*.html (Django template language)
    │   └── static/css/style.css       # shared stylesheet
    │
    ├── flask_login/
    │   ├── app.py                     # everything: config, models, routes, validators, CLI commands
    │   └── templates/                 # base.html, login.html, register.html, dashboard.html,
    │                                   #   forgot_password.html, reset_password.html (Jinja2)
    │
    └── tkinter_login/
        └── main.py                    # Database class (SQLite access) + LoginApp class (GUI)
```

---

## How each system works

### 3.1 Django app internals

**Project vs. app split.** Django separates a *project* (`login_system/` — global settings, the root URL table) from an *app* (`accounts/` — a self-contained unit of functionality: models, views, forms, templates, URLs). This is idiomatic Django: even a one-feature site is organized as "project contains one or more apps."

**`login_system/settings.py`** is the control panel for the whole project:
- `INSTALLED_APPS` lists Django's built-in apps (`admin`, `auth`, `sessions`, `messages`, `staticfiles`) plus the local `accounts` app.
- `MIDDLEWARE` is the request/response pipeline — notably `CsrfViewMiddleware` (blocks cross-site form submissions) and `AuthenticationMiddleware` (attaches `request.user` to every request).
- `AUTH_USER_MODEL = 'accounts.User'` tells Django to use the custom `User` model below instead of its default one — this has to be set before the first migration ever runs.
- `AUTH_PASSWORD_VALIDATORS` plugs in Django's own password-strength checks (similarity to username, minimum length 8, not a common password, not all-numeric) on top of Django's registration form.
- `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL` tell Django's auth views and `@login_required` decorator where to send users before/after login.
- `EMAIL_BACKEND = '...console.EmailBackend'` means password-reset emails are printed to the terminal Django is running in, instead of actually being sent — convenient for local development, and it's the first thing to change for production (see [Environment variables](#environment-variables)).

**`accounts/models.py`:**
- `CustomUserManager` overrides how users and superusers get created (`create_user`, `create_superuser`), since a custom user model needs a matching custom manager.
- `User(AbstractBaseUser, PermissionsMixin)` is a full replacement for Django's built-in user, with a UUID primary key (`uuid.uuid4`) instead of an auto-incrementing integer, `username` as the login field (`USERNAME_FIELD = 'username'`), `email` as a required extra field, plus `email_verified`, `verification_token`, `reset_token`, and `reset_token_expiry` fields for the reset flow.
- `LoginHistory` records every login attempt — one row per attempt, storing the user (foreign key), timestamp, IP address, user agent string, and whether it succeeded.

**`accounts/forms.py`** subclasses Django's built-in auth forms to add HTML styling and extra validation:
- `CustomUserCreationForm` extends `UserCreationForm`, adds an email field with a uniqueness check (`clean_email`), and shows the password rules as help text under the password field.
- `CustomAuthenticationForm` extends `AuthenticationForm` purely to add CSS classes/placeholders.
- `CustomPasswordResetForm` / `CustomSetPasswordForm` extend Django's built-in password-reset forms the same way.

**`accounts/views.py`** — the request handlers:
- `register_view` — on `POST`, validates the form and calls `form.save()` (which hashes the password via Django's password hasher and creates the row), then redirects to login.
- `login_view` — validates credentials via `CustomAuthenticationForm`, calls Django's `login()` to establish the session, records a `LoginHistory` row (success *and* failure cases — on failure it looks the user up by username just to log the failed attempt against them), and updates `last_login`.
- `logout_view` — calls Django's `logout()` to clear the session.
- `dashboard_view` — decorated with `@login_required`; queries the current user's last 10 `LoginHistory` rows and renders them.
- `get_client_ip` — reads `X-Forwarded-For` (set by reverse proxies/load balancers) if present, otherwise falls back to `REMOTE_ADDR`.

**URL routing** is two-layer: `login_system/urls.py` sends `/admin/` to the Django admin and everything else to `accounts/urls.py`, which maps `register/`, `login/`, `logout/`, `dashboard/`, plus four password-reset URLs that plug Django's built-in `PasswordResetView` / `PasswordResetDoneView` / `PasswordResetConfirmView` / `PasswordResetCompleteView` class-based views into the custom templates and forms.

**Password reset flow (Django):** user submits their email → Django generates a signed, time-limited token and emails a link containing `uidb64` (their user ID, base64-encoded) and the token → the confirm view validates both before showing the new-password form → on success, the user is redirected to a "complete" page. This is Django's built-in mechanism, so none of the token logic is hand-written here — it's inherited from `django.contrib.auth`.

### 3.2 Flask app internals

Unlike Django, the entire Flask app lives in one file, `app.py` (430 lines), organized top-to-bottom into clearly marked sections.

**Setup and config (top of file):** creates the `Flask` app object, reads `SECRET_KEY` and mail settings from environment variables (falling back to insecure defaults if unset — see [Security review](#security-review)), and initializes three extensions bound to the app: `SQLAlchemy` (`db`), `Bcrypt` (`bcrypt`), and `Mail` (`mail`).

**Models:**
- `User` — a SQLAlchemy model with `username`, `email`, `password_hash`, `reset_token`, `reset_token_expiry`, `created_at`, `last_login`, `is_active`. `set_password()` hashes with bcrypt; `check_password()` verifies; `generate_reset_token()` creates a URL-safe random token (`secrets.token_urlsafe(32)`) with a 1-hour expiry; `verify_reset_token()` checks both the token match and the expiry.
- `LoginHistory` — one row per login attempt, linked to `User` via a foreign key and SQLAlchemy relationship, storing IP, user agent, timestamp, and success flag.

**Validators:** `validate_password()` enforces the same rule set as the other two apps (8+ chars, upper, lower, digit, special character) and returns a `(bool, message)` tuple; `validate_email()` checks the format with a regex.

**Session handling is hand-rolled**, not delegated to an extension like Flask-Login:
- `login_required` is a custom decorator (`functools.wraps`) that checks `'user_id' in session` and redirects to `/login` if it's missing.
- On successful login, the view manually sets `session['user_id']`, `session['username']`, and `session.permanent = True`.
- `get_client_ip()` checks `X-Forwarded-For` the same way the Django version does.

**Routes, one by one:**
- `GET /` → redirects to `/dashboard` if already logged in, otherwise `/login`.
- `GET/POST /register` → validates all fields are present, passwords match, email format is valid, password meets the strength rules, and username/email aren't already taken — then creates the user and redirects to login.
- `GET/POST /login` → looks up the user by username, rejects if inactive, checks the password, and either establishes the session + logs a successful `LoginHistory` row, or logs a failed one and shows an error. Notably it distinguishes "user not found" from "wrong password" in the flash message (a minor information-disclosure trade-off — see [Security review](#security-review)).
- `GET /logout` (decorated with `@login_required`) → `session.clear()`.
- `GET /dashboard` (decorated) → loads the current user and their last 10 login-history rows.
- `GET/POST /forgot-password` → looks up the user by email; if found, generates a reset token and tries to email a styled HTML reset link via Flask-Mail. If sending fails (e.g. no SMTP configured), it **falls back to flashing the raw token directly on the page** — a convenient local-dev shortcut, but something you'd remove before deploying anywhere public. Either way, it always shows the same generic "if this email exists…" message when the email isn't found, to avoid revealing which emails are registered.
- `GET/POST /reset-password/<token>` → looks the token up, checks `verify_reset_token()`, and on `POST` validates and saves the new password, then clears the token so it can't be reused.
- `404`/`500` error handlers flash a message and redirect home rather than showing Flask's default error pages.

**CLI commands:** `flask init-db` calls `db.create_all()` to (re)create tables; `flask create-admin` interactively prompts for username/email/password (via `click.prompt`, with the password input hidden) and creates a user.

**Startup block:** `if __name__ == '__main__':` creates all tables inside an app context (so `python app.py` "just works" on a fresh clone, no separate migration step needed) and starts Flask's built-in dev server with `debug=True` on `0.0.0.0:5000`.

### 3.3 Tkinter app internals

This app has no web framework at all — it's two Python classes in one file.

**`Database` class** wraps a local SQLite file (`users.db`, created automatically) and owns two tables: `users` (id, username, email, password_hash, reset_token, reset_token_expiry, created_at, last_login, is_active) and `login_history` (id, username, login_time, ip_address, success). Key methods:
- `hash_password(password, salt=None)` — generates a random 32-byte salt with `secrets.token_hex(32)` (which produces a 64-character hex string) if none is given, then derives a hash with **PBKDF2-HMAC-SHA256, 100,000 iterations**, and returns `salt + hash.hex()` concatenated into one string.
- `verify_password(stored_password, provided_password)` — since the salt is always the first 64 characters of the stored string, it slices `stored_password[:64]` back out, re-derives the hash with that same salt, and compares the full strings.
- `register_user`, `authenticate_user`, `generate_reset_token`, `reset_password` mirror the same validation and token logic as the Flask/Django versions, just written against raw SQL (`sqlite3` cursors) instead of an ORM. SQLite's `UNIQUE` constraint on `username`/`email` is what actually enforces "no duplicate accounts" — `register_user` just catches the resulting `sqlite3.IntegrityError`.
- `log_login` / `update_last_login` / `get_login_history` support the same "show my last 10 logins" feature as the web apps.

**`LoginApp` class** is the GUI, built on a single `tk.Tk()` root window (500×600, fixed size, dark background `#1e1e2e`, centered on screen at startup). Rather than opening separate windows per screen, it swaps the contents of the same window between four "screens," each built by its own method: `show_login_screen()`, `show_register_screen()`, `show_forgot_screen()`, and `show_dashboard(username)`. A helper, `create_entry()`, builds consistently styled `ttk.Entry` widgets (with optional placeholder text and password-masking via `show='*'`) so each screen doesn't repeat the same widget styling code.

Because there's no server and no browser, there's also no session, no cookies, and no HTTP — "being logged in" is just whichever screen `LoginApp` is currently showing, held in memory for as long as the window is open. Password reset here doesn't send an email either; since it's an offline desktop tool, the "forgot password" screen generates a token and displays it directly in the UI (there's no email server to send it through).

---

## Comparing the three approaches

| | Django | Flask | Tkinter |
|---|---|---|---|
| Where the "app" lives | Multi-file project/app structure | One file, `app.py` | One file, `main.py` |
| Database access | Django ORM + migrations | SQLAlchemy ORM, `db.create_all()` | Raw `sqlite3` + hand-written SQL |
| Password hashing | Django's built-in hasher (PBKDF2 by default) | bcrypt (`Flask-Bcrypt`) | Manual PBKDF2-HMAC-SHA256, 100k iterations |
| Session mechanism | Django's signed-cookie session framework | Flask's signed-cookie session, used manually | None — in-memory GUI state only |
| CSRF protection | Built in (`CsrfViewMiddleware`, `{% csrf_token %}` in templates) | **Not implemented** — no CSRF tokens anywhere | Not applicable (no HTTP forms) |
| Admin interface | Yes, Django admin (`/admin/`) | No | No |
| Email delivery | Django's email backend (console by default) | Flask-Mail (SMTP), with a console-flash fallback | None — token shown directly in the UI |
| Good for learning | Django's "batteries-included" auth stack and ORM/migrations | Explicit request handling and manual session/security decisions | Building stateful GUIs and working with SQLite directly |

---

## Prerequisites

- **Python 3.10+** (compiled `.pyc` files for 3.12 and 3.14 are included in the repo purely as build artifacts of previous runs — they're not required and any modern Python 3 interpreter will regenerate its own).
- **pip**, to install dependencies.
- **Git**, to clone the repository.
- **Tkinter**, for the desktop app only. It ships with the standard python.org installers on Windows and macOS. On Debian/Ubuntu-based Linux, install it separately:
  ```bash
  sudo apt update && sudo apt install python3-tk
  ```
- A **Gmail account with an App Password** (or any other SMTP provider's credentials), only if you want the Flask app to send real password-reset emails instead of falling back to on-screen tokens.

---

## Installation

**1. Clone the repository:**

```bash
git clone https://github.com/alfiematt/Login.git
cd Login/login_systems
```

**2. Create and activate a virtual environment.** This keeps this project's dependencies isolated from other Python projects on your machine, and is strongly recommended:

```bash
python -m venv venv
```

Activate it — the command differs by platform:

```bash
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows (cmd.exe)
venv\Scripts\Activate.ps1       # Windows (PowerShell)
```

You'll know it worked because your shell prompt gets a `(venv)` prefix.

**3. Install the shared dependencies.** One `requirements.txt` covers both web apps:

```bash
pip install -r requirements.txt
```

What each package is for:

| Package | Used by | Purpose |
|---|---|---|
| `Django>=5.0` | Django app | Web framework, ORM, admin, auth system |
| `Flask>=3.0` | Flask app | Web framework, routing, templating (Jinja2) |
| `Flask-SQLAlchemy>=3.1` | Flask app | ORM layer for the `User`/`LoginHistory` models |
| `Flask-Bcrypt>=1.0` | Flask app | bcrypt password hashing |
| `Flask-Mail>=0.10` | Flask app | Sending password-reset emails via SMTP |

The Tkinter app needs **none of these** — it only imports from the Python standard library (`tkinter`, `sqlite3`, `hashlib`, `secrets`, `re`, `datetime`).

**4. Verify the install:**

```bash
python -c "import django, flask, flask_sqlalchemy, flask_bcrypt, flask_mail; print('OK')"
```

If that prints `OK` with no errors, you're ready to run any of the three apps.

---

## Running and using each system

### A. Django

```bash
cd login_systems/django_login

python manage.py migrate           # create/update the database schema
python manage.py createsuperuser   # optional: create an account for /admin/
python manage.py runserver         # start the dev server
```

The repo already ships with a `db.sqlite3` file, but running `migrate` is safe and idempotent even if the schema is already current — always run it after a fresh clone. `createsuperuser` will interactively ask for a username, email, and password.

Open **http://127.0.0.1:8000/** and you'll be redirected to `/accounts/login/` (or `/accounts/dashboard/` if already logged in — see the root URL's redirect logic in `accounts/urls.py`).

Walking through the flow:
1. Go to **`/accounts/register/`**, fill in username, email, and a password meeting the strength rules (shown as a bulleted list under the password field), confirm it, and submit. You'll be redirected to the login page with a success message.
2. Log in at **`/accounts/login/`**. On success you land on **`/accounts/dashboard/`**, which lists your last 10 login attempts (success/failure, timestamp).
3. **`/accounts/logout/`** clears your session.
4. **`/accounts/password-reset/`** starts the reset flow — enter your email, and Django will print an email containing the reset link to the terminal you ran `runserver` in (because `EMAIL_BACKEND` is the console backend by default). Copy that link into your browser to reach the confirm page and set a new password.
5. **`/admin/`** — log in with the superuser account you created to browse/edit `User` and `LoginHistory` rows directly.

### B. Flask

```bash
cd login_systems/flask_login
python app.py
```

This single command creates `flask_auth.db` on first run (inside an app context, via `db.create_all()`) and starts the dev server on **http://127.0.0.1:5000/**, listening on all interfaces (`0.0.0.0`) so it's also reachable from other devices on your network at your machine's LAN IP.

Walking through the flow:
1. **`/register`** — same field/validation rules as Django. On success, redirects to `/login`.
2. **`/login`** — on success, sets the session and takes you to **`/dashboard`**, which shows your last 10 login-history entries.
3. **`/logout`** — clears the session.
4. **`/forgot-password`** — enter your email. If `MAIL_USERNAME`/`MAIL_PASSWORD` aren't configured (or sending fails for any reason), the app catches the exception and **flashes your reset token directly on the page** instead — copy it into the next step. If mail *is* configured, check that inbox for a styled HTML email with a "Reset Password" button.
5. **`/reset-password/<token>`** — paste the token into the URL (or click the emailed link) to reach the new-password form.

Optional CLI commands (run from `login_systems/flask_login`, with the Flask app discoverable):

```bash
export FLASK_APP=app.py      # Windows (cmd.exe): set FLASK_APP=app.py
flask init-db                # (re)create all tables
flask create-admin           # interactively create a user from the terminal
```

### C. Tkinter

```bash
cd login_systems/tkinter_login
python main.py
```

A 500×600 dark-themed window opens, centered on your screen. `users.db` is created automatically in the same folder the first time you run it.

Walking through the flow:
1. On the **login screen**, click through to **Register**, fill in username/email/password (same strength rules), and submit — you'll be dropped back on the login screen.
2. Log in with those credentials to reach the **dashboard screen**, which lists your recent login history.
3. From the login screen, **Forgot Password?** takes you to a screen where you enter your email; since there's no email server, the generated reset token is displayed directly on screen for you to use immediately.
4. There's a **Logout**/back action on the dashboard to return to the login screen — closing the window ends the "session" entirely, since nothing is persisted except the SQLite database itself.

---

## Environment variables

None of the three apps *require* environment variables to run locally — they all ship with working (if insecure) defaults, precisely so a fresh clone runs immediately. Set these before deploying anywhere real:

### Flask (`login_systems/flask_login/app.py`)

| Variable | Purpose | Default if unset |
|---|---|---|
| `SECRET_KEY` | Signs session cookies; anyone who has it can forge a logged-in session | `dev-secret-key-change-in-production` |
| `MAIL_SERVER` | SMTP host for sending reset emails | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USERNAME` | SMTP account username | `your-email@gmail.com` |
| `MAIL_PASSWORD` | SMTP account password (use a Gmail **App Password**, not your real password, if using Gmail) | `your-app-password` |
| `MAIL_DEFAULT_SENDER` | "From" address on outgoing emails | `noreply@securelogin.com` |

Example:

```bash
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export MAIL_USERNAME="you@gmail.com"
export MAIL_PASSWORD="your-16-character-app-password"
export MAIL_DEFAULT_SENDER="you@gmail.com"
python app.py
```

### Django (`login_systems/django_login/login_system/settings.py`)

Django's `settings.py` currently hardcodes these values rather than reading them from the environment. For anything beyond local development, either edit the file directly or (better) refactor it to read from `os.environ` — a common pattern is to add a package like `python-decouple` or `django-environ` and load a `.env` file. At minimum, replace:

| Setting | Purpose |
|---|---|
| `SECRET_KEY` | Signs sessions and other cryptographic tokens (e.g. password-reset links) — must be long, random, and secret |
| `DEBUG` | Must be `False` outside local development — `True` leaks stack traces and settings to visitors on error pages |
| `ALLOWED_HOSTS` | Domains allowed to serve the app; Django rejects requests with any other `Host` header |
| `EMAIL_BACKEND` / `EMAIL_HOST*` | Switch off the console backend to an SMTP backend so reset emails actually send |

---

## Testing the password-reset flow locally

Since neither web app requires a real mail server to function locally, here's exactly what to expect:

- **Django:** with the default console `EMAIL_BACKEND`, requesting a reset prints the full email (including the reset link) to the same terminal window running `runserver`. Scroll up in that terminal, copy the URL, and paste it into your browser.
- **Flask:** if `MAIL_USERNAME`/`MAIL_PASSWORD` aren't set (or the SMTP call throws for any reason — wrong credentials, no internet, etc.), the app catches it and flashes the raw token on the `/forgot-password` page itself. Take that token and manually visit `/reset-password/<token>` in your browser.
- **Tkinter:** there's no mail step at all — the generated token is shown directly on the "forgot password" screen.

---

## Deployment

### Deploying the Flask app

1. Install a production WSGI server: `pip install gunicorn`.
2. Set the environment variables from the table above on your hosting platform (never commit real credentials to the repo).
3. Move off SQLite if you expect more than one concurrent user — SQLite doesn't handle concurrent writes well. Point `app.config['SQLALCHEMY_DATABASE_URI']` at a managed PostgreSQL/MySQL instance instead, ideally read from an environment variable rather than hardcoded in `app.py`.
4. Replace the dev server with Gunicorn:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```
   (`-w 4` runs 4 worker processes; tune this to your host's CPU count.)
5. Remove `debug=True` from the `app.run(...)` call at the bottom of `app.py` — that block is only used when running `python app.py` directly, which you won't do in production once Gunicorn is running the app.
6. Deploy the Gunicorn command to a platform such as **Render**, **Railway**, **Fly.io**, or **PythonAnywhere**, or to your own VPS with **Nginx** as a reverse proxy in front of Gunicorn. Most managed platforms auto-detect `requirements.txt`, and let you set the start command (`gunicorn app:app`) and environment variables through their dashboard — no Dockerfile required unless you want one.
7. If you'd rather containerize it, a minimal `Dockerfile` looks like:
   ```dockerfile
   FROM python:3.12-slim
   WORKDIR /app
   COPY login_systems/requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt gunicorn
   COPY login_systems/flask_login .
   ENV PORT=8000
   CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
   ```

### Deploying the Django app

1. Set `DEBUG = False` and populate `ALLOWED_HOSTS` with your real domain(s).
2. Move `SECRET_KEY` and email credentials into environment variables — see [Environment variables](#environment-variables).
3. Point `DATABASES['default']` at a production database (PostgreSQL is the common default for Django) if you need more than single-user local testing.
4. Install a WSGI server and a static-file handler:
   ```bash
   pip install gunicorn whitenoise
   python manage.py collectstatic
   ```
   (`collectstatic` gathers `static/css/style.css` and anything else in `STATICFILES_DIRS` into one directory for serving in production.)
5. Run with Gunicorn against the WSGI entry point already provided in `login_system/wsgi.py`:
   ```bash
   gunicorn login_system.wsgi:application -b 0.0.0.0:8000
   ```
6. Deploy to **Render**, **Railway**, **Heroku**, or a VPS with Nginx in front of Gunicorn, the same way as the Flask app. Set `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and switch `EMAIL_BACKEND` to the SMTP backend so reset emails actually send instead of going to a console no one can see.
7. Run `python manage.py migrate` against the production database as part of your deploy step (most platforms let you run a one-off "release command" for this).
8. A minimal `Dockerfile`, if you'd rather containerize:
   ```dockerfile
   FROM python:3.12-slim
   WORKDIR /app
   COPY login_systems/requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt gunicorn whitenoise
   COPY login_systems/django_login .
   RUN python manage.py collectstatic --noinput
   CMD ["gunicorn", "login_system.wsgi:application", "-b", "0.0.0.0:8000"]
   ```

### "Deploying" the Tkinter app

There's no server to host — a desktop app is "deployed" by packaging it into a standalone executable that end users can double-click without installing Python themselves:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed login_systems/tkinter_login/main.py
```

- `--onefile` bundles everything into a single executable.
- `--windowed` (a.k.a. `--noconsole`) suppresses the background console window on Windows/macOS, since this is a GUI app.
- The output lands in a `dist/` folder — `main.exe` on Windows, or a native binary on macOS/Linux.
- **PyInstaller builds are platform-specific** — you must run it on Windows to produce a Windows `.exe`, on macOS to produce a macOS app, and so on; there's no cross-compiling from one OS to another.
- `users.db` is created next to wherever the executable is actually run from, so ship it standalone, or use `--add-data` if you want to bundle a pre-populated database.
- Some antivirus tools flag freshly built PyInstaller executables as suspicious purely because of *how* PyInstaller bundles a Python interpreter (a well-known false-positive pattern) — code-signing the executable reduces this if you're distributing it widely.

---

## Security review

These are educational/demo implementations, not audited production code. Specific issues worth knowing about before using any of them beyond local testing:

- **Hardcoded secrets.** Django's `SECRET_KEY` and Flask's default mail credentials are committed in plain text in the source. Anyone with read access to the repo can forge Django session cookies or password-reset tokens using that key. Move every secret to an environment variable and rotate it before any real deployment.
- **`DEBUG = True` / `debug=True`.** Both frameworks' debug modes show detailed stack traces on error and, in Flask's case, expose an **interactive in-browser debugger that can execute arbitrary Python code** if reached by an attacker. Both must be turned off outside local development.
- **No CSRF protection in the Flask app.** Django has it built in (`CsrfViewMiddleware` + `{% csrf_token %}` in every form). The Flask app has no CSRF tokens at all — anyone can trick a logged-in user's browser into submitting the register/login/password forms from another site. Adding `Flask-WTF`'s CSRF protection (or manually issuing/validating a token per session) closes this gap.
- **Username enumeration.** The Flask login route shows "User not found" vs. "Invalid password" as separate messages, which lets an attacker confirm which usernames exist by trying logins. A generic "Invalid username or password" message for both cases avoids this. (The password-reset routes in all three apps already do this correctly — they show the same message regardless of whether the email exists.)
- **No rate limiting anywhere.** Nothing stops repeated automated login or password-reset attempts. In production, add rate limiting (e.g. `Flask-Limiter`, `django-ratelimit`, or a reverse-proxy/WAF rule) on `/login`, `/register`, and the password-reset endpoints.
- **SQLite in all three apps.** Fine for learning and for the Tkinter app's single-user use case, but SQLite is not built for concurrent writes from many simultaneous web users — a production web deployment should move to PostgreSQL or MySQL.
- **The Tkinter app's password hashing is hand-rolled**, not using a vetted library — it's PBKDF2-HMAC-SHA256 at 100,000 iterations with a fresh random salt per user, which is a reasonable choice, but note that OWASP's current guidance recommends higher iteration counts for PBKDF2-SHA256 (upwards of 600,000) as hardware gets faster; the Django and Flask apps use battle-tested hashers (Django's built-in PBKDF2 hasher and bcrypt, respectively) that are easier to keep current.
- **No enforced HTTPS.** Both web apps run over plain HTTP locally; deploy behind HTTPS in production (most platforms named above provide this automatically, or terminate TLS at Nginx).

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `ModuleNotFoundError: No module named 'flask'` (or `django`, etc.) | Your virtual environment isn't activated, or `pip install -r requirements.txt` wasn't run inside it. |
| `ModuleNotFoundError: No module named 'tkinter'` | On Linux, install the OS package: `sudo apt install python3-tk`. |
| `OSError: [Errno 98] Address already in use` (Flask) or similar for Django | Something else is already using port 5000/8000. Stop it, or run on a different port: `flask run -p 5001` / `python manage.py runserver 8001`. |
| `django.db.utils.OperationalError: no such table` | You haven't run `python manage.py migrate` yet. |
| `sqlite3.OperationalError: database is locked` | SQLite doesn't handle many simultaneous writers well — this is more likely under concurrent load; avoid running multiple write-heavy processes against the same `.db` file at once. |
| Password-reset email never arrives (Flask) | Check that `MAIL_USERNAME`/`MAIL_PASSWORD` are set and correct. If using Gmail, you need an **App Password** (Google blocks plain-password SMTP logins by default) — or just use the token that gets flashed on the page as a fallback. |
| Password-reset email never arrives (Django) | Expected in local dev — check the terminal running `runserver` for the printed email (console backend). |
| Tkinter window opens but looks unstyled/tiny fonts | This is a platform-rendering difference in `ttk` themes, not a bug in the app logic; it doesn't affect functionality. |

---

## Suggested improvements

If you're extending this repo (e.g. for a coursework or portfolio project), reasonable next steps in rough priority order:

1. Add CSRF protection to the Flask app (`Flask-WTF`).
2. Move all secrets (Django `SECRET_KEY`, Flask `SECRET_KEY`/mail credentials) into environment variables read via `os.environ`, loaded from a local `.env` file with `python-dotenv` for development.
3. Add rate limiting on login, registration, and password-reset endpoints in both web apps.
4. Add automated tests (`pytest` + Django's/Flask's test clients) covering registration validation, login success/failure, and the reset-token expiry logic.
5. Add email verification on registration (the Django `User` model already has an unused `email_verified` field ready for this).
6. Containerize both web apps with the sample `Dockerfile`s above and add a `docker-compose.yml` that also runs PostgreSQL, for a more production-like local setup.
7. Increase the Tkinter app's PBKDF2 iteration count, or swap in `bcrypt`/`argon2` if you add it as a dependency.

---

## License

No license file is currently included in this repository. Add a `LICENSE` file (MIT is a common, permissive choice) if you intend for others to reuse this code.
