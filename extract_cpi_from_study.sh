#!/bin/bash

# exit if error occures
set -e

# Repeat given char 80 times using shell function
repeat(){
    for i in $(seq 1 $2); do echo -n "$1"; done
}

# parse cores and benchmarks
cores=$(ls -d traces/Simple*)
set -- $cores
embenchs=$(ls $1)

# print header
printf "%16s\t" "embench"
for core in $cores; do
    core=$(basename $core)
    printf "%-10s\t" "${core#*_H_}"
done
printf "diff\n%s\n" $(repeat "-" 80)

# print table (each row is an embench)
for embench in $embenchs; do
    printf -- "%16s\t" $embench
    filename="${embench}_cpi.txt"
    # each core is a column
    for core in $cores; do
        path="$core/$embench/"
        # extract cpi from log and save to a file
        $(cat $path/${embench}_log.txt | grep -P 'processor cycles per instruction: .+' | grep -oP '\d+\.\d+' > $path/$filename)
        # update cpi variables
        last_cpi=$curr_cpi
        curr_cpi=$(< $path/$filename)
        printf "%-10s\t" $curr_cpi
    done
    # print cpi diff
    diff=$(echo "${curr_cpi}-${last_cpi}" | bc)
    echo $diff
done
