from __future__ import annotations

import shutil
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from pyk.utils import run_process

if TYPE_CHECKING:
    from .utils import SkribeDefinition


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
