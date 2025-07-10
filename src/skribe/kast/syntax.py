from __future__ import annotations

from typing import TYPE_CHECKING

from pyk.kast.inner import KApply, build_cons
from pyk.kast.prelude.collections import map_of
from pyk.kast.prelude.utils import token

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from pyk.kast.inner import KInner


STEPS_TERMINATOR = KApply('.List{"skribeSteps"}')


def steps_of(steps: Iterable[KInner]) -> KInner:
    return build_cons(STEPS_TERMINATOR, 'skribeSteps', steps)


def set_exit_code(i: int) -> KInner:
    return KApply('setExitCode', [token(i)])


def new_account(id: int) -> KInner:
    return KApply('newAccount', [token(id)])


def set_balance(id: int, value: int) -> KInner:
    return KApply('setBalance', [token(id), token(value)])


def set_contract(id: int, code: KInner, storage: Mapping[int, int]) -> KInner:
    # TODO fix type error
    #       Argument 1 to "map_of" has incompatible type "dict[KToken, KToken]";
    #       expected "dict[KInner, KInner] | Iterable[tuple[KInner, KInner]]"  [arg-type]
    storage_kast = map_of({token(k): token(v) for k, v in storage.items()})  # type: ignore
    return KApply('setContract', [token(id), code, storage_kast])


def account(id: int | None) -> KInner:
    return token(id) if id is not None else KApply('.Account')


def call_stylus(from_account: int | None, to_account: int | None, data: KInner, value: int) -> KInner:
    """Constructs a KApply term for the 'callStylus' operation. `data` is a KInner instead of 'bytes' to allow
    passing symbolic or concrete terms (KVariable or KToken) when fuzzing
    """
    return KApply('callStylus', [account(from_account), account(to_account), data, token(value)])


def check_output(bs: bytes) -> KInner:
    return KApply('checkOutput', [token(bs)])
