import shutil
from pathlib import Path
from typing import Generator

import pytest
import requests

from readimc import MCDFile, TXTFile

_imc_test_data_asset_url = (
    "https://github.com/BodenmillerGroup/TestData"
    "/releases/download/v1.0.7/210308_ImcTestData_raw.tar.gz"
)
_imc_test_data_raw_dir = "datasets/210308_ImcTestData/raw"
_imc_test_data_mcd_file = "20210305_NE_mockData1/20210305_NE_mockData1.mcd"
_imc_test_data_txt_file = "20210305_NE_mockData1/20210305_NE_mockData1_ROI_001_1.txt"


def _download_and_extract_asset(tmp_dir_path: Path, asset_url: str):
    asset_file_path = tmp_dir_path / "asset.tar.gz"
    response = requests.get(asset_url, stream=True)
    if response.status_code == 200:
        with asset_file_path.open(mode="wb") as f:
            f.write(response.raw.read())
    shutil.unpack_archive(asset_file_path, tmp_dir_path)


@pytest.fixture(scope="session")
def imc_test_data_raw_path(tmp_path_factory) -> Generator[Path, None, None]:
    tmp_dir_path = tmp_path_factory.mktemp("raw")
    _download_and_extract_asset(tmp_dir_path, _imc_test_data_asset_url)
    yield tmp_dir_path / Path(_imc_test_data_raw_dir)
    shutil.rmtree(tmp_dir_path)


@pytest.fixture
def imc_test_data_mcd_file(
    imc_test_data_raw_path: Path,
) -> Generator[MCDFile, None, None]:
    path = imc_test_data_raw_path / Path(_imc_test_data_mcd_file)
    with MCDFile(path) as f:
        yield f


@pytest.fixture
def imc_test_data_txt_file(
    imc_test_data_raw_path: Path,
) -> Generator[TXTFile, None, None]:
    path = imc_test_data_raw_path / Path(_imc_test_data_txt_file)
    with TXTFile(path) as f:
        yield f
