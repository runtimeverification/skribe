from __future__ import annotations

from typing import TYPE_CHECKING

from pyk.kast.inner import KApply, build_cons
from pyk.prelude.utils import token

if TYPE_CHECKING:
    from collections.abc import Iterable

    from pyk.kast.inner import KInner


STEPS_TERMINATOR = KApply('.List{"skribeSteps"}')


def steps_of(steps: Iterable[KInner]) -> KInner:
    return build_cons(STEPS_TERMINATOR, 'skribeSteps', steps)


def set_exit_code(i: int) -> KInner:
    return KApply('setExitCode', [token(i)])


def set_stylus_contract(id: int, code: KInner) -> KInner:
    return KApply('setStylusContract', [token(id), code])


def account(id: int | None) -> KInner:
    return token(id) if id is not None else KApply('.Account')


def call_stylus(from_account: int | None, to_account: int | None, data: bytes, value: int) -> KInner:

    return KApply('callStylus', [account(from_account), account(to_account), token(data), token(value)])
