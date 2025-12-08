import sys
from pathlib import Path

import pytest
from pyk.kdist import kdist
from pyk.ktool.krun import _krun

from skribe import simulation
from skribe.skribe import Skribe
from skribe.utils import RECURSION_LIMIT, concrete_definition

sys.setrecursionlimit(RECURSION_LIMIT)

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


BUILD_AND_FUZZ_TEST_FAIL = {
    'test-foundry-simple': {
        'AssertTest.test_failing_branch',
        'AssertTest.test_assert_false',
        'AssertTest.checkFail_assert_false',
        'AssertTest.test_revert_branch',
        'AssumeTest.testFail_assume_true',
        'AssumeTest.test_assume_false',
    }
}


@pytest.mark.parametrize('contract_dir', TEST_CONTRACT_DIRS, ids=lambda p: p.name)
def test_build_and_fuzz(contract_dir: Path) -> None:

    skribe = Skribe(concrete_definition, contract_dir)

    skribe.build_contract()

    errors = skribe.deploy_and_run(100)

    if contract_dir.name in BUILD_AND_FUZZ_TEST_FAIL:
        assert BUILD_AND_FUZZ_TEST_FAIL[contract_dir.name] == {e.description for e in errors}
    else:
        assert not errors
