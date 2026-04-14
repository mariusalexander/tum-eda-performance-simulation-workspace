import csv
import os
import argparse
import sys
import json
import math
import re
from pathlib import Path
from itertools import combinations
from itertools import product
from contextlib import ExitStack

def delay_combinations(data):
    metrics = data.keys()
    delay_weight_dicts = [data[metric] for metric in metrics]
    delay_values_lists = [list(dw.keys()) for dw in delay_weight_dicts]

    # Cartesian product of delay values (all combinations)
    combined_results = []
    for delays_combination in product(*delay_values_lists):
        combined_weight = 1.0
        variables = {}

        for metric, delay in zip(data.keys(), delays_combination):
            weight = data[metric][delay]
            combined_weight *= weight
            variables       |= {metric: delay}

        assert len(variables) == len(data), "Possibly generated duplicate variables!"

        if len(variables) == 0:
            continue

        combined_results.append({
            "weight": combined_weight,
            "variables": variables
        })

    return combined_results

def rows_from_csv_files(files, delimiter):
    """Generator to yield rows from multiple CSV files sequentially."""
    for f in files:
        reader = csv.reader(f, delimiter=delimiter)
        next(reader) # skip header
        for row in reader:
            yield row

def extract_target_metrics(path, check_filename, targets, delimiter=',', pcs=None, per_instruction=False):
    if not os.path.isdir(path):
        raise ValueError(f"'{path}' is not a valid directory!")

    directory = os.fsencode(path)
    print(f"Parsing traces in '{path}'...")


    timing_files = []
    trace_files  = []

    is_timing_file = lambda f: f.endswith(".csv") and "_timing_" in f
    is_trace_file  = lambda f: f.endswith(".csv") and "_trace_" in f
    # find files
    for csv_file in os.listdir(directory):
        filename = os.fsdecode(csv_file)
        if is_timing_file(filename):
            filename = f"{path}/{filename}"
            timing_files.append(filename)
        elif is_trace_file(filename):
            filename = f"{path}/{filename}"
            trace_files.append(filename)
        else:
            print(f"- skipping {filename}")

    assert len(timing_files)
    assert len(trace_files)

    targets_idx = { }
    with open(timing_files[0], 'r') as f:
        reader = csv.reader(f, delimiter=',')
        header = next(reader)
        print(f"> Header columns:   {', '.join(header)}")
        for target in targets:
            targets_idx[target] = header.index(target)
    pc_idx = -1
    with open(trace_files[0], 'r') as f:
        reader = csv.reader(f, delimiter='|')
        header = next(reader)
        for col in header:
            pc_idx += 1
            if "pc" in col:
                break
    print(f"> Target indicies:  pc={pc_idx}, {', '.join(f"{k}={v}" for k,v in targets_idx.items())}")

    targets_results    = {}
    total_instructions = 0

    with ExitStack() as stack:
        open_timing_files = [stack.enter_context(open(fname, 'r')) for fname in timing_files]
        open_trace_files  = [stack.enter_context(open(fname, 'r')) for fname in trace_files]

        timing_files = rows_from_csv_files(open_timing_files, delimiter=',')
        trace_files  = rows_from_csv_files(open_trace_files , delimiter='|')

        for timings, trace in zip(timing_files, trace_files):
            total_instructions += 1
            if pcs is not None:
                pc = int(trace[pc_idx], 16)
                if pc not in pcs:
                    continue
                if per_instruction:
                    instr_num = pcs[pc]
            for target, target_idx in targets_idx.items():
                if per_instruction:
                    base_target = target
                    target += f"_{instr_num[0]}:{instr_num[1]}"
                if target not in targets_results:
                    targets_results[target] = {}
                result = timings[target_idx].strip()
                if result not in targets_results[target]:
                    targets_results[target][result] = 0
                targets_results[target][result] += 1

        assert(next(timing_files, None) is None)
        assert(next(trace_files,  None) is None)

    print(f"> Counted {total_instructions} total instructions")
    print(f"> Accumulated {len(targets_results)} results!")
    if len(targets_results) == 0:
        return targets_results

    print(f"> Found following metrics:")
    total_weights = { name : sum(results[e] for e in results if e.isdigit()) for name, results in targets_results.items()}

    for name, results in targets_results.items():
        results = list((e, results[e]) for e in results if e.isdigit())
        results.sort(key=lambda e: -e[1])

        if len(results) > 0:
            print(f"  > {name}:")
            print(f"\t{"key":>5} {"count":>8} {"weight":>32}")
            print(f"\t" + "-" * 47)
            print("\t" + "\n\t".join(f"> {e[0]:>3} {e[1]:>8} (total {(e[1] / total_instructions) * 100:2.5f}%, rel {(e[1] / total_weights[name]) * 100:2.5f}%)" for e in results))
        targets_results[name] = {int(e[0]) : (e[1] / total_weights[name]) for e in results}

    targets_results = {metric: delays for metric, delays in targets_results.items() if len(delays) > 0}
    return targets_results

def main():

    def exisiting_file_type(path):
        """" Enforces that an argument is a path to a valid location """
        if os.path.exists(path) and os.path.isfile(path):
            return path
        raise argparse.ArgumentTypeError(f"'{path}' is not a valid file!")

    def exisiting_dir_type(path):
        """" Enforces that an argument is a path to a valid location """
        if os.path.exists(path) and os.path.isdir(path):
            return path
        raise argparse.ArgumentTypeError(f"'{path}' is not a valid directory!")

    def valid_path_type(path):
        """" Enforces that an argument is a directory """
        if os.path.isdir(path) or not os.path.exists(path):
            return path
        raise argparse.ArgumentTypeError(f"'{path}' is not a valid path!")

    argParser = argparse.ArgumentParser()
    argParser.add_argument("targets"              , nargs='+', type=str, help="Which timing columns to extract.")
    argParser.add_argument("-r" , "--replacements", nargs='+', type=str, help="Replacements for each extracted timing column.")
    argParser.add_argument("-tp"                  , nargs=  1, type=exisiting_dir_type, help="Directory of performance traces.")
    argParser.add_argument("-e"   , "--export"    , nargs=  1, type=exisiting_dir_type, help="Directory to export extracted basic blocks to.")
    argParser.add_argument("--bbs-only"           , action="store_true", help="Whether to extract metrics only for the basic blocks listed in the experiment.json file.")
    argParser.add_argument("--per-instruction"    , action="store_true", help="Whether to extract metrics for each instruction in the basic blocks (must be used with --bbs-only).")
    argParser.add_argument("--average"            , action="store_true", help="Whether to create an average.")
    argParser.add_argument("--best-and-average"   , action="store_true", help="Whether to extract the best and the average.")

    args = argParser.parse_args()

    assert not any(';' in t for t in args.targets), "Invalid targets!"
    if args.replacements:
        if len(args.targets) != len(args.replacements):
            argParser.error(f"Replacements must match number of targets! Input: {args.targets} vs {args.replacements}")

    path = None
    export_path = None

    if args.tp is not None:
        path = args.tp[0]
        target_metric  = 7
        delimiter      = ','
        check_filename = lambda f: f.endswith(".csv") and "_timing_" in f
    else:
        argParser.error("Missing argument: Directory of performance traces.")

    # create export path for basic blocks
    if args.export is not None:
        export_path = f"{args.export[0]}/experiment.json"
        if not os.path.exists(export_path):
            argParser.error("Missing experiment.json. Extract basic blocks first!")
    pc_ranges = None
    if args.bbs_only:
        if export_path is None:
            argParser.error("Requires experiment.json to read pc ranges for each basic block!")
        print(f"Parsing '{export_path}'...")
        with open(export_path, 'r') as f:
            data = json.load(f)
        assert len(data) > 0
        export_dir  = Path(export_path).resolve().parent
        pc_ranges   = {}
        bb_names    = []
        instr_count = 0
        for bb in data:
            bb_name = bb["name"]
            file = export_dir / bb_name
            bb_names.append(bb_name)
            with open(file, 'r') as f:
                lines        = f.readlines()
                instr_count += len(lines)
            idx = 0
            for raw_instruction in lines:
                address = re.search(r"^0x[a-z0-9]{8}\s", raw_instruction)
                assert address
                pc_ranges[int(address.group(), 16)] = (idx, bb_name)
                idx += 1
        print(f"> Found {len(pc_ranges)} instructions!")
        assert instr_count == len(pc_ranges), f"Expected {instr_count} instructions!"
    if args.per_instruction:
        if not args.bbs_only:
            argParser.error("Requires the --bbs-only option!")
        if not args.average and not args.best_and_average:
            argParser.error("Requires the --average or --best-and-average option!")

    # parse traces and extract metrics
    results = extract_target_metrics(path, check_filename=check_filename, targets=args.targets, delimiter=delimiter, pcs=pc_ranges, per_instruction=args.per_instruction)
    
    # replace tracing variables with microop names
    if args.replacements:
        replacements = dict(zip(args.targets, args.replacements))
        new_results = {}
        for variable, values in results.items():
            replacement_found = False
            for target in args.targets:
                if target in variable:
                    replacement_found = True
                    variable = variable.replace(target, replacements[target])
                    if not args.per_instruction:
                        variable += '*'
                    break
            assert replacement_found
            new_results[variable] = values
        results = new_results
    
    if len(results) == 0:
        print(f"No results found!")
    
    # build average
    if args.average:
        results = [
            { 
                "weight": 1, 
                "variables": { name: sum(value * weight for value, weight in values.items()) for name, values in results.items() } 
            }
        ]
        print(1, results[0]["variables"])
    # include smallest delay and build average of rest accordingly
    elif args.best_and_average:
        min_values  = { name: min(value for value in values) for name, values in results.items() }
        min_weights = { name: values[min_values[name]] for name, values in results.items() }

        min_values_weight = math.prod(weight for name, values in results.items() for value, weight in values.items() if value == min_values[name])
        
        average = { name: sum(value * weight for value, weight in values.items()) for name, values in results.items() }
        print("average", average)

        target_weight = 0.5
        average_substracted = { name: (average[name] - (min_values[name] * target_weight)) * (1 / (1 - target_weight)) for name in results }
        print("average_substracted", average_substracted)
        average_substracted = { name: value if value > 0 else min_values[name] for name, value in average_substracted.items() }
        print("average_substracted", average_substracted)

        results = [
            {
                "weight": target_weight, 
                "variables": min_values
            },
            {
                "weight": 1 - target_weight, 
                "variables": average_substracted
            }
        ]
        print(1, results[0]["weight"], results[0]["variables"])
        print(2, results[1]["weight"], results[1]["variables"])
    # build all possible combinatons
    else:
        results = delay_combinations(results)
    
    if len(results) == 0:
        print(f"No results found!")

    total_weight = sum(entry["weight"] for entry in results)
    assert min(entry["weight"] for entry in results) > 0, f"Negative weight!"
    assert all(value for entry in results for value in entry["variables"].values()) > 0, f"Contains variables with a delay < 1!"
    assert abs(total_weight - 1.0) < sys.float_info.epsilon, f"Total weight {total_weight * 100} is not equal to 100%!"

    # export results
    if export_path is not None:
        print(f"Updating '{export_path}'...")
        with open(export_path, 'r') as f:
            data = json.load(f)
        for bb in data:
            this_results = results
            if args.per_instruction:
                this_results = [ {"weight": b["weight"], "variables": { name.replace(f":{bb["name"]}", ""): value for name, value in b["variables"].items() if bb["name"] in name } } for b in this_results ]
            bb["dynamic_delays"] = this_results
        with open(export_path, 'w') as f:
            f.write(json.dumps(data, indent=4))
        print("> done!")

if __name__ == "__main__":
    main()
