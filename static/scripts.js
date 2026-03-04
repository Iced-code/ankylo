function setTheme(){
    document.body.classList.toggle("light")
    document.body.classList.toggle("dark")

    if (document.body.classList.contains("light")){
        document.getElementById("themeButton").innerHTML = "&#x263E;";
    }
    else {
        document.getElementById("themeButton").innerHTML = "&#x2600;";
    }
}
