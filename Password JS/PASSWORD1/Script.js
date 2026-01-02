// -----------------------------
// Utilities
// -----------------------------
function strToUint8(str){ return new TextEncoder().encode(str); }
function uint8ToStr(buf){ return new TextDecoder().decode(buf); }
function base64Encode(buf){ return btoa(String.fromCharCode(...buf)); }
function base64Decode(str){ return Uint8Array.from(atob(str), c=>c.charCodeAt(0)); }

// -----------------------------
// Crypto
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
    return base64Encode(new Uint8Array([...salt,...iv,...new Uint8Array(encrypted)]));
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
// Admin / Manager
// -----------------------------
let masterPassword;
let autoLockTimer;
const AUTO_LOCK_MINUTES = 3;

async function unlockManager(){
    masterPassword = document.getElementById("masterPassword").value;
    if(!masterPassword){ alert("Enter master password"); return; }
    document.getElementById("manager").style.display="block";
    startAutoLock();
    await loadDemoData();
    loadEntries();
}

// -----------------------------
// Auto-lock
// -----------------------------
function startAutoLock(){
    clearTimeout(autoLockTimer);
    autoLockTimer = setTimeout(() => {
        masterPassword=null;
        document.getElementById("manager").style.display="none";
        alert("Session locked due to inactivity");
    }, AUTO_LOCK_MINUTES*60*1000);
}
document.addEventListener('mousemove', startAutoLock);
document.addEventListener('keypress', startAutoLock);

// -----------------------------
// Password JS Strength Meter
// -----------------------------
const passwordInput = document.getElementById("password");
const strengthDiv = document.getElementById("passwordStrength");
passwordInput.addEventListener("input", () => {
    const pwd = passwordInput.value;
    let score=0;
    if(pwd.length>=8) score++;
    if(/[A-Z]/.test(pwd)) score++;
    if(/[0-9]/.test(pwd)) score++;
    if(/[^A-Za-z0-9]/.test(pwd)) score++;
    const levels=["Very Weak","Weak","Medium","Strong","Very Strong"];
    strengthDiv.textContent="Password JS Strength: "+levels[score];
});

// -----------------------------
// Generate Password JS
// -----------------------------
function generatePassword(){
    const chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()";
    let pwd=""; for(let i=0;i<16;i++) pwd+=chars[Math.floor(Math.random()*chars.length)];
    passwordInput.value=pwd; passwordInput.dispatchEvent(new Event('input'));
}

// -----------------------------
// CRUD Entries
// -----------------------------
async function saveEntry(){
    const site=document.getElementById("site").value.trim();
    const username=document.getElementById("username").value.trim();
    const password=document.getElementById("password").value.trim();
    if(!site||!username||!password){ alert("All fields required"); return; }

    const encrypted = await encrypt(JSON.stringify({site,username,password}), masterPassword);
    const entries=JSON.parse(localStorage.getItem("pmEntries")||"[]");
    entries.push(encrypted);
    localStorage.setItem("pmEntries", JSON.stringify(entries));
    clearForm();
    loadEntries();
}

function clearForm(){
    document.getElementById("site").value="";
    document.getElementById("username").value="";
    document.getElementById("password").value="";
    strengthDiv.textContent="Password JS Strength:";
}

// -----------------------------
// Load / Filter Entries
// -----------------------------
async function loadEntries(filter=""){
    const tbody=document.querySelector("#passwordTable tbody");
    tbody.innerHTML="";
    const entries=JSON.parse(localStorage.getItem("pmEntries")||"[]");
    for(const [i,e] of entries.entries()){
        const decrypted=await decrypt(e,masterPassword);
        if(!decrypted) continue;
        const obj=JSON.parse(decrypted);
        if(filter && !obj.site.toLowerCase().includes(filter.toLowerCase()) && !obj.username.toLowerCase().includes(filter.toLowerCase())) continue;

        const tr=document.createElement("tr");
        const strength = getStrengthLevel(obj.password);
        tr.innerHTML=`<td>${obj.site}</td>
                    <td>${obj.username}</td>
                    <td>${obj.password}</td>
                    <td>${strength}</td>
                    <td>
                      <button onclick="deleteEntry(${i})">Delete</button>
                      <button onclick="copyPassword('${obj.password}')">Copy</button>
                    </td>`;
        tbody.appendChild(tr);
    }
}

function filterEntries(){
    const filter = document.getElementById("search").value.trim();
    loadEntries(filter);
}

function deleteEntry(index){
    const entries=JSON.parse(localStorage.getItem("pmEntries")||"[]");
    entries.splice(index,1);
    localStorage.setItem("pmEntries", JSON.stringify(entries));
    loadEntries();
}

function copyPassword(pwd){
    navigator.clipboard.writeText(pwd);
    alert("Password JS copied to clipboard!");
}

// -----------------------------
// Password JS Strength for Stored Passwords
// -----------------------------
function getStrengthLevel(pwd){
    let score=0;
    if(pwd.length>=8) score++;
    if(/[A-Z]/.test(pwd)) score++;
    if(/[0-9]/.test(pwd)) score++;
    if(/[^A-Za-z0-9]/.test(pwd)) score++;
    const levels=["Very Weak","Weak","Medium","Strong","Very Strong"];
    return levels[score];
}

// -----------------------------
// Dark / Light Mode
// -----------------------------
function toggleTheme(){ document.body.classList.toggle("light-mode"); }

// -----------------------------
// Sample Demo Data
// -----------------------------
async function loadDemoData(){
    const entries=JSON.parse(localStorage.getItem("pmEntries")||"[]");
    if(entries.length>0) return;

    const demoEntries = [
        {site:"GitHub", username:"demo_user", password:"GitHub123!"},
        {site:"Gmail", username:"demo@gmail.com", password:"GmailPass#1"},
        {site:"Facebook", username:"demo.fb", password:"FbSecure$88"},
    ];

    for(const entry of demoEntries){
        const encrypted = await encrypt(JSON.stringify(entry), masterPassword);
        entries.push(encrypted);
    }
    localStorage.setItem("pmEntries", JSON.stringify(entries));
}
