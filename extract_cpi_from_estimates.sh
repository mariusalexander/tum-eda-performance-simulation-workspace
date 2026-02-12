#!/bin/bash

# exit if error occures
set -e

# Repeat given char 80 times using shell function
repeat(){
    for i in $(seq 1 $2); do printf $1; done
}

estimates=$1
if [ -z $estimates ] || [ ! -f $estimates ]; then
    echo "Invalid path to estimates! ($estimates)"
    exit 1
fi
traces=$(dirname $estimates)

# construct list of cores (only nfw cores)
cores=$(for br in Dyn; do printf "SimpleRISCV_H_nfw_${br}BrPred "; done)
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
    printf "%-10s, %-10s " "diff" "coverage"
done

# print hline
array=($cores)
len=${#array[@]}
#printf "\n%s\n" $(repeat "-" $((41+len*43)))
printf "\n" #%s\n" $(repeat "-" $((41+len*43)))

#echo $embenchs

# print table (each row is an embench)
for embench in $embenchs; do
    printf -- "%20s , " $embench

    # extract cpi from log and save to a file
    output=$(grep "$embench " < $estimates | grep -Po "\d+\.\d+")
    count=$(echo $output | wc -w)
    set -- $output
    nfw=0
    fw=0
    sum=0
    for i in $(seq 3 3 $count); do
        sum=$(echo "$sum + (${!i})" | bc)
    done
    fraction=$(echo "1 / $sum" | bc -l)
    for i in $(seq 1 3 $count); do
        idx=$i
        current_nfw=${!idx}
        idx=$((idx + 1))
        current_fw=${!idx}
        idx=$((idx + 1))
        current_percentage=${!idx}
        nfw=$(echo "$nfw + ($current_nfw * $current_percentage * $fraction)" | bc)
        fw=$(echo "$fw + ($current_fw * $current_percentage * $fraction)" | bc)
    done
    diff=$(echo "scale=4; ($fw - $nfw) / 1" | bc)
    nfw=$(echo "scale=4; $nfw / 1" | bc)
    fw=$(echo "scale=4; $fw / 1" | bc)
    printf "%-15s, %-15s, %-10s, %-10s\n" $nfw $fw $diff "$sum%"
    #exit 0
done
