#!/bin/bash

# exit if error occures
set -e

repeat(){
    for i in $(seq 1 $2); do printf $1; done
}

workspace=$(dirname $0)
config_params="$workspace/study_params.txt"
config_cores="$workspace/study_cores.txt"
config_options="$workspace/study_script_options.txt"

traces=$1
if [ -z $traces ] || [ ! -d $traces ]; then
    echo "Invalid path to traces! ($traces)"
    exit 1
fi

if [ ! -f $config_params ] || [ ! -f $config_cores ] || [ ! -f $config_options ]; then
    echo "Config file '$config_params', '$config_cores' or '$config_options' is missing!"
    exit 2
fi

echo $0
cores=$(cut -f1 -d',' < $config_cores)
embenchs=$(cut -f1 -d',' < $config_params)
cutoffs=$(cut -f2 -d',' < $config_params)
options=$(grep ${0:2} < $config_options | cut -f2 -d',')
echo -e "### options: $options"
echo -e "### cores:\n$cores"
echo -e "### embenchs:\n$embenchs"

for embench in $embenchs; do
    echo -en "\n\n### $embench " ; repeat "#" 60; echo -en "\n"
    for core in $cores; do
        echo -en "\n### $core " ; repeat "-" 60; echo -en "\n"

        target_metrics=$(grep "$core " < $config_cores | cut -f2 -d',' | tr ";" " " | xargs echo)
        replacements=$(grep "$core " < $config_cores   | cut -f3 -d',' | tr ";" " " | xargs echo)

        if [ -z "$target_metrics" ]; then
            echo "### WARNING: No metrics to extract!"
            continue
        fi

        log_path="$traces/$core/$embench"
        if [ ! -d $log_path ]; then
            echo "### ERROR: $log_path does not exist!"
            continue
        fi
        tp_path="$log_path/tp"
        if [ ! -d $tp_path ]; then
            echo "### ERROR: $tp_path does not exist!"
            continue
        fi
        export_path="$log_path/export"
        if [ ! -d $export_path ]; then
            echo "### ERROR: $export_path does not exist!"
            continue
        fi

        metric_log_path="$log_path/${embench}_metrics_log.txt"
        echo -e "\n### python3 $workspace/extract_target_metrics.py -tp=$tp_path -e=$export_path $target_metrics $options -r $replacements"
        (python3 $workspace/extract_target_metrics.py -tp=$tp_path -e=$export_path $target_metrics $options -r $replacements | tee $metric_log_path)
        if [ ${PIPESTATUS[0]} -ne 0 ]; then
            echo "### ERROR!"
            exit 1
        fi
    done
done
