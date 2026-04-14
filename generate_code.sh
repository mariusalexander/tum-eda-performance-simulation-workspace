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

for core in $cores; do
    file="$traces/$core/$core.corePerfDsl"
    echo -e "\n\n### $workspace/scripts/code_gen.sh/$file"
    ($workspace/scripts/code_gen.sh $file)
done
