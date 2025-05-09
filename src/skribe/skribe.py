from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any

from eth_abi.tools._strategies import get_abi_strategy
from hypothesis import strategies
from pyk.prelude.bytes import bytesToken
from pyk.utils import run_process
from pykwasm.wasm2kast import wasm2kast
from skribe.simulation import call_data_encoder

if TYPE_CHECKING:
    from hypothesis.strategies import SearchStrategy
    from pyk.kast.inner import KInner

    from skribe.utils import SkribeDefinition


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

    def kast_from_wasm(self, wasm: Path) -> KInner:
        """Get a kast term from a wasm program."""
        return wasm2kast(open(wasm, 'rb'))

    def contract_metadata(self, contract_dir: Path) -> ContractMetadata:
        manifest_path = (contract_dir / 'Cargo.toml').resolve()
        proc_res = run_process(
            [str(self._cargo_bin), 'metadata', '--no-deps', '--manifest-path', str(manifest_path)], check=True
        )
        manifest = json.loads(proc_res.stdout)
        # filter out other packages in the workspace and get the one that matches the contract
        contract_package = [p for p in manifest['packages'] if Path(p['manifest_path']) == manifest_path][0]
        name = contract_package['name']
        target_dir = manifest['target_directory']

        bindings = self.contract_bindings(contract_dir)

        return ContractMetadata(
            manifest_path=manifest_path,
            name=name,
            bindings=bindings,
            target_dir=target_dir,
        )

    def contract_bindings(self, contract_dir: Path) -> tuple[ContractBinding, ...]:
        """Reads a stylus wasm contract, and returns a list of the function bindings for it."""
        proc_res = run_process(
            [str(self._cargo_bin), 'stylus', 'export-abi', '--json'],
            cwd=contract_dir,
            check=True,
        )
        bindings_list = json.loads(proc_res.stdout)

        return tuple(
            ContractBinding.from_dict(binding_dict)
            for binding_dict in bindings_list
            if binding_dict['type'] == 'function'
        )

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
    def deploy_test(
        contract: KInner, child_contracts: tuple[KInner, ...], init: bool
    ) -> tuple[KInner, dict[str, KInner]]:
        """Takes a Stylus contract and its dependencies as kast terms and deploys them in a fresh configuration.

        Args:
            contract: The test contract to deploy, represented as a kast term.
            child_contracts: A tuple of child contracts required by the test contract.
            init: Whether to initialize the contract by calling its 'init' function after deployment.

        Returns:
            A configuration with the contract deployed.

        Raises:
            AssertionError if the deployment fails
        """

        def wasm_id(i: int) -> bytes:
            return str(i).encode()

        def call_init() -> tuple[KInner, ...]:
            wasm_ids = tuple(wasm_id(i) for i in range(len(child_contracts)))
            upload_wasms = tuple(upload_wasm(h, c) for h, c in zip(hashes, child_contracts, strict=False))

            from_addr = account_id(b'test-account')
            to_addr = contract_id(b'test-contract')
            args = [sc_bytes(h) for h in hashes]
            init_tx = call_tx(from_addr, to_addr, 'init', args, SC_VOID)

            return upload_wasms + (init_tx,)

        # Set up the steps that will deploy the contract
        steps = steps_of(
            [
                set_exit_code(1),
                upload_wasm(b'test', contract),
                set_account(b'test-account', 9876543210),
                deploy_contract(b'test-account', b'test-contract', b'test'),
                *(call_init() if init else ()),
                set_exit_code(0),
            ]
        )

        # Run the steps and grab the resulting config as a starting place to call transactions
        proc_res = concrete_definition.krun_with_kast(steps, sort=KSort('Steps'), output=KRunOutput.KORE)
        assert proc_res.returncode == 0

        kore_result = KoreParser(proc_res.stdout).pattern()
        kast_result = kore_to_kast(concrete_definition.kdefinition, kore_result)

        conf, subst = split_config_from(kast_result)

        return conf, subst

    def deploy_and_run(
        self, contract_dir: Path, max_examples: int = 100, id: str | None = None
    ) -> None:
        contract_metadata = self.contract_metadata(contract_dir)

        contract_kast = self.kast_from_wasm(contract_metadata.wasm_path)

        conf, subst = self.deploy_test(contract_kast)

        pass
@dataclass(frozen=True)
class ContractBinding:
    """Represents one of the function bindings for a Stylus contract."""

    name: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]

    @staticmethod
    def from_dict(d: dict[str, Any]) -> ContractBinding:
        name = d['name']
        inputs = tuple(inp['type'] for inp in d['inputs'])
        outputs = tuple(out['type'] for out in d['outputs'])
        return ContractBinding(name, inputs, outputs)

    @cached_property
    def strategy(self) -> SearchStrategy[KInner]:
        input_strategies = (get_abi_strategy(arg) for arg in self.inputs)
        tuple_strategy = strategies.tuples(*input_strategies)

        return tuple_strategy.map(call_data_encoder(self.name, self.inputs)).map(bytesToken)


@dataclass(frozen=True)
class ContractMetadata:
    manifest_path: Path
    name: str
    bindings: tuple[ContractBinding, ...]
    target_dir: Path

    @cached_property
    def wasm_target_dir(self) -> Path:
        return (self.target_dir / 'wasm32-unknown-unknown' / 'release').resolve()

    @cached_property
    def wasm_path(self) -> Path:
        wasm_file_name = self.name.replace('-', '_') + '.wasm'
        wasm_path = self.wasm_target_dir / wasm_file_name
        return wasm_path.resolve()
