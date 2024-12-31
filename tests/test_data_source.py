from unittest.mock import Mock, mock_open, patch

import pandas as pd
import pytest

from exposurestats.config import Config
from exposurestats.data_source import DataSource


@pytest.fixture
def mock_config():
    cfg = Mock(spec=Config)
    cfg.FIELDS_TO_READ = {
        "CreateDate": "xmp:CreateDate",
        "Camera": "tiff:Model",
        "Lens": "exifEX:LensModel",
        "FocalLength": "exif:FocalLength",
        "FNumber": "exif:FNumber",
        "Keywords": "dc:subject",
        "Flag": "xmp:Label",
    }
    cfg.FILE_TYPE = [".exposurex6", ".exposurex7"]
    cfg.current_version = "exposurex7"
    cfg.DEFAULT_PATH = "/test/path"
    cfg.DIRS_TO_AVOID = ["incoming", "recycling"]
    cfg.DROP_FILTERS = {}
    cfg.FIELDS_TO_PROCESS = {"Lens": "strip"}
    return cfg


@pytest.fixture
def data_source(mock_config):
    return DataSource(mock_config)


def test_init(data_source):
    assert data_source.dangling_sidecars == 0
    assert data_source.unloaded_sidecars == 0
    assert data_source.recognised_versions == ["exposurex6", "exposurex7"]


def test_extract_keywords(data_source):
    # Test with valid keywords
    test_data = {"rdf:Bag": {"rdf:li": ["kywd:||nature|", "kywd:||landscape|"]}}
    result = data_source._extract_keywords(test_data)
    assert result == ["nature", "landscape"]

    # Test with single keyword
    test_data = {"rdf:Bag": {"rdf:li": "kywd:||nature|"}}
    result = data_source._extract_keywords(test_data)
    assert result == ["nature"]

    # Test with empty/invalid data
    assert data_source._extract_keywords({}) == []
    assert data_source._extract_keywords(None) == []


def test_file_has_extension(data_source):
    assert data_source._file_has_extension("test.exposurex6", [".exposurex6", ".exposurex7"])
    assert data_source._file_has_extension("test.exposurex7", [".exposurex6", ".exposurex7"])
    assert not data_source._file_has_extension("test.jpg", [".exposurex6", ".exposurex7"])


@pytest.fixture
def mock_sidecar_data():
    return {
        "x:xmpmeta": {
            "rdf:RDF": {
                "rdf:Description": {
                    "xmp:CreateDate": "2024-01-01",
                    "tiff:Model": "Test Camera",
                    "exifEX:LensModel": "Test Lens",
                    "exif:FocalLength": "50/1",
                    "exif:FNumber": "1.8/1",
                    "dc:subject": {"rdf:Bag": {"rdf:li": ["kywd:||test|"]}},
                    "xmp:Label": "1",
                }
            }
        }
    }


@patch("builtins.open", new_callable=mock_open)
@patch("xmltodict.parse")
def test_read_one_sidecar(mock_parse, mock_file, data_source, mock_sidecar_data):
    mock_parse.return_value = mock_sidecar_data
    result = data_source.read_one_sidecar("test.exposurex7")

    assert result["Camera"] == "Test Camera"
    assert result["Lens"] == "Test Lens"
    assert result["Keywords"] == ["test"]


def test_sidecars_to_dataframe(data_source):
    test_sidecars = [
        {
            "CreateDate": "2024-01-01",
            "Camera": "Test Camera",
            "Lens": "Test Lens",
            "FocalLength": "50/1",
            "FNumber": "1.8/1",
            "Keywords": ["test"],
            "Flag": "1",
            "name": "test1",
        }
    ]

    df = data_source._sidecars_to_dataframe(test_sidecars)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["Camera"] == "Test Camera"
    assert df.iloc[0]["FocalLength"] == 50
    assert df.iloc[0]["FNumber"] == 1.8
