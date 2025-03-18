from pathlib import Path

import pytest
from pyk.kdist import kdist
from pyk.ktool.krun import _krun

TEST_WAST_DATA = (Path(__file__).parent / 'data' / 'wast').resolve(strict=True)
TEST_WAST_FILES = TEST_WAST_DATA.glob('*.wast')

DEFINITION_DIR = kdist.get('stylus-semantics.llvm')


@pytest.mark.parametrize('program', TEST_WAST_FILES, ids=str)
def test_run_wast(program: Path, tmp_path: Path) -> None:
    _krun(
        input_file=program,
        definition_dir=DEFINITION_DIR,
        check=True,
    )
