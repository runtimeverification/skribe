from __future__ import annotations

import json
import sys
from argparse import ArgumentParser
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING

from eth_abi import encode
from eth_utils import function_signature_to_4byte_selector
from pyk.cli.utils import file_path
from pyk.kast.inner import KSort
from pyk.kast.prelude.bytes import bytesToken
from pyk.ktool.kprint import KAstOutput, _kast
from pyk.utils import abs_or_rel_to

from skribe.kast.syntax import call_stylus, check_output, set_exit_code, set_stylus_contract, steps_of

from .utils import concrete_definition, load_wasm

if TYPE_CHECKING:
    from collections.abc import Iterable
    from subprocess import CompletedProcess
    from typing import Any

    from pyk.kast.inner import KInner


def call_data(function: str, types: Iterable[str], args: Iterable[Any]) -> bytes:
    arg_types = ','.join(types)
    signature = f'{function}({arg_types})'
    selector = function_signature_to_4byte_selector(signature)

    encoded_args = encode(types=types, args=args)

    return selector + encoded_args


def call_data_from_dict(d: dict[str, Any]) -> bytes:
    return call_data(
        function=d['function'],
        types=d['types'],
        args=d['args'],
    )


def run(test_file: Path, depth: int | None) -> CompletedProcess:
    test = json.loads(test_file.read_text())

    steps_dict = test['steps']

    kast_steps = (step for item in steps_dict for step in steps_from_dict(item, test_file))
    program = steps_of(kast_steps)

    return concrete_definition.krun_with_kast(pgm=program, sort=KSort('Steps'), depth=depth)


def steps_from_dict(d: dict[str, Any], file_path: Path) -> list[KInner]:
    step_type = d['type']

    match step_type:
        case 'setExitCode':
            return [set_exit_code(int(d['value']))]
        case 'setStylusContract':
            wasm_path = abs_or_rel_to(Path(d['code']), file_path.parent)
            return [set_stylus_contract(id=int(d['id']), code=load_wasm(wasm_path), storage=d.get('storage', {}))]
        case 'callStylus':

            call_cmd = call_stylus(
                from_account=d.get('from', None),
                to_account=d.get('to', None),
                data=bytesToken(call_data_from_dict(d['data'])),
                value=int(d.get('value', 0)),
            )

            if 'output' not in d:
                return [call_cmd]

            output = d['output']
            expected_output = encode([output['type']], [output['value']])

            return [call_cmd, check_output(expected_output)]

    raise ValueError(f'Invalid step type: {step_type}')


def _exec_run(test_file: Path, output: KAstOutput, depth: int | None) -> None:
    res = run(test_file, depth)

    if output == KAstOutput.KORE:
        _exit_with_output(res)

    with NamedTemporaryFile() as f:
        tmp_file = Path(f.name)
        tmp_file.write_text(res.stdout)

        kast_res = _kast(tmp_file, definition_dir=concrete_definition.path, input='kore', output=output)

        if kast_res.returncode:
            _exit_with_output(kast_res)

        print(kast_res.stdout)

        if res.returncode:
            print(res.stderr, end='', file=sys.stderr, flush=True)
        sys.exit(res.returncode)


def main() -> None:
    sys.setrecursionlimit(8000)

    parser = _argument_parser()
    args, rest = parser.parse_known_args()

    if args.command == 'run':
        _exec_run(test_file=args.program, output=args.output, depth=args.depth)


def _argument_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog='skribe-simulation',
        description='A CLI tool for simulating Stylus smart contract executions using formal semantics.',
    )
    command_parser = parser.add_subparsers(dest='command', required=True)

    run_parser = command_parser.add_parser('run', help='run a concrete test')
    run_parser.add_argument(
        'program',
        metavar='PROGRAM',
        type=file_path,
        help='Path to a JSON file describing the test case as a sequence of simulation steps',
    )
    run_parser.add_argument(
        '--output',
        metavar='FORMAT',
        type=KAstOutput,
        default=KAstOutput.KORE,
        help='Output format for the final state (default: kore)',
    )
    run_parser.add_argument('--depth', type=int, help='Maximum number of execution (K) steps to simulate')

    return parser


def _exit_with_output(cp: CompletedProcess) -> None:
    print(cp.stdout, end='', flush=True)
    status = cp.returncode
    if status:
        print(cp.stderr, end='', file=sys.stderr, flush=True)
    sys.exit(status)
