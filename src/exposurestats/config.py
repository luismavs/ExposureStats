import datetime
import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

##TODO : remove unwanted photos


@dataclass
class Config:
    # data reading

    DEFAULT_PATH: str

    current_version: str = "exposurex7"
    # if True, issues a breakpoint if duplicate image files are suspected
    run_for_duplicates: bool = True

    FIELDS_TO_READ: dict = field(
        default_factory=lambda: {
            "CreateDate": "@xmp:CreateDate",
            "FocalLength": "@exif:FocalLength",
            "FNumber": "@exif:FNumber",
            "Camera": "@tiff:Model",
            "Lens": "@alienexposure:lens",
            "Flag": "@alienexposure:pickflag",
            "Keywords": "alienexposure:virtualpaths",
        }
    )

    fields_to_read_alternative: dict = field(
        default_factory=lambda: {
            "CreateDate": "@photoshop:DateCreated",
            "FocalLength": "@exif:FocalLength",
            "FNumber": "@exif:FNumber",
            "Camera": "@tiff:Model",
            "Lens": "@alienexposure:lens",
            "Flag": "@alienexposure:pickflag",
            "Keywords": "alienexposure:virtualpaths",
        }
    )

    fields_to_read_alternative_2: dict = field(
        default_factory=lambda: {
            "CreateDate": "@alienexposure:capture_time",
            "FocalLength": "@exif:FocalLength",
            "FNumber": "@exif:FNumber",
            "Camera": "@tiff:Model",
            "Lens": "@alienexposure:lens",
            "Flag": "@alienexposure:pickflag",
            "Keywords": "alienexposure:virtualpaths",
        }
    )

    FIELDS_TO_PROCESS: dict = field(default_factory=lambda: {"Lens": "strip"})

    FILE_TYPE: list[str] = field(default_factory=lambda: ["exposurex6", "exposurex7"])
    PATH_IN_XML: list[str] = field(default_factory=lambda: ["x:xmpmeta", "rdf:RDF", "rdf:Description"])
    DIRS_TO_AVOID: list[str] = field(default_factory=lambda: ["recycling", "incoming"])

    # FILTERS = {'remove__rejected' = {'alienexposure:pickflag' : 2}}
    DROP_FILTERS: dict[str, list] = field(default_factory=lambda: {"Flag": [2]})

    # operational
    # delete sidecars if the associated image is not found
    delete_dangling_sidecars: bool = True

    DEFAULT_START_DATE: datetime.date = datetime.date(2020, 1, 1)

    def __post_init__(self):
        self.DEFAULT_PATH = Path(self.DEFAULT_PATH)

    def __repr__(self) -> str:
        str_ = ""
        for attr_ in dir(self):
            if attr_.startswith("_") is False:
                str_ += f"{attr_}: {getattr(self, attr_)}\n"
        return str_

    @classmethod
    def from_yaml(cls, path_to_yaml: Path | str):
        with open(path_to_yaml, "r") as f:
            cfg = yaml.safe_load(f)

        del cfg["test_image"]

        return Config(**cfg)

    @classmethod
    def from_env(cls):
        """Read configuration from environment and dot-env files.
        TODO: generalise this
        """
        load_dotenv()

        return Config(DEFAULT_PATH=os.environ.get("DEFAULT_PATH", None))
