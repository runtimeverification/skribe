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

from skribe.simulation import call_data_encoder

if TYPE_CHECKING:
    from hypothesis import SearchStrategy
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

    def contract_bindings(self, contract_dir: Path) -> list[ContractBinding]:
        """Reads a stylus wasm contract, and returns a list of the function bindings for it."""
        proc_res = run_process(
            [str(self._cargo_bin), 'stylus', 'export-abi', '--json'],
            cwd=contract_dir,
            check=True,
        )
        bindings_list = json.loads(proc_res.stdout)

        return [
            ContractBinding.from_dict(binding_dict)
            for binding_dict in bindings_list
            if binding_dict['type'] == 'function'
        ]


@dataclass(frozen=True)
class ContractBinding:
    """Represents one of the function bindings for a stylus contract."""

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
