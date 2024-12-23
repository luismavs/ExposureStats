from pathlib import Path

import yaml

from exposurestats.config import Config
from exposurestats.data_source import DataSource
import os
from dotenv import load_dotenv


load_dotenv()


def test_build_library():
    cfg = Config.from_env()

    ds = DataSource(cfg)
    ds.build_exposure_library()

    assert True


def test_read_one_sidecar():
    cfg = Config.from_env()

    load_dotenv()
    file_path = Path(".") / "tests" / "data" / "P9220262dxoap.jpg.exposurex7"

    ds = DataSource(cfg)
    ds.read_one_sidecar(file_path)

    assert True


if __name__ == "__main__":
    test_read_one_sidecar()

    test_build_library()
