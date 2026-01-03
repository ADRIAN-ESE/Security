const MAX_ATTEMPTS = 5;
const LOCKOUT_DURATION = 30 * 1000; // 30 seconds

/* ---------- Storage Helpers ---------- */
function load(key) {
    return JSON.parse(localStorage.getItem(key)) || {};
}

function save(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
}

/* ---------- Crypto ---------- */
async function hashPassword(password, salt = crypto.randomUUID()) {
    const enc = new TextEncoder();

    const keyMaterial = await crypto.subtle.importKey(
        "raw",
        enc.encode(password),
        { name: "PBKDF2" },
        false,
        ["deriveBits"]
    );

    const hash = await crypto.subtle.deriveBits(
        {
            name: "PBKDF2",
            salt: enc.encode(salt),
            iterations: 100000,
            hash: "SHA-256"
        },
        keyMaterial,
        256
    );

    return `${salt}$${btoa(String.fromCharCode(...new Uint8Array(hash)))}`;
}

async function verifyPassword(stored, password) {
    const [salt] = stored.split("$");
    return stored === await hashPassword(password, salt);
}

/* ---------- UI Feedback ---------- */
function show(msg, type = "info") {
    const box = document.getElementById("message");
    box.innerText = msg;
    box.className = type;
}

/* ---------- Auth Logic ---------- */
async function register() {
    const user = username.value.trim();
    const pass = password.value;

    if (!user || pass.length < 4) {
        show("Username and stronger password required", "error");
        return;
    }

    const users = load("users");

    if (users[user]) {
        show("Username already exists", "error");
        return;
    }

    users[user] = {
        password: await hashPassword(pass),
        created: Date.now()
    };

    save("users", users);
    show("Registration successful", "success");
}

async function login() {
    const user = username.value.trim();
    const pass = password.value;

    const users = load("users");
    const attempts = load("attempts");
    const now = Date.now();

    const record = attempts[user] || { fails: 0, locked_until: 0 };

    if (record.locked_until > now) {
        show(
            `Account locked. Try again in ${Math.ceil((record.locked_until - now) / 1000)}s`,
            "error"
        );
        return;
    }

    if (users[user] && await verifyPassword(users[user].password, pass)) {
        localStorage.setItem("loggedInUser", user);
        delete attempts[user];
        save("attempts", attempts);
        window.location.href = "dashboard.html";
        return;
    }

    record.fails++;

    if (record.fails >= MAX_ATTEMPTS) {
        record.locked_until = now + LOCKOUT_DURATION;
        show("Too many attempts. Account locked.", "error");
    } else {
        show(`Login failed (${record.fails}/${MAX_ATTEMPTS})`, "error");
    }

    attempts[user] = record;
    save("attempts", attempts);
}
