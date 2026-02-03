#!/bin/bash

# exit if error occures
set -e

workspace=$(dirname $0)
config="$workspace/study_params.txt"

if [ -z $1 ]; then
    echo "Invalid path to traces!"
    exit 1
fi

if [ ! -f $config ]; then
    echo "Config file is missing!"
    exit 2
fi

cores=$(for br in No Sta Dyn; do for fw in nfw fw; do printf "SimpleRISCV_H_${fw}_${br}BrPred "; done; done)

workspace=$(dirname 0)
embenchs=($(cut -f1 -d',' < $config))

for core in $cores; do
    echo $core
    for embench in ${embenchs[@]}; do
        echo $embench
        ./run_perf_study_for_core.sh $core $embench $1
    done
done
