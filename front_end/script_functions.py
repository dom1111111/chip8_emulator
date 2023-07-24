"""JS and general functions to be accessed by python"""
from webview.window import Window

def draw_to_screen(window:Window, char_rows:list):
    """`charRows` should be a list of strings representing each row of the text-character-based screen"""
    window.evaluate_js(fr"""
        let charRows = {char_rows}
        let screenChars = '';
        for (const row of charRows) {{screenChars += row + '<br>'}};
        screen.innerHTML = screenChars;
    """)    #double curly braces is needed to excape curly braces

def display_emu_state(window:Window, props:dict):
    """`props` should be a dictionary with all the properties and values relating to the emulators current state"""
    js_str = fr"""
        let props = {props}
        let s = '';
        let c = 0;
        for (const [propName, value] of Object.entries(props)) {{
            c += 255/(Object.keys(props).length);         // value of 'g' in 'rbg' color is increased evenly from 0 to 255 for each value in `props`
            // add each `props` key and value html to single line string (`s`), spacing them apart with whitespace, and adding color variation to values to make them easier to read
            s += `${{propName}}: <b style="color:rgb(255,${{c}},0)">${{value}}</b>` + ' '.repeat(5);
        }};
        //append new html string `s` to infobox
        infobox.insertAdjacentHTML('beforeend', s + '<br>')
    """
    window.evaluate_js(js_str)
