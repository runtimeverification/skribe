from __future__ import annotations

import json
import sys
from argparse import ArgumentParser
from pathlib import Path

from pyk.cli.utils import ensure_dir_path
from rich.console import Console

from .skribe import InitializationError, Skribe
from .utils import RECURSION_LIMIT, concrete_definition


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

    skribe = Skribe(concrete_definition, dir_path)

    skribe.build_contract()

    exit(0)


def _exec_export_specs(dir_path: Path | None) -> None:
    """
    Exports the fuzzer specifications for the contracts located in the specified directory.

    If `dir_path` is None, the export is executed in the current working directory (CWD).

    Args:
        dir_path (Path | None): Path to the directory containing the contract sources.
                                If None, defaults to the current working directory.

    Returns:
        None
    """
    dir_path = Path.cwd() if dir_path is None else dir_path
    skribe = Skribe(concrete_definition, dir_path)
    specs = skribe.export_specs()
    print(json.dumps([spec.dict for spec in specs]))
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
    err_console = Console(stderr=True)

    dir_path = Path.cwd() if dir_path is None else dir_path

    skribe = Skribe(concrete_definition, dir_path)

    try:
        failed = skribe.deploy_and_run(id=id, max_examples=max_examples)
    except InitializationError:
        err_console.print('[bold red]Initialization failed[/bold red]')
        exit(1)

    if not failed:
        exit(0)

    err_console.print(f'[bold red]{len(failed)}[/bold red] test(s) failed:')

    for err in failed:
        err_console.print(f'  {err.description} {err.counterexample}')

    exit(1)


def _argument_parser() -> ArgumentParser:
    parser = ArgumentParser(prog='skribe')
    parser.add_argument(
        '--directory',
        '-C',
        type=ensure_dir_path,
        default=None,
        help="The test contract\'s directory (defaults to the current working directory).",
    )

    command_parser = parser.add_subparsers(dest='command', required=True)

    command_parser.add_parser('build', help='build the test contract')
    command_parser.add_parser('export-specs', help='print the fuzzer specifications')

    run_parser = command_parser.add_parser('run', help='run tests with fuzzing')
    run_parser.add_argument(
        '--id', help='Name of the test function to run. If not specified, all test functions will be executed.'
    )
    run_parser.add_argument(
        '--max-examples', type=int, default=100, help='Maximum number of fuzzing inputs to generate (default: 100).'
    )

    return parser


def main() -> None:
    sys.setrecursionlimit(RECURSION_LIMIT)

    parser = _argument_parser()
    args, rest = parser.parse_known_args()

    match args.command:
        case 'run':
            _exec_run(dir_path=args.directory, id=args.id, max_examples=args.max_examples)
        case 'build':
            _exec_build(dir_path=args.directory)
        case 'export-specs':
            _exec_export_specs(dir_path=args.directory)

    raise RuntimeError(f'Command not implemented: {args.command}')
