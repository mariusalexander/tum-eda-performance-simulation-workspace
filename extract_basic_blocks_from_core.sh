#!/bin/bash

# exit if error occures
set -e

workspace=$(dirname $0)
config_params="$workspace/study_params.txt"
config_cores="$workspace/study_cores.txt"

path=$1
if [ -z $path ] || [ ! -d $path ]; then
    echo "Invalid path to traces! ($path)"
    exit 1
fi

if [ ! -f $config_params ] || [ ! -f $config_cores ]; then
    echo "Config file '$config_params' or '$config_cores' is missing!"
    exit 2
fi

core="$(basename $path) "
if [ -z "$(grep $core < $config_cores)" ]; then
    echo "Core $core not found in config file '$config_cores'!"
    exit 3
fi

# tr to replace characters, xargs to strip whitespaces
target_metrics=$(grep "$core" < $config_cores | cut -f2 -d',' | tr ";" " " | xargs echo)
replacements=$(grep "$core" < $config_cores   | cut -f3 -d',' | tr ";" " " | xargs echo)

embenchs=($(cut -f1 -d',' < $config_params))
cutoffs=($(cut -f2 -d',' < $config_params))

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

    bb_log_path="$log_path/${embench}_bb_log.txt"
    echo -e "\n### python3 $workspace/extract_basic_blocks.py -ta=$ta_path -tp=$tp_path -e=$export_path --cut-off=$cutoff"
    python3 $workspace/extract_basic_blocks.py -ta=$ta_path -tp=$tp_path -e=$export_path --cut-off=$cutoff | tee $bb_log_path
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        exit 1
    fi
    if [ ! -z "$target_metrics" ]; then
        metric_log_path="$log_path/${embench}_metrics_log.txt"
        echo -e "\n### python3 $workspace/extract_target_metrics.py -tp=$tp_path -e=$export_path $target_metrics -r $replacements"
        python3 $workspace/extract_target_metrics.py -tp=$tp_path -e=$export_path $target_metrics -r $replacements | tee $metric_log_path
        if [ ${PIPESTATUS[0]} -ne 0 ]; then
            exit 1
        fi
    fi
    echo -e "\n"
done
