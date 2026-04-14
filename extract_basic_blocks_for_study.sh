#!/bin/bash

# exit if error occures
set -e

repeat(){
    for i in $(seq 1 $2); do printf $1; done
}

workspace=$(dirname $0)
config_params="$workspace/study_params.txt"
config_cores="$workspace/study_cores.txt"

traces=$1
if [ -z $traces ] || [ ! -d $traces ]; then
    echo "Invalid path to traces! ($traces)"
    exit 1
fi

if [ ! -f $config_params ] || [ ! -f $config_cores ]; then
    echo "Config file '$config_params' or '$config_cores' is missing!"
    exit 2
fi

cores=$(cut -f1 -d',' < $config_cores)

embenchs=$(cut -f1 -d',' < $config_params)
cutoffs=$(cut -f2 -d',' < $config_params)
echo -e "### cores:\n$cores"
echo -e "### embenchs:\n$embenchs"

for embench in $embenchs; do
    echo -en "\n\n### $embench " ; repeat "#" 60; echo -en "\n"
    for core in $cores; do
        echo -en "\n\n### $core " ; repeat "-" 60; echo -en "\n"

        cutoff=$(grep "$embench " < $config_params   | cut -f2 -d',' | tr ";" " " | xargs echo)

        if [ -z "$cutoff" ]; then
            echo "### WARNING: No cutoff found!"
            continue
        fi

        log_path="$traces/$core/$embench"
        if [ ! -d $log_path ]; then
            echo "### ERROR: $log_path does not exist!"
            continue
        fi
        ta_path="$log_path/ta"
        if [ ! -d $tp_path ]; then
            echo "### ERROR: $ta_path does not exist!"
            continue
        fi
        tp_path="$log_path/tp"
        if [ ! -d $tp_path ]; then
            echo "### ERROR: $tp_path does not exist!"
            continue
        fi

        export_path="$log_path/export"
        bb_log_path="$log_path/${embench}_bb_log.txt"
        echo -e "\n### python3 $workspace/extract_basic_blocks.py -ta=$ta_path -tp=$tp_path -e=$export_path --cut-off=$cutoff"
        (python3 $workspace/extract_basic_blocks.py -ta=$ta_path -tp=$tp_path -e=$export_path --cut-off=$cutoff | tee $bb_log_path)
        if [ ${PIPESTATUS[0]} -ne 0 ]; then
            echo "### ERROR!"
            exit 1
        fi
    done
done
