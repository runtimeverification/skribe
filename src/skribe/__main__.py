from __future__ import annotations

import json
import sys
from argparse import ArgumentParser
from pathlib import Path

from pyk.cli.utils import ensure_dir_path
from pyk.utils import abs_or_rel_to
from rich.console import Console

from .skribe import InitializationError, Skribe
from .utils import concrete_definition


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

    skribe = Skribe(concrete_definition)

    if (dir_path / 'foundry.toml').exists():
        skribe.build_foundry_contract(contract_dir=dir_path)
    else:
        skribe.build_stylus_contract(contract_dir=dir_path)

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

    skribe = Skribe(concrete_definition)

    child_wasms = _read_config_file(skribe, dir_path)

    try:
        failed = skribe.deploy_and_run(contract_dir=dir_path, child_wasms=child_wasms, id=id, max_examples=max_examples)
    except InitializationError:
        err_console.print('[bold red]Initialization failed[/bold red]')
        exit(1)

    if not failed:
        exit(0)

    err_console.print(f'[bold red]{len(failed)}[/bold red] test(s) failed:')

    for err in failed:
        err_console.print(f'  {err.test_name} {err.counterexample}')

    exit(1)


def _read_config_file(skribe: Skribe, dir_path: Path | None = None) -> tuple[Path, ...]:
    dir_path = Path.cwd() if dir_path is None else dir_path
    config_path = dir_path / 'skribe.json'

    def get_wasm_path(c: Path) -> Path:
        c = abs_or_rel_to(c, dir_path)
        assert c.is_file() and c.suffix == '.wasm'
        return c

    if config_path.is_file():
        with open(config_path) as f:
            config = json.load(f)
            return tuple(get_wasm_path(Path(c)) for c in config['contracts'])

    return ()


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
