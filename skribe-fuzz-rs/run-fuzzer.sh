#!/usr/bin/env bash

cargo run --bin skribe-fuzz -- --fuzz-spec fuzz-spec.json --contract-name stylus-hello-world --function-name testCallIncrement $@
