import webview
from os import path
from threading import Event

#################################################################
# python methods to be accessed by JS

class JS_API:
    def do_thing():
        print('suh')

#################################################################
# Pywebview setup

is_loaded = Event()                    # used to keep track of whether or not the webview window is running

html_path = path.join(path.dirname(__file__), 'index.html')

# setup pywebview window, attaching HTML file and JS_API class
window = webview.create_window('CHIP-8 Emulator', html_path, js_api=JS_API)

def on_loaded():
    print('webview window is loaded')
    is_loaded.set()

def on_closed():
    print('webview window is closed')
    is_loaded.clear()

# register functions to load and close to set/clear `is_running` event
window.events.loaded += on_loaded
window.events.closed += on_closed

def start_webview():
    """start rendering the front end GUI in a webview. This function is blocking!
    MUST BE CALLED BEFORE ANY OTHER FUNCTIONS"""
    webview.start()

#################################################################
# JS and general functions to be accessed by python

def draw_to_screen(charRows:list):
    """`charRows` should be a list of strings representing each row of the text-character-based screen"""
    window.evaluate_js(fr"""
        const screen = document.querySelector(".screen");
        let screenChars = '';
        for (const row of {charRows}) {{screenChars += row + '<br>'}};
        screen.innerHTML = screenChars;
    """)    #double curly braces is needed to excape curly braces

def display_emu_state(props:dict):
    """`props` should be a dictionary with all the properties and values relating to the emulators current state"""
    window.evaluate_js(fr"""
        let s = '';
        let c = 0;
        for (const [propName, value] of Object.entries({props})) {{
            c += 255/(Object.keys(propsObject).length);         // value of 'g' in 'rbg' color is increased evenly from 0 to 255 for each value in `propsObject`
            // add each `propsObject` key and value html to single line string (`s`), spacing them apart with whitespace, and adding color variation to values to make them easier to read
            s += `${{propName}}: <b style="color:rgb(255,${{c}},0)">${{value}}</b>` + ' '.repeat(5);
        }};
        //append new html string `s` to infobox
        const infobox = document.querySelector(".info");
        infobox.insertAdjacentHTML('beforeend', s + '<br>')
    """)
