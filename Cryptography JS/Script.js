const encoder = new TextEncoder();
const decoder = new TextDecoder();

async function deriveKey(password, salt) {
    const keyMaterial = await crypto.subtle.importKey(
        "raw",
        encoder.encode(password),
        "PBKDF2",
        false,
        ["deriveKey"]
    );

    return crypto.subtle.deriveKey(
        {
            name: "PBKDF2",
            salt: salt,
            iterations: 200000,
            hash: "SHA-256"
        },
        keyMaterial,
        { name: "AES-GCM", length: 256 },
        false,
        ["encrypt", "decrypt"]
    );
}

function base64Encode(buffer) {
    return btoa(String.fromCharCode(...new Uint8Array(buffer)));
}

function base64Decode(base64) {
    return Uint8Array.from(atob(base64), c => c.charCodeAt(0));
}

async function encryptMessage() {
    const message = document.getElementById("message").value;
    const password = document.getElementById("password").value;
    if (!message || !password) return alert("Enter message and password");

    const salt = crypto.getRandomValues(new Uint8Array(16));
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const key = await deriveKey(password, salt);

    const encrypted = await crypto.subtle.encrypt(
        { name: "AES-GCM", iv },
        key,
        encoder.encode(message)
    );

    const combined = new Uint8Array([
        ...salt,
        ...iv,
        ...new Uint8Array(encrypted)
    ]);

    document.getElementById("result").value = base64Encode(combined);
}

async function decryptMessage() {
    try {
        const data = base64Decode(document.getElementById("message").value);
        const password = document.getElementById("password").value;

        const salt = data.slice(0, 16);
        const iv = data.slice(16, 28);
        const encrypted = data.slice(28);

        const key = await deriveKey(password, salt);

        const decrypted = await crypto.subtle.decrypt(
            { name: "AES-GCM", iv },
            key,
            encrypted
        );

        document.getElementById("result").value = decoder.decode(decrypted);
    } catch {
        alert("Wrong password or corrupted message");
    }
}

function copyResult() {
    const result = document.getElementById("result");
    result.select();
    document.execCommand("copy");
    alert("Copied to clipboard");
}
