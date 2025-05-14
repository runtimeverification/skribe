from __future__ import annotations

import sys
from argparse import ArgumentParser
from pathlib import Path

from pyk.cli.utils import ensure_dir_path


def _exec_build(dir_path: Path | None) -> None:
    """
    Builds the contract located in the specified directory.

    If `dir_path` is None, the build is executed in the current working directory (CWD).

    Args:
        dir_path (Path | None): Path to the directory containing the contract source.
                                If None, defaults to the current working directory.

    Returns:
        None
    """
    dir_path = Path.cwd() if dir_path is None else dir_path

    exit(0)


def _exec_run(dir_path: Path | None, id: str | None, max_examples: int) -> None:
    """
    Executes fuzz tests for the Skribe test contract located at the given path.

    If `id` is specified, only the test function with that name is executed.
    Otherwise, all available test functions are fuzzed.

    Args:
        dir_path (Path | None): Path to the Skribe test contract directory.
                                If None, defaults to the current working directory.
        id (str | None): Name of the test function to run. If None, runs all tests.
        max_examples (int): Maximum number of fuzzing examples to run per test.

    Returns:
        None
    """
    dir_path = Path.cwd() if dir_path is None else dir_path

    exit(0)


def _argument_parser() -> ArgumentParser:
    parser = ArgumentParser(prog='skribe')
    command_parser = parser.add_subparsers(dest='command', required=True)

    build_parser = command_parser.add_parser('build', help='build the test contract')
    build_parser.add_argument(
        '--directory',
        '-C',
        type=ensure_dir_path,
        default=None,
        help="The test contract\'s directory (defaults to the current working directory).",
    )

    run_parser = command_parser.add_parser('run', help='run tests with fuzzing')
    run_parser.add_argument(
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
        _exec_run(dir_path=args.directory, id=args.id, max_examples=args.max_examples)
    elif args.command == 'build':
        _exec_build(dir_path=args.directory)

    raise RuntimeError(f'Command not implemented: {args.command}')
