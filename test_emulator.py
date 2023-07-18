import emulator
from time import sleep

if __name__ == "__main__":
    emu = emulator.Emulator()
    emu.start()                 # this is blocking
    #emu.load_program('./ch8_programs/test_opcode.ch8')
    #print('running!')
    #emu.run()
