from pathlib import Path

import yaml

from exposurestats.config import Config
from exposurestats.data_source import DataSource
import os
from dotenv import load_dotenv


load_dotenv()


def _test_build_library():
    """Running this test may delete orphaned sidecars!"""
    cfg = Config.from_env()
    ds = DataSource(cfg)
    ds.build_exposure_library()

    assert True


def test_read_one_sidecar():
    """Reading an orphaned sidecar, so it may be autodeleted!"""
    cfg = Config.from_env()
    load_dotenv()
    file_path = Path(".") / "tests" / "data" / "P9220262dxoap.jpg.exposurex7"

    ds = DataSource(cfg)
    ds.read_one_sidecar(file_path)

    assert True


if __name__ == "__main__":
    test_read_one_sidecar()

    test_build_library()
