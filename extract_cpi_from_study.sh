#!/bin/bash

# exit if error occures
set -e

# Repeat given char 80 times using shell function
repeat(){
    for i in $(seq 1 $2); do printf $1; done
}

workspace=$(dirname $0)
config_params="$workspace/study_params.txt"
config_cores="$workspace/study_cores.txt"

traces=$1
if [ -z $traces ] || [ ! -d $traces ]; then
    echo "Invalid path to traces!"
    exit 1
fi

if [ ! -f $config_params ] || [ ! -f $config_cores ]; then
    echo "Config file '$config_params' or '$config_cores' is missing!"
    exit 2
fi

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
printf "\n"

# print table (each row is an embench)
for embench in $embenchs; do
    printf "%20s , " $embench
    filename="${embench}_cpi.txt"

    for core in $cores; do
        path="$traces/$core/$embench"
        # extract cpi from log and save to a file
        (grep -P 'processor cycles per instruction: .+' < $path/${embench}_log.txt | grep -oP '\d+\.\d+' > $path/$filename)
        curr_cpi=$(< $path/$filename)
        printf "%-${max_len}s, " $curr_cpi
    done
    printf "\n"
done
