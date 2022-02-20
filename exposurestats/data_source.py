from pathlib import Path
from tqdm import tqdm
import os
import logging
from typing import Tuple, List, Any
from time import time
import pandas as pd
import xmltodict
from exposurestats.config import Config

logger = logging.getLogger("exposurestats")


class DataSource:
    """Interact with Exposure Data"""

    def __init__(self, cfg: Config):

        self.cfg = cfg

        # monitoring
        self.dangling_sidecars = 0
        self.unloaded_sidecars = 0

    def library_as_df(self):

        df = self._read_dir()

        return df

    def get_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """[summary]

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]: main_data, cameras, lenses, keywords
        """

        t1 = time()

        df = self.library_as_df()
        df["Lens"] = df["Lens"].fillna("No Lens")
        df.loc[df["Lens"].str.len() == 0, "Lens"] = "No Lens"

        cameras = df["Camera"].unique().tolist()
        cameras = sorted(cameras)

        lenses = df["Lens"].unique().tolist()
        lenses = sorted(lenses)

        keywords = df[["name", "Camera", "Lens", "Keywords"]].explode("Keywords")

        t2 = time()

        logger.info(f"It took {round(t2-t1)}s to get the data")

        return df, cameras, lenses, keywords

    def read_one_sidecar(self, file_path: Path):

        with open(file_path, "rb") as f:
            d1 = xmltodict.parse(f)

        d2 = d1["x:xmpmeta"]["rdf:RDF"]["rdf:Description"]

        try:
            d3 = self._extract_data_from_sidecar(self.cfg.FIELDS_TO_READ, d2, file_path)
        except KeyError as e:
            d3 = self._image_exception_handler(d1, file_path, e)

        return d3

    def _image_exception_handler(self, sidecar: dict, file_path: Path, missing_key: str) -> dict:
        """handle execptions when reading image data

        Args:
            cfg (Config): [description]
            sidecar (dict): [description]
            error (Any): [description]

        Returns:
            dict
        """

        e = ""

        # delete the sidecar if the image does not exist
        image_file = file_path.parents[2] / ".".join(file_path.name.split(".")[0:-1])

        if os.path.exists(image_file) is False:
            logger.warning("sidecar xmp has no matching image")
            self.dangling_sidecars += 1
            if self.cfg.delete_dangling_sidecars:
                logger.warning("deleting dangling sidecar")
                os.remove(file_path)
                return {}

        # files created by dxo pure raw + affinity photo have a different structure
        if "CreateDate" in str(missing_key):
            description = sidecar["x:xmpmeta"]["rdf:RDF"]["rdf:Description"]
            try:
                d3 = self._extract_data_from_sidecar(self.cfg.fields_to_read_alternative, description, file_path)
                return d3

            except KeyError as e:
                logger.warning(f"Missing ke: {e}")
                pass

        # do not return anything
        self.unloaded_sidecars += 1
        logger.warning("Could not read data from sidecar")
        logger.warning(f"Missing key: {missing_key}")
        logger.warning(file_path)

        return {}

    def _extract_data_from_sidecar(self, parser: dict, sidecar: dict, file_path: Path):

        d3 = {k: sidecar[v] for k, v in parser.items()}

        for k, v in self.cfg.FIELDS_TO_PROCESS.items():
            if v == "strip":
                d3[k] = str(d3[k]).strip()

        for ft in self.cfg.FILE_TYPE:
            if file_path.name.endswith(ft):
                image_name = file_path.name.replace(ft, "")[:-1]

        # some fields need extra processing
        d3["Keywords"] = self._extract_keywords(d3["Keywords"])
        d3["name"] = image_name

        return d3

    def _extract_keywords(self, d_: dict) -> List[str]:
        """extracts keywords from dict

            improve the too generic exception

        Args:
            d_ (dict): data from extracted field

        Returns:
            List[str]: list of keywords
        """

        default_out = []
        keywords = []

        try:
            bag_ = d_.get("rdf:Bag", {}).get("rdf:li", [])
        except AttributeError:
            return default_out

        for item in bag_:
            if item.startswith("kywd"):
                kw = item.replace("kywd:||", "").replace("|", "")
                keywords.append(kw)

        return keywords

    def _file_has_extension(self, file: str, file_type_list: list) -> bool:

        return any([file.endswith(ft) for ft in file_type_list])

    def _read_dir(self):

        # recursively find all exposure files
        imgs = []
        files_list = []
        for (dirpath, dirnames, filenames) in os.walk(Path(self.cfg.DEFAULT_PATH)):
            if dirpath.split("/")[-1].lower() not in self.cfg.DIRS_TO_AVOID:
                files = [Path(dirpath) / f for f in filenames if self._file_has_extension(f, self.cfg.FILE_TYPE)]
                files_list.extend(files)

        for f in tqdm(files_list):
            img = self.read_one_sidecar(f)
            if img != {}:
                imgs.append(img)

        # converted list of sidecar dicts to a formatted df
        df = pd.DataFrame(imgs)
        df.info()

        df["CreateDate"] = pd.to_datetime(df["CreateDate"])
        # df['FocalLength'] = df['FocalLength'].str.replace('/1', 'mm')
        df["FocalLength"] = df["FocalLength"].apply(eval)
        df["FocalLength"] = df["FocalLength"].round(0).astype(int)
        # df['FocalLength'] = df['FocalLength'].astype(str) + 'mm'
        df["FNumber"] = df["FNumber"].str.replace("/1", "").apply(eval)
        df.loc[df["FNumber"] > 90, "FNumber"] = df.loc[df["FNumber"] > 90, "FNumber"] / 100.0
        # probably for manual lens
        df.loc[df["FNumber"] > 90, "FNumber"] = df.loc[df["FNumber"] > 90, "FNumber"] / 100.0
        
        df["Flag"] = df["Flag"].astype(int)

        df["Camera"] = df["Camera"].str.rstrip()
        # df['CropFactor'] = 2
        # df.loc[df['Camera'] == 'NIKON D3300', 'CropFactor'] = 1.5
        df.loc[df["Camera"] == "OLYMPUS E-M5 MARK III", "CropFactor"] = 2
        # df['FocalLength_'] = df['FocalLength'].str.replace('mm','').astype(float)
        df["FocalLength_"] = df["FocalLength"]
        df["EquivalentFocalLength"] = df["FocalLength_"].mul(df["CropFactor"])
        df["EquivalentFocalLength"] = df["EquivalentFocalLength"].astype(str) + "mm"
        df = df.drop(columns=["FocalLength_"])
        df["Date"] = df["CreateDate"].dt.date

        # filter df
        for k, v in self.cfg.DROP_FILTERS.items():
            df = df.loc[~df[k].isin(v), :]

        logger.warning(f"{len(df)} photos in library")
        logger.warning(f"{self.dangling_sidecars} dangling sidecar files found")
        logger.warning(f"{self.unloaded_sidecars} unloaded sidecar files found")

        return df
