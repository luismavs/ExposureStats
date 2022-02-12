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

    def __init__(self, cfg:Config):

        self.cfg = cfg

    
    def image_exception_handler(self, sidecar:dict, file_path:Path, missing_key:str) -> dict:
        """handle execptions when reading image data

        Args:
            cfg (Config): [description]
            sidecar (dict): [description]
            error (Any): [description]

        Returns:
            dict
        """

        logger.warning(f'Missing key: {missing_key}')
        logger.warning(f"do some editing in Exposure to register this properly")
        logger.warning(file_path)


        # does the image file exist?

        image_file = file_path.parents[2] / '.'.join(file_path.name.split('.')[0:-1])

        # delete the sidecar if not
        if os.path.exists(image_file) is False:
            logger.warning('sidecar xmp has no matching image')

        d3 = {}

        return d3


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

        keywords = df[['name','Keywords']].explode('Keywords')

        t2 = time()

        logger.info(f"It took {round(t2-t1)}s to get the data")

        return df, cameras, lenses, keywords


    def _read_one_image(self, file_path: Path):

        with open(file_path, "rb") as f:
            d1 = xmltodict.parse(f)

        d2 = d1["x:xmpmeta"]["rdf:RDF"]["rdf:Description"]

        try:
            d3 = {k: d2[v] for k, v in self.cfg.FIELDS_TO_READ.items()}

            for k, v in self.cfg.FIELDS_TO_PROCESS.items():
                if v == "strip":
                    d3[k] = str(d3[k]).strip()

            for ft in self.cfg.FILE_TYPE:
                if file_path.name.endswith(ft):
                    image_name = file_path.name.replace(ft, "")[:-1]

            # some fields need extra processing
            d3["Keywords"] = self._extract_keywords(d3['Keywords'])

            d3["name"] = image_name

        except KeyError as e:
            logger.warning(f"key not in dict: {e}")
            
            d3 = self.image_exception_handler(d1, file_path, e)


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
            img = self._read_one_image(f)
            if img != {}:
                imgs.append(img)

        # list of dicts to formatted df
        df = pd.DataFrame(imgs)

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

        logger.info(f"{len(df)} photos in library")

        return df


    def library_as_df(self):

        df = self._read_dir()

        return df
