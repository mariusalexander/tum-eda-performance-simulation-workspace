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
config_options="$workspace/study_script_options.txt"

path=$1
if [ -z $path ] || [ ! -d $path ]; then
    echo "Invalid path to traces of core! ($path)"
    exit 1
fi

if [ ! -f $config_params ] || [ ! -f $config_cores ] || [ ! -f $config_options ]; then
    echo "Config file '$config_params', '$config_cores' or '$config_options' is missing!"
    exit 2
fi

m2isarperf="$workspace/code_gen/generators/M2-ISA-R-Perf"
if [ ! -d $m2isarperf ]; then
    echo "M2-ISA-R-PERF not found!"
    exit 3
fi
analyzer="$workspace/code_gen/code-analyzer"
if [ ! -d $analyzer ]; then
    echo "Code Analyzer not found!"
    exit 3
fi
source "$analyzer/venv/bin/activate"

# parse cores and benchmarks
cores=$(cut -f1 -d',' < $config_cores)
embenchs=$(cut -f1 -d',' < $config_params)
options=$(grep ${0:2} < $config_options | cut -f2 -d',')
echo -e "### options: $options"
echo -e "### cores:   \n$cores"
echo -e "### embenchs:\n$embenchs"

for embench in $embenchs; do
    echo -e "\n\n### $embench"

    for core in $cores; do
        log_path="$path/$core/$embench/${embench}_estimates_log.txt"
        export_dir="$path/$core/$embench/export"
        echo -e "\n\n### PYTHONPATH=$m2isarperf/m2isar_perf/ python3 $analyzer/main.py $path/$core --files $export_dir/experiment.json $options"
        (PYTHONPATH=$m2isarperf/m2isar_perf/ python3 $analyzer/main.py $path/$core --files $export_dir/experiment.json $options | tee $log_path)
    done
done
