#!/bin/bash

# exit if error occures
set -e

# Repeat given char 80 times using shell function
repeat(){
    for i in $(seq 1 $2); do printf "$1"; done
}

workspace=$(dirname $0)
# min ninstr
cutoff=2

path=$1
if [ -z $path ] || [ ! -d $path ]; then
    echo "Invalid path to traces! ($path)"
    exit 1
fi

m2isarperf="$workspace/code_gen/generators/M2-ISA-R-Perf"
source "$m2isarperf/venv/bin/activate"

# parse cores and benchmarks
embenchs=$(ls $path)
for embench in $embenchs; do
    echo $embench
    for bb in $(ls $path/$embench/export); do
        bbpath=$path/$embench/export/$bb
        # strip extension
        bb=${bb%.*}
        ninstr=$(wc -l < $bbpath)
        if [[ $ninstr -le $cutoff ]]; then
            #echo "Skipping bb $bb (too few instructions)"
            continue
        fi
        output=$($m2isarperf/m2isar_perf/run.py $m2isarperf/../../descriptions/core_perf_dsl/SimpleRISCV.corePerfDsl -b $bbpath | grep CPI)
        output=$(echo $output | grep -Po "_fw_.*$" | grep -Po "= \d+\.\d+" | grep -Po "\d+\.\d+" )
        set -- $output
        # extract weight of bb
        weight=$(grep $bb < $path/$embench/${embench}_bb_log.txt | grep -Po "\d+\.\d+")
        fw_output=$1
        nfw_output=$2
        #echo -e "OUTPUT:\n$output"
        echo -e "0x$bb \t$ninstr instr. \t$fw_output \t$nfw_output \t$weight%"
    done
    repeat "-" 95
    printf "\n"
done
