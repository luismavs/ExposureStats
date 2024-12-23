import os
from pathlib import Path
from time import time

import pandas as pd
import xmltodict
from loguru import logger
from tqdm import tqdm

from exposurestats.config import Config


class DataSource:
    def __init__(self, cfg: Config):
        """Read an Exposure Library with sidecar files into an useful in-memory structure

            May perform cleaning on the filesystem, such as removing duplicates and dangling sidecars!

        Args:
            cfg: Configuration object
        """

        # configuration
        self.cfg = cfg
        # the library as a dataframe
        self.exlib: pd.DataFrame

        # monitoring
        self.dangling_sidecars = 0
        self.unloaded_sidecars = 0

        # more internal configs
        self.recognised_versions = ["exposurex6", "exposurex7"]

    def build_exposure_library(
        self,
    ) -> tuple[pd.DataFrame, list[str], list[str], pd.DataFrame]:
        """Get exposure library together with auxilliary information

            Use the return methods to feed streamlit
            Use the self attributes when doing interactive analysis

        Returns:
            main_data dataframe, cameras list, lenses list, keywords dataframe
        """

        t1 = time()

        df = self._read_dir()
        df["Lens"] = df["Lens"].fillna("No Lens")
        df.loc[df["Lens"].str.len() == 0, "Lens"] = "No Lens"

        cameras = df["Camera"].unique().tolist()
        cameras = sorted(cameras)

        lenses = df["Lens"].unique().tolist()
        lenses = sorted(lenses)

        keywords = df[["name", "Camera", "Lens", "Keywords"]].explode("Keywords")

        t2 = time()

        logger.info(f"It took {round(t2-t1)}s to get the data")

        self.exlib = df

        return df, cameras, lenses, keywords

    def read_one_sidecar(self, file_path: Path | str) -> dict:
        """Read properties from a sidecar .exposureXX file as a python dict

        Args:
            file_path: path to the sidecar in the filesystem

        Returns:
            Sidecar dict
        """

        if isinstance(file_path, str):
            file_path = Path(file_path)

        with open(file_path, "rb") as f:
            d1 = xmltodict.parse(f)

        d2 = d1["x:xmpmeta"]["rdf:RDF"]["rdf:Description"]

        try:
            d3 = self._extract_data_from_sidecar(self.cfg.FIELDS_TO_READ, d2, file_path)
        except KeyError as e:
            d3 = self._image_exception_handler(d1, file_path, e)

        return d3

    def _read_dir(self) -> pd.DataFrame:
        """ "Read the directory recursively

        Returns:
            pandas dataframe with the directory information
        """

        # recursively find all exposure files
        sidecars = []
        files_list = []
        for dirpath, dirnames, filenames in os.walk(Path(self.cfg.DEFAULT_PATH)):
            logger.info(f'Analysing dir:{dirpath.split("/")[-1].lower()}')
            avoid = False
            for dir_ in self.cfg.DIRS_TO_AVOID:
                if dir_ in dirpath.split("/"):
                    logger.warning(f"Skipping directory to avoid: {dir_}")
                    avoid = True
            if avoid is False:
                files = [Path(dirpath) / f for f in filenames if self._file_has_extension(f, self.cfg.FILE_TYPE)]
                files_list.extend(files)

        self._deal_with_duplicates(files_list)

        for f in tqdm(files_list):
            scar = self.read_one_sidecar(f)
            if scar:
                sidecars.append(scar)

        df = self._sidecars_to_dataframe(sidecars)

        logger.warning(f"{len(df)} photos in library")
        logger.warning(f"{self.dangling_sidecars} dangling sidecar files found")
        logger.warning(f"{self.unloaded_sidecars} unloaded sidecar files found")

        logger.warning("incoming and recycling dirs avoided")

        return df

    def _sidecars_to_dataframe(self, sidecars: list[dict]) -> pd.DataFrame:
        """Convert list of sidecar dicts to a formatted df

        Args:
            sidecars:

        Returns:
            dataframe
        """

        df = pd.DataFrame(sidecars)
        df.info()

        # detect bad dates by coercing to Nat
        df["CreateDate"] = pd.to_datetime(df["CreateDate"], utc=True, dayfirst=True, format="ISO8601", errors="coerce")
        bad_dates = df.loc[df["CreateDate"].isna(), :]

        if len(bad_dates) > 0:
            logger.error("Sidecars with bad CreateDate found")
            logger.error(bad_dates)
            logger.error("ignoring them")
            df = df.loc[df["CreateDate"].notna(), :]

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
        try:
            df["Date"] = df["CreateDate"].dt.date
        except AttributeError as e:
            logger.warning(e)
            breakpoint()

        # filter df
        for k, v in self.cfg.DROP_FILTERS.items():
            df = df.loc[~df[k].isin(v), :]

        return df

    def _image_exception_handler(self, sidecar: dict, file_path: Path, missing_key: str) -> dict:
        """Extract data from sidecar, while handling exceptions when reading image data

        Can modify the file system

        Args:
            sidecar: loaded sidecar data
            file_path: path to sidecar in filesystem
            missing_key: missing key in sidecar

        Returns:
            Extracted sidecar data, if any
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
                logger.warning(f"Missing key: {e}")
                pass

            try:
                d3 = self._extract_data_from_sidecar(self.cfg.fields_to_read_alternative_2, description, file_path)
                return d3
            except KeyError as e:
                logger.warning(f"Missing key: {e}")
                pass

            logger.warning(f"Missing key: {missing_key}")

        # do not return anything
        self.unloaded_sidecars += 1
        logger.warning(f"Could not read data from sidecar: {file_path}")

        return {}

    def _extract_data_from_sidecar(self, parser: dict, sidecar: dict, file_path: Path) -> dict:
        """Extract data from raw sidecar dict

        Args:
            parser: parsing instructions
            sidecar: sidecar raw dict
            file_path: path to sidecar in filesystem

        Returns:
            extracted sidecar data
        """

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

    def _deal_with_duplicates(self, sidecars: list[Path]):
        """Process for duplicates

        Removes duplicates from the filesystem

        Args:
            sidecars: list of sidecar paths

        """

        # identify duplicated sidecars...
        files = pd.DataFrame(
            {
                "full": sidecars,
                "name": [f.name.removesuffix("exposurex6").removesuffix("exposurex7") for f in sidecars],
                "suffix": [f.suffix for f in sidecars],
            }
        )
        files_group = pd.DataFrame(files.groupby("name").size()).rename(columns={0: "Count"})
        duplicated_sidecars = files_group.loc[files_group["Count"] > 1, :].index.to_list()
        files = files.merge(files_group, left_on="name", right_index=True)
        dupes = files.loc[files["Count"] > 1, :]

        logger.warning(f"{len(duplicated_sidecars)} duplicated sidecars detected")

        # delete sidecars from old Exposure versions
        ds = dupes.groupby("name")["suffix"].nunique()
        dupe_versions = ds[ds > 1].index.tolist()

        for dupe in dupe_versions[0:10]:
            paths_to_delete = files.loc[
                (files["name"] == dupe) & (~files["suffix"].str.contains(self.cfg.current_version, case=False)),
                "full",
            ].tolist()
            for path in paths_to_delete:
                logger.warning(f"Removing duplicated sidecar from a previous exposure version: {path}")
                os.remove(path)

        if len(dupe_versions) > 0:
            self._read_dir()

        # flag duplicated sidecars arising from duplicated files in different directories
        if self.cfg.run_for_duplicates:
            pd.set_option("display.max_colwidth", 200)
            for dupe_ in duplicated_sidecars:
                image_files = (
                    files.loc[files["name"] == dupe_, "full"]
                    .astype(str)
                    .str.removesuffix("." + self.cfg.current_version)
                ).rename("image_path")
                image_files = image_files.apply(lambda x: Path(x).parents[2] / Path(x).name)

                files_ = files.loc[files["name"] == dupe_, :].merge(image_files, left_index=True, right_index=True)
                files_["image_exists"] = files_["image_path"].apply(lambda x: os.path.isfile(x))

                for phantom_sidecar in files_.loc[files_["image_exists"] == False, "full"].tolist():
                    breakpoint()
                    try:
                        logger.warning(f"removing sidecar {phantom_sidecar} without associated image file")
                        os.remove(phantom_sidecar)
                    except FileNotFoundError:
                        logger.warning("file not found, moving on.")

    def _extract_keywords(self, d_: dict) -> list[str]:
        """Extract keywords from dict

            TODO: improve the too generic exception

        Args:
            d_: data from extracted field

        Returns:
            list of extracted keywords
        """

        default_out = []
        keywords = []

        logger.trace(f"extracting keywords from {d_}")

        try:
            bag_: list[str] = d_.get("rdf:Bag", {}).get("rdf:li", [])
        except AttributeError:
            logger.trace("attribute error")
            return default_out

        if isinstance(bag_, str):
            bag_ = [bag_]

        for item in bag_:
            logger.trace(item)
            if item.startswith("kywd"):
                kw = item.replace("kywd:||", "").replace("|", "")
                keywords.append(kw)

        logger.trace(f"extracted keywords: {keywords}")

        return keywords

    def _file_has_extension(self, file: str, file_type_list: list) -> bool:
        return any([file.endswith(ft) for ft in file_type_list])

    @classmethod
    def from_yaml(cls, path=str):
        cfg = Config.from_yaml(path)
        return cls(cfg)


if __name__ == "__main__":
    ds = DataSource(cfg=Config.from_env())
    main_df, cameras, lenses, keywords = ds.build_exposure_library()
    main_df.to_csv("data/data.csv")
    keywords.to_csv("data/keywords.csv")
