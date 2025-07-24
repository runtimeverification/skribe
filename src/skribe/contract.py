from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cached_property, partial
from pathlib import Path
from typing import TYPE_CHECKING, Any
from kontrol import foundry
from eth_abi.tools._strategies import get_abi_strategy
from hypothesis import strategies
from pyk.utils import run_process

from .simulation import call_data

if TYPE_CHECKING:

    from hypothesis.strategies import SearchStrategy
    from kontrol.foundry import Foundry


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
    def strategy(self) -> SearchStrategy[bytes]:
        input_strategies = (get_abi_strategy(arg) for arg in self.inputs)
        tuple_strategy = strategies.tuples(*input_strategies)

        encoder = partial(call_data, self.name, self.inputs)
        return tuple_strategy.map(encoder)

    @cached_property
    def is_test(self) -> bool:
        return self.name.startswith('test')

    @cached_property
    def arity(self) -> int:
        return len(self.inputs)


@dataclass(frozen=True)
class ContractMetadata:
    is_foundry: bool
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

    @cached_property
    def init_func(self) -> ContractBinding | None:
        for b in self.bindings:
            if self.is_foundry and b.name == 'setUp':
                return b
            if not self.is_foundry and b.name == 'init':
                return b
        return None

    @cached_property
    def has_init(self) -> bool:
        return self.init_func is not None

    @cached_property
    def test_functions(self) -> tuple[ContractBinding, ...]:
        return tuple(b for b in self.bindings if b.is_test)

    def typecheck(self) -> None:
        for b in self.bindings:
            if b.name == 'init':
                no_output = not b.outputs
                only_address = all(i == 'address' for i in b.inputs)
                if no_output and only_address:
                    continue
            if not b.is_test:
                continue
            if not b.outputs:
                continue
            if b.outputs == ('bool',):
                continue

            raise TypeError(f'Invalid type: {b.name}{b.inputs} -> {b.outputs}')


def read_contract_bindings(cargo_bin: Path, contract_dir: Path) -> tuple[ContractBinding, ...]:
    """Reads a stylus wasm contract, and returns a list of the function bindings for it."""
    proc_res = run_process(
        [str(cargo_bin), 'stylus', 'export-abi', '--json'],
        cwd=contract_dir,
        check=True,
    )
    json_output = proc_res.stdout.split('\n', 3)[3]  # remove the headers
    bindings_list = json.loads(json_output)

    return tuple(
        ContractBinding.from_dict(binding_dict) for binding_dict in bindings_list if binding_dict['type'] == 'function'
    )


def read_rust_contract_metadata(cargo_bin: Path, contract_dir: Path) -> ContractMetadata:
    manifest_path = (contract_dir / 'Cargo.toml').resolve()
    proc_res = run_process(
        [str(cargo_bin), 'metadata', '--no-deps', '--manifest-path', str(manifest_path), '--format-version', '1'],
        check=True,
    )
    manifest = json.loads(proc_res.stdout)

    # filter out other packages in the workspace and get the one that matches the contract
    contract_package = [p for p in manifest['packages'] if Path(p['manifest_path']) == manifest_path][0]
    name = contract_package['name']
    target_dir = Path(manifest['target_directory']).resolve()

    bindings = read_contract_bindings(cargo_bin, contract_dir)

    res = ContractMetadata(
        is_foundry=False,
        manifest_path=manifest_path,
        name=name,
        bindings=bindings,
        target_dir=target_dir,
    )
    res.typecheck()

    return res


def is_foundry_test(ctr: foundry.Contract) -> bool:
    if ctr.is_test_contract:
        for m in ctr.methods:
            if m.is_test:
                return True
    return False


def read_foundry_contract_metadata(foundry: Foundry, contract_dir: Path) -> list[ContractMetadata]:
    foundry_toml = contract_dir / 'foundry.toml'

    foundry.all_tests
    res = []
    for full_name, ctr in foundry.contracts.items():
        if not is_foundry_test(ctr):
            continue

        contract_name = full_name.split('%')[-1]
        bindings = []
        for m in ctr.methods:
            binding = ContractBinding(
                name=m.name,
                inputs=m.arg_types,
                outputs=(),  # TODO identify the correct return type
            )
            bindings.append(binding)

        res.append(
            ContractMetadata(
                is_foundry=True,
                manifest_path=foundry_toml,
                name=contract_name,
                bindings=tuple(bindings),
                target_dir=contract_dir / 'out' / f'{contract_name}.sol',
            )
        )

    return res
