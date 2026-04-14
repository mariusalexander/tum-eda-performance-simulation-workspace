#!/bin/bash

# exit if error occures
set -e

workspace=$(dirname $0)
config_cores="$workspace/study_cores.txt"

traces=$1
if [ -z $traces ]; then
    echo "Invalid path to traces!"
    exit 1
fi

if [ ! -f $config_cores ]; then
    echo "Config file '$config_cores' is missing!"
    exit 2
fi
cores=$(cut -f1 -d',' < $config_cores)
echo -e "### cores:   \n$cores"

m2isarperf="$workspace/code_gen/generators/M2-ISA-R-Perf"
if [ ! -d $m2isarperf ]; then
    echo "M2-ISA-R-PERF not found!"
    exit 3
fi
source "$m2isarperf/venv/bin/activate"

for core in $cores; do
    file="$traces/$core/$core.corePerfDsl"
    echo -e "\n\n### python3 $m2isarperf/m2isar_perf/run.py $file -s -d=$traces/$core/"
    (python3 $m2isarperf/m2isar_perf/run.py $file -s -d=$traces/$core/)
done
