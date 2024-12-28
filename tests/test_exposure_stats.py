from pathlib import Path

from exposurestats.config import Config
from exposurestats.data_source import DataSource

# load_dotenv()
# test_cfg = Config.from_env()
test_cfg = Config(DEFAULT_PATH="tests/testdata", delete_dangling_sidecars=False)


def test_build_library():
    ds = DataSource(test_cfg)
    ds.build_exposure_library()

    assert True


def test_read_one_sidecar():
    file_path = Path(".") / "tests" / "testdata" / "P9220262dxoap.jpg.exposurex7"

    ds = DataSource(test_cfg)
    out = ds.read_one_sidecar(file_path)
    assert out == {
        "CreateDate": "2021-09-22T15:08:33",
        "FocalLength": "12/1",
        "FNumber": "28/5",
        "Camera": "E-M5MarkIII",
        "Lens": "OLYMPUS M.12-45mm F4.0",
        "Flag": "0",
        "Keywords": ["irina"],
        "name": "P9220262dxoap.jpg",
    }


if __name__ == "__main__":
    test_read_one_sidecar()

    test_build_library()
