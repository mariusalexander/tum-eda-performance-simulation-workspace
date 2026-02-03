#!/bin/bash

# exit if error occures
set -e

workspace=$(dirname $0)
config="$workspace/study_params.txt"
path=$1

if [ ! -f $config ]; then
    echo "Config file is missing!"
    exit 2
fi

if [ -z $path ] || [ ! -d $path ]; then
    echo "Invalid path to traces! ($path)"
    exit 1
fi

workspace=$(dirname 0)
embenchs=($(cut -f1 -d',' < $config))
cutoffs=($(cut -f2 -d',' < $config))
for i in $(seq 1 ${#embenchs[@]} ); do
    embench=${embenchs[((i-1))]}
    cutoff=${cutoffs[((i-1))]}
    log_path="$path/$embench"
    if [ ! -d $log_path ]; then
        continue
    fi
    echo "Extracting basic blocks from '$embench' (cutoff = $cutoff)..."
    ta_path="$log_path/ta"
    tp_path="$log_path/tp"
    export_path="$log_path/export"
    log_path="$log_path/${embench}_bb_log.txt"
    python3 $workspace/extract_basic_blocks.py -ta=$ta_path -tp=$tp_path -e=$export_path --print --cut-off=$cutoff | tee $log_path
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        exit 1
    fi
    echo -e "\n"
done
