from pathlib import Path
from exposurestats.data_source import DataSource
from exposurestats.config import Config
import yaml


def test_build_library():
    cfg = Config.from_yaml("./config.yaml")

    ds = DataSource(cfg)
    ds.build_exposure_library()

    assert True


def test_read_one_sidecar():
    cfg = Config.from_yaml("./config.yaml")

    print(cfg)

    #    file_path = Path('/Users/luis/Pictures/Lisboa 2020-/2021/07/31 - Dornes/Exposure Software/Exposure X6/P8011007.JPG.exposurex6')

    with open("./config.yaml", "rt") as f:
        cfg_ = yaml.safe_load(f)

    file_path = Path(cfg_["test_image"])

    ds = DataSource(cfg)
    ds._read_one_sidecar(file_path)

    assert True


if __name__ == "__main__":
    test_read_one_sidecar()

    test_build_library()
