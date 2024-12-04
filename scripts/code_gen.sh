#!/bin/bash

set -e

. $(dirname "${0}")/../.env

${PSW_SCRIPTS_SUPPORT}/code_gen_helper.py $1
