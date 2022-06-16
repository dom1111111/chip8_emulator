import CPU

def fake_check_key_that_always_says_key_is_pressed(key):
    return True

##### tests #####

# pip install pytest
# then just `pytest`
def test_ibm_rom_loaded():
    return
    emulator = CPU.Emulator()
    assert emulator.memory[512] == 0x00
    assert emulator.memory[513] == 0xE0

def test_first_ibm_opcode_runs_correctly():
    return
    emulator = CPU.Emulator()
    CPU.step(emulator, fake_check_key_that_always_says_key_is_pressed)
    CPU.step(emulator, fake_check_key_that_always_says_key_is_pressed)
    assert emulator.i == 0x22A

def test_bytetobits():
    return
    test_cases = [
        (255, ['1','1','1','1','1','1','1','1']),
        (0, ['0','0','0','0','0','0','0','0'])
    ]
    for (input, expected_output) in test_cases:
        actual_output = CPU.byte_to_bits(input)
        assert actual_output == expected_output

def test_7X():
    emulator = CPU.Emulator()
    emulator.registers[6] = 43
    emulator.memory[512] = 0x76
    emulator.memory[513] = 0xFF
    CPU.step(emulator, None)
    assert emulator.registers[6] == 42

