#!/bin/bash

set -e

# Source environment
. $(dirname "${0}")/../.env

# Setup etiss-perf-sim
${PSW_PERF_SIM}/setup_simulator.sh

# Setup M2-ISA-R
cd ${PSW_M2ISAR}
python3 -m venv venv
source venv/bin/activate
pip install git+https://github.com/tum-ei-eda/M2-ISA-R@coredsl2
deactivate

# Setup M2-ISA-R-Perf
cd ${PSW_M2ISAR_PERF}
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
