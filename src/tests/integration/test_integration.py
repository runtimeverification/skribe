import sys
from pathlib import Path

import pytest
from pyk.kdist import kdist
from pyk.ktool.krun import _krun

from skribe import simulation
from skribe.skribe import Skribe
from skribe.utils import concrete_definition

sys.setrecursionlimit(8000)

DATA_DIR = Path(__file__).parent / 'data'

TEST_WAST_DATA = (DATA_DIR / 'wast').resolve(strict=True)
TEST_WAST_FILES = TEST_WAST_DATA.glob('*.wast')

SIMULATION_DIR = (DATA_DIR / 'simulation').resolve(strict=True)
SIMULATION_FILES = SIMULATION_DIR.glob('*.json')

DEFINITION_DIR = kdist.get('stylus-semantics.llvm')

CONTRACTS_DIR = DATA_DIR / 'contracts'
TEST_CONTRACT_DIRS = CONTRACTS_DIR.glob('test*')


@pytest.mark.parametrize('program', TEST_WAST_FILES, ids=str)
def test_run_wast(program: Path, tmp_path: Path) -> None:
    _krun(
        input_file=program,
        definition_dir=DEFINITION_DIR,
        check=True,
    )


@pytest.mark.parametrize('test_file', SIMULATION_FILES, ids=str)
def test_simulation(test_file: Path) -> None:
    simulation.run(test_file, depth=None)


@pytest.mark.parametrize('contract_dir', TEST_CONTRACT_DIRS, ids=str)
def test_build(contract_dir: Path) -> None:

    skribe = Skribe(concrete_definition)
    skribe.build_stylus_contract(contract_dir=contract_dir)
