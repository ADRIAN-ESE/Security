function protectPage() {
    if (!localStorage.getItem("loggedInUser")) {
        window.location.href = "index.html";
    }
}

function logout() {
    localStorage.removeItem("loggedInUser");
    window.location.href = "index.html";
}

function loadData() {
    return JSON.parse(localStorage.getItem("finance")) || {
        income: [],
        expenses: []
    };
}

function saveData(data) {
    localStorage.setItem("finance", JSON.stringify(data));
}

function addTransaction(type) {
    const desc = document.getElementById("desc").value;
    const amount = parseFloat(document.getElementById("amount").value);
    const date = document.getElementById("date").value || new Date().toISOString().split("T")[0];

    if (!desc || amount <= 0) {
        alert("Invalid input");
        return;
    }

    const data = loadData();
    data[type].push({ desc, amount, date });
    saveData(data);

    render();
}

function deleteTransaction(type, index) {
    const data = loadData();
    data[type].splice(index, 1);
    saveData(data);
    render();
}

function render() {
    const data = loadData();

    const incomeTotal = data.income.reduce((a, b) => a + b.amount, 0);
    const expenseTotal = data.expenses.reduce((a, b) => a + b.amount, 0);

    document.getElementById("summary").innerText =
        `Income: $${incomeTotal.toFixed(2)} | Expenses: $${expenseTotal.toFixed(2)} | Balance: $${(incomeTotal - expenseTotal).toFixed(2)}`;

    const box = document.getElementById("transactions");
    box.innerHTML = "";

    ["income", "expenses"].forEach(type => {
        data[type].forEach((t, i) => {
            box.innerHTML += `
                <div class="row">
                    ${type.toUpperCase()} — ${t.desc} ($${t.amount}) [${t.date}]
                    <button onclick="deleteTransaction('${type}', ${i})">✖</button>
                </div>
            `;
        });
    });
}

render();
