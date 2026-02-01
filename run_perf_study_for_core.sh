#!/bin/bash

# exit if error occures
set -e

# check whether to log traces
if [ ! -z $3 ]; then
    if [ $3 != "--traces" ]; then
        echo "Unkown argument!"
        exit 1
    fi
    log_traces=1
fi

core=$1
embench=$2
workspace=$(dirname $0)
traces="traces"

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

echo "core = $1; embench = $embench"

# create target directories for log
log_path="$traces/$core/$embench"
mkdir -pv $log_path

if [ $log_traces -eq 1 ]; then
    # create target directories for traces
    ta_path="$log_path/ta"
    tp_path="$log_path/tp"
    mkdir -pv $ta_path
    mkdir -pv $tp_path
    args="-ta=$ta_path -tp=$tp_path"
fi

# execute simulation
log_path="$log_path/${embench}_log.txt"
$workspace/etiss-perf-sim/run_simulator.py $embench_path --core $core $args 2>&1 | tee $log_path
