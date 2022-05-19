
# Links

CHIP-8:

CHIP-8 Guide: https://tobiasvl.github.io/blog/write-a-chip-8-emulator/
CHIP-8 Wiki: https://en.wikipedia.org/wiki/CHIP-8
CHIP-8 game jam: https://itch.io/jam/octojam-6
CHIP-8 games: https://johnearnest.github.io/chip8Archive/?sort=platform

Other CPU stuff:

https://en.wikipedia.org/wiki/Von_Neumann_architecture
https://en.wikipedia.org/wiki/Zilog_Z80
https://en.wikipedia.org/wiki/Call_stack

Other Stuff:

https://gist.github.com/jboner/2841832 - Latency Numbers Every Programmer Should Know 

https://surma.dev/things/raw-wasm/ - WebAssembly

## Using an Emulator

https://massung.github.io/CHIP-8/

btw it might be useful to download and use an emulator like this to compare to your implementation, while you develop. feed the same code into it as your program is running and step through it, cycle-by-cycle;

that debugger shows you the:
1) contents of the memory, and what opcodes it maps to
2) contents of all the registers V0-VF
3) contents of the timers (DT and ST)
4) content of the index (I)
5) content of the program counter (PC)
6) content of the stack pointer (SP)
not sure what R0 through R7 are

---

# Process Notes

* "Python uses the prefix '0x' to indicate that it's a number in the hexadecimal system"
* So I messed up all the the opcodes with `X` in them (Vx). These are *vairables* for the **register**, and not just a character to compare against the other ones - so I re-wrote the code accordingly
* I wanted to test if two values of different encoding (but same in numerical value) could be compared - needed this for `8XY4` which needs to check if the result is above '255'
    * so yea, this prints `True` , so it works just fine:
```python
x = 5
y = 0b101   # this is 5 in binary
print(x==y)
```
* this was the old code I had for my `check_key` function, which works fine, but Nikita gave me a better example:
```python
def check_key(key):
    if key == 0x0:
        return keyboard.is_pressed('x')
    elif key == 0x1:
        return keyboard.is_pressed('1')
    elif key == 0x2:
        return keyboard.is_pressed('2')
    elif key == 0x3:
        return keyboard.is_pressed('3')
    elif key == 0x4:
        return keyboard.is_pressed('q')
    elif key == 0x5:
        return keyboard.is_pressed('w')
    elif key == 0x6:
        return keyboard.is_pressed('e')
    elif key == 0x7:
        return keyboard.is_pressed('a')
    elif key == 0x8:
        return keyboard.is_pressed('s')    
    elif key == 0x9:
        return keyboard.is_pressed('d')
    elif key == 0xA:
        return keyboard.is_pressed('z')
    elif key == 0xB:
        return keyboard.is_pressed('c')
    elif key == 0xC:
        return keyboard.is_pressed('4')
    elif key == 0xD:
        return keyboard.is_pressed('r')
    elif key == 0xE:
        return keyboard.is_pressed('f')
    elif key == 0xF:
        return keyboard.is_pressed('v')
    else:
        pass
```


TODO:
* do the commands related to the screen - clear screen and display
* implement the other components
* 
