import emu_runner
from time import sleep

if __name__ == "__main__":
    emu = emu_runner.EmulatorRunner()
    emu.start()                 # this is blocking
