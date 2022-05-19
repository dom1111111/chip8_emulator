import CPU

def fake_check_key_that_always_says_key_is_pressed(key):
    return True

##### tests #####

# pip install pytest
# then just `pytest`
def test_ibm_rom_loaded():
    emulator = CPU.Emulator()
    assert emulator.memory[512] == 0x00
    assert emulator.memory[513] == 0xE0

def test_first_ibm_opcode_runs_correctly():
    emulator = CPU.Emulator()
    CPU.step(emulator, fake_check_key_that_always_says_key_is_pressed)
    CPU.step(emulator, fake_check_key_that_always_says_key_is_pressed)
    assert emulator.i == 0x22A