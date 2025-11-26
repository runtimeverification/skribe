from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from kevm_pyk.kompile import KompileTarget, kevm_kompile
from kontrol.kdist.utils import KSRC_DIR as FOUNDRY_KSRC_DIR
from pyk.kbuild.utils import k_version
from pyk.kdist.api import Target

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from typing import Any, Final


class SourceTarget(Target):
    SRC_DIR: Final = Path(__file__).parent

    def build(self, output_dir: Path, deps: dict[str, Path], args: dict[str, Any], verbose: bool) -> None:
        shutil.copytree(deps['wasm-semantics.source'] / 'wasm-semantics', output_dir / 'wasm-semantics')
        shutil.copytree(self.SRC_DIR / 'stylus-semantics', output_dir / 'stylus-semantics')

    def source(self) -> tuple[Path, ...]:
        return (self.SRC_DIR,)

    def deps(self) -> tuple[str]:
        return ('wasm-semantics.source',)


# TODO use kevm_pyk.kdist.plugin.KEVMTarget
class SkribeTarget(Target):
    _kompile_args: Callable[[Path], Mapping[str, Any]]

    def __init__(self, kompile_args: Callable[[Path], Mapping[str, Any]]):
        self._kompile_args = kompile_args

    def build(self, output_dir: Path, deps: dict[str, Path], args: dict[str, Any], verbose: bool) -> None:
        kompile_args = self._kompile_args(deps['stylus-semantics.source'])
        enable_llvm_debug = bool(args.get('enable-llvm-debug', ''))
        debug_build = bool(args.get('debug-build', ''))
        ccopts = [ccopt for ccopt in args.get('ccopts', '').split(' ') if ccopt]

        kevm_kompile(
            output_dir=output_dir,
            enable_llvm_debug=enable_llvm_debug,
            verbose=verbose,
            ccopts=ccopts,
            plugin_dir=deps['evm-semantics.plugin'],
            debug_build=debug_build,
            **kompile_args,
        )

    def deps(self) -> tuple[str, ...]:
        return (
            'evm-semantics.plugin',
            'stylus-semantics.source',
        )

    # TODO
    # def source(self) -> tuple[Path, ...]:
    #     ...

    def context(self) -> dict[str, str]:
        return {'k-version': k_version().text}


__TARGETS__: Final = {
    'source': SourceTarget(),
    'llvm': SkribeTarget(
        lambda src_dir: {
            'target': KompileTarget.LLVM,
            'main_file': src_dir / 'stylus-semantics/skribe.md',
            'main_module': 'SKRIBE',
            'syntax_module': 'SKRIBE-SYNTAX',
            'includes': [src_dir, FOUNDRY_KSRC_DIR],
        },
    ),
}
