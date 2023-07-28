"""
This uses a chip8 file called 'test_opcode.ch8' gotten from: https://github.com/corax89/chip8-test-rom.
This file should be in a folder called "ch8_programs", that is itself within this script's directory
"""
import emu_runner
from time import sleep
from threading import Thread
from os import path

if __name__ == "__main__":
    emu = emu_runner.EmulatorRunner()

    def run_opcode_test_prog():
        emu.wv_loaded.wait()            # wait for window to be loaded
        sleep(0.5)
        test_oc_path = path.join(path.dirname(__file__), path.join("ch8_programs", "test_opcode.ch8"))
        emu.load_program(test_oc_path)
        sleep(0.5)
        emu.set_emulation_speed(10)     # speed is set slow so it's easier to keep track of what's happening
        emu.run_loop()

    Thread(target=run_opcode_test_prog, daemon=True).start()
    emu.start()
