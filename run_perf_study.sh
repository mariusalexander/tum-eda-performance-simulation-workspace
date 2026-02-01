#!/bin/bash

# exit if error occures
set -e

cores=$(for br in No Sta Dyn; do for fw in nfw fw; do printf "SimpleRISCV_H_${fw}_${br}BrPred "; done; done)

workspace=$(dirname 0)
embenchs=$(ls $workspace/target_sw/examples/cv32e40p/embench/)

for core in $cores; do
    echo $core
    for embench in $embenchs; do
        echo $embench
        ./run_perf_study_for_core.sh $core $embench
    done
done
