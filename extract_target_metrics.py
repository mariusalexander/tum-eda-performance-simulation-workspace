import csv
import os
import argparse
import sys
import json
from pathlib import Path
from itertools import combinations
from itertools import product

def delay_combinations(data):
    metrics = data.keys()
    delay_weight_dicts = [data[metric] for metric in metrics]
    delay_values_lists = [list(dw.keys()) for dw in delay_weight_dicts]

    # Cartesian product of delay values (all combinations)
    combined_results = []
    for delays_combination in product(*delay_values_lists):
        combined_weight = 1.0
        variables = []

        for metric, delay in zip(data.keys(), delays_combination):
            weight = data[metric][delay]
            combined_weight *= weight
            variables.append({metric: delay})

        if len(variables) == 0:
            continue

        combined_results.append({
            "weight": combined_weight,
            "variables": variables
        })

    return combined_results

def extract_target_metrics(path, check_filename, targets, delimiter=','):
    if not os.path.isdir(path):
        raise ValueError(f"'{path}' is not a valid directory!")

    directory = os.fsencode(path)
    print(f"Parsing traces in '{path}'...")

    targets_idx     = { }
    targets_results = { t:{} for t in targets }
    total_instructions = 0

    # find files
    for csv_file in os.listdir(directory):
        filename = os.fsdecode(csv_file)
        if not check_filename(filename):
            print(f"- skipping {filename}")
            continue
        filename = f"{path}/{filename}"
        with open(filename, 'r') as csv_file:
            reader = csv.reader(csv_file, delimiter=delimiter)
            # find indicies for targets
            if len(targets_idx) == 0:
                for header in reader:
                    idx = 0
                    for column in header:
                        for target in targets:
                            if target == column:
                                targets_idx[target] = idx
                                break
                        idx += 1
                    assert len(targets_idx) == len(targets), f"Some targets were not found! Found: {targets_idx}"
                    break
            else: # skip header
                next(reader) 
            for row in reader:
                total_instructions += 1
                for name, idx in targets_idx.items():
                    result = row[idx].strip()
                    if result not in targets_results[name]:
                        targets_results[name][result] = 0
                    targets_results[name][result] += 1
    print(f"-> Counted {total_instructions} total instructions:"
    )
    print(f"-> Found following metrics:")

    total_weights = { name : sum(results[e] for e in results if e.isdigit()) for name, results in targets_results.items()}

    for name, results in targets_results.items():
        results = list((e, results[e]) for e in results if e.isdigit())
        results.sort(key=lambda e: -e[1])
        if len(results) > 0:
            print(f"  -> {name}:\n\t" + ",\n\t".join(f"{e[0]:>2}: {e[1]:>8} ({(e[1] / total_instructions) * 100:.5f}%, rel {(e[1] / total_weights[name]) * 100:.5f}%)" for e in results))
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
    argParser.add_argument("targets", nargs='+', type=str, help="Config file for cores and their metrics.")
    argParser.add_argument("-tp"    , nargs=1, type=exisiting_dir_type, help="Directory of performance traces.")
    argParser.add_argument("-e", "--export", nargs=1, type=exisiting_dir_type, help="Directory to export extracted basic blocks to.")
    argParser.add_argument("-r", "--replacements", nargs='+', type=str, help="")

    args = argParser.parse_args()
    print(args)

    assert not any(';' in t for t in args.targets), "Invalid targets!"
    if args.replacements:
        assert len(args.targets) == len(args.replacements), f"Invalid replacements! {args.targets} vs {args.replacements}"

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

    # parse traces and extract metrics
    results = extract_target_metrics(path, check_filename=check_filename, targets=args.targets, delimiter=delimiter)
    # replace tracing variables with microop names
    if args.replacements:
        replacements = dict(zip(args.targets, args.replacements))
        results = { replacements[target]: result for target,result in results.items() }

    results = delay_combinations(results)
    if len(results) == 0:
        exit(0)

    total_weight = sum(entry["weight"] for entry in results)
    assert abs(total_weight - 1.0) < sys.float_info.epsilon, f"Total weight {total_weight * 100} is not equal to 100%!"

    if export_path is not None:
        with open(export_path, 'r') as f:
            data = json.load(f)
        for bb in data:
            bb["dynamic_delays"] = results
        with open(export_path, 'w') as f:
            f.write(json.dumps(data, indent=4))

if __name__ == "__main__":
    main()
