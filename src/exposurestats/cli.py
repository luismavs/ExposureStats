import sys
from datetime import date
from pathlib import Path

import polars as pl
from dotenv import load_dotenv
from loguru import logger
from typer import Typer

from exposurestats.config import Config
from exposurestats.data_source import DataSource
from exposurestats.db import Database

app = Typer()


@app.command(name="keywords")
def get_keywords():
    """Get keywords from Exposure image directory and write them to a CSV file"""

    ds = DataSource(Config.from_env())

    _, _, _, keywords = ds.build_exposure_library()
    df_kws = pl.from_pandas(keywords).select(pl.col("Keywords").is_not_nan())
    df_ = df_kws.group_by("Keywords").agg(pl.col("name").count()).sort("Keywords", descending=False)
    df_.write_csv(Path("data") / ("keywords-" + str(date.today()) + ".csv"))


@app.command(name="build-db")
def build_db():
    """ "Build EXPS db from EXP files"""
    ds = DataSource(Config.from_env())
    image_data, _, _, _ = ds.build_exposure_library()

    with Database("data/database.db") as conn:
        conn.create_tables(drop=True)
        conn.insert_image_data(data=pl.from_pandas(image_data))


if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stderr, level="SUCCESS")
    load_dotenv()
    app()
