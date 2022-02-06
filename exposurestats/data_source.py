from pathlib import Path
import pandas as pd
import xmltodict
from tqdm import tqdm
import os
from config import Config
import logging
from typing import Tuple, List
from time import time

logger = logging.getLogger("exposurestats")


def get_data(cfg: Config) -> Tuple[pd.DataFrame]:
    """[summary]

    Args:
        cfg (Config):

    Returns:
        Tuple[pd.DataFrame]: main_data, cameras, lenses
    """

    t1 = time()

    df = library_as_df(cfg)
    df["Lens"] = df["Lens"].fillna("No Lens")
    df.loc[df["Lens"].str.len() == 0, "Lens"] = "No Lens"

    cameras = df["Camera"].unique().tolist()
    cameras = sorted(cameras)
    lenses = df["Lens"].unique().tolist()
    lenses = sorted(lenses)
    t2 = time()

    logger.info(f"It took {round(t2-t1)}s to get the data")

    return df, cameras, lenses


def _read_one_image(cfg: Config, file_path: Path):

    with open(file_path, "rb") as f:
        d1 = xmltodict.parse(f)

    d2 = d1["x:xmpmeta"]["rdf:RDF"]["rdf:Description"]

    try:
        d3 = {k: d2[v] for k, v in cfg.FIELDS_TO_READ.items()}

        for k, v in cfg.FIELDS_TO_PROCESS.items():
            if v == "strip":
                d3[k] = str(d3[k]).strip()

        for ft in cfg.FILE_TYPE:
            if file_path.name.endswith(ft):
                image_name = file_path.name.replace(ft, "")[:-1]

        # some fields need extra processing
        d3["Keywords"] = _extract_keywords(d3['Keywords'])

        d3["name"] = image_name

    except KeyError as e:
        logger.warning(f"key not in dict: {e}")
        logger.warning(f"do some editing in Exposure to register this properly")
        logger.warning(file_path)
        d3 = {}

    return d3


def _extract_keywords(d_: dict) -> List[str]:
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


def _file_has_extension(file: str, file_type_list: list) -> bool:

    return any([file.endswith(ft) for ft in file_type_list])


def _read_dir(cfg: Config):

    # recursively find all exposure files
    imgs = []
    files_list = []
    for (dirpath, dirnames, filenames) in os.walk(Path(cfg.DEFAULT_PATH)):
        if dirpath.split("/")[-1].lower() not in cfg.DIRS_TO_AVOID:
            files = [Path(dirpath) / f for f in filenames if _file_has_extension(f, cfg.FILE_TYPE)]
            files_list.extend(files)

    for f in tqdm(files_list):
        img = _read_one_image(cfg, f)
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
    for k, v in cfg.DROP_FILTERS.items():
        df = df.loc[~df[k].isin(v), :]

    logger.info(f"{len(df)} photos in library")

    return df


def library_as_df(cfg: Config):

    df = _read_dir(cfg)

    return df
