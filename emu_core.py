from random import getrandbits
from components import *
from webview.window import Window

class EmulatorCore():
    """CHIP-8 Emulator Core. Contains all instructions and components"""

    def __init__(self, fr_end_window:Window):
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
        self.display = Display(64, 32, fr_end_window)   # 64x32-pixel monochrome display

        # misc settings
        self.font_mem_adr = 0x050               # starting address of where the font should be loaded into memory
        self.screen_partial_wrap = False
            # ^ if set to True, then sprites which start within screen dimensions, but then *partially* go outside of them, 
            # will have this outside parts wrap around to the other side of the screen. If False, then they will be clipped

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
                self.display.reset()

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
                        if not self.display.get_cell(x_c, y_c):         # and cell at coordinate is off,
                            self.display.set_cell(x_c, y_c, True)       # then set cell to on (True)
                        else:
                            self.display.set_cell(x_c, y_c, False)      # otherwise if both are on/1 (a collision), then set cell to off (False)
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

    #---------
    # main method

    def cycle(self) -> int:
        """Perform one complete cycle of the emulator (fetch instruction, decode, execute).
        Returns the instruction/opcode that was executed"""
        instruction = self._fetch()
        self._execute(*(self._decode(instruction)))
        return instruction