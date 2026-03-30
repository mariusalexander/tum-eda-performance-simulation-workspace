#!/bin/bash

# exit if error occures
set -e

# Repeat given char 80 times using shell function
repeat(){
    for i in $(seq 1 $2); do printf "$1"; done
}

workspace=$(dirname $0)
config_params="$workspace/study_params.txt"
config_cores="$workspace/study_cores.txt"

path=$1
if [ -z $path ] || [ ! -d $path ]; then
    echo "Invalid path to traces of core! ($path)"
    exit 1
fi

if [ ! -f $config_params ] || [ ! -f $config_cores ]; then
    echo "Config file '$config_params' or '$config_cores' is missing!"
    exit 2
fi

m2isarperf="$workspace/code_gen/generators/M2-ISA-R-Perf"
analyzer="$workspace/code_gen/code-analyzer"
source "$analyzer/venv/bin/activate"

# parse cores and benchmarks
cores=$(cut -f1 -d',' < $config_cores)
embenchs=$(cut -f1 -d',' < $config_params)

# get len of cores
max_len=0
for core in $cores; do
    len=${#core}
    if [ $len -gt $max_len ]; then
        max_len=$len
    fi
done

# print header
printf "%20s , " "embench"
for core in $cores; do
    printf -- "%-${max_len}s, " "$core"
done
printf "\b\b  \n"

for embench in $embenchs; do
    printf "%20s , " $embench
    filename="${embench}_cpi_estimates.txt"
    
    for core in $cores; do
        log_path="$path/$core/$embench/${embench}_estimates_log.txt"
        (grep -Po "total CPI:\s+\d+\.\d+" < $log_path | grep -Po "\d+\.\d+" > $path/$core/$embench/$filename)
        curr_cpi=$(< $path/$core/$embench/$filename)
        printf "%-${max_len}s, " $curr_cpi
    done
    printf "\n"
done
