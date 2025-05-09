from __future__ import annotations

import sys
from argparse import ArgumentParser
from typing import TYPE_CHECKING

from pyk.cli.utils import file_path, ensure_dir_path

from .skribe import Skribe
from .utils import concrete_definition
if TYPE_CHECKING:
    from pathlib import Path


def _exec_build(dir_path: Path | None) -> None:
    """Build the test contract in the specified directory. If not specified, defaults to CWD
    """
    dir_path = Path.cwd() if dir_path is None else dir_path

    skribe = Skribe(concrete_definition)
    skribe.build_stylus_contract(contract_dir=dir_path)

    exit(0)


def _exec_run(dir_path: Path, id: str | None, max_examples: int) -> None:
    """Run a stylus test contract given its compiled wasm file.

    Exits successfully when all the tests pass.
    """
    dir_path = Path.cwd() if dir_path is None else dir_path

    skribe = Skribe(concrete_definition)
    skribe.deploy_and_run()

    exit(0)


def _argument_parser() -> ArgumentParser:
    parser = ArgumentParser(prog='skribe')
    command_parser = parser.add_subparsers(dest='command', required=True)

    build_parser = command_parser.add_parser('build', help='build the test contract')
    build_parser.parser.add_argument(
        '--directory',
        '-C',
        type=ensure_dir_path,
        default=None,
        help="The test contract\'s directory (defaults to the current working directory).",
    )

    run_parser = command_parser.add_parser('run', help='run tests with fuzzing')
    run_parser.parser.add_argument(
        '--directory',
        '-C',
        type=ensure_dir_path,
        default=None,
        help="The test contract\'s directory (defaults to the current working directory).",
    )
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
