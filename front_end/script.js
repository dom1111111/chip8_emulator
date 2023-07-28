////////////////////

// constants for elements
const screen = document.querySelector(".screen");
const infobox = document.querySelector(".info");
const loadButton = document.querySelector(".load-program");
const runButton = document.querySelector(".run-pause");
const speedSlider = document.querySelector(".speed-slider");
const speedBox = document.querySelector(".speed-box");


////////////////////
// Functions

//function which connects to internal python function to set speed
function setSpeed(val) {
    pywebview.api.set_emulation_speed(parseInt(val))    // value of Elemtents is str, must be converted to int with `parseInt`
}

/**
 * Draw to screen
 * @param {Array} charRows -- should be an array of arrays representing rows, and each of those rows should be filled with binary ints (0 or 1) 
 * - The number of "rows" should correspond to the intended *height* of the screen
 * - the number ints in the rows should correspond to the intended *width* of the screen
*/
function drawToScreen(charRows) {
    // there are 2 characters for each on/off_char string in order to widen the screen horizontally, 
    // so that width is more even with height (because characters cells are taller than they are wide))
    const on_char = "██"
    const off_char = "  "
    let screenChars = '';
    for (const row of charRows) {
        for (const charState of row) {
            if (charState === 1) {
                screenChars += on_char;
            } else if (charState === 0) {
                screenChars += off_char;
            };
        };
        screenChars += '<br>';
    };
    screen.innerHTML = screenChars;
};

/** 
 * Display emulator properties in infobar
 * @param {Object} props - should be an Object with key:value pairs of all the properties and values relating to the emulators current state
*/
function displayEmuState(props) {
    let s = '';
    let c = 0;
    for (const [propName, value] of Object.entries(props)) {
        c += 255/(Object.keys(props).length);           // value of 'g' in 'rbg' color is increased evenly from 0 to 255 for each value in `props`
        // add each `props` key and value html to single line string (`s`), spacing them apart with whitespace, and adding color variation to values to make them easier to read
        s += `${propName}: <b style="color:rgb(255,${c},0)">${value}</b>` + ' '.repeat(5);
    };
    //append new html string `s` to infobox
    infobox.insertAdjacentHTML('beforeend', s + '<br>');
    infobox.scroll(0, infobox.scrollHeight);            // scroll to bottom
};


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
screen.innerHTML = ('  '.repeat(64) + '<br>').repeat(32);