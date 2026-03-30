#!/bin/bash

# exit if error occures
set -e

repeat(){
    for i in $(seq 1 $2); do printf $1; done
}

workspace=$(dirname $0)
config_cores="$workspace/study_cores.txt"

traces=$1
if [ -z $traces ] || [ ! -d $traces ]; then
    echo "Invalid path to traces!"
    exit 1
fi

if [ ! -f $config_cores ]; then
    echo "Config file '$config_cores' is missing!"
    exit 2
fi

cores=$(cut -f1 -d',' < $config_cores)

for core in $cores; do
    echo -en "\n\n$core "
    repeat "-" 60
    echo
    echo -e "### $workspace/extract_basic_blocks_from_core.sh $traces/$core"
    $workspace/extract_basic_blocks_from_core.sh $traces/$core
done
