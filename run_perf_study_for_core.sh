#!/bin/bash

# exit if error occures
set -e

core=$1
embench=$2
workspace=$(dirname $0)

echo "core = $1; embench = $embench"

# check if core is valid by checking if .ini file exists
if [[ ! -f "$workspace/etiss-perf-sim/simulator/ini/${core}.ini" ]] then
    echo "Core '$core' is invalid!"
    exit 1
fi
# check if embench exists
embench_path="$workspace/target_sw/examples/cv32e40p/embench/$embench"
if [[ ! -f "$embench_path" ]]; then
    echo "Embench '$embench' not found!"
    res=$(eval ls "$workspace/target_sw/examples/cv32e40p/embench/")
    echo "$res"
    exit 1
fi

# create target directories for traces
ta_path="traces/$core/${embench}/ta"
tp_path="traces/$core/${embench}/tp"
mkdir -pv "$ta_path"
mkdir -pv "$tp_path"

# execute simulation
log_path="traces/$core/${embench}/${embench}_log.txt"
$workspace/etiss-perf-sim/run_simulator.py $embench_path --core $core -ta=$ta_path -tp=$tp_path 2>&1 | tee -a $log_path

# extract basic blocks
export_path="traces/$core/${embench}/export"
python3 $workspace/extract_basic_blocks.py -ta=$ta_path -tp=$tp_path -e=$export_path --print --cut-off=0.02 | tee -a $log_path
