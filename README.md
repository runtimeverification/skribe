# skribe


## Installation

Prerequsites: `python >= 3.10`, [`uv`](https://docs.astral.sh/uv/).

```bash
make build
pip install dist/*.whl
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
* `make test-integration`: Run integration tests

