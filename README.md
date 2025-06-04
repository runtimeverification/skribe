# Skribe


## Installation

Prerequsites: [K framework](https://github.com/runtimeverification/k/releases/latest), `python >= 3.10`, `pip >= 20.0.2`, `poetry >= 1.3.2`.

```bash
make build
pip install dist/*.whl
```
## Usage

Skribe has two subcommands: `build` and `run`.

```
$ skribe --help
usage: skribe [-h] {build,run} ...

positional arguments:
  {build,run}
    build      build the test contract
    run        run tests with fuzzing

options:
  -h, --help   show this help message and exit
```

### Build

Compile the test contract located in the specified directory.

```bash
skribe build --directory path/to/contract
```

If no directory is provided, Skribe defaults to the current working directory.

**Options:**

* `--directory`, `-C`: Path to the test contract directory (default: `.`)

### Run Tests

Run fuzz tests on the test contract.

```bash
skribe run --directory path/to/contract --id test_function --max-examples 200
```

**Options:**

* `--directory`, `-C`: Path to the test contract directory (default: `.`)
* `--id`: Name of a single test function to run. If not specified, Skribe runs **all** test functions.
* `--max-examples`: Maximum number of fuzzing inputs to generate (default: `100`)

### Example

```bash
cd src/tests/integration/data/contracts/test-hello-world
skribe build
skribe run --max-examples 500
```

## `skribe-simulation`

`skribe-simulation` is a CLI tool for simulating Stylus smart contracts.

Test cases are written in JSON as sequences of steps that:
- Deploy contracts  
- Call functions  
- Check expected results  

Here is an example test case:

```json
{
  "steps": [
      {
          "type": "setExitCode", "value": 1
      },
      {
          "type": "setStylusContract",
          "id": 1,
          "code": "path/to/contract.wasm"
      },
      {
          "type": "callStylus",
          "to": 1,
          "data": {
              "function": "number", "types": [], "args": []
          },
          "output": {
              "type": "uint256",
              "value": 1
          },
          "value": 0
      },
      {
          "type": "setExitCode", "value": 0
      }
  ]
}
```

This scenario:

1. Sets the status code to 1 (indicating failure if the simulation doesn't finish),
1. Deploys a Stylus contract from a WASM file,
1. Calls the `number()` function on the contract and checks the output is 1,
1. Resets the expected exit code to 0 (indicating success).

Under the hood, JSON scenarios are translated to K terms and executed using Stylus formal semantics via `krun`.
For debugging purposes, you can use skribe-simulation to generate an initial configuration term in Kore format and execute it with krun:

```shell
skribe-simulation run path/to/test.json --depth 0 > initial-state.kore
krun --definition $(kdist which stylus-semantics.llvm) initial-state.kore --parser cat --term
```

## For Developers

Use `make` to run common tasks (see the [Makefile](Makefile) for a complete list of available targets).

* `make build`: Build wheel
* `make check`: Check code style
* `make format`: Format code
* `make test-unit`: Run unit tests

For interactive use, spawn a shell with `poetry shell` (after `poetry install`), then run an interpreter.
