#!/bin/bash

# exit if error occures
set -e

# Repeat given char 80 times using shell function
repeat(){
    for i in $(seq 1 $2); do printf $1; done
}

traces=$1
if [ -z $traces ] || [ ! -d $traces ]; then
    echo "Invalid path to traces! ($traces)"
    exit 1
fi

# construct list of cores (only nfw cores)
cores=$(for br in No Sta Dyn; do printf "SimpleRISCV_H_nfw_${br}BrPred "; done)
# check which trace directories exist
cores=$(for core in $cores; do if [ -d $traces/$core ]; then printf "$core "; fi; done)

set -- $cores
embenchs=$(ls $traces/$1)

# print header
printf "%20s , " "embench"
for core in $cores; do
    core=$(basename $core)
    printf "NFW %-11s, " "${core##*_}"
    core=${core/_nfw_/_fw_}
    printf "FW %-12s, " "${core##*_}"
    printf "%-10s, " "diff"
done

# print hline
array=($cores)
len=${#array[@]}
#printf "\n%s\n" $(repeat "-" $((23+len*43)))
printf "\n"

# print table (each row is an embench)
for embench in $embenchs; do
    printf -- "%20s , " $embench
    filename="${embench}_cpi.txt"
    # each core is a column
    for base_core in $cores; do
        # iterate over "nfw" and "fw" variant
        for core in $base_core ${base_core/_nfw_/_fw_}; do
            path="$traces/$core/$embench/"
            # extract cpi from log and save to a file
            (grep -P 'processor cycles per instruction: .+' < $path/${embench}_log.txt | grep -oP '\d+\.\d+' > $path/$filename)
            # update cpi variables
            last_cpi=$curr_cpi
            curr_cpi=$(< $path/$filename)
            printf "%-15s, " $curr_cpi
        done
        # print cpi diff
        diff=$(echo "${curr_cpi}-${last_cpi}" | bc)
        printf "%-10s, " $diff
    done
    printf "\n"
done
