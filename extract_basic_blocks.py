import csv
import sys
import os
import argparse
from pathlib import Path

# hardcoded for trace
pc_idx = 0
br_target_idx = 7

def extract_basic_blocks_from_traces(path):
    if not os.path.isdir(path):
        raise ValueError(f"'{path}' is not a valid directory!")

    directory = os.fsencode(path)
    print(f"Parsing traces in '{path}'...")
    files = []
    basic_blocks = {}

    # find files
    for csv_file in os.listdir(directory):
        filename = os.fsdecode(csv_file)
        if not filename.endswith(".txt") or "instr_trace_" not in filename:
            print(f"- skipping {filename}")
            continue
        filename = f"{path}/{filename}"
        files.append(filename)
        with open(filename, 'r') as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            next(reader) # skip header
            for row in reader:
                #total_instructions += 1
                col = row[br_target_idx].strip()
                if col.startswith("-"):
                    continue
                basic_blocks[int(row[pc_idx], 16) + 4] = 0
                basic_blocks[int(row[br_target_idx], 16)] = 0
    print(f"-> Found {len(basic_blocks)} basic blocks!")

    # count how often each basic blocks is used, accumulate assembly trace for basic block
    print("Extracting basic block usages...")
    for file in files:
        with open(file, 'r') as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            next(reader) # skip header
            for row in reader:
                current_pc = int(row[pc_idx], 16)
                if current_pc in basic_blocks:
                    basic_blocks[current_pc] += 1

    return basic_blocks

def extract_basic_blocks_csv(filepath):
    if not os.path.exists(filepath):
        raise ValueError(f"'{filepath}' does not exist!")

    filepath = os.fsdecode(filepath)
    print(f"Parsing traces in '{filepath}'...")

    basic_blocks = {}
    with open(filepath, 'r') as csv_file:
        reader = csv.reader(csv_file, delimiter=',')
        next(reader) # skip header
        for row in reader:
            basic_blocks[int(row[0], 16)] = int(row[3])
    
    return basic_blocks

def extract_asm_from_traces(address_start, length, path, parse=True):
    if not os.path.isdir(path):
        raise ValueError(f"'{path}' is not a valid directory!")

    directory = os.fsencode(path)

    assembly = []
    # find files
    for csv_file in os.listdir(directory):
        filename = os.fsdecode(csv_file)
        if not filename.endswith(".txt"):
            print(f"- skipping {filename}")
            continue
        if "asm_trace_" in filename:
            delimiter = ';'
            asm_idx = 1
        elif "instr_trace" not in filename:
            print(f"- skipping {filename}")
            continue
        else:
            delimiter = ','
            asm_idx   = 2
        filename = f"{path}/{filename}"
        with open(filename, 'r') as csv_file:
            reader = csv.reader(csv_file, delimiter=delimiter)
            next(reader) # skip header
            found_pc = False
            for row in reader:
                pc  = int(row[pc_idx], 16)
                if pc == address_start:
                    found_pc = True
                if found_pc:
                    if length <= 0:
                        return assembly
                    trace = row[asm_idx].strip()
                    assembly.append(parse_asm(trace) if parse else trace)
                    length -= 1
    raise RuntimeError(f"Failed to find assembly for '{hex(address_start)}'")

def parse_asm(trace):
    idx = trace.index("#")
    instr_name = trace[:idx].strip()
    idx = trace.index('[')
    trace = trace[idx+1:]
    registers = trace.replace(']', '').split('|')
    registers = [ r.strip() for r in registers]
    return (instr_name, registers)

def export_basic_blocks(path, basic_blocks):
    basic_block_addresses = list(basic_blocks.keys())
    basic_block_addresses.sort(key=lambda key: key)
    
    string = "start, end, instructions, count\n"

    next_idx = 0
    for bb_start in basic_block_addresses[:-1]: # skip last entry
        next_idx += 1
        count  = basic_blocks[bb_start]
        bb_end = basic_block_addresses[next_idx] - 4
        ninstructions = ((bb_end - bb_start) // 4) + 1
        string += f'0x{bb_start:08x}, 0x{bb_end:08x}, {ninstructions}, {count}\n'

    with open(path, 'w') as out_file:
        out_file.write(string)

def count_total_instructions(basic_blocks):
    basic_block_addresses = list(basic_blocks.keys())
    basic_block_addresses.sort(key=lambda key: key)

    total_instructions = 0
    next_idx = 0
    for bb_start in basic_block_addresses[:-1]: # skip last entry
        next_idx += 1
        count  = basic_blocks[bb_start]
        bb_end = basic_block_addresses[next_idx] - 4
        ninstructions = ((bb_end - bb_start) // 4) + 1
        total_instructions += ninstructions * count

    return total_instructions

def main():

    def path_type(path):
        """" Enforces that an argument is a path to a valid location """
        if os.path.exists(path):
            return path
        raise argparse.ArgumentTypeError(f"'{path}' is not a valid path!")

    def dir_type(path):
        """" Enforces that an argument is a directory """
        if os.path.isdir(path) or not os.path.exists(path):
            return path
        raise argparse.ArgumentTypeError(f"'{path}' is not a valid path!")

    argParser = argparse.ArgumentParser()
    argParser.add_argument("--asm", nargs="?", type=path_type, const=True, help="Directory to assembly traces.")
    argParser.add_argument("-c", "--cut-off", nargs="?", type=int, const=100, help="Filters any basic block that was entered at least this often.")
    argParser.add_argument("-p", "--print", action="store_true", help="If flag is set, all basic blocks that match the cut-off are printed to stdout.")
    argParser.add_argument("--export_asm", nargs=1, type=dir_type, help="...")
    argParser.add_argument("path", type=path_type, help="Directory to instruction trace or extracted basic blocks.")
    args = argParser.parse_args()
    print(args)

    is_trace_directory = os.path.isdir(args.path)
    path = args.path
    if is_trace_directory:
        if args.asm == True:
            args.asm = path
    elif os.path.isfile(args.path) and os.path.basename(args.path).endswith("_basic_blocks.csv"):
        if args.asm == True:
            argParser.error("Must provide directory to traces that contain the assembly code!")
    else:
        argParser.error("Expected directory to trace or extracted basic blocks in .csv file!")

    if args.export_asm is not None:
        [args.export_asm] = args.export_asm
        if args.asm is None:
            argParser.error("Must provide directory to traces that contain the assembly code!")

    if is_trace_directory:
        # parse traces and extract basic blocks
        basic_blocks = extract_basic_blocks_from_traces(path)
        outpath = os.path.dirname(f"{path}/").decode('utf-8')
        export_basic_blocks(f"{outpath}_basic_blocks.csv", basic_blocks)
    else:
        # read basic blocks from csv file 
        basic_blocks = extract_basic_blocks_csv(path)

    total_instructions = count_total_instructions(basic_blocks)

    if args.print:
        basic_block_addresses = list(basic_blocks.keys())
        basic_block_addresses.sort(key=lambda key: key)
        next_idx = 0
        covered_ninstructions = 0
        
        for bb_start in basic_block_addresses:
            next_idx += 1
            count = basic_blocks[bb_start]
            if count <= args.cut_off:
                continue
            if next_idx >= len(basic_block_addresses):
                print(f'address 0x{bb_start:08x} - 0x???????? | instructions ???? | count {count} ')
                continue
            bb_end  = basic_block_addresses[next_idx] - 4
            ninstructions = ((bb_end - bb_start) // 4) + 1
            covered_ninstructions += ninstructions * count
            print(f'address 0x{bb_start:08x} - 0x{bb_end:08x} | instructions {ninstructions:<4} | count {count:<6} ({(ninstructions * count / total_instructions) * 100:.3}%)')
            if args.asm is not None:
                assembly = extract_asm_from_traces(bb_start, ninstructions, args.asm)
                for instruction in assembly:
                    print(f" -> {instruction[0]:<5} {', '.join([f"{r:<8}" for r in instruction[1]])}")

        print(f"-> Basic blocks cover {covered_ninstructions} of {total_instructions} instructions ({((covered_ninstructions / total_instructions) * 100):.5}%)")

    if args.export_asm is not None:
        export_asm_path = Path(args.export_asm)
        export_asm_path.mkdir(exist_ok=True)

        basic_block_addresses = list(basic_blocks.keys())
        basic_block_addresses.sort(key=lambda key: key)
        next_idx = 0
        covered_ninstructions = 0
        
        for bb_start in basic_block_addresses:
            next_idx += 1
            count = basic_blocks[bb_start]
            if count <= args.cut_off:
                continue
            if next_idx >= len(basic_block_addresses):
                raise RuntimeError("Cannot export last basic block as its length is unkown in the current script version!")
            bb_end  = basic_block_addresses[next_idx] - 4
            ninstructions = ((bb_end - bb_start) // 4) + 1

            assembly = extract_asm_from_traces(bb_start, ninstructions, args.asm, parse=False)
            with open(f"{args.export_asm}/{hex(bb_start)}.txt", 'w') as asm_file:
                asm_file.write("\n".join(assembly))

if __name__ == "__main__":
    main()