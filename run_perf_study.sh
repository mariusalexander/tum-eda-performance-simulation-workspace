#!/bin/bash

# exit if error occures
set -e

cores="SimpleRISCV_H_nfw_StaBrPred SimpleRISCV_H_fw_StaBrPred"
workspace=$(dirname 0)
embenchs=$(ls $workspace/target_sw/examples/cv32e40p/embench/)

for core in $cores; do
    echo $core
    for embench in $embenchs; do
        echo $embench
        ./run_perf_study_for_core.sh $core $embench
    done
done
