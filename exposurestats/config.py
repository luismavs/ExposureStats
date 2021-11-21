from dataclasses import dataclass, field
from typing import List, Dict, Union
import yaml
from pathlib import Path

##TODO : remove unwanted photos


@dataclass
class Config:

    DEFAULT_PATH: str

    FIELDS_TO_READ: dict = field(
        default_factory=lambda: {
            "CreateDate": "@xmp:CreateDate",
            "FocalLength": "@exif:FocalLength",
            "FNumber": "@exif:FNumber",
            "Camera": "@tiff:Model",
            "Lens": "@alienexposure:lens",
            "Flag": "@alienexposure:pickflag",
        }
    )

    FIELDS_TO_PROCESS: dict = field(default_factory=lambda: {"Lens": "strip"})

    FILE_TYPE: List[str] = field(default_factory=lambda: ["exposurex6", "exposurex7"])
    PATH_IN_XML: List[str] = field(default_factory=lambda: ["x:xmpmeta", "rdf:RDF", "rdf:Description"])
    DIRS_TO_AVOID: List[str] = field(default_factory=lambda: ["recycling"])

    # FILTERS = {'remove__rejected' = {'alienexposure:pickflag' : 2}}
    DROP_FILTERS: Dict[str, list] = field(default_factory=lambda: {"Flag": [2]})

    def __post_init__(self):
        self.DEFAULT_PATH = Path(self.DEFAULT_PATH)


def get_config(path_to_yaml: Union[Path, str]):

    with open(path_to_yaml, "r") as f:
        cfg = yaml.safe_load(f)

    return Config(**cfg)
