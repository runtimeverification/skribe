#!/usr/bin/env bash

set -euxo pipefail

SKRIBE_DIR="${PWD}/skribe"
CONTRACT_DIR="${PWD}/9lives"
FUZZ_SPEC="${PWD}/fuzz-spec.json"

UV_RUN="uv --project ${SKRIBE_DIR} run --"
SKRIBE="${UV_RUN} skribe"

ITERATIONS=25
CONTRACT_NAME=TestSkribeEndToEnd
FUNCTION_NAME=test_end_to_end_intense

export KLLVM_LIBRARY_PATH="$(${UV_RUN} kdist which stylus-semantics.llvm-library)"
export LD_LIBRARY_PATH="${KLLVM_LIBRARY_PATH}"

: '########################################'
: '#  Initialization                      #'
: '########################################'

: 'Build skribe-fuzz'
cd "${SKRIBE_DIR}/skribe-fuzz-rs"
cargo clippy --workspace --all-targets
cargo build --release
cd -
cp "${SKRIBE_DIR}/skribe-fuzz-rs/target/release/skribe-fuzz" .

: 'Build skribe-fuzz-libfuzzer'
cd "${SKRIBE_DIR}/skribe-fuzz-rs/fuzz"
cargo +nightly fuzz build --release
cd -
cp "${SKRIBE_DIR}/skribe-fuzz-rs/target/x86_64-unknown-linux-gnu/release/fuzz_target_1" skribe-fuzz-libfuzzer

: 'Build test contract'
cd "${CONTRACT_DIR}"
./build-skribe.sh
${SKRIBE} build
cd -

: 'Export fuzzer specification'
cd "${CONTRACT_DIR}"
time ${SKRIBE} export-specs > "${FUZZ_SPEC}"
cd -

: '########################################'
: '#  Python Fuzzer                       #'
: '########################################'

time ${SKRIBE} run               \
  --max-examples "${ITERATIONS}" \
  --fuzz-spec "${FUZZ_SPEC}"     \
  --id "${FUNCTION_NAME}"

: '########################################'
: '#  libFuzzer-based Fuzzer              #'
: '########################################'

time ./skribe-fuzz-libfuzzer         \
  -runs="${ITERATIONS}"              \
  --fuzz-spec="${FUZZ_SPEC}"         \
  --contract-name="${CONTRACT_NAME}" \
  --function-name="${FUNCTION_NAME}"

: '########################################'
: '#  LibAFL-based Fuzzer w/o Coverage    #'
: '########################################'

time ./skribe-fuzz                   \
  --iterations "${ITERATIONS}"       \
  --fuzz-spec "${FUZZ_SPEC}"         \
  --contract-name "${CONTRACT_NAME}" \
  --function-name "${FUNCTION_NAME}"

: '########################################'
: '#  LibAFL-based Fuzzer w/ Coverage     #'
: '########################################'

time ./skribe-fuzz                   \
  --iterations "${ITERATIONS}"       \
  --fuzz-spec "${FUZZ_SPEC}"         \
  --contract-name "${CONTRACT_NAME}" \
  --function-name "${FUNCTION_NAME}" \
  --coverage
