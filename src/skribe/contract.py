from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cached_property, partial
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeAlias

from eth_abi.tools._strategies import get_abi_strategy
from hypothesis import strategies
from kontrol.solc_to_k import Contract as EVMContract
from kontrol.solc_to_k import contract_name_with_path, method_sig_from_abi
from pyk.kast.inner import KSort
from pyk.utils import run_process, single

from skribe.simulation import call_data

if TYPE_CHECKING:

    from hypothesis.strategies import SearchStrategy


Method: TypeAlias = EVMContract.Method


@dataclass
class StylusContract:
    contract_path: Path
    _cargo_bin: Path

    def __init__(self, cargo_bin: Path, contract_dir: Path):
        self.contract_path = contract_dir.resolve()
        self._cargo_bin = cargo_bin

    @cached_property
    def name_with_path(self) -> str:
        return contract_name_with_path(str(self.contract_path), self._name)

    @cached_property
    def manifest_path(self) -> Path:
        return self.contract_path / 'Cargo.toml'

    @cached_property
    def manifest(self) -> dict[str, Any]:
        return json.loads(
            run_process(
                [
                    str(self._cargo_bin),
                    'metadata',
                    '--no-deps',
                    '--manifest-path',
                    str(self.manifest_path),
                    '--format-version',
                    '1',
                ],
                check=True,
            ).stdout
        )

    @cached_property
    def contract_package(self) -> dict[str, Any]:
        return single(p for p in self.manifest['packages'] if Path(p['manifest_path']) == self.manifest_path)

    @cached_property
    def _name(self) -> str:
        return self.contract_package['name']

    @cached_property
    def abi(self) -> list[dict[str, Any]]:
        proc_res = run_process(
            [str(self._cargo_bin), 'stylus', 'export-abi', '--json'],
            cwd=self.contract_path,
            check=True,
        )
        json_output = proc_res.stdout.split('\n', 3)[3]  # remove the headers
        return json.loads(json_output)

    @cached_property
    def methods(self) -> tuple[Method, ...]:
        return tuple(
            EVMContract.Method(
                msig=method_sig_from_abi(method_abi, True),
                id=0,
                abi=method_abi,
                ast=None,
                contract_name_with_path=self.name_with_path,
                contract_digest='',
                contract_storage_digest='',
                sort=KSort(f'{EVMContract.escaped(self.name_with_path, "S2K")}Method'),
                devdoc=None,
                function_calls=None,
            )
            for method_abi in self.abi
            if method_abi['type'] == 'function'
        )

    @cached_property
    def deployed_bytecode(self) -> bytes:
        wasm_file_name = self._name.replace('-', '_') + '.wasm'
        wasm_path = Path(self.manifest['target_directory']) / 'wasm32-unknown-unknown' / 'release' / wasm_file_name
        return wasm_path.read_bytes()


ArbitrumContract: TypeAlias = EVMContract | StylusContract


def setup_method(c: ArbitrumContract) -> Method | None:
    for m in c.methods:
        if m.name == 'setUp':
            return m
    return None


def is_foundry_test(ctr: EVMContract) -> bool:
    if ctr.is_test_contract:
        for m in ctr.methods:
            if m.is_test:
                return True
    return False


def argument_strategy(m: Method) -> SearchStrategy[bytes]:
    input_strategies = (get_abi_strategy(arg) for arg in m.arg_types)
    tuple_strategy = strategies.tuples(*input_strategies)
    encoder = partial(call_data, m.name, m.arg_types)
    return tuple_strategy.map(encoder)
