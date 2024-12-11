#!/usr/bin/env python3

# 
# Copyright 2024 Chair of EDA, Technical University of Munich
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#       http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# 

import argparse
import os
import subprocess
import pathlib
import shutil

####################################### INPUT ARGUMENT PARSING  #######################################

argParser = argparse.ArgumentParser()
argParser.add_argument("inputDescription", help="Input description. Supported formats are .json(monitor description) or .corePerfDsl (performance model)")
argParser.add_argument("-i", "--info_print", action="store_true", help="Run M2ISAR-Perf with info prints enabled")
args = argParser.parse_args()
inputFile = pathlib.Path(args.inputDescription).resolve()


####################################### PARSING CORE-DSL WITH M2ISAR #######################################

# Define handover item
m2isarModel = None

# NOTE: Currently hard-coded to use default ETISS CoreDSL
coreDsl = os.environ.get("PSW_DEFAULT_CORE_DSL")

# Calling M2ISAR to parse CoreDSL description
m2isar_run = os.environ.get("PSW_SCRIPTS_SUPPORT") + "/m2isar_run_wrapper.sh"
subprocess.run([m2isar_run, "coredsl2_parser", coreDsl], check=True)

# Move generated M2ISAR-model to intermediate directory
coreDsl_dir = pathlib.Path(coreDsl).resolve().parent
genModel_dir = coreDsl_dir / "gen_model"
m2isarModel_dir = pathlib.Path(os.environ.get("PSW_TEMP_M2ISAR_MODEL")).resolve() / coreDsl_dir.name
m2isarModel_dir.mkdir(parents=True, exist_ok=True)
shutil.copytree(genModel_dir, m2isarModel_dir, dirs_exist_ok=True)
shutil.rmtree(genModel_dir)

# Extract M2ISAR-model
modelCnt = 0
for file_i in m2isarModel_dir.iterdir():
    if file_i.is_file() and file_i.suffix == ".m2isarmodel":
        modelCnt += 1
        m2isarModel = file_i

if modelCnt > 1:
    raise RuntimeError("More than one (1) M2ISAR-model generated. Don't know how to handle this...")


####################################### CODE GENERATION WITH M2ISAR-PERF #######################################

# Define handover item
monitorDescriptionList = []

# Only if input description is of type .corePerfDsl
if inputFile.suffix == ".corePerfDsl":

    m2isar_perf_run = os.environ.get("PSW_SCRIPTS_SUPPORT") + "/m2isar_perf_run_wrapper.sh"

    # Generate estimator models (with or without info prints)
    flags = "-c"
    if args.info_print:
        flags += " -i"
    subprocess.run([m2isar_perf_run, str(inputFile), flags, ("-o=" + os.environ.get("PSW_CODE_GEN_OUT"))], check=True)

    # Generate monitor description (Need to store in temp directory, to keep track of which descriptions were generated this run. Will be deleted afterwards)
    dumpDir = pathlib.Path(__file__).parent/ "temp"
    subprocess.run([m2isar_perf_run, str(inputFile), "-m", ("-o=" + str(dumpDir))], check=True)

    # Extract monitor description and copy them to intermediate directory
    intermDir_monitor = pathlib.Path(os.environ.get("PSW_TEMP_MONITOR_DESCRIPTION")).resolve()
    for subDir_i in dumpDir.iterdir():
        if subDir_i.is_dir():
            monitor_dir = intermDir_monitor / subDir_i.name
            monitor_dir.mkdir(parents=True, exist_ok=True)
            for file_i in subDir_i.iterdir():
                if file_i.is_file() and (file_i.suffix == ".json"):
                    monitor_file = monitor_dir / file_i.name
                    shutil.copy(file_i, monitor_file)
                    monitorDescriptionList.append(monitor_file)

    # Remove temp dir
    shutil.rmtree(dumpDir)

####################################### MONITOR GENERATION WITH M2ISAR #######################################

# Defien hand-over item
# Note: This implies that variant dirs contain both perf-model and monitor files. Since all perf-models also need a monitor, it is then sufficient to generate the hand-over item here.
variantDirList = []

# Make sure that a (list of) monitor descriptions exists
if inputFile.suffix == ".json":
    monitorDescriptionList = [inputFile]

if not monitorDescriptionList:
    raise RuntimeError("No monitor description(s) specified for monitor generation")

# Check that M2ISAR-model is available
if m2isarModel == None:
    raise RuntimeError("No M2ISAR-model specified for monitor generation")

# Call M2ISAR to generate monitor files
# Use a temp directory (dump):
# a) to keep track on which models were generated
# b) as a temp work-around, as long as the output directory format of M2ISAR trace_gen is not aligned to M2ISAR-Perf's
# Temp directory will be removed afterwards
dumpDir = pathlib.Path(__file__).parent / "temp"
dumpDir.mkdir(parents=True, exist_ok=True)
m2isar_run = os.environ.get("PSW_SCRIPTS_SUPPORT") + "/m2isar_run_wrapper.sh"
for monitor_i in monitorDescriptionList:
    subprocess.run([m2isar_run, "trace_gen", str(monitor_i), str(m2isarModel), ("-o=" + str(dumpDir))],check=True)

# Extract generated variant files (e.g.: CV32E40P) and copy them to output directory
for tempVar_i in dumpDir.iterdir():
    if tempVar_i.is_dir():

        # Check if output directoryfor this variant exists. If not, generate
        variantDir = pathlib.Path(os.environ.get("PSW_CODE_GEN_OUT")) / tempVar_i.name 
        outDir = variantDir / "code"
        if not outDir.is_dir():
            outDir.mkdir(parents=True)

        # Add variantDir to hand-over item
        variantDirList.append(variantDir)

        # Copy the generated module files (e.g. monitor) to the target variant dir
        for tempMod_i in tempVar_i.iterdir():
            if tempMod_i.is_dir():
                shutil.copytree(tempMod_i, (outDir / tempMod_i.name), dirs_exist_ok=True)

# Remove temp directory
shutil.rmtree(dumpDir)

   
####################################### DEPLOY GENERATED CODE #######################################

if not variantDirList:
    raise RuntimeError("List of generated variants is empty. Cannot deploy variants.")

deploy_run = os.environ.get("PSW_SCRIPTS_SUPPORT") + "/deploy_SWEvalLib.py"

for variant_i in variantDirList:
    print("Deploying: " + variant_i.name)
    subprocess.run([deploy_run, variant_i], check=True)


####################################### RE_BUILD ETISS #######################################

rebuild_run = os.environ.get("PSW_PERF_SIM") + "/rebuild.sh"
subprocess.run([rebuild_run], check=True)
