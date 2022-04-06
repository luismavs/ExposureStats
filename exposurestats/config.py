from dataclasses import dataclass, field
from typing import List, Dict, Union
import yaml
from pathlib import Path

##TODO : remove unwanted photos


@dataclass
class Config:

    # data reading

    DEFAULT_PATH: str

    current_version: str = "exposurex7"
    # if True, issues a breakpoint when there appears to be duplicate image files
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

    FILE_TYPE: List[str] = field(default_factory=lambda: ["exposurex6", "exposurex7"])
    PATH_IN_XML: List[str] = field(default_factory=lambda: ["x:xmpmeta", "rdf:RDF", "rdf:Description"])
    DIRS_TO_AVOID: List[str] = field(default_factory=lambda: ["recycling"])

    # FILTERS = {'remove__rejected' = {'alienexposure:pickflag' : 2}}
    DROP_FILTERS: Dict[str, list] = field(default_factory=lambda: {"Flag": [2]})

    # ------------------------------------------------------
    # operational

    delete_dangling_sidecars: bool = True

    def __post_init__(self):
        self.DEFAULT_PATH = Path(self.DEFAULT_PATH)

    def __repr__(self) -> str:
        str_ = ""
        for attr_ in dir(self):
            if attr_.startswith("_") is False:
                str_ += f"{attr_}: {getattr(self, attr_)}\n"
        return str_


def get_config(path_to_yaml: Union[Path, str]):

    with open(path_to_yaml, "r") as f:
        cfg = yaml.safe_load(f)

    del cfg["test_image"]

    return Config(**cfg)
