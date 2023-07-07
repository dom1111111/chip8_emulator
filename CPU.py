from time import sleep
import os
from threading import Thread, Lock, Event
from random import getrandbits
#import PyAudio
import keyboard

#################################################################
# Classes to make CHIP-8 components

class FixedBit:
    """Parent class to inherit from for making classes surrounding integers whose values must always be postive, 
    and no greater than the max possible value of a binary number with `bit_size` bits"""
    def __init__(self, bit_size:int):
        self._bit_size = bit_size

    def _ensure_bit_limit(self, value:int):
        """make sure that val is between 0 and max value of bit size"""
        if not isinstance(value, int) or not isinstance(self._bit_size, int):
            raise TypeError('value and bit  must be an int')
        elif not value >= 0:
            raise ValueError('value must be positive (above 0)')
        elif not value <= (2 ** self._bit_size - 1):
            raise ValueError(f'value must be no higher than max value of a {self._bit_size}-bit number')


class FixedBitInt(FixedBit):
    """Create a positive integer which can have a value bteween 0 to n, 
    where n is the max possible value of a binary number with `bit_size` bits"""
    def __init__(self, bit_size:int):
        super().__init__(bit_size)
        self._val = 0

    def get(self) -> int:
        """get value"""
        return self._val

    def set(self, value:int):
        """set value"""
        self._ensure_bit_limit(value)
        self._val = value

    def add(self, n:int):
        """add `n` to value (can be negative for subtraction)"""
        self._val += n


class FixedBitArray(FixedBit):
    """Create an array, where each item is an int with max bit size, and fixed length (number of items)"""
    def __init__(self, bit_size:int, length:int):
        super().__init__(bit_size)
        self._mem = [0] * length
    
    def write(self, index:int, value:int):
        """Set value at array index to `value`. Value must be no more than `bit_size`"""
        self._ensure_bit_limit(value)
        self._mem[index] = value

    def read(self, index:int) -> int:
        """Get value at array index"""
        return self._mem[index]

    def clear(self):
        """resets all array slots to 0"""
        self._mem = [0] * len(self._mem)


class FixedBitStack(FixedBit):
    """Create a stack, where each item is an int with max bit size, and max length (number of items)"""
    def __init__(self, bit_size:int, length:int):
        super().__init__(bit_size)
        self._stack = []
        self._len = length

    def push(self, value:int):
        """add value to top of of the stack"""
        self._ensure_bit_limit(value)
        if len(self._stack) >= self._len:
            raise OverflowError
        self._stack.append(value)

    def pop(self) -> int:
        """remove value from top of the stack and return the value"""
        return self._stack.pop()
    
    def peek(self) -> int:
        """return value from top of the stack (but don't remove it)"""
        return self._stack[-1]


class FixedBitCountDown(FixedBitInt):
    """Works just like FixedBitInt, but decrements value by 1 at `rate` Hz while above 0"""
    def __init__(self, bit_size:int, rate:int):
        super().__init__(bit_size)
        self.rate = rate                # rate in Hz that value should be decremented
        self.lock = Lock()              # used to safely access `_val` between threads
        self.flag = Event()             # used to make the _main_loop thread wait until `_val` is above 0
        Thread(target=self._main_loop, daemon=True).start()     # call _main_loop in new thread

    def _main_loop(self):
        while True:
            if self._val > 0:
                with self.lock:
                    self._val -= 1
                sleep(1/self.rate)      # wait time needed in order to run at `self.rate` Hz
            else:
                self.flag.clear()       # if value is not above 0, clear the flag
                self.flag.wait()        # and wait until it's above 0 (flag will be set in `self.set()` if value is above 0)

    def get(self) -> int:
        """get value"""
        with self.lock:
            return self._val

    def set(self, value:int):
        """set value"""
        self._ensure_bit_limit(value)
        with self.lock:
            self._val = value
        if value > 0:
            self.flag.set()             # set flag if value above 0


class PlayTone():
    """used to generate and play a constant tone at `pitch` hz"""
    def __init__(self, pitch:int):
        self.tone_on = Event()
        self.pitch = pitch
    
    def start(self):
        pass

    def stop(self):
        pass

    def is_playing(self):
        pass


class NoisyCountDown(FixedBitCountDown):
    """Works just like FixedBitCountDown, but will play a tone as long as the set value is above 0"""
    def __init__(self, bit_size:int, rate:int):
        super().__init__(bit_size, rate)
        self.tone = PlayTone()
    
    def _main_loop(self):
        while True:
            if self._val > 0:
                if not self.tone.is_playing():
                    self.tone.start()   # if value is above 1, and the tone is not already playing, then start playing it
                with self.lock:
                    self._val -= 1
                sleep(1/self.rate)      # wait time needed in order to run at `self.rate` Hz
            else:
                self.flag.clear()       # if value is not above 0, clear the flag
                self.tone.stop()        # and stop playing the tone
                self.flag.wait()        # and wait until it's above 0 (flag will be set in `self.set()` if value is above 0)


class HexKeyPad:
    def __init__(self):
        self._key_map = {                # this is arranged in the same way the keypad would be
            0x1: '1', 0x2: '2', 0x3: '3', 0xC: '4', 
            0x4: 'q', 0x5: 'w', 0x6: 'e', 0xD: 'r',
            0x7: 'a', 0x8: 's', 0x9: 'd', 0xE: 'f',
            0xA: 'z', 0x0: 'x', 0xB: 'c', 0xF: 'v',
        }
        self._reversed_key_map = {value:key for key, value in self.key_map.items()}
    
    def is_key_pressed(self, key:int) -> bool:
        """Return True if key is pressed, otherwise False."""
        if not key in range(16):
            raise ValueError("`key` argument must be a hex number from 0 - F (0 - 15 in decimal)")
        return keyboard.is_pressed(self._key_map.get(key))  # "Returns True if the key is pressed" - https://github.com/boppreh/keyboard#keyboard.is_pressed

    def wait_for_keypress(self) -> int:
        """Block program until any of the keypad keys are pressed, and then return which key it was (hex value)"""
        while True:
            keypress = keyboard.read_key()                  # "Blocks until a keyboard event happens, then returns that event's name or, if missing, its scan code." - # https://github.com/boppreh/keyboard#keyboardread_keysuppressfalse
            if keypress in self._reversed_key_map:
                return self._reversed_key_map.get(keypress)


class TerminalDisplay:
    """
    Create a simple 'text-mode' screen within the terminal window, made up solely of characters to act as pixels.

    Instantiate with with int args for screen width and height.

    Methods:
    * call `get_char()` to get the state (on or off) of a character at an x,y coordinate in the screen data
    * call `set_char()` to set the state of a character at an x,y coordinate in the screen data
    * call `clear_screen()` to reset screen data to completely blank state
    * call `draw_screen` to actually draw the screen in the terminal

    So in order to see any changes done in calls to `set_char()` or `clear_screen()`
    on the terminal window, a subsequent call to `draw_screen` must be made.

    For get/set_char methods, coordinates start at '0,0' at the top left corner.
    They range from `0` to `width/height - 1` (so a dimension of `10`, has a coordinate value range from `0` to `9`).
    """
    def __init__(self, width:int=64, height:int=32):
        self.width = width              # screen width
        self.height = height            # screen height
        # there are 2 characters for each on/off_char string in order to widen the screen horizontally, so that width is more even with height (because characters cells are taller than they are wide))
        self.on_char = '()'             # characters representing on-state
        self.off_char = '  '            # character representing off-state
        self.reset_screen()             # generate blank screen matrix data
        self.clear_on_draw = False      # if True, the terminal window will be cleared on every call to `draw_screen`

    def reset_screen(self):
        """Resets the screen so that all characters are in off state"""
        # The 'text mode' screen is made up solely of text characters, rather than pixels.
        # All the characters are stored in a list of lists with strings of characters in them. 
        # The length of the sub-lists is determined by width, and the number of strings in the list is determined by height.
        self._screen_matrix = [([self.off_char] * self.width) for row in range(self.height)]      # generate a list of lists of strings to represent screen matrix  

    def _enforce_xy_limit(self, x:int, y:int):
        """ensure that coordinate is within the screen width and height"""
        if x not in range(self.width) or y not in range(self.height):
            raise ValueError('x and y values must be within width and height')

    def get_char(self, x:int, y:int) -> bool:
        """Get state of character cell at x,y coordinate on screen matrix. `True` means on, `False` means off."""
        self._enforce_xy_limit(x, y)
        return True if self._screen_matrix[y][x] == self.on_char else False

    def set_char(self, x:int, y:int, state:bool):
        """Set state of character cell at x,y coordinate on screen matrix. State `True` means on, `False` means off."""
        self._enforce_xy_limit(x, y)
        self._screen_matrix[y][x] = self.on_char if state else self.off_char

    def draw_screen(self):
        """Draw screen by printing each string row in screen_matrix to terminal"""
        if self.clear_on_draw:                                          # first clear terminal screen (if self.clear_on_draw is True)
            os.system('cls' if os.name == 'nt' else 'clear')            # (should work across OS -> 'nt' means windows)
        # '--' and '|' characters are added to print a border around the screen
        x_border = '|-' + ('--' * self.width) + '-|'
        print(x_border)
        for row in self._screen_matrix:
            print('| ', end='')
            for char in row:
                print(char, end='')
            print(' |')
        print(x_border)


#################################################################
# CHIP-8 Emulator class

class Emulator():
    """CHIP-8 Emulator. ... """

    def __init__(self):
        # CHIP-8 components
        ## memory
        self.memory = FixedBitArray(8, 4096)    # 4KB (4,096 bytes) of RAM, where each cell is 1 byte
        ## stack
        self.stack = FixedBitStack(16, 16)      # LIFO array of 16 x 16-bit values - stores the address to return to after finishing a subroutine
        ## registers
        self.v_registers = FixedBitArray(8, 16) # 16 x 8-bit general purpose registers, labeled V0-Vf (1-16 in hexidecimal). Vf is a carry flag, and should not be used by the programs directly
        self.pc = FixedBitInt(16)               # 16-bit program counter - points to the memory address of the current instruction
        self.i = FixedBitInt(16)                # 16-bit index register - stores memory addresses
        ### timers
        self.dt = FixedBitCountDown(8, 60)      # 8-bit delay timer - automatically decremented at a rate of 60 Hz (60 times per second) until it reaches 0
        self.st = NoisyCountDown(8, 60)         # 8-bit sound timer - functions like the delay timer, but which also gives off a beeping sound as long as it’s not 0
        ## keypad
        self.keypad = HexKeyPad()               # 16-key hexadecimal keypad
        ## display
        self.display = TerminalDisplay(64, 32)  # 64x32-pixel monochrome display

        self.emu_speed = 500                    # an int representing the Hz (cycles per second) that the emulator's main loop should run at
        
        # if set to True, then sprites which start within screen dimensions, but then *partially* go outside of them, 
        # will have this outside parts wrap around to the other side of the screen. If False, then they will be clipped
        self.screen_partial_wrap = False

        self.font_mem_adr = 0x050               # starting address of where the font should be loaded into memory
        self.standard_font = [                  # a list to hold the sprite data of 16 hex characters for the display
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

    #---------
    # Instruction cycle methods

    def _fetch(self) -> int:
        """Fetch the instruction from memory at the current program counter (pc) value"""
        byte1 = self.memory.read(self.pc.get())
        byte2 = self.memory.read(self.pc.get()+1)
        instruction = (byte1 << 8) + byte2
            # each instruction is 2 bytes long and stored with the most-significant-byte first (big-endian),
            # so read 2 bytes and combine them together (using bitwise shift)
        self.pc.add(2)          # iterate the program counter by two, to point to the next opcode in memory
        return instruction

    def _decode(self, instruction:int):
        """Decode the instruction into seperate "nibbles" (4-bit groups)"""
        # each instruction is devided into 4 nibbles
        oc1 = (instruction & 0b1111000000000000) >> 12   
        oc2 = (instruction & 0b0000111100000000) >> 8
        oc3 = (instruction & 0b0000000011110000) >> 4
        oc4 = (instruction & 0b0000000000001111)
        # ^ bitwise shift and bitwise operator AND to get each nibble
        return oc1, oc2, oc3, oc4

    def _execute(self, oc1:int, oc2:int, oc3:int, oc4:int):
        """Execute the instruction (opcode) based on the value of its nibbles"""
        
        # All of the following instructions have a 4 character name. 
        # Each of the characters coresponds to each nibble of the instruction (oc1 - oc4)
            # so for example: `5XY0` means that: `oc1` represents `5`, `oc2` - `X`, `0c3` - `Y`, `oc4` - `0`

        # set up opcode variables
        # Each instruction can have one of the formats: `CXYN`, `CXNN` or `CNNN`
        c = oc1                 # C - the first nibble always represents the broad instruction group
        vx = oc2                 # X - used to look up one of the 16 register values v0 - vF (self.v_registers)
        vy = oc3                 # Y - like X, also used to refference one of the 16 registers
        n = oc4                 # N - a 4-bit number
        nn = (oc3 << 4) + n     # NN - an 8-bit number
        nnn = (oc2 << 8) + nn   # NNN - a 12-bit value - always refers to a memory address


        ##########################################################
        #################### ALL INSTRUCTIONS ####################
        ##########################################################

        # ----- 0x0 group -----
        if c == 0x0:
        
        ########## 0NNN ########## - run machine code routine at address NNN
            # this instruction is skipped
            # was only used on old computers running original CHIP-8 interpreters

        ########## 00E0 ########## - Clear the screen
            if n == 0x0:
                # reset the screen to be blank
                self.display.reset_screen()

        ########## 00EE ########## - Return from a subroutine
            elif n == 0xE:
                # pop value from top of the stack, and set PC to value
                self.pc.set(self.stack.pop())
        
        ########## 1NNN ########## - Jump to address NNN
        elif c == 0x1:
            # set pc value to nnn
            self.pc.set(nnn)

        ########## 2NNN ########## - Call subroutine at address NNN
        elif c == 0x2:
            # push value of pc on to the stack
            self.stack.push(self.pc.get())
            # set pc value to nnn
            self.pc.set(nnn)

        ########## 3XNN ########## - Skip the next instruction if Vx equals NN
        elif c == 0x3:
            # if value of register Vx, is equal to nn
            if self.v_registers.read(vx) == nn:
                # increment pc by 2 (to next instruction address, which will then be skipped)
                self.pc.add(2)

        ########## 4XNN ########## - Skip the next instruction if Vx does not equal NN
        elif c == 0x4:
            # if value of register Vx, is not equal to nn
            if self.v_registers.read(vx) != nn:
                # increment pc by 2 (to next instruction address, which will then be skipped)
                self.pc.add(2)

        ########## 5XY0 ########## - Skip the next instruction if Vx equals Vy
        elif c == 0x5:
            # if value of register Vx, is equal to register Vy
            if self.v_registers.read(vx) == self.v_registers.read(vy):
                # increment pc by 2 (to next instruction address, which will then be skipped)
                self.pc.add(2)

        ########## 6XNN ########## - Set Vx to NN
        elif c == 0x6:
            # set value of register Vx to nn
            self.v_registers.write(vx, nn)

        ########## 7XNN ########## - Add NN to Vx
        elif c == 0x7:
            # set value of register Vx to nn + Vx
            self.v_registers.write(vx, (self.v_registers.read(vx) + nn))

        # ----- 0x8 group -----
        elif c == 0x8:
        
        ########## 8XY0 ########## - Set Vx to Vy
            if n == 0x0:
                # set value of register Vx, to value of register Vy
                self.v_registers.write(vx, self.v_registers.read(vy))

        ########## 8XY1 ########## - Set Vx to bitwise OR of Vx and Vy
            elif n == 0x1:
                # set value of register Vx, to result of bitwise OR operation on values of registers Vx and Vy
                self.v_registers.write(vx, (self.v_registers.read(vx) | self.v_registers.read(vx)))

        ########## 8XY2 ########## - Set Vx to bitwise AND of Vx and Vy
            elif n == 0x2:
                # set value of register Vx, to result of bitwise AND operation on values of registers Vx and Vy
                self.v_registers.write(vx, (self.v_registers.read(vx) & self.v_registers.read(vx)))

        ########## 8XY3 ########## - Set Vx to bitwise XOR of Vx and Vy
            elif n == 0x3:
                # set value of register Vx, to result of bitwise exclusive-OR operation on values of registers Vx and Vy
                self.v_registers.write(vx, (self.v_registers.read(vx) ^ self.v_registers.read(vx)))

        ########## 8XY4 ########## - Add Vy to Vx. Set Vf to carry
            elif n == 0x4:
                result = (self.v_registers.read(vx) + self.v_registers.read(vy))
                # set value of register Vx, to Vx + Vy
                self.v_registers.write(vx, result)
                # if the result is greater than the max value of a byte (i.e. there's overflow)
                if result > 0xff:
                    # then set vF to 1
                    self.v_registers.write(0xf, 1)
                else:
                    # otherwise, set Vf to 0
                    self.v_registers.write(0xf, 0)

        ########## 8XY5 ########## - Subtract Vy from Vx. Set Vf to NOT borrow
            elif n == 0x5:
                # set value of register Vx, to Vx - Vy
                self.v_registers.write(vx, (self.v_registers.read(vx) - self.v_registers.read(vy)))
                # if the Vx is greater than Vy
                if self.v_registers.read(vx) > self.v_registers.read(vy):
                    # then set vF to 1
                    self.v_registers.write(0xf, 1)
                else:
                    # otherwise, set Vf to 0
                    self.v_registers.write(0xf, 0)

        ########## 8XY6 ########## - Set Vf to least significant bit of Vx. Shift Vx 1 bit to the right
            elif n == 0x6:
                # OPTIONAL -> set Vx to value of Vy (or shift Vy and put result in Vx?) (this was done in the original CHIP 8 interpreter - modern one's just ignore the Y)
                # set value of register Vf to least significant bit of Vx. (can be determined by Vx modulo 2 -> a number with 0 as LSB and will devide evenly (% 2 = 0), but 1 as LSB will not (% 2 = 1)
                self.v_registers.write(0xf, (self.v_registers.read(vx) % 2))
                # then set value of Vx, to Vx shifted 1 bit to the right (same as deviding by 2)
                self.v_registers.write(vx, (self.v_registers.read(vx) >> 1))
                

        ########## 8XY7 ########## - Subtract Vx from Vy. Set Vf to NOT borrow
            elif n == 0x7:
                # set value of register Vx, to Vy - Vx
                self.v_registers.write(vx, (self.v_registers.read(vy) - self.v_registers.read(vx)))
                # if the Vy is greater than Vx
                if self.v_registers.read(vy) > self.v_registers.read(vx):
                    # then set vF to 1
                    self.v_registers.write(0xf, 1)
                else:
                    # otherwise, set Vf to 0
                    self.v_registers.write(0xf, 0)

        ########## 8XYE ########## - Set Vf to most significant bit of Vx. Shift Vx 1 bit to the left
            elif n == 0xE:
                # OPTIONAL -> set Vx to value of Vy (or shift Vy and put result in Vx?) (this was done in the original CHIP 8 interpreter - modern one's just ignore the Y)
                # set value of register Vf to most significant bit of Vx. (can be determined shifting 3 bits to right)
                self.v_registers.write(0xf, (self.v_registers.read(vx) >> 3))
                # then set value of Vx, to Vx shifted 1 bit to the left (same as multiplying by 2)
                self.v_registers.write(vx, (self.v_registers.read(vx) << 1))

        ########## 9XY0 ########## - Skip the next instruction if Vx does not equal Vy
        elif c == 0x9:
            # if value of register Vx, is not equal to register Vy
            if self.v_registers.read(vx) != self.v_registers.read(vy):
                # increment pc by 2 (to next instruction address, which will then be skipped)
                self.pc.add(2)

        ########## ANNN ########## - Set I to the address NNN
        elif c == 0xA:
            # set value of i to nnn
            self.i.set(nnn)

        ########## BNNN ########## - Jump to location NNN + V0
        elif c == 0xB:
            # set pc value to nnn + register V0
            self.pc.set(nnn + self.v_registers.read(0x0))

        ########## CXNN ########## - Set Vx to bitwise AND of a random byte value and NN
        elif c == 0xC:
            # set value of register Vx, to result of bitwise AND operation on a random number from 0-255 and nn
            self.v_registers.write(vx, (getrandbits(8) & nn))

        ########## DXYN ########## - Display N-byte sprite starting at memory location I, at coordinates (Vx, Vy). Set VF = collision
        elif c == 0xD:
            # if initial coordinate value (so not including offset) is past the dimensions of the screen, then 'wrap' it back around (done with modulo)
            # this will always happen, and has nothing to do with the setting related to `self.screen_partial_wrap`

            # if any "collision" happens (a previously 'on' screen cell becomes 'off), then Vf will be set to 1
            # but if this doesn't happen, then Vf should be 0. so that's done now and only changed in following code if the collision happens
            self.v_registers.write(0xF, 0)                              # set register Vf (flag) to 0
            
            for y_offset in range(n):                                   # n represents the 'height' (number of bytes/rows) of the sprite
                # get y-coordinate from register Vy mod display height + y_offset
                y_c = (self.v_registers.read(vy) % self.display.height) + y_offset
                if y_c >= self.display.height:                          # if the y-coordinate is past the screen height:                     
                    if self.screen_partial_wrap:                        # and `screen_partial_wrap` is True,
                        y_c = y_c % self.display.height                 # then set y-coordinate to wrap the sprite back over the top (again with modulo)
                    else:
                        break                                           # otherwise, clip the sprite (stop drawing to screen)
                # read sprite byte from memory adress i + y_offset (current loop cycle number out of n loops)
                sprite_row = self.memory.read(self.i.get() + y_offset)  
                # convert byte number its 8-bit visual representation
                sprite_row = str(bin(sprite_row))[2:].zfill(8)          # (convert to string of binary number with `str(bin(sprite_row))`, get rid of '0b' with `[2:]`, and fill in leading zeros as needed with `zfill(8)`)  

                for x_offset, bit in enumerate(sprite_row):
                    # get x-coordinate from register Vx mod display width + x_offset
                    x_c = (self.v_registers.read(vx) % self.display.width) + x_offset
                    if x_c >= self.display.height:                      # if the x-coordinate is past the screen width:                     
                        if self.screen_partial_wrap:                    # and `screen_partial_wrap` is True,
                            y_c = y_c % self.display.height             # then set x-coordinate to wrap the sprite back over to the left side (again with modulo)
                        else:
# MAKE THIS EXIT OUT OF BOTH LOOPS
                            break                                       # otherwise, clip the sprite (stop drawing to screen)

                    # now draw bit to screen at coordinates - with XOR:
                    if bit == '1':                                      # if bit is 1, # (if bit is 0, then don't need to change anything)
                        if not self.display.get_char(x_c, y_c):         # and cell at coordinate is off,
                            self.display.set_char(x_c, y_c, True)       # then set cell to on (True)
                        else:
                            self.display.set_char(x_c, y_c, False)      # otherwise if both are on/1 (a collision), then set cell to off (False)
                            self.v_registers.write(0xF, 1)              # and also set register Vf (flag) to 1

            self.display.draw_screen()      # finally, actually update the screen with the changes made

        # ----- 0xE group -----
        elif c == 0xE:

        ########## EX9E ########## - Skip the next instruction if key with the value of Vx is pressed
            if n == 0xE:
                # if the key with the value of register Vx is pressed,
                if self.keypad.is_key_pressed(self.v_registers.read(vx)):
                    # increment pc by 2 (to next instruction address, which will then be skipped)
                    self.pc.add(2)

        ########## EXA1 ########## - Skip the next instruction if key with the value of Vx is not pressed
            elif n == 0x1:
                # if the key with the value of register Vx is NOT pressed,
                if not self.keypad.is_key_pressed(self.v_registers.read(vx)):
                    # increment pc by 2 (to next instruction address, which will then be skipped)
                    self.pc.add(2)

        # ----- 0xF group -----
        if c == 0xF:

        ########## FX07 ########## - Set Vx to DT
            if n == 0x7:
                # set value of register Vx to value of delay timer
                self.v_registers.write(vx, self.dt.get())

        ########## FX0A ########## - Wait for a key press, set Vx to value of key.
            elif n == 0xA:
                # wait for a key to be pressed on keypad, and then set value of register Vx to hex value of the key that was pressed
                self.v_registers.write(vx, self.keypad.wait_for_keypress())

        ########## FX15 ########## - Set DT to Vx
            elif oc3 == 0x1 and n == 0x5:
                # set value of delay timer to value of register Vx
                self.dt.set(self.v_registers.read(vx))

        ########## FX18 ########## - Set ST to Vx
            elif n == 0x8:
                # set value of sound timer to value of register Vx
                self.st.set(self.v_registers.read(vx))

        ########## FX1E ########## - Add Vx to I
            elif n == 0xE:
                # NOTE: https://en.wikipedia.org/wiki/CHIP-8#cite_note-18 - only case where this instruction affects Vf
                # set value of index register, to value of register Vx + index register
                self.i.add(self.v_registers.read(vx))

        ########## FX29 ########## - Set I to location of sprite for character in Vx
            elif n == 0x9:
                # set value of i to location of font character sprite representing Vx
                self.i.set(self.font_mem_adr + (vx * 5))
                # location is determined by multiplying Vx value by 5 (because each sprite is 5 bytes long),
                # and then offsetting the result from the font's starting address (self.font_mem_adr)

        ########## FX33 ########## - Write 'binary coded decimal' representation of Vx in memory locations I, I+1, and I+2
            elif n == 0x3:
                # using the decimal value of register Vx (which is a byte (so any value from 0-255)):
                # set memory address of i, to the hundreds digit
                self.memory.write(self.i.get(), int(self.v_registers.read(vx) / 100))            # devide Vx by 100 and round down to get hundreds digit 
                # set memory address of i+1, to the tens digit
                self.memory.write(self.i.get() + 1, int((self.v_registers.read(vx) % 100) / 10)) # do Vx modulo 100 and devide by 10 to get tens digit
                # set memory address of i+2, to the ones digit
                self.memory.write(self.i.get() + 2, self.v_registers.read(vx) % 10)              # do Vx modulo 10 to get ones digit

        ########## FX55 ########## - Write values of registers V0 - Vx, into memory starting at location I
            elif oc3 == 0x5 and n == 0x5:
                for n in range(vx + 1):      # `+ 1` is needed because python's range() function is *exclusive*, and Vx itself must be included as well
                    # for each loop, write value of register Vn, into memory address i+n
                    self.memory.write(self.i.get() + n, self.v_registers.read(n))

        ########## FX65 ########## - Set registers V0 to Vx, with the values in memory starting at address I
            elif oc3 == 0x6 and n == 0x7:
                for n in range(vx + 1):
                    # for each loop, write value at memory adress i+n, into register Vn
                    self.v_registers.write(n, self.memory.read(self.i.get() + n))

    def _cycle(self):
        instruction = self._fetch()
        self._execute(self._decode(instruction))

    #---

    def _load_font(self, font_data:list=None):
        """load font sprite data into memory. Must be sprites representing hex values 0 - F, and in that order!"""
        font = font_data if font_data else self.standard_font   # if no data is provided, then `self.standard_font` will be used
        for n, byte in enumerate(font):                         # write each byte number of font into memory,
            self.memory.write(self.font_mem_adr, byte)          # starting at `font_mem_adr`

    def _load_program(self, file_path:str):
        """load a CHIP-8 program file from provided path"""
        prog_start_mem_adr = 0x200                      # program start memory address - convention is to load programs starting at memory address 0x200 (512 in dec)
        with open(file_path, "rb") as program:          # open file as read-only bytes
            for i, byte in enumerate(program.read()):   # read entire file (returns a bytes object), enumerate to get index of each byte, 
                i = prog_start_mem_adr + i
                self.memory.write(i, byte)              # and then write each byte to memory, with offset from the program start memory address

    def set_emulation_speed(self, hz:int):
        """set the emulation speed in Hz (cycles per second)"""
        if not isinstance(hz, int):
            raise ValueError('hz arg must be int')
        self.emu_speed = hz

    def run(self, program_file_path:str, font_data:list=None):
        """Run a CHIP-8 program/rom (from provided file path) on this CHIP-8 emulator!

        Additionally, you can supply font sprite data, which should be a list of 80 bytes numbers 
        (5 numbers per sprite character, 16 characters (hex 0 - F)).
        MUST be in order from 0 - F!
        """
        self.memory.clear()                     # clear/reset memory
        self._load_font(font_data)              # load the font sprite data into memory
        self._load_program(program_file_path)   # load the program into memory

        # main loop
        cycle_delay = 1/self.emu_speed
        while True:
            self._cycle()                       # execute one cycle
            sleep(cycle_delay)
            # ^ enforce emulation speed by pausing execution for aproximiately
            # the seconds spent for one cycle at `self.emu_speed` Hz,
