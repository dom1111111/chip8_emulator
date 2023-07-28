from time import sleep
from os import path
from threading import Event, Lock, Thread
import webview
from emu_core import EmulatorCore

# a list to hold the sprite data of 16 hex characters for the display
standard_font = [
    0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
    0x20, 0x60, 0x20, 0x20, 0x70, # 1
    0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
    0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
    0x90, 0x90, 0xF0, 0x10, 0x10, # 4
    0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
    0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
    0xF0, 0x10, 0x20, 0x40, 0x40, # 7
    0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
    0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
    0xF0, 0x90, 0xF0, 0x90, 0x90, # A
    0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
    0xF0, 0x80, 0x80, 0x80, 0xF0, # C
    0xE0, 0x90, 0x90, 0x90, 0xE0, # D
    0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
    0xF0, 0x80, 0xF0, 0x80, 0x80  # F
]

# the file path of the HTML front end
html_path = path.join(path.join(path.dirname(__file__), 'front_end'), 'index.html')


#################################################################
# Main class

class EmulatorRunner():
    """
    Runs the emulator core and the front end.

    Call `start()` to run emulator GUI. 
    From there, you can load programs/ROMS, adjust settings, and then actually run the emulation cycle loop
    """
    def __init__(self):
        self.window = webview.create_window('CHIP-8 Emulator', html_path)   # setup pywebview window, attaching HTML file
        self.emu = EmulatorCore(self.window)                                # Instantiate emulator core
        self.loop = Event()             # used to run/pause emulation loop
        self.wv_loaded = Event()        # used to keep track of whether or not the webview window is running
        self.lock = Lock()              # used to safely change settings across threads
        self._emu_speed = 500           # an int representing the Hz (cycles per second) that the emulator's main loop should run at

    #---------
    # Settings methods

    def load_font(self, font_data:list):
        """Load font sprite data into memory.
        Should be a list of 80 bytes numbers making up sprites representing hex values 0 - F 
        (5 numbers per sprite character, 16 hex characters). Sprites MUST be in order from 0 - F!
        """
        for n, byte in enumerate(font_data):                    # write each byte number of font into memory,
            self.emu.memory.write(self.emu.font_mem_adr, byte)  # starting at `font_mem_adr`
        print('font loaded into memory')

    def load_program(self, file_path:str):
        """load a CHIP-8 program file from provided path"""
        prog_start_mem_adr = 0x200                      # program start memory address - convention is to load programs starting at memory address 0x200 (512 in dec)
        with open(file_path, "rb") as program:          # open file as read-only bytes
            for i, byte in enumerate(program.read()):   # read entire file (returns a bytes object), enumerate to get index of each byte, 
                i = prog_start_mem_adr + i
                self.emu.memory.write(i, byte)          # and then write each byte to memory, with offset from the program start memory address
        self.emu.pc.set(prog_start_mem_adr)
        print('program loaded into memory')

    def get_program_then_load(self):
        path = self.window.create_file_dialog(webview.OPEN_DIALOG, file_types=('CHIP8 Files (*.ch8)', ))[0]
        if path:
            self.load_program(path)

    def set_emulation_speed(self, hz:int):
        """set the emulation speed in Hz (cycles per second)"""
        if not isinstance(hz, int):
            raise ValueError('hz arg must be int')
        with self.lock:
            self._emu_speed = hz
        print('emulation speed changed to', hz)

    #---------
    # Pywebview methods

    def _on_loaded(self):
        print('webview window is loaded')
        self.wv_loaded.set()

    def _on_closed(self):
        print('webview window is closed')
        self.wv_loaded.clear()

    #---------
    # Main run methods

    def _start_loop(self):
        print('emulator core ready')
        self.wv_loaded.wait()                   # wait until webview window is loaded
        # main loop:
        while True:
            self.loop.wait()                    # if loop event is not set, wait until it is. Otherwise this does nothing
            instruction = self.emu.cycle()      # execute one cycle
            emu_props = {                       # dictionary of emulator properties
                'pc':       self.emu.pc.get(),
                'opcode':   instruction,
                # stack
                # registers
                'i':        self.emu.i.get(),
                'dt':       self.emu.dt.get(),
                'st':       self.emu.st.get()
            }
            # display emulator properties in front end, by evaluting js of a functioncall to `displayEmuState`:
            self.window.evaluate_js(f"displayEmuState({emu_props})")
            with self.lock:                     # lock is needed so that emulation speed can be changed while running!
                sleep(1/self._emu_speed)
                # enforce emulation speed by pausing execution for aproximiately
                # the seconds spent for one cycle at `self.emu_speed` Hz

    def run_loop(self):
        """start emulation loop or resume if paused. If no CHIP-8 program/ROM has been loaded yet, this won't do much"""
        self.loop.set()
        print('emulation loop running')

    def pause_loop(self):
        """pause emulation loop"""
        self.loop.clear()
        print('emulation loop paused')

# INCOMPLETE
    def reset(self):
        """stop running and reset emulator"""
        pass
        # self.loop.clear()
        # self.memory.clear()
        print('emulator reset')
    
    def start(self):
        """Start up CHIP-8 emulator! Then call `run()` to start cycle loop. THIS IS BLOCKING"""
        self.load_font(standard_font)   # load font (can be called again, but initially just use `standard_font`)
        # register functions to load and close events to set/clear `is_running`
        self.window.events.loaded += self._on_loaded
        self.window.events.closed += self._on_closed
        # expose methods to JS domain so that they can be used by front-end js script
        self.window.expose(self.get_program_then_load, self.set_emulation_speed, self.run_loop, self.pause_loop, self.reset)
        # start main loop in new thread 
            # (this could be passed as first arg to `webview.start()` which would do the same thing, 
            # but it seems the thread is not daemon and program persists even after window is closed,
            # so manual thread creation is neccessary)
        Thread(target=self._start_loop, daemon=True).start()
        # start rendering the front end GUI in a webview. This function is blocking!
        webview.start(debug=False)      # set `debug` to True to show browser window console, etc. (F12)


#################################################################

if __name__ == "__main__":
    emu = EmulatorRunner()
    emu.start()     # this is blocking