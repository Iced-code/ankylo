function setTheme(){
    document.body.classList.toggle("light")
    document.body.classList.toggle("dark")
}

function toggleDisplay(name){
    let el = document.getElementById(name); 
    if(el.style.display === "none"){
        el.style.display = "block";   
    }
    else {
        el.style.display = "none";   
    } 
}

async function loadEntries() {
    const res = await fetch("http://127.0.0.1:5000/entries");
    const data = await res.json()

    const list = document.getElementById("list");
    list.innerHTML = "";

    data.forEach(entry => {
        const li = document.createElement("li");
        li.textContent = entry.name;
        li.value = entry.name;

        // li.addEventListener('click', getEntry(entry.name));
        list.appendChild(li);
    });
}

async function getEntry(name) {
    const res = await fetch(`http://127.0.0.1:5000/get/${name}`);
    const data = await res.json()

    console.log(data["entry"]);
}

async function addEntry() {
    const name = document.getElementById("name").value;
    const api_key = document.getElementById("apiKey").value;

    const response = await fetch("http://127.0.0.1:5000/add", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ name: name, api_key: api_key })
    });
    
    loadEntries();
}

async function loginUser() {
    const password = document.getElementById("login").value;
    
    const response = await fetch("http://127.0.0.1:5000/unlock", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ password: password })
    });
    const data = await response.json();

    // console.log(response);

    if(data["status"] === "OK"){
        loadEntries();
        toggleDisplay("loginField")
    }
    else {
        document.getElementById("msg").innerText = "Invalid Password";
    }
}

// loginUser();
// loadEntries();