import emu_runner
from time import sleep

if __name__ == "__main__":
    emu = emu_runner.EmulatorRunner()
    emu.start()                 # this is blocking
    #emu.load_font()
    #emu.load_program('./ch8_programs/test_opcode.ch8')
    #print('running!')
    #emu.run()
