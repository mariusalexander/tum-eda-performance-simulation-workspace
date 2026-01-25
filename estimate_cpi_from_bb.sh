#!/bin/bash

# exit if error occures
set -e

# Repeat given char 80 times using shell function
repeat(){
    for i in {1..80}; do echo -n "$1"; done
}

workspace="workspace"
m2isarperf="$workspace/code_gen/generators/M2-ISA-R-Perf"
source "$m2isarperf/venv/bin/activate"
core="SimpleRISCV_H_nfw_StaBrPred"

# parse cores and benchmarks
embenchs=$(ls traces/$core)
for embench in $embenchs; do
    echo $embench
    for bb in $(ls traces/$core/$embench/export); do
        $m2isarperf/m2isar_perf/run.py $m2isarperf/../../descriptions/core_perf_dsl/SimpleRISCV.corePerfDsl -b traces/$core/$embench/export/$bb | grep CPI
    done
    repeat "-"
    printf "\n"
done
