
/**
 * @param {Array} charRows should be an array of strings 
*/
function drawToScreen(charRows) {
    const screen = document.querySelector(".screen");
    let screenChars = '';
    for (const row of charRows) {screenChars += row + '<br>'};
    screen.innerHTML = screenChars;
};

/** generate initial empty screen chars */
function generateEmptyScreenChars() {
    const emptyChar = '  ';
    return Array(32).fill(emptyChar.repeat(64));
};

/** 
 * display emulator properties in infobar
 * @param {Object} propsObject should be an Object with key:value pairs of all the properties and values relating to the emulators current state
*/
function displayEmuState(propsObject) {
    let s = '';
    let c = 0;
    for (const [propName, value] of Object.entries(propsObject)) {
        c += 255/(Object.keys(propsObject).length);         // value of 'g' in 'rbg' color is increased evenly from 0 to 255 for each value in `propsObject`
        // add each `propsObject` key and value html to single line string (`s`), spacing them apart with whitespace, and adding color variation to values to make them easier to read
        s += `${propName}: <b style="color:rgb(255,${c},0)">${value}</b>` + ' '.repeat(5);
    };
    //append new html string `s` to infobox
    const infobox = document.querySelector(".info");
    infobox.insertAdjacentHTML('beforeend', s + '<br>')
};


// fill up screen with empty characters 
drawToScreen(generateEmptyScreenChars())





///////////////////////////////////////////////////////////////////////
// TESTING

/*
for (let i = 0; i < 15; i++) {
    appendToInfobar('yas'.repeat(100))
}
*/

const emuProps = {
    opcode: 'FXYN', 
    pc: 231,
    i: 14,
    st: 201,
    dt: 96
};

displayEmuState(emuProps);
