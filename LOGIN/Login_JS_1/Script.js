const MAX_ATTEMPTS = 5;
const LOCKOUT_DURATION = 30 * 1000; // ms

/* ---------- Utilities ---------- */

function load(key) {
    return JSON.parse(localStorage.getItem(key)) || {};
}

function save(key, data) {
    localStorage.setItem(key, JSON.stringify(data));
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

/* ---------- Core Logic ---------- */

async function register() {
    const user = username.value.trim();
    const pass = password.value;

    const users = load("users");

    if (users[user]) {
        return show("Username already exists");
    }

    users[user] = {
        password: await hashPassword(pass),
        created_at: Date.now()
    };

    save("users", users);
    show("User registered successfully");
}

async function login() {
    const user = username.value.trim();
    const pass = password.value;

    const users = load("users");
    const attempts = load("attempts");
    const now = Date.now();

    let record = attempts[user] || { fails: 0, locked_until: 0 };

    if (record.locked_until > now) {
        return show(`Account locked. Try again in ${Math.ceil((record.locked_until - now)/1000)}s`);
    }

    if (users[user] && await verifyPassword(users[user].password, pass)) {
        delete attempts[user];
        save("attempts", attempts);
        show("Login successful");
        return;
    }

    record.fails++;

    if (record.fails >= MAX_ATTEMPTS) {
        record.locked_until = now + LOCKOUT_DURATION;
        show("Too many attempts. Account locked.");
    } else {
        show(`Login failed (${record.fails}/${MAX_ATTEMPTS})`);
    }

    attempts[user] = record;
    save("attempts", attempts);
}

/* ---------- UI ---------- */

function show(msg) {
    document.getElementById("message").innerText = msg;
}
