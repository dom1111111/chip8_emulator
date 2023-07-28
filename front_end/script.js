////////////////////
// Functions

//function which connects to internal python function to set speed
function setSpeed(val) {
    pywebview.api.set_emulation_speed(parseInt(val))    // value of Elemtents is str, must be converted to int with `parseInt`
}

// MOVE ON JS FUNCS TO THIS!

// fix draw screen characters
// mayeb even make it so that in operates on booleans, instead of characters? - and then let front end handle characters, as it should!

////////////////////

// constants for elements
const screen = document.querySelector(".screen");
const infobox = document.querySelector(".info");
const loadButton = document.querySelector(".load-program");
const runButton = document.querySelector(".run-pause");
const speedSlider = document.querySelector(".speed-slider");
const speedBox = document.querySelector(".speed-box");


////////////////////
// Set actions and control logic for elements with listeners

// listener for loading program from button
loadButton.addEventListener("click", function(){
    pywebview.api.get_program_then_load()
});
/* OLD 
loadButton.addEventListener("change", function(){
    infobox.insertAdjacentHTML('beforeend', this.files[0].name)
    //pywebview.api.load_program(loadButton.files[0])
});
*/

// add toggle function to runButton
runButton.addEventListener("click", function() {
    if (runButton.textContent === "Run") {
        runButton.textContent = "Pause";
        runButton.style.color = "red";
        setSpeed(speedSlider.value)                             // set internal cycle speed to slider value
        pywebview.api.run_loop()                                // call run_loop function in python
    } else if (runButton.textContent === "Pause") {
        runButton.textContent = "Run";
        runButton.style.color = "green";
        pywebview.api.pause_loop()                              // call pause_loop function in python
    };
});

//connect cycle-speed slider and speed box, and connect both to internal cycle speed function
speedSlider.addEventListener("input", function() {
    speedBox.value = this.value
    setSpeed(this.value)
});
speedBox.addEventListener("input", function() {
    speedSlider.value = this.value
    setSpeed(this.value)
});

////////////////////////////////////////
// starting script

// generate initial empty screen
document.querySelector(".screen").innerHTML = ('  '.repeat(64) + '<br>').repeat(32);