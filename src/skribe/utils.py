from __future__ import annotations

from functools import cached_property
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

from eth_abi import decode, encode
from pyk.kast.inner import KSort, KToken
from pyk.kast.outer import read_kast_definition
from pyk.kast.prelude.bytes import bytesToken, pretty_bytes
from pyk.kast.prelude.string import pretty_string
from pyk.kdist import kdist
from pyk.konvert import kast_to_kore, kore_to_kast
from pyk.kore.manip import substitute_vars
from pyk.kore.parser import KoreParser
from pyk.kore.syntax import App
from pyk.ktool.kompile import DefinitionInfo
from pyk.ktool.kprove import KProve
from pyk.ktool.krun import KRun
from pyk.utils import abs_or_rel_to
from pykwasm.wasm2kast import wasm2kast

from skribe.kast.syntax import pyk_hook_result

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from subprocess import CompletedProcess
    from typing import Any, Final

    from pyk.kast.inner import KInner
    from pyk.kast.outer import KDefinition
    from pyk.kore.syntax import EVar, Pattern
    from pyk.ktool.kompile import KompileBackend


EXIT_CODE_PYK_HOOK: Final = 2


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
        res = self.krun.run_process(kore_term, expand_macros=False, **kwargs)
        return res

    def krun_with_kast_with_pyk_hooks(
        self, pgm: KInner, hooks: PykHooks, sort: KSort | None = None, **kwargs: Any
    ) -> CompletedProcess:
        proc_res = self.krun_with_kast(pgm, sort, **kwargs)
        if proc_res.returncode != EXIT_CODE_PYK_HOOK:
            return proc_res

        kore_term = KoreParser(proc_res.stdout).pattern()

        kwargs['pmap'] = None
        kwargs['cmap'] = None
        return self.krun_term_with_pyk_hooks(kore_term, hooks, **kwargs)

    def krun_term_with_pyk_hooks(self, kore_term: Pattern, hooks: PykHooks, **kwargs: Any) -> CompletedProcess:

        apply_hooks_k_cell = update_nested([0, 1, 0, 0], lambda pat: hooks(pat, self.kdefinition))
        while True:
            kore_term = apply_hooks_k_cell(kore_term)
            proc_res = self.krun.run_process(kore_term, term=True, expand_macros=False, **kwargs)
            if proc_res.returncode != EXIT_CODE_PYK_HOOK:
                return proc_res

            kore_term = KoreParser(proc_res.stdout).pattern()


class PykHooks:

    project_root: Path

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def __call__(self, kore_term: Pattern, definition: KDefinition) -> Pattern:
        def apply_func(pat: Pattern) -> Pattern:
            if isinstance(pat, App) and pat.symbol == "Lblskribe'Stop'pykHook":
                func_sig = kore_to_kast(definition, pat.args[0])
                args = kore_to_kast(definition, pat.args[1])

                assert isinstance(func_sig, KToken)
                func_sig_str = pretty_string(func_sig)
                result: KInner
                match func_sig_str:
                    case 'readFile(string)':
                        assert isinstance(args, KToken)
                        decoded_args = decode(types=('string',), data=pretty_bytes(args))
                        file_path = abs_or_rel_to(Path(decoded_args[0]), self.project_root)
                        txt_content = file_path.read_text()
                        abi_encoded_content = encode(types=('string',), args=(txt_content,))
                        result = bytesToken(abi_encoded_content)
                    case 'readFileBinary(string)':
                        assert isinstance(args, KToken)
                        decoded_args = decode(types=('string',), data=pretty_bytes(args))
                        file_path = abs_or_rel_to(Path(decoded_args[0]), self.project_root)
                        bin_content = file_path.read_bytes()
                        abi_encoded_content = encode(types=('bytes',), args=(bin_content,))
                        result = bytesToken(abi_encoded_content)
                    case 'parseWasmBytecode(KBytes)':
                        assert isinstance(args, KToken)
                        bytecode = pretty_bytes(args)
                        result = wasm2kast(BytesIO(bytecode))
                    case _:
                        raise ValueError(f'Unknown function {func_sig_str}')

                return kast_to_kore(definition, pyk_hook_result(func_sig_str, result), KSort('KItem'))

            return pat

        return kore_term.bottom_up(apply_func)


concrete_definition = SkribeDefinition(kdist.get('stylus-semantics.llvm'))


def parse_wasm_file(wasm: Path) -> KInner:
    return wasm2kast(open(wasm, 'rb'))


def update_arg(arg_ix: int, f: Callable[[Pattern], Pattern]) -> Callable[[Pattern], Pattern]:
    def res(p: Pattern) -> Pattern:
        match p:
            case App() if len(p.args) > arg_ix:
                y = f(p.args[arg_ix])
                args_ = list(p.args)
                args_[arg_ix] = y
                return App(p.symbol, p.sorts, args_)
        raise ValueError(p)

    return res


def update_nested(path: list[int], f: Callable[[Pattern], Pattern]) -> Callable[[Pattern], Pattern]:
    for ix in reversed(path):
        f = update_arg(ix, f)

    return f


def subst_on_k_cell(template: Pattern, subst: Mapping[EVar, Pattern]) -> Pattern:
    def subst_func(pat: Pattern) -> Pattern:
        assert isinstance(pat, App)
        assert pat.symbol == "Lbl'-LT-'k'-GT-'", pat.symbol
        return substitute_vars(pat, subst)

    return update_nested([0, 1, 0, 0], subst_func)(template)
