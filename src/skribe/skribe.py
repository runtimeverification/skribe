from __future__ import annotations

import shutil
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from eth_abi import decode, encode
from pyk.kast.inner import KSort, KToken, KVariable
from pyk.kast.manip import Subst, split_config_from
from pyk.kast.prelude.bytes import BYTES, bytesToken, pretty_bytes
from pyk.kast.prelude.k import GENERATED_TOP_CELL
from pyk.konvert import kast_to_kore, kore_to_kast
from pyk.kore.parser import KoreParser
from pyk.kore.syntax import EVar, SortApp
from pyk.ktool.kfuzz import KFuzzHandler, fuzz
from pyk.ktool.krun import KRunOutput
from pyk.utils import run_process

from .contract import read_contract_metadata
from .kast.syntax import call_stylus, check_output, set_exit_code, set_stylus_contract, steps_of
from .progress import FuzzProgress
from .simulation import call_data
from .utils import SkribeError, concrete_definition, parse_wasm_file, subst_on_program_cell

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Any

    from pyk.kast.inner import KInner
    from pyk.kore.syntax import Pattern

    from .contract import ContractBinding, ContractMetadata
    from .progress import FuzzTask
    from .utils import SkribeDefinition


CALLDATA = KVariable('CALLDATA', BYTES)
CALLDATA_EVAR = EVar('VarCALLDATA', SortApp('SortBytes'))

TRUE_DATA = encode(['bool'], [True])
EMPTY_DATA = encode([], [])

TEST_CALLER_ID = 0
TEST_CONTRACT_ID = 1


class Skribe:

    definition: SkribeDefinition

    def __init__(self, definition: SkribeDefinition):
        self.definition = definition

    def _which(self, cmd: str) -> Path:
        path_str = shutil.which(cmd)
        if path_str is None:
            raise RuntimeError(
                f"Couldn't find {cmd!r} executable. Please make sure {cmd!r} is installed and on your path."
            )
        return Path(path_str)

    @cached_property
    def _cargo_bin(self) -> Path:
        return self._which('cargo')

    def build_stylus_contract(self, contract_dir: Path) -> None:
        run_process(
            [
                str(self._cargo_bin),
                'build',
                '--lib',
                '--release',
                '--target',
                'wasm32-unknown-unknown',
            ],
            cwd=contract_dir,
            check=True,
        )

    @staticmethod
    def deploy_test(contract: KInner, init: bool, child_contracts: list[KInner]) -> KInner:
        """Takes a Stylus contract and its dependencies as kast terms and deploys them in a fresh configuration.

        Args:
            contract: The test contract to deploy, represented as a kast term.
            init: Whether to initialize the contract by calling its 'init' function after deployment.
            child_contracts: The child contracts to deploy, represented as kast terms.

        Returns:
            A configuration with the contract deployed.

        Raises:
            InitializationError if the deployment fails
        """

        # Stylus currently does not support constructors. As a workaround,
        # test contracts that require constructor-like behavior are expected to
        # implement an `init` function
        def call_init(init: bool) -> tuple[KInner, ...]:
            if not init:
                return ()

            # Set up the steps that will deploy the child contracts
            # Contract IDs 0 and 1 are reserved
            deploy_children = [set_stylus_contract(i, c, {}) for i, c in enumerate(child_contracts, start=2)]

            data = call_data(
                'init',
                ['address'] * len(child_contracts),
                [i.to_bytes(length=20, byteorder='big') for i in range(2, 2 + len(child_contracts))],
            )

            return (
                *deploy_children,
                call_stylus(TEST_CALLER_ID, TEST_CONTRACT_ID, bytesToken(data), 0),
                check_output(EMPTY_DATA),
            )

        # Set up the steps that will deploy the contract
        steps = steps_of(
            [
                set_exit_code(1),
                set_stylus_contract(TEST_CONTRACT_ID, contract, {}),
                *(call_init(init)),
                set_exit_code(0),
            ]
        )

        # Run the steps and grab the resulting config as a starting place to call transactions
        proc_res = concrete_definition.krun_with_kast(steps, sort=KSort('Steps'), output=KRunOutput.KORE)
        if proc_res.returncode:
            print(proc_res.stdout)
            raise InitializationError

        kore_result = KoreParser(proc_res.stdout).pattern()
        result_config = kore_to_kast(concrete_definition.kdefinition, kore_result)

        return result_config

    def run_test(
        self,
        conf: KInner,
        subst: dict[str, KInner],
        binding: ContractBinding,
        max_examples: int,
        task: FuzzTask,
    ) -> None:
        """Given a configuration with a deployed test contract, fuzz over the tests for the supplied binding.

        Args:
            conf: The template configuration.
            subst: A substitution mapping such that 'Subst(subst).apply(conf)' gives the initial configuration with the
                   deployed contract.
            binding: The contract binding that specifies the test name and parameters.
            max_examples: The maximum number of fuzzing test cases to generate and execute.

        Raises:
            AssertionError if the test fails
        """

        def calldata_to_kore(data: bytes) -> Pattern:
            return kast_to_kore(self.definition.kdefinition, bytesToken(data), BYTES)

        subst['PROGRAM_CELL'] = steps_of(
            [
                set_exit_code(1),
                call_stylus(TEST_CALLER_ID, TEST_CONTRACT_ID, CALLDATA, 0),
                check_output(EMPTY_DATA if not binding.outputs else TRUE_DATA),
                set_exit_code(0),
            ]
        )
        template_config = Subst(subst).apply(conf)
        template_config_kore = kast_to_kore(self.definition.kdefinition, template_config, GENERATED_TOP_CELL)

        template_subst = {CALLDATA_EVAR: binding.strategy.map(calldata_to_kore)}

        fuzz(
            self.definition.path,
            template_config_kore,
            template_subst,
            check_exit_code=True,
            max_examples=max_examples,
            handler=KometFuzzHandler(self.definition, task),
            subst_func=subst_on_program_cell,
        )

    def select_tests(self, contract_metadata: ContractMetadata, id: str | None) -> tuple[ContractBinding, ...]:
        if id is None:
            tests = contract_metadata.test_functions
            print(f'Discovered {len(tests)} test(s):')
        else:
            tests = tuple(b for b in contract_metadata.test_functions if b.name == id)
            if not tests:
                raise KeyError(f'Test function {id!r} not found.')
            print('Selected a single test function:')

        print()

        return tests

    def deploy_and_run(
        self, contract_dir: Path, child_wasms: tuple[Path, ...], max_examples: int, id: str | None = None
    ) -> list[FuzzError]:
        contract_metadata = read_contract_metadata(self._cargo_bin, contract_dir)

        contract_kast = parse_wasm_file(contract_metadata.wasm_path)
        child_wasm_kasts = []
        if contract_metadata.init_func is not None:
            if contract_metadata.init_func.arity != len(child_wasms):
                raise TypeError(f'Expected {contract_metadata.init_func.arity} children, found {len(child_wasms)}')
            child_wasm_kasts = [parse_wasm_file(p) for p in child_wasms]

        init_config = self.deploy_test(contract_kast, contract_metadata.has_init, child_wasm_kasts)
        template_conf, init_subst = split_config_from(init_config)

        tests = self.select_tests(contract_metadata, id)
        failed: list[FuzzError] = []
        with FuzzProgress(tests, max_examples) as progress:
            for task in progress.fuzz_tasks:
                try:
                    task.start()
                    self.run_test(template_conf, init_subst, task.binding, max_examples, task)
                    task.end()
                except FuzzError as e:
                    task.fail()
                    failed.append(e)

        return failed


class KometFuzzHandler(KFuzzHandler):
    # Fuzz handler with progress tracking

    definition: SkribeDefinition
    task: FuzzTask
    failed: bool

    def __init__(self, definition: SkribeDefinition, task: FuzzTask):
        self.definition = definition
        self.task = task
        self.failed = False

    def handle_test(self, args: Mapping[EVar, Pattern]) -> None:
        # Hypothesis reruns failing examples to confirm the failure.
        # To avoid misleading progress updates, the progress bar is not advanced
        # when a test fails and Hypothesis reruns the same example.
        if not self.failed:
            self.task.advance()

    def handle_failure(self, args: Mapping[EVar, Pattern]) -> None:
        if not self.failed:
            self.failed = True

        calldata_kast = self.definition.krun.kore_to_kast(args[CALLDATA_EVAR])
        assert isinstance(calldata_kast, KToken)
        calldata = pretty_bytes(calldata_kast)
        decoded = decode(self.task.binding.inputs, calldata[4:])
        raise FuzzError(self.task.binding.name, decoded)


class FuzzError(SkribeError):
    test_name: str
    counterexample: tuple[Any, ...]

    def __init__(self, test_name: str, counterexample: tuple[KInner, ...]):
        self.test_name = test_name
        self.counterexample = counterexample


class InitializationError(SkribeError): ...
