#!/bin/bash

# exit if error occures
set -e

workspace=$(dirname $0)
config_params="$workspace/study_params.txt"
config_cores="$workspace/study_cores.txt"

traces=$1
if [ -z $traces ]; then
    echo "Invalid path to traces!"
    exit 1
fi

if [ ! -z $2 ]; then
    if [ $2 != "--traces" ]; then
        echo "Unknown argument '$2'!"
        exit 1
    fi
    log_traces=$2 
fi

if [ ! -f $config_params ] || [ ! -f $config_cores ]; then
    echo "Config file '$config_params' or '$config_cores' is missing!"
    exit 2
fi

cores=$(cut -f1 -d',' < $config_cores)
embenchs=$(cut -f1 -d',' < $config_params)

for core in $cores; do
    echo $core
    for embench in $embenchs; do
        echo -e "\n\n### $workspace/run_perf_study_for_core.sh $core $embench $traces $log_traces"
        $workspace/run_perf_study_for_core.sh $core $embench $traces $log_traces
    done
done
