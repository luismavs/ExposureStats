from typer import Typer
from exposurestats.data_source import DataSource
from exposurestats.config import Config
import pandas as pd
from pathlib import Path
from datetime import date

app = Typer()


@app.command(name="keywords")
def get_keywords():
    """Save keywords table as csv"""
    ds = DataSource(Config.get_config("config.yaml"))

    _, _, _, keywords = ds.build_exposure_library()
    df_kws = keywords.loc[
        (keywords["Keywords"].notna()),
        :,
    ]

    df_ = pd.DataFrame(df_kws.groupby("Keywords")["name"].count())
    df_ = df_.reset_index()
    df_ = df_.sort_values("Keywords", ascending=True)

    df_.to_csv(Path("data") / ("keywords-" + str(date.today()) + ".csv"))


@app.command()
def dummy():
    pass


if __name__ == "__main__":
    app()
