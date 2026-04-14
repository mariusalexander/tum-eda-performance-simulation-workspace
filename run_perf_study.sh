#!/bin/bash

# exit if error occures
set -e

repeat(){
    for i in $(seq 1 $2); do printf $1; done
}

workspace=$(dirname $0)
config_params="$workspace/study_params.txt"
config_cores="$workspace/study_cores.txt"

traces=$1
if [ -z $traces ]; then
    echo "Invalid path to traces!"
    exit 1
fi

log_traces=0
if [ ! -z $2 ]; then
    if [ $2 != "--traces" ]; then
        echo "Unknown argument '$2'!"
        exit 1
    fi
    log_traces=1
fi

if [ ! -f $config_params ] || [ ! -f $config_cores ]; then
    echo "Config file '$config_params' or '$config_cores' is missing!"
    exit 2
fi

cores=$(cut -f1 -d',' < $config_cores)
embenchs=$(cut -f1 -d',' < $config_params)
echo -e "### cores:\n$cores"
echo -e "### embenchs:\n$embenchs"

for core in $cores; do
    echo -en "\n\n### $core " ; repeat "#" 60; echo -en "\n"

    # check if core is valid by checking if .ini file exists
    if [[ ! -f "$workspace/etiss-perf-sim/simulator/ini/${core}.ini" ]] then
        echo "Core '$core' is invalid! (.ini file does not exist)"
        exit 1
    fi

    for embench in $embenchs; do
        echo -en "\n### $embench " ; repeat "-" 60; echo -en "\n"
        # check if embench exists
        embench_path="$workspace/target_sw/examples/cv32e40p/embench/$embench"
        if [[ ! -f "$embench_path" ]]; then
            embench_path="$workspace/target_sw/examples/cv32e40p/dhrystone/$embench"
            if [[ ! -f "$embench_path" ]]; then
                echo "Embench '$embench' not found!"
                exit 1
            fi
        fi
        
        log_path="$traces/$core/$embench"
        mkdir -pv $log_path

        if [ $log_traces -eq 1 ]; then
            # create target directories for traces
            ta_path="$log_path/ta"
            tp_path="$log_path/tp"
            mkdir -v $ta_path
            mkdir -v $tp_path
            args="-ta=$ta_path -tp=$tp_path"
        fi

        # execute simulation
        log_file="$log_path/${embench}_log.txt"
        echo -e "### $workspace/etiss-perf-sim/run_simulator.py $embench_path --core $core $args"
        ($workspace/etiss-perf-sim/run_simulator.py $embench_path --core $core $args 2>&1 | tee $log_file)
        if [ ${PIPESTATUS[0]} -ne 0 ]; then
            exit ${PIPESTATUS[0]}
        fi
    done
done
