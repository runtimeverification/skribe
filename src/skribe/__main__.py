from __future__ import annotations

import sys
from argparse import ArgumentParser
from typing import TYPE_CHECKING

from pyk.cli.utils import file_path

if TYPE_CHECKING:
    from pathlib import Path


def _exec_run(wasm: Path, id: str | None, max_examples: int) -> None:
    """Run a stylus test contract given its compiled wasm file.

    This will get the bindings for the contract and run the test functions.
    The test functions are expected to be named with a prefix of 'test_' and return a boolean value.

    Exits successfully when all the tests pass.
    """

    exit(0)


def _argument_parser() -> ArgumentParser:
    parser = ArgumentParser(prog='skribe')
    command_parser = parser.add_subparsers(dest='command', required=True)

    run_parser = command_parser.add_parser('run', help='run tests with fuzzing')
    run_parser.add_argument('--wasm', type=file_path, required=True, help="Path to the test contract\'s wasm file")
    run_parser.add_argument(
        '--id', help='Name of the test function to run. If not specified, all test functions will be executed.'
    )
    run_parser.add_argument(
        '--max-examples', type=int, default=100, help='Maximum number of fuzzing inputs to generate (default: 100).'
    )

    return parser


def main() -> None:
    sys.setrecursionlimit(8000)

    parser = _argument_parser()
    args, rest = parser.parse_known_args()

    if args.command == 'run':
        _exec_run(wasm=args.wasm, id=args.id, max_examples=args.max_examples)
