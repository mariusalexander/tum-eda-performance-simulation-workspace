#!/bin/bash

# exit if error occures
set -e

core=$1
workspace=$(dirname $0)
traces="traces"
cutoff="0.02"

path="$traces/$core"

# check if core is valid by checking if .ini file exists
if [ ! -d $path ]; then
    echo "Core '$core' is invalid!"
    exit 1
fi

workspace=$(dirname 0)
embenchs=$(ls $traces/$core)
for embench in $embenchs; do
    echo "Extracting basic blocks from '$embench'..."
    log_path="$path/$embench"
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