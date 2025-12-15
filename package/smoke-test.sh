#!/usr/bin/env bash

set -euxo pipefail

skribe-simulation --help

skribe-simulation run --verbose src/tests/integration/data/simulation/set_exit_code.json

skribe --help
