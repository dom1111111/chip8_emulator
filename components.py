from time import sleep
import os
from threading import Thread, Lock, Event
import keyboard
#import PyAudio
from webview.window import Window

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
        self.tone = PlayTone(440)
        super().__init__(bit_size, rate)
    
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
        self._reversed_key_map = {value:key for key, value in self._key_map.items()}
    
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


class TextModeDisplay:
    """
    Create a simple 'text-mode' screen, made up solely of characters to act as pixels.

    Instantiate with with int args for screen width and height, + a window object to render screen in the front-end

    Methods:
    * call `get_char()` to get the state (on or off) of a character at an x,y coordinate in the screen data
    * call `set_char()` to set the state of a character at an x,y coordinate in the screen data
    * call `clear_screen()` to reset screen data to completely blank state
    * call `draw_screen` to actually draw the screen

    So in order to see any changes done in calls to `set_char()` or `clear_screen()`
    on the screen, a subsequent call to `draw_screen` must be made.

    For get/set_char methods, coordinates start at '0,0' at the top left corner.
    They range from `0` to `width/height - 1` (so a dimension of `10`, has a coordinate value range from `0` to `9`).
    """
    def __init__(self, width:int, height:int, window:Window):
        self.width = width              # screen width
        self.height = height            # screen height
        # there are 2 characters for each on/off_char string in order to widen the screen horizontally, so that width is more even with height (because characters cells are taller than they are wide))
        self.on_char = '()'             # characters representing on-state
        self.off_char = '  '            # character representing off-state
        self.reset_screen()             # generate blank screen matrix data
        self.window = window            # Front-end window (used by display instruction)

    def _enforce_xy_limit(self, x:int, y:int):
        """ensure that coordinate is within the screen width and height"""
        if x not in range(self.width) or y not in range(self.height):
            raise ValueError('x and y values must be within width and height')

    def reset_screen(self):
        """Resets the screen so that all characters are in off state"""
        # The 'text mode' screen is made up solely of text characters, rather than pixels.
        # All the characters are stored in a list of lists with strings of characters in them. 
        # The length of the sub-lists is determined by width, and the number of strings in the list is determined by height.
        self._screen_matrix = [([self.off_char] * self.width) for row in range(self.height)]      # generate a list of lists of strings to represent screen matrix  

    def get_char(self, x:int, y:int) -> bool:
        """Get state of character cell at x,y coordinate on screen matrix. `True` means on, `False` means off."""
        self._enforce_xy_limit(x, y)
        return True if self._screen_matrix[y][x] == self.on_char else False

    def set_char(self, x:int, y:int, state:bool):
        """Set state of character cell at x,y coordinate on screen matrix. State `True` means on, `False` means off."""
        self._enforce_xy_limit(x, y)
        self._screen_matrix[y][x] = self.on_char if state else self.off_char

    def draw_screen(self):
        """Draw screen by adding each string row in screen_matrix to text box"""
        char_rows = [''.join(row) for row in self._screen_matrix]
        self.window.evaluate_js(f"drawToScreen({char_rows})")
