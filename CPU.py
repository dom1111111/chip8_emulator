# module imports
from time import sleep
import pygame
from pygame import mixer
from pygame.locals import *
from random import getrandbits
import keyboard

# the code needed for audio
mixer.init()
mixer.music.load("1son+1soff_tone.wav")
mixer.music.set_volume(0.7)


#################################################################

class Emulator():
    def __init__(self):

        # code to change the mode of the 8XY6 and 8XYE shift opcodes - https://tobiasvl.github.io/blog/write-a-chip-8-emulator/#8xy6-and-8xye-shift
        self.y_to_x = 1                 # `1` is just for this setting, but it could be anything

        # CHIP-8 components
        self.memory = []                 # 4096 memory locations, each one a byte (4kb total)
        self.pc = 512                    # program counter - points at the current instruction in memory
        self.i = 0b000000000000          # "The address register, which is named I, is 12 bits wide and is used with several opcodes that involve memory operations."
        self.stack = []                  # A stack for 16-bit addresses, which is used to call subroutines/functions and return from them
        self.delay_timer = 0             # An 8-bit (1 byte) delay timer which is decremented at a rate of 60 Hz (60 times per second) until it reaches 0
        self.sound_timer = 0             # An 8-bit (1 byte) sound timer which functions like the delay timer, but which also gives off a beeping sound as long as it’s not 0
        self.registers = []              # 16 8-bit (one byte) general-purpose variable registers numbered 0 through F hexadecimal, ie. 0 through 15 in decimal, called V0 through VF. # VF is a carry flag

        # code for creating locations in the data storage structures
        for x in range(0, 4096):
            self.memory.append(0)
        assert len(self.memory) == 4096  # "The assert keyword lets you test if a condition in your code returns True, if not, the program will raise an AssertionError." - https://www.w3schools.com/python/ref_keyword_assert.asp

        for x in range(0, 16):
            self.registers.append(0)
        assert len(self.registers) == 16

        load_rom(self)

#################################################################

# keypad functions
# https://tobiasvl.github.io/blog/write-a-chip-8-emulator/#keypad

key_map = {
    0x0: 'x',
    0x1: '1',
    0x2: '2',
    0x3: '3',
    0x4: 'q',
    0x5: 'w',
    0x6: 'e',
    0x7: 'a',
    0x8: 's',
    0x9: 'd',
    0xA: 'z',
    0xB: 'c',
    0xC: '4',
    0xD: 'r',
    0xE: 'f',
    0xF: 'v',
}

def real_check_key(key_index):
    assert key_index in range(0x0, 0xF + 1), "Key index must be a hex char in the range [0x0, 0xF]"
        # the `+ 1` becauase python's range() is *exclusive*
    key = key_map.get(key_index)
    return keyboard.is_pressed(key)             # "Returns True if the key is pressed" - https://github.com/boppreh/keyboard#keyboard.is_pressed

def get_hexkey_from_key(pressed_key):
    keys_list = list(key_map.keys())            # gets a list of the keys from the `key_map` dictionary
    values_list = list(key_map.values())        # gets a list of the values from the `key_map` dictionary
    if pressed_key in values_list:              # checks if pressed_key is in the values of the key_map dictionary
        index = values_list.index(pressed_key)  # get index of pressed_key in values_list
        related_hexkey = keys_list[index]       # return element with the same index of pressed_key from keys_list   
        return hex(related_hexkey)
    else:
        pass

#################################################################

# display functions

# creates the screen
scale = 10
screen_physical_width = 64 * scale
screen_physical_height = 32 * scale
screen = pygame.display.set_mode((screen_physical_width, screen_physical_height))

black = (255, 255, 255)
white = (0, 0, 0)

def draw_to_screen(x, y):
    pos = (x * scale, y * scale)
    width = 1 * scale
    height = 1 * scale
    current_pixel_colour = screen.get_at(pos)
    if current_pixel_colour == black:
        screen.fill(white, (pos, (width, height)))      # turn off
        return True
    elif current_pixel_colour == white:
        screen.fill(black, (pos, (width, height)))      # turn on
        return False
    else:
        print("oh my fucking god what is this shit")

def byte_to_bits(byte):
    print("BYYYYTTTEEEEETOBIIIITS: ", byte)
    bits = str(bin(byte))[2:]
    bits = bits.zfill(8)                # adds "padding" - https://thispointer.com/python-how-to-pad-strings-with-zero-space-or-some-other-character/
    bits = list(bits)
    return bits

##########

# The font
font = [
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

# storing the font sprite data in memory
"""
counter = 0
for sprite in font:
    Emulator().memory[0x050 + counter] = sprite
    counter += 1
"""

#################################################################

# load rom

def load_rom(emulator):
    rom = "test_opcode.ch8"

    with open(rom, "rb") as file:       # `rb` means *read* file as *bytes*
        #for index, byte in enumerate(file):
        #    memory[512+index] = byte
        offset = 0
        while True:
            chunk = file.read(1)
            if not chunk:
                break
            for byte in chunk:
                assert type(byte) == int
                emulator.memory[512 + offset] = byte
                offset += 1

#################################################################

def step(emulator, check_key):
    # code needed for display
    pygame.display.flip()
    sleep(0.016)

    # FETCH the instruction from memory at the current PC (program counter)
    fetch = (emulator.memory[emulator.pc] << 8) + emulator.memory[emulator.pc+1]            # https://python-reference.readthedocs.io/en/latest/docs/operators/bitwise_left_shift.html
        # "An instruction is two bytes, so you will need to read two successive bytes from memory and combine them into one 16-bit instruction."
        # `memory`` is a list, `pc`` is the index of said list > it is being bitshifted to the left 
        # and combined with the next slot in memory to form a complete opcode
    emulator.pc += 2
        # iterate the program counter by two (the next opcode in memory)
    
    # DECODE the instruction to find out what the emulator should do
        # "CHIP-8 instructions are divided into broad categories by the first “nibble”, or “half-byte”, 
        # which is the first hexadecimal number."
            # so the entire opcode is 16 bits (2 bytes), and it is devided into 4 "nibbles" (4 bits)
            # - each group of 4 bits represents an opcode category, or character - so each character is 4 bits (a nibble)
                # (in hexidecimal, the whole instruction 4 characters and each character represents a discrete peice of infomration in the opcode)
    opcodechar1 = (fetch & 0b1111000000000000) >> 12    # `&` - bitwise operator AND - "Sets each bit to 1 if both bits are 1" - https://www.w3schools.com/python/python_operators.asp
    opcodechar2 = (fetch & 0b0000111100000000) >> 8     # `0b` is binary literal - https://stackoverflow.com/questions/1476/how-do-you-express-binary-literals-in-python
    opcodechar3 = (fetch & 0b0000000011110000) >> 4
    opcodechar4 = (fetch & 0b0000000000001111)
    completeopcode = opcodechar1 + opcodechar2 + opcodechar3 + opcodechar4
    print("b", bin(completeopcode))
    
    # EXECUTE the instruction and do what it tells you
    # 00E0 - "Clears the screen"
    if opcodechar1 == 0x0 and opcodechar2 == 0x0 and opcodechar3 == 0xE and opcodechar4 == 0x0:
        screen.fill(white)      # set entire screen to white (blank) - clears screen
    # 00EE - SUBROUTINES - "Returns from a subroutine" - "does this by removing (“popping”) the last address from the stack and setting the PC to it."
    if opcodechar1 == 0x0 and opcodechar2 == 0x0 and opcodechar3 == 0xE and opcodechar4 == 0xE:
        address = emulator.stack.pop()
        emulator.pc = address
    # 0NNN - "Calls machine code routine at address NNN."
    if opcodechar1 == 0x0:              
        pass    # You can just skip this
    # 1NNN - JUMP - "Jumps to address NNN" - "set PC to NNN, causing the program to jump to that memory location"
    if opcodechar1 == 0x1:
        address = (opcodechar2 << 8) + (opcodechar3 << 4) + (opcodechar4)
        emulator.pc = address
    # 2NNN - SUBROUTINES - Calls subroutine at NNN - # https://tobiasvl.github.io/blog/write-a-chip-8-emulator/#00ee-and-2nnn-subroutines
    if opcodechar1 == 0x2:
        nn = (opcodechar2 << 8) + (opcodechar3 << 4) + (opcodechar4)
        emulator.stack.append(emulator.pc)
        emulator.pc = nn
    # 3XNN - SKIP - "Skips the next instruction if VX equals NN"
    if opcodechar1 == 0x3:
        nn = (opcodechar3 << 4) + (opcodechar4)
        if emulator.registers[opcodechar2] == nn:
            emulator.pc += 2
    # 4XNN - SKIP - "Skips the next instruction if VX does not equal NN"
    if opcodechar1 == 0x4:
        nn = (opcodechar3 << 4) + (opcodechar4)
        if emulator.registers[opcodechar2] != nn:
            emulator.pc += 2
    # 5XY0 - SKIP - "Skips the next instruction if VX equals VY"
    if opcodechar1 == 0x5:
        if emulator.registers[opcodechar2] == emulator.registers[opcodechar3]:
            emulator.pc += 2
    # 6XNN - SET - "Sets VX to NN" - "set the register VX to the value NN"
    if opcodechar1 == 0x6:
        nn = (opcodechar3 << 4) + opcodechar4
        emulator.registers[opcodechar2] = nn
    # 7XNN - ADD - "Add the value NN to VX"-"(Carry flag is not changed)"
    if opcodechar1 == 0x7:
        nn = (opcodechar3 << 4) + opcodechar4
        emulator.registers[opcodechar2] += nn
    # 8XY0 - SET - "Sets VX to the value of VY"
    if opcodechar1 == 0x8 and opcodechar4 == 0x0:
        emulator.registers[opcodechar2] = emulator.registers[opcodechar3]
    # 8XY1 - BINARY OR - "Sets VX to VX or VY"
    if opcodechar1 == 0x8 and opcodechar4 == 0x1:
        emulator.registers[opcodechar2] |= emulator.registers[opcodechar3]
    # 8XY2 - BINARY AND - "Sets VX to VX and VY"
    if opcodechar1 == 0x8 and opcodechar4 == 0x2:
        emulator.registers[opcodechar2] &= emulator.registers[opcodechar3]
    # 8XY3 - XOR - "Sets VX to VX xor VY"
    if opcodechar1 == 0x8 and opcodechar4 == 0x3:
        emulator.registers[opcodechar2] ^= emulator.registers[opcodechar3]
    # 8XY4 - ADD - "Adds VY to VX." - "If the result is larger than 255 (and thus overflows the 8-bit register VX), the flag register VF is set to 1. If it doesn’t overflow, VF is set to 0"
        # why is '255' the max? because each register is 8 bits, and the max value of an 8 bit binary number is 255 (in decimal)
    if opcodechar1 == 0x8 and opcodechar4 == 0x4:
        emulator.registers[opcodechar2] += emulator.registers[opcodechar3]
        # set the carry flag in emulator.registers (VF) to 1 if it overflows
        if emulator.registers[opcodechar2] > 255:
            emulator.registers[0xF] = 1
        else:
            emulator.registers[0xF] = 0
    # 8XY5 - SUBTRACT - "sets VX to the result of VX - VY" "If the first operand is larger than the second operand, VF will be set to 1" - otherwise, it will be set to 0 if the second is larger
    if opcodechar1 == 0x8 and opcodechar4 == 0x5:
        emulator.registers[opcodechar2] -= emulator.registers[opcodechar3]
        # set the carry flag in registers (VF)
        if emulator.registers[opcodechar2] > emulator.registers[opcodechar3]:
            vf = 1
            emulator.registers[0xF] = vf
        elif emulator.registers[opcodechar2] < emulator.registers[opcodechar3]:
            vf = 0
            emulator.registers[0xF] = vf
    # 8XY6 - SHIFT - "Stores the least significant bit of VX in VF and then shifts VX to the right by 1" - https://tobiasvl.github.io/blog/write-a-chip-8-emulator/#8xy6-and-8xye-shift
    if opcodechar1 == 0x8 and opcodechar4 == 0x6:
        if emulator.y_to_x == 1:                                                # this is configurable
            emulator.registers[opcodechar2] = emulator.registers[opcodechar3]   # set VX to the value of VY
        least_significant_bit_of_vx = emulator.registers[opcodechar2] & 0b0001  # getting the least significant bit of VX
        vf = least_significant_bit_of_vx                                        # set least significant bit of VX to VF
        emulator.registers[0xF] = vf
        emulator.registers[opcodechar2] >>= 1                                   # bitwise shift the value of VX to the right by 1
    # 8XY7 - SUBTRACT - "sets VX to the result of VY - VX"
    if opcodechar1 == 0x8 and opcodechar4 == 0x7:
        emulator.registers[opcodechar2] = emulator.registers[opcodechar3] - emulator.registers[opcodechar2]
        # set the carry flag in registers (VF)
        if emulator.registers[opcodechar3] > emulator.registers[opcodechar2]:
            vf = 1
            emulator.registers[0xF] = vf
        elif emulator.registers[opcodechar3] < emulator.registers[opcodechar2]:
            vf = 0
            emulator.registers[0xF] = vf
    # 8XYE - SHIFT - "Stores the most significant bit of VX in VF and then shifts VX to the left by 1" - https://tobiasvl.github.io/blog/write-a-chip-8-emulator/#8xy6-and-8xye-shift
    if opcodechar1 == 0x8 and opcodechar4 == 0xE:
        if emulator.y_to_x == 1:                                                # this is configurable
            emulator.registers[opcodechar2] = emulator.registers[opcodechar3]   # set VX to the value of VY
        most_significant_bit_of_vx = emulator.registers[opcodechar2] & 0b1000   # getting the most significant bit of VX
        vf = most_significant_bit_of_vx                                         # set least significant bit of VX to VF
        emulator.registers[0xF] = vf
        emulator.registers[opcodechar2] <<= 1                                   # bitwise shift the value of VX to the left by 1
    # 9XY0 - SKIP - "Skips the next instruction if VX does not equal VY"
    if opcodechar1 == 0x9:
        if emulator.registers[opcodechar2] != emulator.registers[opcodechar3]:
            emulator.pc += 2
    # ANNN - SET INDEX - "Sets I to the address NNN"
    if opcodechar1 == 0xA:
        address = (opcodechar2 << 8) + (opcodechar3 << 4) + (opcodechar4)
        emulator.i = address
    # BNNN - JUMP WITH OFFSET - "Jumps to the address NNN plus V0" - Make this configurable if needed! > https://tobiasvl.github.io/blog/write-a-chip-8-emulator/#bnnn-jump-with-offset
    if opcodechar1 == 0xB:
        address = (opcodechar2 << 8) + (opcodechar3 << 4) + (opcodechar4)
        emulator.pc = address + emulator.registers[0x0]
    # CXNN - RANDOM - "Sets VX to the result of a bitwise and operation on a random number (Typically: 0 to 255) and NN"
    if opcodechar1 == 0xC:
        nn = (opcodechar3 << 4) + opcodechar4
        emulator.registers[opcodechar2] = getrandbits(8) & nn
    # DXYN - DISPLAY - https://tobiasvl.github.io/blog/write-a-chip-8-emulator/#dxyn-display
    if opcodechar1 == 0xD:
        vx = emulator.registers[opcodechar2]                 # this is X in the opcode
        vy = emulator.registers[opcodechar3]                 # this is Y in the opcode
        screen_logical_width = 64
        screen_logical_height = 32
        x = vx % screen_logical_width
        y = vy % screen_logical_height
        emulator.registers[0xF] = 0                          # vf flag register - set to 0
        sprite_height = opcodechar4
        for row_offset in range(0, sprite_height):
            if y + row_offset >= screen_logical_height:
                break
            sprite_row = emulator.i + row_offset
            sprite_data = emulator.memory[sprite_row]
            bits = byte_to_bits(sprite_data)
            for column_offset, pixel in enumerate(bits):
                if x + column_offset >= screen_logical_width:
                    break
                if pixel == "1":
                    turned_off = draw_to_screen(x + column_offset, y + row_offset)
                    if turned_off:
                        emulator.registers[0xF] = 1          # vf flag register - set to 0

    # EX9E - SKIP IF KEY - skip one instruction if the key corresponding to the value in VX is pressed
    if opcodechar1 == 0xE and opcodechar3 == 0x9:
        vx = emulator.registers[opcodechar2]
        if check_key(hex(vx)):
            emulator.pc += 2
    # EXA1 - SKIP IF NOT KEY - skip one instruction if the key corresponding to the value in VX is NOT pressed"
    if opcodechar1 == 0xE and opcodechar3 == 0xA:
        vx = emulator.registers[opcodechar2]
        if not check_key(hex(vx)):
            emulator.pc += 2
    # FX07 - DELAY TIMER - "Sets VX to the value of the delay timer"
    if opcodechar1 == 0xF and opcodechar4 == 0x7:
        emulator.registers[opcodechar2] = emulator.delay_timer
    # FX0A - GET KEY - "A key press is awaited, and then stored in VX" - this blocks the program until a key is pressed
    if opcodechar1 == 0xF and opcodechar4 == 0xA:
        while True:
            keypress = keyboard.read_key()              # "Blocks until a keyboard event happens, then returns that event's name or, if missing, its scan code." - # https://github.com/boppreh/keyboard#keyboardread_keysuppressfalse
            kexkey = get_hexkey_from_key(keypress)      # pass keypress to the function to turn it into a hex number
            if kexkey:                                  # if the function returns a value (which will always be a hex)
                emulator.registers[opcodechar2] = kexkey
                break
            else:
                pass
    # FX15 - DELAY TIMER - "sets the delay timer to the value in VX"
    if opcodechar1 == 0xF and opcodechar3 == 0x1 and opcodechar4 == 0x5:
        emulator.delay_timer = emulator.registers[opcodechar2]
    # FX18 - SOUND TIMER - "sets the sound timer to the value in VX"
    if opcodechar1 == 0xF and opcodechar4 == 0x8:
        emulator.sound_timer = emulator.registers[opcodechar2]
    # FX1E - ADD TO INDEX - "Adds VX to I. VF is not affected"
        # https://en.wikipedia.org/wiki/CHIP-8#cite_note-18 - a rare case where this opcode should be modifed
    if opcodechar1 == 0xF and opcodechar4 == 0xE:
        vx = emulator.registers[opcodechar2]
        emulator.i += vx
    # FX29 - FONT - "Sets I to the location of the sprite for the character in VX"
    if opcodechar1 == 0xF and opcodechar4 == 0x9:
        vx = emulator.registers[opcodechar2]
        sprite_adress = (vx * 5) + 0x050    # `0x050 is where the font sprite data is located`
        emulator.i = sprite_adress
# BROKEN    # FX33 - BINARY CODED DECIMAL CONVERSION - "It takes the number in VX and converts it to three decimal digits, storing these digits in memory at the address in the index register I" - https://tobiasvl.github.io/blog/write-a-chip-8-emulator/#fx33-binary-coded-decimal-conversion
    if opcodechar1 == 0xF and opcodechar3 == 0x3:
        vx = emulator.registers[opcodechar2]
        emulator.memory[emulator.i] = int(vx / 100)
        emulator.memory[emulator.i + 1] = int((vx % 100) / 10)
        emulator.memory[emulator.i + 2] = vx % 10
# BROKEN    # FX55 - WRTIE TO MEMORY - Stores values from registers V0 to VX (including VX) to memory, starting at address I
        # **has alternate behavior for old roms** - https://tobiasvl.github.io/blog/write-a-chip-8-emulator/#fx55-and-fx65-store-and-load-memory
    if opcodechar1 == 0xF and opcodechar3 == 0x5:
        vx = emulator.registers[opcodechar2]
        counter = 0
        for x in range(vx + 1):
            emulator.memory[emulator.i + counter] = emulator.registers[counter]
            counter =+ 1
    # FX65 - READ FROM MEMORY - "Fills values to registers V0 to VX (including VX) from memory, starting at address I"
        # **has alternate behavior for old roms** - https://tobiasvl.github.io/blog/write-a-chip-8-emulator/#fx55-and-fx65-store-and-load-memory
    if opcodechar1 == 0xF and opcodechar3 == 0x6:
        vx = emulator.registers[opcodechar2]
        counter = 0
        for x in range(vx + 1):
            emulator.registers[counter] = emulator.memory[emulator.i + counter]
            counter =+ 1
    
    ########################
    
    # decremate sound timer
    emulator.sound_timer = max(0, emulator.sound_timer - 1) 

    # check sound_timer
    if emulator.sound_timer <= 0:
        mixer.music.stop()
    else:
        sleep(0.002)                                   # simulates the 700 cycles per second clock speed

    # make sure that the register value is within its proper minimum and maximum value
    for register_index in range(16):
        emulator.registers[register_index] = emulator.registers[register_index] & 0xFF  # make sure that register is within the correct range (8 bit binary number)
        assert emulator.registers[register_index] in range(0, 256), 'shits broke yo! (overflow)'

    ######################

    # testing
    print("pc: ", emulator.pc)
    print("hex pc: ", hex(emulator.pc))
    print("current opcode: ", emulator.memory[emulator.pc], emulator.memory[emulator.pc + 1])
    print("i: ", emulator.i)
    print("hex i", hex(emulator.i))
    print("registers: ", emulator.registers)
    print("hex registers", [hex(x) for x in emulator.registers])

# if not running in tests, actually start the game loop
if __name__ == "__main__":
    emulator = Emulator()
    # main loop
    while True:
        # event loop
        while True:
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                assert False, "fixme"
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    break
        step(emulator, real_check_key)
