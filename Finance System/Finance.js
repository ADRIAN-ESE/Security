function user(){ return localStorage.getItem("loggedInUser"); }
function key(){ return `finance_${user()}`; }

function loadData(){
    return JSON.parse(localStorage.getItem(key())) || {income:[],expenses:[]};
}
function saveData(d){ localStorage.setItem(key(),JSON.stringify(d)); }

function init(){
    if(!user()) location.href="index.html";
    userTitle.innerText=`Welcome, ${user()}`;
    render();
}

function addTransaction(type){
    const d=desc.value;
    const a=parseFloat(amount.value);
    const dt=date.value||new Date().toISOString().split("T")[0];
    if(!d||a<=0) return alert("Invalid input");

    const data=loadData();
    data[type].push({d,a,dt});
    saveData(data);
    render();
}

function render(){
    const data=loadData();
    const i=data.income.reduce((x,y)=>x+y.a,0);
    const e=data.expenses.reduce((x,y)=>x+y.a,0);
    summary.innerText=`Income: $${i} | Expenses: $${e} | Balance: $${i-e}`;

    transactions.innerHTML="";
    ["income","expenses"].forEach(t=>{
        data[t].forEach((x,i)=>{
            transactions.innerHTML+=`
            <div class="row">
                ${t.toUpperCase()} — ${x.d} ($${x.a}) ${x.dt}
                <button onclick="del('${t}',${i})">✖</button>
            </div>`;
        });
    });
}

function del(t,i){
    const d=loadData();
    d[t].splice(i,1);
    saveData(d);
    render();
}

function logout(){
    localStorage.removeItem("loggedInUser");
    location.href="index.html";
}

function switchAccount(){
    logout();
}

function deleteAccount(){
    if(!confirm("Delete account permanently?")) return;
    localStorage.removeItem(key());
    const users=load("users");
    delete users[user()];
    save("users",users);
    logout();
}

function exportData(){
    const blob=new Blob([JSON.stringify(loadData(),null,2)],{type:"application/json"});
    const a=document.createElement("a");
    a.href=URL.createObjectURL(blob);
    a.download=`${user()}_finance.json`;
    a.click();
}
