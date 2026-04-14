#!/bin/bash

# exit if error occures
set -e

workspace=$(dirname $0)
config_params="$workspace/study_params.txt"
config_cores="$workspace/study_cores.txt"

traces=$1
if [ -z $traces ]; then
    echo "Invalid path to traces!"
    exit 1
fi

if [ ! -f $config_params ] || [ ! -f $config_cores ]; then
    echo "Config file '$config_params' or '$config_cores' is missing!"
    exit 2
fi
cores=$(cut -f1 -d',' < $config_cores)
embenchs=$(cut -f1 -d',' < $config_params)
echo -e "### cores:   \n$cores"
echo -e "### embenchs:\n$embenchs"

for core in $cores; do
    echo -e "\n### $core"
    for embench in $embenchs; do
        echo -e "### $embench"
        if [ -d $traces/$core/$embench/ ]; then
            echo -e "### rm -r $traces/$core/$embench/export/"
            rm -r $traces/$core/$embench/export/
        fi
    done
done
