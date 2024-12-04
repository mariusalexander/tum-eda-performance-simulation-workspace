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
import pathlib
import shutil

######################################### SUPPORT FUNCTIONS #########################################

def getHeaderFiles(dir_):
    return getFiles((dir_ / "include"), ".h")

def getSrcFiles(dir_):
    return getFiles((dir_ / "src"), ".cpp")

def getFiles(dir_, suffix_):
    files = []
    for file_i in dir_.iterdir():
        if file_i.is_file() and (file_i.suffix == suffix_):
            files.append(file_i)
    return files

def checkTargetDir(dir_):
    if not dir_.is_dir():
        dir_.mkdir(parents=True)

def writeCMakeLists(dir_, lib_, files_):
    cmake_file = dir_ / "CMakeLists.txt"

    # Check if file exists and print warning
    if cmake_file.is_file():
        print("WARNING: Overwriting CMakeLists: " + str(cmake_file))

    # Write file
    with cmake_file.open('w') as f:
        f.write("TARGET_SOURCES(" + lib_.upper() + " PRIVATE\n")
        for file_i in files_:
            f.write("\tsrc/" + file_i.name + "\n")
        f.write(")\n\n")
        f.write("TARGET_INCLUDE_DIRECTORIES(" + lib_.upper() + " PRIVATE\n")
        f.write("\tinclude\n")
        f.write(")")

def copyFiles(files_, targetDir_):
    for file_i in files_:
        print(" > Copy: " + file_i.name + " to " + str(targetDir_) + " ...", end='')
        shutil.copyfile(file_i, (targetDir_ / file_i.name))
        print("Done.")


def deploy(targetLib_, subLib_, modelName_, fileDict_):

    # Make sure target directory and sub directories exist
    targetDir = targetLib_ / "libs" / subLib_ / "variants" / modelName_
    targetDir_include = targetDir / "include"
    targetDir_src = targetDir / "src"
    checkTargetDir(targetDir_include)
    checkTargetDir(targetDir_src)

    # Create or over-write CMakeLists
    writeCMakeLists(targetDir, ("SWEVAL_" + subLib_.upper() + "_LIB"), fileDict_["src"])

    # Copy files to backend
    copyFiles(fileDict_["include"], targetDir_include)
    copyFiles(fileDict_["src"], targetDir_src)
        
######################################### MAIN ROUTINE #########################################

## INPUT ARGUMENT PARSING ##

argParser = argparse.ArgumentParser()
argParser.add_argument("sourceDir", help="Path to source directory containing files for deployment")
argParser.add_argument("targetLib", help="Path to target SWEvalLib")
args = argParser.parse_args()

sourceDir = pathlib.Path(args.sourceDir).resolve()
targetLib = pathlib.Path(args.targetLib).resolve()


## GATHER SOURCE FILES ##

modelName = sourceDir.name

backendFiles = {"include":[], "src":[]}
monitorFiles = {"include":[], "src":[]}

for dir_i in (sourceDir / "code").iterdir():
    if dir_i.is_dir():
        if dir_i.name in ["perf_model"]:
            backendFiles["include"].extend(getHeaderFiles(dir_i))
            backendFiles["src"].extend(getSrcFiles(dir_i))
        elif dir_i.name in ["channel", "printer"]:
            backendFiles["include"].extend(getHeaderFiles(dir_i))
            backendFiles["src"].extend(getSrcFiles(dir_i))
        elif dir_i.name in ["monitor"]:
            monitorFiles["include"].extend(getHeaderFiles(dir_i))
            monitorFiles["src"].extend(getSrcFiles(dir_i))


## DEPLOY FILES ##

deploy(targetLib, "backends", modelName, backendFiles)
deploy(targetLib, "monitors", modelName, monitorFiles)
