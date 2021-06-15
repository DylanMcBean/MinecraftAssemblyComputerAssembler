import re
import sys


def process_file(file):
    output_bytes = ""
    # * Process File test
    print("Assembling script...")
    with open(file) as f:
        for line in f.read().splitlines():
            parts = re.findall('[a-zA-Z0-9]+', line)
            op_code = parts[0]
            instructions = parts[1:]

            # > get each instruction type
            for i in range(len(instructions)):
                if re.match('E[ABCD]X', instructions[i]):
                    instructions[i] = {
                        "instruction": instructions[i], "type": "reg"}
                elif re.match('0x[a-fA-F0-9]+', instructions[i]):
                    instructions[i] = {
                        "instruction": instructions[i], "type": "mem"}
                elif re.match('\d+', instructions[i]):
                    instructions[i] = {
                        "instruction": instructions[i], "type": "const"}

            # > process all 1 instruction op codes
            if len(instructions) == 1:
                if instructions[0]["type"] == "reg":
                    op_code_numbers = {"INC": "010", "DEC": "012",
                                       "PRINT": "029", "PUSH": "031", "POP": "034"}
                    output_bytes += f'{["EAX","EBX","ECX","EDX"].index(instructions[0]["instruction"]):05x}{op_code_numbers[op_code]}'
                elif instructions[0]["type"] == "mem":
                    op_code_numbers = {"INC": "011", "DEC": "013", "JMP": "019", "JE": "01A", "JNE": "01B", "JZ": "01C", "JG": "01D",
                                       "JGE": "01E", "JL": "01F", "JLE": "020", "PRINT": "02A", "SSTK": "030", "PUSH": "032", "POP": "035"}
                    output_bytes += f'{int(instructions[0]["instruction"].replace("0x",""),16):05x}{op_code_numbers[op_code]}'
                elif instructions[0]["type"] == "const":
                    op_code_numbers = {"RJMP": "021", "RJE": "022", "RJNE": "023", "RJZ": "024",
                                       "RJG": "025", "RJGE": "026", "RJL": "027", "RJLE": "028", "PUSH": "033"}
                    output_bytes += f'{int(instructions[0]["instruction"]):05x}{op_code_numbers[op_code]}'
            elif len(instructions) == 2:
                if instructions[0]["type"] == "reg":
                    op_code_numbers = {"MOVreg": "001", "MOVmem": "002", "MOVconst": "004", "ADDreg": "006", "ADDmem": "007", "ADDconst": "009", "SUBreg": "00B",
                                       "SUBmem": "00C", "SUBconst": "00E", "CMPreg": "014", "CMPmem": "015", "CMPconst": "017", "IMULreg": "02B", "IMULmem": "02C", "IMULconst": "02E"}
                    output_bytes += f'{["EAX","EBX","ECX","EDX"].index(instructions[0]["instruction"]):05x}{op_code_numbers[op_code+instructions[1]["type"]]}'
                elif instructions[0]["type"] == "mem":
                    op_code_numbers = {"MOVreg": "003", "MOVconst": "005", "ADDreg": "008", "ADDconst": "00A", "SUBreg": "00D",
                                       "SUBconst": "00F", "CMPreg": "016", "CMPconst": "018", "IMULreg": "02D", "IMULconst": "02F"}
                    output_bytes += f'{int(instructions[0]["instruction"].replace("0x",""),16):05x}{op_code_numbers[op_code+instructions[1]["type"]]}'

                if instructions[1]["type"] == "reg":
                    output_bytes += f'{["EAX","EBX","ECX","EDX"].index(instructions[1]["instruction"]):08x}'
                elif instructions[1]["type"] == "mem":
                    output_bytes += f'{int(instructions[1]["instruction"].replace("0x",""),16):08x}'
                elif instructions[1]["type"] == "const":
                    output_bytes += f'{int(instructions[1]["instruction"]):08x}'
            if op_code in ["HLT", "NOP"]:
                output_bytes += {"HLT": "000000FF", "NOP": "00000000"}[op_code]

    print("Creating minecraft commands...")
    minecraft_commands = []
    colours = ["white", "orange", "magenta", "light_blue", "yellow", "lime", "pink",
               "gray", "light_gray", "cyan", "purple", "blue", "brown", "green", "red", "black"]
    x = 0
    y = 0
    z = 0
    for byte in output_bytes:
        if byte != "0":
            minecraft_commands.append(
                f"setblock ~{'' if x == 0 else x} ~{'' if y == 0 else y} ~{'' if z == 0 else z} {colours[int(byte,16)]}_concrete replace\n")
        y += 1
        if y == 8:
            y = 0
            x += 1
            if x == 64:
                x = 0
                z += 2

    minecraft_commands = ["function scripts:clearmemory\n"] + \
        minecraft_commands[::-1]
    with open(file.replace(".mcac", ".mcfunction"), "w+") as f:
        f.writelines(minecraft_commands)
    print("Finnished :)")


if __name__ == "__main__":
    process_file(sys.argv[1])
