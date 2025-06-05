from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from pyk.kast.outer import read_kast_definition
from pyk.kdist import kdist
from pyk.konvert import kast_to_kore
from pyk.kore.manip import substitute_vars
from pyk.kore.prelude import generated_top
from pyk.kore.syntax import App
from pyk.ktool.kompile import DefinitionInfo
from pyk.ktool.kprove import KProve
from pyk.ktool.krun import KRun
from pykwasm.wasm2kast import wasm2kast

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path
    from subprocess import CompletedProcess
    from typing import Any

    from pyk.kast.inner import KInner, KSort
    from pyk.kast.outer import KDefinition
    from pyk.kore.syntax import EVar, Pattern
    from pyk.ktool.kompile import KompileBackend


class SkribeError(RuntimeError): ...


def load_wasm(file_path: Path) -> KInner:
    with file_path.open(mode='rb') as f:
        return wasm2kast(f, str(file_path))


class SkribeDefinition:

    definition_info: DefinitionInfo

    def __init__(self, path: Path) -> None:
        self.definition_info = DefinitionInfo(path)

    @cached_property
    def path(self) -> Path:
        return self.definition_info.path

    @cached_property
    def backend(self) -> KompileBackend:
        return self.definition_info.backend

    @cached_property
    def kdefinition(self) -> KDefinition:
        return read_kast_definition(self.path / 'compiled.json')

    @cached_property
    def krun(self) -> KRun:
        return KRun(self.path)

    @cached_property
    def kprove(self) -> KProve:
        return KProve(self.path)

    def krun_with_kast(self, pgm: KInner, sort: KSort | None = None, **kwargs: Any) -> CompletedProcess:
        """Run the semantics on a kast term.

        Args:
            pgm: The kast term to run
            sort: The target sort of `pgm`. This should normally be `Steps`, but can be `GeneratedTopCell` if kwargs['term'] is True
            kwargs: Any arguments to pass to KRun.run_process

        Returns:
            The CompletedProcess of the interpreter
        """
        kore_term = kast_to_kore(self.kdefinition, pgm, sort=sort)
        return self.krun.run_process(kore_term, **kwargs)


concrete_definition = SkribeDefinition(kdist.get('stylus-semantics.llvm'))


def parse_wasm_file(wasm: Path) -> KInner:
    return wasm2kast(open(wasm, 'rb'))


def subst_on_program_cell(template: Pattern, subst: Mapping[EVar, Pattern]) -> Pattern:
    def skribe_cell(program_cell: Pattern, stylus_cell: Pattern, exit_code_cell: Pattern) -> Pattern:
        return App("Lbl'-LT-'skribe'-GT-'", args=(program_cell, stylus_cell, exit_code_cell))

    match template:
        case App(
            "Lbl'-LT-'generatedTop'-GT-'",
            args=(
                App("Lbl'-LT-'skribe'-GT-'", args=(program_cell, stylus_cell, exit_code_cell)),
                generated_counter_cell,
            ),
        ):
            program_cell_ = substitute_vars(program_cell, subst)
            return generated_top((skribe_cell(program_cell_, stylus_cell, exit_code_cell), generated_counter_cell))

    raise ValueError(template)
