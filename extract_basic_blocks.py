import csv
import sys
import os
import argparse
from pathlib import Path

def extract_basic_blocks_from_traces(path, check_filename, pc_idx, br_target_idx, delimiter=','):
    if not os.path.isdir(path):
        raise ValueError(f"'{path}' is not a valid directory!")

    directory = os.fsencode(path)
    print(f"Parsing traces in '{path}'...")
    files = []
    basic_blocks = {}

    # find files
    for csv_file in os.listdir(directory):
        filename = os.fsdecode(csv_file)
        if not check_filename(filename):
            print(f"- skipping {filename}")
            continue
        filename = f"{path}/{filename}"
        files.append(filename)
        with open(filename, 'r') as csv_file:
            reader = csv.reader(csv_file, delimiter=delimiter)
            next(reader) # skip header
            prev_pc = 0
            for row in reader:
                #total_instructions += 1
                col = row[br_target_idx].strip()
                curr_pc = int(row[pc_idx], 16)
                if col.startswith("-"):
                    if prev_pc + 4 != curr_pc:
                        basic_blocks[curr_pc] = 0
                    prev_pc = curr_pc
                    continue
                basic_blocks[curr_pc + 4] = 0
                basic_blocks[int(row[br_target_idx], 16)] = 0
                prev_pc = curr_pc
    print(f"-> Found {len(basic_blocks)} basic blocks!")

    # count how often each basic blocks is used, accumulate assembly trace for basic block
    print("Extracting basic block usages...")
    for file in files:
        with open(file, 'r') as csv_file:
            reader = csv.reader(csv_file, delimiter=delimiter)
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

def extract_asm_from_traces(address_start, length, path, check_filename, pc_idx, asm_idx, delimiter=','):
    if not os.path.isdir(path):
        raise ValueError(f"'{path}' is not a valid directory!")

    directory = os.fsencode(path)

    assembly = []
    # find files
    for csv_file in os.listdir(directory):
        filename = os.fsdecode(csv_file)
        if not check_filename(filename):
            print(f"- skipping {filename}")
            continue
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
                    assembly.append(trace)
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

    def exisiting_dir_type(path):
        """" Enforces that an argument is a path to a valid location """
        if os.path.exists(path) and os.path.isdir(path):
            return path
        raise argparse.ArgumentTypeError(f"'{path}' is not a valid directory!")

    def exisiting_file_type(path):
        """" Enforces that an argument is a path to a valid location """
        if os.path.exists(path) and os.path.isfile(path):
            return path
        raise argparse.ArgumentTypeError(f"'{path}' is not a valid file!")

    def valid_path_type(path):
        """" Enforces that an argument is a directory """
        if os.path.isdir(path) or not os.path.exists(path):
            return path
        raise argparse.ArgumentTypeError(f"'{path}' is not a valid path!")

    def positive_number(num):
        """" Enforces that an argument is a positive number """
        num = float(num)
        if num <= 0:
            raise argparse.ArgumentTypeError(f"expected positive number greater than 0!")
        if num // 1 == num:
            return int(num)
        else:
            return num

    argParser = argparse.ArgumentParser()
    argParser.add_argument("-tp" , nargs=1, type=exisiting_dir_type, help="Directory to performance traces.")
    argParser.add_argument("-ta" , nargs=1, type=exisiting_dir_type, help="Directory to assembly traces.")
    argParser.add_argument("-ti" , nargs=1, type=exisiting_dir_type, help="Directory to instruction traces.")
    argParser.add_argument("-csv", nargs=1, type=exisiting_file_type, help="Directory to extracted basic blocks.")
    argParser.add_argument("-c", "--cut-off", nargs="?", type=positive_number, const=100, default=100, help="Filters any basic block that was entered at least this often.")
    argParser.add_argument("-p", "--print", action="store_true", help="If this flag is set, all basic blocks that match the cut-off are printed to stdout.")
    argParser.add_argument("-a", "--asm", action="store_true", help="If this flag is set and print is set, the assembly code is printed to stdout as well.")
    argParser.add_argument("-e", "--export", nargs=1, type=valid_path_type, help="Directory to export extracted basic blocks to.")
    args = argParser.parse_args()

    print(args)

    path = None
    am_path = None
    export_path = None

    do_extract_from_trace = True
    # path to instruction traces, contains both asm and br info
    if args.ti is not None:
        path = asm_path = args.ti[0]
        pc_idx = asm_pc_idx = 0
        asm_idx = 2
        br_target_idx = 7
        delimiter = asm_delimiter = ','
        check_filename = asm_check_filename = lambda f: f.endswith(".txt") and "instr_trace_" in f
        if args.tp is not None and args.tp is not None:
            argParser.error("Incompatible arguments: Either pass directory to performance traces or directory to instruction traces.")
    # path to performance traces, contains only br info
    elif args.tp is not None:
        [path] = args.tp
        pc_idx = 0
        br_target_idx = 1
        delimiter = '|'
        check_filename = lambda f: f.endswith(".csv") and "_trace_" in f
    # path to extracted traces
    elif args.csv is not None:
        [path] = args.csv
        do_extract_from_trace = False
    else:
        argParser.error("Missing argument: Either pass directory to traces or csv file to extract basic blocks.")
    # path to assembly traces
    if args.ta is not None:
        [asm_path] = args.ta
        asm_idx = 1
        asm_pc_idx = 0
        asm_delimiter = ';'
        asm_check_filename = lambda f: f.endswith(".txt") and "asm_trace_" in f

    # create export path for basic blocks
    if args.export is not None:
        export_path = args.export[0]
        if asm_path is None:
            argParser.error("Must provide directory to traces that contain the assembly code!")
        export_asm_path = Path(export_path)
        export_asm_path.mkdir(exist_ok=True)

    if args.asm and asm_path is None:
        argParser.error("Must provide directory to traces that contain the assembly code!")

    if do_extract_from_trace:
        # parse traces and extract basic blocks
        basic_blocks = extract_basic_blocks_from_traces(path, check_filename=check_filename, pc_idx=pc_idx, br_target_idx=br_target_idx, delimiter=delimiter)
        export_basic_blocks(f"{path}/../basic_blocks.csv", basic_blocks)
    else:
        # read basic blocks from csv file
        basic_blocks = extract_basic_blocks_csv(path)

    if export_path is None and not args.print:
        # nothing to do
        exit(0)

    total_instructions = count_total_instructions(basic_blocks)

    cut_off_by_percentage = args.cut_off < 1

    basic_block_addresses = list(basic_blocks.keys())
    basic_block_addresses.sort(key=lambda key: key)
    next_idx = 0
    total_convered_instruction_count = 0

    # iterate over all basic blocks
    for bb_start in basic_block_addresses:
        next_idx += 1
        call_count = basic_blocks[bb_start]
        if next_idx >= len(basic_block_addresses):
            # end of last basic block cannot be determined currently
            print(f"skipping basic block at '{hex(bb_start)}' (count={call_count})!")
            continue
        bb_end  = basic_block_addresses[next_idx] - 4
        instruction_count = ((bb_end - bb_start) // 4) + 1
        convered_instruction_count = instruction_count * call_count
        converd_percentage = (convered_instruction_count / total_instructions)
        # check number of calls to bb
        if not cut_off_by_percentage:
            if call_count < args.cut_off:
                continue
        # check percentage of covered instructions
        elif converd_percentage < args.cut_off:
            continue
        # bb exceeds cut-off
        total_convered_instruction_count += convered_instruction_count
        if asm_path is not None:
            assembly = extract_asm_from_traces(bb_start, instruction_count, asm_path, check_filename=asm_check_filename, pc_idx=asm_pc_idx, asm_idx=asm_idx, delimiter=asm_delimiter)
        if args.print:
            print(f'address 0x{bb_start:08x} - 0x{bb_end:08x} | instructions {instruction_count:<4} | count {call_count:<6} ({converd_percentage * 100:.3}%)')
            if args.asm:
                for instruction in assembly:
                    instruction = parse_asm(instruction)
                    print(f" -> {instruction[0]:<5} {', '.join([f"{r:<8}" for r in instruction[1]])}")
        if export_path is not None:
            with open(f"{export_path}/{hex(bb_start)}.txt", 'w') as asm_file:
                asm_file.write("\n".join(assembly))

    if args.print:
        print(f"-> Basic blocks cover {total_convered_instruction_count} of {total_instructions} instructions ({((total_convered_instruction_count / total_instructions) * 100):.5}%)")

if __name__ == "__main__":
    main()
