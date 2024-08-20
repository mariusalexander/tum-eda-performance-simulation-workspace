# PerformanceSimulation_workspace
Example workspace for software performance simulation with ETISS-based performance simulator (WiP!)

## Overview
This is an example workspace for the ETISS-based performance simulator. It contains:
- The ETISS-based performance simulator etiss-perf-sim
- The M2-ISA-R-Perf code generator to adjust the performance models
- The Embench benchmark suite, compiled for the CV32E40P (RV32IM) and CVA6 (RV64IM), as a target-software example

## First Time Setup

### Create workspace

Clone this repository and navigate to its top folder. (The given example uses an SSH-based link; adapt if necessary)

      $ git clone git@github.com:tum-ei-eda/PerformanceSimulation_workspace.git <YOUR_WORKSPACE_NAME>
      $ cd <YOUR_WORKSPACE_NAME>

NOTE: This workspace repository is currently work-in-progress (WiP). Make sure to switch to the main branch for the most recent updates:

      $ git checkout main

Initialize required git-submodules:

      $ git submodule update --init --recursive

### Install workspace

Install the workspace by calling:

      $ ./scripts/setup_workspace.sh


## Usage

### Performance Simulation

Example: Run a performance simulation for the embench-crc32 benchmark on the CV32E40P:

      $ ./scripts/run.sh em:crc32 cv32e40p

Example: Run a performance simulation for the embench-ud benchmark on the CVA6 and create a performance-trace:

      $ ./scripts/run.sh em:ud cva6 -tp=<YOUR/TRACE/PATH>

Example: Run an instruction simulation (without performance estimation) for the embench-crc32 benchmark on the CV32E40P:

      $ ./scripts/run.sh em:crc32 cv32e40p -np

### Code Generation

Please refer to the README of the M2-ISA-R-Perf tool. The generated code must be deployed to the SoftwareEvalLib plugin of the etiss-perf-sim.
