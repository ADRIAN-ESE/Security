// -----------------------------
// Utilities
// -----------------------------
function strToUint8(str){ return new TextEncoder().encode(str); }
function uint8ToStr(buf){ return new TextDecoder().decode(buf); }
function base64Encode(buf){ return btoa(String.fromCharCode(...buf)); }
function base64Decode(str){ return Uint8Array.from(atob(str), c=>c.charCodeAt(0)); }

// -----------------------------
// Encryption
// -----------------------------
async function deriveKey(master, salt){
    const keyMaterial = await crypto.subtle.importKey(
        "raw", strToUint8(master), "PBKDF2", false, ["deriveKey"]
    );
    return crypto.subtle.deriveKey(
        {name:"PBKDF2", salt, iterations:200000, hash:"SHA-256"},
        keyMaterial, {name:"AES-GCM", length:256}, false, ["encrypt","decrypt"]
    );
}

async function encrypt(text, master){
    const salt = crypto.getRandomValues(new Uint8Array(16));
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const key = await deriveKey(master, salt);
    const encrypted = await crypto.subtle.encrypt({name:"AES-GCM", iv}, key, strToUint8(text));
    const combined = new Uint8Array([...salt, ...iv, ...new Uint8Array(encrypted)]);
    return base64Encode(combined);
}

async function decrypt(dataB64, master){
    try{
        const data = base64Decode(dataB64);
        const salt = data.slice(0,16);
        const iv = data.slice(16,28);
        const encrypted = data.slice(28);
        const key = await deriveKey(master, salt);
        const decrypted = uint8ToStr(await crypto.subtle.decrypt({name:"AES-GCM", iv}, key, encrypted));
        return decrypted;
    }catch{ return null; }
}

// -----------------------------
// Password Manager Logic
// -----------------------------
let masterPassword;
function unlockManager(){
    masterPassword = document.getElementById("masterPassword").value;
    if(!masterPassword){ alert("Enter master password"); return; }
    document.getElementById("manager").style.display="block";
    loadEntries();
}

// Generate random password
function generatePassword(){
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()";
    let pwd=""; for(let i=0;i<16;i++) pwd+=chars[Math.floor(Math.random()*chars.length)];
    document.getElementById("password").value=pwd;
}

// Save entry
async function saveEntry(){
    const site=document.getElementById("site").value.trim();
    const username=document.getElementById("username").value.trim();
    const password=document.getElementById("password").value.trim();
    if(!site||!username||!password){ alert("All fields required"); return; }

    const encrypted = await encrypt(JSON.stringify({site,username,password}), masterPassword);
    const entries = JSON.parse(localStorage.getItem("pmEntries")||"[]");
    entries.push(encrypted);
    localStorage.setItem("pmEntries", JSON.stringify(entries));
    loadEntries();
}

// Load entries
async function loadEntries(){
    const tbody = document.querySelector("#passwordTable tbody");
    tbody.innerHTML="";
    const entries = JSON.parse(localStorage.getItem("pmEntries")||"[]");
    for(const [i,e] of entries.entries()){
        const decrypted = await decrypt(e, masterPassword);
        if(!decrypted) continue;
        const obj = JSON.parse(decrypted);
        const tr=document.createElement("tr");
        tr.innerHTML=`<td>${obj.site}</td><td>${obj.username}</td><td>${obj.password}</td>
      <td><button onclick="deleteEntry(${i})">Delete</button></td>`;
        tbody.appendChild(tr);
    }
}

// Delete entry
function deleteEntry(index){
    const entries = JSON.parse(localStorage.getItem("pmEntries")||"[]");
    entries.splice(index,1);
    localStorage.setItem("pmEntries", JSON.stringify(entries));
    loadEntries();
}

// Dark / Light mode
function toggleTheme(){ document.body.classList.toggle("light-mode"); }
