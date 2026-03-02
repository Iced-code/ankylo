function toggleDisplay(elementID){
    const element = document.getElementById(elementID);
    if(element.style.display === "none"){
        element.style.display = "inline";
    }
    else {
        element.style.display = "none";
    }
}

function checkFlag(answer){
    const element = document.getElementById("flag");
    if(element.value === answer){
        element.style.color = "green";
    }
}