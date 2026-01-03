const MAX_ATTEMPTS = 5;
const LOCKOUT = 30000;

function load(k){ return JSON.parse(localStorage.getItem(k)) || {}; }
function save(k,v){ localStorage.setItem(k,JSON.stringify(v)); }

async function hash(password, salt=crypto.randomUUID()){
    const enc=new TextEncoder();
    const key=await crypto.subtle.importKey("raw",enc.encode(password),"PBKDF2",false,["deriveBits"]);
    const bits=await crypto.subtle.deriveBits({name:"PBKDF2",salt:enc.encode(salt),iterations:100000,hash:"SHA-256"},key,256);
    return `${salt}$${btoa(String.fromCharCode(...new Uint8Array(bits)))}`;
}

async function verify(stored, pass){
    const [salt]=stored.split("$");
    return stored===await hash(pass,salt);
}

function msg(t,c="info"){
    message.innerText=t;
    message.className=c;
}

async function register(){
    const u=username.value.trim();
    const p=password.value;
    if(!u||p.length<4) return msg("Invalid input","error");

    const users=load("users");
    if(users[u]) return msg("User exists","error");

    users[u]={password:await hash(p),created:Date.now()};
    save("users",users);
    msg("Account created","success");
}

async function login(){
    const u=username.value.trim();
    const p=password.value;
    const users=load("users");
    const at=load("attempts");
    const now=Date.now();
    let r=at[u]||{fails:0,locked:0};

    if(r.locked>now) return msg("Account locked","error");

    if(users[u] && await verify(users[u].password,p)){
        localStorage.setItem("loggedInUser",u);
        delete at[u];
        save("attempts",at);
        location.href="dashboard.html";
        return;
    }

    r.fails++;
    if(r.fails>=MAX_ATTEMPTS){ r.locked=now+LOCKOUT; }
    at[u]=r;
    save("attempts",at);
    msg("Login failed","error");
}
