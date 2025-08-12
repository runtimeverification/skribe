import sys
from pathlib import Path

import pytest
from pyk.kdist import kdist
from pyk.ktool.krun import _krun

from skribe import simulation
from skribe.__main__ import _read_config_file
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
        cmap=simulation.config_vars(),
        pmap=simulation.CONFIG_VAR_PARSERS,
        no_expand_macros=True,
    )


@pytest.mark.parametrize('test_file', SIMULATION_FILES, ids=str)
def test_simulation(test_file: Path) -> None:
    simulation.run(test_file, depth=None).check_returncode()


@pytest.mark.parametrize('contract_dir', TEST_CONTRACT_DIRS, ids=str)
def test_build_and_fuzz(contract_dir: Path) -> None:

    skribe = Skribe(concrete_definition)

    if (contract_dir / 'foundry.toml').exists():
        skribe.build_foundry_contract(contract_dir=contract_dir)
    else:
        skribe.build_stylus_contract(contract_dir=contract_dir)

    child_wasms = _read_config_file(skribe, contract_dir)
    errors = skribe.deploy_and_run(contract_dir, child_wasms, 100)
    assert not errors
