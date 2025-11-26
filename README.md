# Skribe


## Installation

Prerequsites: [K framework](https://github.com/runtimeverification/k/releases/latest), `python >= 3.10`, `pip >= 20.0.2`, [`uv`](https://docs.astral.sh/uv/).

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
### Skribe test contract structure

A *Skribe test contract* is a regular Stylus contract written in Rust, organized in a way that allows Skribe to discover
and execute test functions automatically. It can include an optional init function for setup and any number of test
functions following a specific naming and return convention.

#### `init` function and `skribe.json` file

The test contract may optionally define an `init` function, which Skribe calls once before executing any tests. This
function serves as a workaround for Stylus's current lack of constructor support and can be used to perform setup logic,
such as initializing state or linking to other contracts. If the `init` function takes arguments, they must be contract
addresses referring to other contracts that the test will interact with. These are specified in a `skribe.json` file,
which contains a `"contracts"` field listing the paths to the relevant Wasm files. Skribe deploys these contracts ahead
of time and passes their addresses to the `init` function in the given order.


Example contract with `init` function:

```rust
#[public]
impl TestCounter {
    pub fn setUp(&mut self, counter: Address) {
        self.counter.set(counter);
    }
    // ...
}
```

Example `skribe.json` file for the contract above:

```json
{
  "contracts": [
    "../stylus-hello-world/target/wasm32-unknown-unknown/release/stylus_hello_world.wasm"
  ]
}
```

#### Test functions

Test functions must start with the `test_` prefix and return `()`. A panic is
considered a test failure. Skribe automatically discovers these test functions and runs them with randomized input
values as part of the fuzzing process.

Example test function:

```rust
#[public]
impl TestCounter {
    // ...

    pub fn test_call_set_get_number(&mut self, x: U256) {
        let counter = ICounter::new(self.counter.get());
        counter.set_number(Call::new_in(self), x).unwrap();

        assert_eq!(counter.number(self).unwrap(), x)
    }
}
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

The `skribe run` command performs the following sequence of actions:

1. **Create contracts**
  Skribe reads the `skribe.json` file in the specified directory, and creates contracts from the provided Wasm files,
  obtaining their addresses.

2. **Initialize the test contract**
  Skribe creates the test contract. If the test contract defines an `init` function, Skribe invokes it once before
  executing any tests, passing the addresses of the deployed child contracts in the order specified in `skribe.json`.
  This allows for setup tasks such as linking to child contracts or initializing the blockchain state.

3. **Discover test functions**
  Skribe scans the test contract for functions with names starting with the `test_` prefix, and displays them as a
  progress bar.

4. **Execute fuzz tests**
  Skribe fuzzes the test functions, either all discovered or the one specified by the `--id` option—up to the limit set
  by `--max-examples` or until a failure occurs. The progress of fuzzing each test function is displayed with a progress
  bar.

5. **Report results**
  Failures are detected when a test function panics or returns `false`. Skribe reports any failing inputs and outcomes
  to the user.

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
* `make test-integration`: Run integration tests

