
// generate initial empty screen
document.querySelector(".screen").innerHTML = ('  '.repeat(64) + '<br>').repeat(32);


// constants for elements
const runButton = document.querySelector(".run-pause");
const screen = document.querySelector(".screen");
const infobox = document.querySelector(".info");


// add toggle function to runButton
runButton.addEventListener("click", function() {
    if (runButton.textContent === "Run") {
        runButton.textContent = "Pause";
        runButton.style.color = "red";
        pywebview.api.run_loop()                        // this is a function in python
    } else if (runButton.textContent === "Pause") {
        runButton.textContent = "Run";
        runButton.style.color = "green";
        pywebview.api.pause_loop()                      // this is a function in python
    };
});
