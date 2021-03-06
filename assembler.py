import re
import sys


def process_file(file):
    varible_bytes = {}
    memory_bytes = {}
    output_bytes = ""
    labels = {}
    section = None
    # * Process File test
    print("Pre Assembly Pass...")
    with open(file) as f:
        for line in f.read().splitlines():
            if 'section .' in line and ((line.index('section .') > line.index('section .')) if ';' in line else True):
                line = line.replace(":", "").replace(" ", "")
                line = re.sub("section.", "", line)
                section = line

            if section == "CODE":
                if ':' in line and ((line.index(';') > line.index(':')) if ';' in line else True):
                    line = line.replace(":", "").replace(" ", "")
                    line = re.sub(";.*$", "", line)
                    labels[line] = None
            elif '.define' in line and ((line.index(';') > line.index('.define')) if ';' in line else True):
                varible = re.sub(".define", "", line).replace(
                    " ", "").split("=")
                # > get memory value varible
                if re.match('\[(\d+|0x[a-fA-F0-9]+)\]', varible[1]):
                    varible[1] = varible[1][1:-1]
                    varible[1] = int(
                        varible[1], 10 if "x" not in varible[1] else 16)
                    varible[1] = {
                        "varible_value": varible[1],
                        "type": "mem",
                        "array": False,
                        "mem location": 1 if varible_bytes == {} else varible_bytes[list(varible_bytes)[-1]]["mem location"]+1}
                # > get constant value varible
                elif re.match('(\d+|0x[a-fA-F0-9]+)', varible[1]):
                    varible[1] = int(
                        varible[1], 10 if "x" not in varible[1] else 16)
                    varible[1] = {
                        "varible_value": varible[1],
                        "type": "constant",
                        "array": False,
                        "mem location": 1 if varible_bytes == {} else varible_bytes[list(varible_bytes)[-1]]["mem location"]+1}
                # > get memory array varible
                elif re.match('\[(\[(\d+|0x[a-fA-F0-9]+)\],?)+\]', varible[1]):
                    varible[1] = [int(x[1:-1], 10 if "x" not in x[1:-1] else 16)
                                  for x in re.findall("(?<=\[).*(?=\])", varible[1])[0].split(",")]
                    varible[1] = {
                        "varible_value": varible[1],
                        "type": "mem",
                        "array": True,
                        "mem location": 1 if varible_bytes == {} else varible_bytes[list(varible_bytes)[-1]]["mem location"]+len(varible[1])}
                # > get constant array varible
                elif re.match('\[((0x[a-fA-F0-9]+|\d+),?)+\]', varible[1]):
                    varible[1] = [int(x, 10 if "x" not in x else 16) for x in re.findall(
                        "(?<=\[).*(?=\])", varible[1])[0].split(",")]
                    varible[1] = {
                        "varible_value": varible[1],
                        "type": "constant",
                        "array": True,
                        "mem location": 1 if varible_bytes == {} else varible_bytes[list(varible_bytes)[-1]]["mem location"]+len(varible[1])}
                varible_bytes[varible[0]] = varible[1]

    print("Assembling Script...")
    with open(file) as f:
        for line in f.read().splitlines():

            # Check for comments
            line_comment = re.findall(';.*$', line)
            line = line.replace(line_comment[0] if len(
                line_comment) == 1 else "", "")

            # check for blank line
            if len(line) == 0:
                continue

            if 'section .' in line and ((line.index('section .') > line.index('setion .')) if ';' in line else True):
                line = line.replace(":", "").replace(" ", "")
                line = re.sub("section.", "", line)
                section = line

            if section == "DATA":
                continue

            # check for labels
            if ':' in line and ((line.index(';') > line.index(':')) if ';' in line else True) and "section" not in line:
                line_holder = line.replace(":", "").replace(" ", "")
                line_holder = re.sub(";.*$", "", line_holder)
                labels[line_holder] = list(memory_bytes.items(
                ))[-1][1]["mem location"] + (len(list(memory_bytes.items())[-1][1]["bytes"])//8)
                # > check if label has got a pointer in the output bytes and if so replace it
                try:
                    output_bytes = output_bytes.replace(
                        f"<<{line_holder}>>", f"{len(output_bytes)//8:05x}")
                except:
                    pass

            parts = re.findall('[\[a-zA-Z0-9_\]]+', line)
            op_code = parts[0]
            instructions = parts[1:]

            # > get each instruction type
            for i in range(len(instructions)):
                if re.match('E[ABCD]X', instructions[i]):
                    instructions[i] = {
                        "instruction": instructions[i], "type": "reg"}
                elif re.match('\[(\d+|0x[a-fA-F0-9]+)\]', instructions[i]):
                    instructions[i] = instructions[i][1:-1]
                    instructions[i] = int(
                        instructions[i], 10 if "x" not in instructions[i] else 16)
                    instructions[i] = {
                        "instruction": instructions[i], "type": "mem"}
                elif re.match('(\d+|0x[a-fA-F0-9]+)', instructions[i]):
                    instructions[i] = int(
                        instructions[i], 10 if "x" not in instructions[i] else 16)
                    instructions[i] = {
                        "instruction": instructions[i], "type": "const"}
                elif instructions[i] in labels.keys():
                    instructions[i] = {
                        "instruction": instructions[i], "type": "label"}

            # > process all 1 instruction op codes
            if len(instructions) == 1:
                if instructions[0]["type"] == "reg":
                    op_code_numbers = {"INC": "010", "DEC": "012",
                                       "PRINT": "029", "PUSH": "031", "POP": "034"}
                    memory_bytes[len(memory_bytes.keys())] = {
                        "parts": parts,
                        "bytes": f'{["EAX","EBX","ECX","EDX"].index(instructions[0]["instruction"]):05x}{op_code_numbers[op_code]}',
                        "mem location": 0 if (varible_bytes == {} and memory_bytes == {}) else (varible_bytes[list(varible_bytes)[-1]]["mem location"]+1) if memory_bytes == {} else memory_bytes[list(memory_bytes)[-1]]["mem location"]+1
                    }
                elif instructions[0]["type"] == "mem":
                    op_code_numbers = {"INC": "011", "DEC": "013", "JMP": "019", "JE": "01A", "JNE": "01B", "JZ": "01C", "JG": "01D",
                                       "JGE": "01E", "JL": "01F", "JLE": "020", "PRINT": "02A", "SSTK": "030", "PUSH": "032", "POP": "035"}
                    memory_bytes[len(memory_bytes.keys())] = {
                        "parts": parts,
                        "bytes": f'{instructions[0]["instruction"]:05x}{op_code_numbers[op_code]}',
                        "mem location": 0 if (varible_bytes == {} and memory_bytes == {}) else (varible_bytes[list(varible_bytes)[-1]]["mem location"]+1) if memory_bytes == {} else memory_bytes[list(memory_bytes)[-1]]["mem location"]+1
                    }
                elif instructions[0]["type"] == "const":
                    op_code_numbers = {"RJMP": "021", "RJE": "022", "RJNE": "023", "RJZ": "024",
                                       "RJG": "025", "RJGE": "026", "RJL": "027", "RJLE": "028", "PUSH": "033"}
                    memory_bytes[len(memory_bytes.keys())] = {
                        "parts": parts,
                        "bytes": f'{instructions[0]["instruction"]:05x}{op_code_numbers[op_code]}',
                        "mem location": 0 if (varible_bytes == {} and memory_bytes == {}) else (varible_bytes[list(varible_bytes)[-1]]["mem location"]+1) if memory_bytes == {} else memory_bytes[list(memory_bytes)[-1]]["mem location"]+1
                    }
                elif instructions[0]["type"] == "label":
                    # > Check if labels is in script and check if labels has already been seen or not
                    if instructions[0]["instruction"] in labels.keys():
                        op_code_numbers = {"JMP": "019", "JE": "01A", "JNE": "01B", "JZ": "01C", "JG": "01D",
                                           "JGE": "01E", "JL": "01F", "JLE": "020"}
                        if labels[instructions[0]["instruction"]] != None:
                            memory_bytes[len(memory_bytes.keys())] = {
                                "parts": parts,
                                "bytes": f'{labels[instructions[0]["instruction"]]:05x}{op_code_numbers[op_code]}',
                                "mem location": 0 if (varible_bytes == {} and memory_bytes == {}) else (varible_bytes[list(varible_bytes)[-1]]["mem location"]+1) if memory_bytes == {} else memory_bytes[list(memory_bytes)[-1]]["mem location"]+1
                            }
                        else:
                            memory_bytes[len(memory_bytes.keys())] = {
                                "parts": parts,
                                "bytes": f"<<{instructions[0]['instruction']}>>{op_code_numbers[op_code]}",
                                "mem location": 0 if (varible_bytes == {} and memory_bytes == {}) else (varible_bytes[list(varible_bytes)[-1]]["mem location"]+1) if memory_bytes == {} else memory_bytes[list(memory_bytes)[-1]]["mem location"]+1
                            }
                    else:
                        print(
                            f"Assembly Error: Label[{instructions[0]['instruction']}] not present, line -> {line}")
            # > process all opcodes with 2 instructions
            elif len(instructions) == 2:
                if instructions[0]["type"] == "reg":
                    op_code_numbers = {"MOVreg": "001", "MOVmem": "002", "MOVconst": "004", "ADDreg": "006", "ADDmem": "007", "ADDconst": "009", "SUBreg": "00B",
                                       "SUBmem": "00C", "SUBconst": "00E", "CMPreg": "014", "CMPmem": "015", "CMPconst": "017", "IMULreg": "02B", "IMULmem": "02C", "IMULconst": "02E"}
                    memory_bytes[len(memory_bytes.keys())] = {
                        "parts": parts,
                        "bytes": f'{["EAX","EBX","ECX","EDX"].index(instructions[0]["instruction"]):05x}{op_code_numbers[op_code+instructions[1]["type"]]}',
                        "mem location": 0 if (varible_bytes == {} and memory_bytes == {}) else (varible_bytes[list(varible_bytes)[-1]]["mem location"]+1) if memory_bytes == {} else memory_bytes[list(memory_bytes)[-1]]["mem location"]+1
                    }
                elif instructions[0]["type"] == "mem":
                    op_code_numbers = {"MOVreg": "003", "MOVconst": "005", "ADDreg": "008", "ADDconst": "00A", "SUBreg": "00D",
                                       "SUBconst": "00F", "CMPreg": "016", "CMPconst": "018", "IMULreg": "02D", "IMULconst": "02F"}
                    memory_bytes[len(memory_bytes.keys())] = {
                        "parts": parts,
                        "bytes": f'{instructions[0]["instruction"]:05x}{op_code_numbers[op_code+instructions[1]["type"]]}',
                        "mem location": 0 if (varible_bytes == {} and memory_bytes == {}) else (varible_bytes[list(varible_bytes)[-1]]["mem location"]+1) if memory_bytes == {} else memory_bytes[list(memory_bytes)[-1]]["mem location"]+1
                    }

                if instructions[1]["type"] == "reg":
                    memory_bytes[list(
                        memory_bytes)[-1]]["bytes"] += f'{["EAX","EBX","ECX","EDX"].index(instructions[1]["instruction"]):08x}'
                    memory_bytes[list(memory_bytes)[-1]]["mem location"] += 1
                elif instructions[1]["type"] == "mem":
                    memory_bytes[list(
                        memory_bytes)[-1]]["bytes"] += f'{instructions[1]["instruction"]:08x}'
                    memory_bytes[list(memory_bytes)[-1]]["mem location"] += 1
                elif instructions[1]["type"] == "const":
                    memory_bytes[list(
                        memory_bytes)[-1]]["bytes"] += f'{instructions[1]["instruction"]:08x}'
                    memory_bytes[list(memory_bytes)[-1]]["mem location"] += 1
            if op_code in ["HLT", "NOP", "RET"]:
                memory_bytes[len(memory_bytes.keys())] = {
                    "parts": parts,
                    "bytes": {"HLT": "000000FF", "NOP": "00000000", "RET": "00000036"}[op_code],
                    "mem location": 0 if (varible_bytes == {} and memory_bytes == {}) else (varible_bytes[list(varible_bytes)[-1]]["mem location"]+1) if memory_bytes == {} else memory_bytes[list(memory_bytes)[-1]]["mem location"]+1
                }

    print("Post Assembly pass...")
    # > Add the data section to the output bytes
    # > add the jump to the start of the code section
    if varible_bytes != {}:
        output_bytes += f"{(varible_bytes[list(varible_bytes)[-1]]['mem location']+1):05x}021"
    # > ass the varibles to output bytes
    for key, value in varible_bytes.items():
        if not value["array"]:
            output_bytes += f"{value['varible_value']:08x}"
        else:
            for inner_value in value["varible_value"]:
                output_bytes += f"{inner_value:08x}"

    # > Add the code section to the output bytes
    for key, value in memory_bytes.items():
        output_bytes += value["bytes"]

    print("Creating Minecraft Commands...")
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
    print("Finnished!!")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        process_file(sys.argv[1])
    else:
        process_file("tester.mcac")
