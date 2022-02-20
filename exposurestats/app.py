import datetime
import streamlit as st
import altair as alt
import pandas as pd
from time import time
import logging
from typing import Tuple

from exposurestats.config import get_config, Config
from exposurestats.data_source import DataSource

logger = logging.getLogger("exposurestats")


# @st.cache
@st.experimental_memo
def build_exposure_library_with_cache(_cfg: Config) -> Tuple[pd.DataFrame, list, list, pd.DataFrame]:

    ds = DataSource(_cfg)

    return ds.build_exposure_library()


def draw_count_by_lens(df: pd.DataFrame):

    df_ = pd.DataFrame(df.groupby("Lens")["name"].count())
    df_ = df_.reset_index()

    chart = (
        alt.Chart(df_)
        .mark_bar()
        .encode(
            y="Lens",
            x=alt.X("name", title="Count", scale=alt.Scale(zero=True, domain=[0, df_["name"].max() * 1.05])),
            color=alt.Color("name", legend=None),
        )
    )

    text = chart.mark_text(
        align="left",
        baseline="middle",
        # dx=1  # Nudges text to right so it doesn't appear on top of the bar
    ).encode(text="name:Q")

    chart = (chart + text).configure_axis(grid=False)

    return chart


def draw_count_by_keyword(df: pd.DataFrame):

    df_ = pd.DataFrame(df.groupby("Keywords")["name"].count())
    df_ = df_.reset_index()
    df_ = df_.sort_values("Keywords", ascending=True)

    chart = (
        alt.Chart(df_)
        .mark_bar()
        .encode(
            y=alt.Y("Keywords", sort="-x"),
            x=alt.X("name", title="Count", scale=alt.Scale(zero=True, domain=[0, df_["name"].max() * 1.05])),
            color=alt.Color("name", legend=None),
        )
    )

    text = chart.mark_text(
        align="left",
        baseline="middle",
        # dx=1  # Nudges text to right so it doesn't appear on top of the bar
    ).encode(text="name:Q")

    chart = (chart + text).configure_axis(grid=False)

    return chart


def draw_count_by_focal_length(df: pd.DataFrame):

    df_ = pd.DataFrame(df.groupby("FocalLength")["name"].count())
    df_ = df_.reset_index()

    chart = (
        alt.Chart(df_)
        .mark_bar()
        .encode(
            x=alt.X(
                "FocalLength",
                scale=alt.Scale(zero=False, domain=[df["FocalLength"].min(), df["FocalLength"].max()]),
                title="Focal Length (mm)",
                # tooltip=
            ),
            y=alt.Y(
                "name",
                title="Count",
            ),
            tooltip=[alt.Tooltip("FocalLength")],
        )
    )

    return chart.configure_axis(grid=False)


def draw_count_by_date(df: pd.DataFrame):

    df_ = pd.DataFrame(df.groupby("Date")["name"].count()).reset_index()

    chart = (
        alt.Chart(df_)
        .mark_bar()
        .encode(
            x="Date:T",
            y=alt.Y(
                "name",
                title="Count",
                type="quantitative",
                # color=alt.Color('name', legend=None)
            ),
            tooltip=[alt.Tooltip("Date")],
        )
    )

    return chart.configure_axis(grid=False)


def main():

    st.title("Exposure Stats")

    cfg = get_config("config.yaml")

    logger.info(f"path to get stats: {cfg.DEFAULT_PATH}")

    # button before function call to avoid missing the 1st rerun
    if st.sidebar.button("Reload"):
        st.experimental_memo.clear()

    df, cameras, lenses, keywords = build_exposure_library_with_cache(cfg)

    d1 = st.sidebar.date_input("Start Date", datetime.date(2020, 1, 1))
    d2 = st.sidebar.date_input("End Date", datetime.datetime.today())

    selected_cameras = st.sidebar.multiselect("Select the Camera", options=cameras, default=cameras)

    all_lenses = st.sidebar.checkbox("All lenses")

    lenses_ = st.sidebar.multiselect("Select the Lens", options=lenses, default=lenses[0])
    if all_lenses:
        selected_lenses = lenses
    else:
        selected_lenses = lenses_

    # filter data according to widgets
    df = df.loc[df["Lens"].isin(selected_lenses), :]
    df = df.loc[df["Camera"].isin(selected_cameras), :]
    df = df.loc[(df["Date"] > d1) & (df["Date"] < d2), :]

    chart1 = draw_count_by_lens(df)
    st.altair_chart(chart1.interactive().properties(width=600))

    chart2 = draw_count_by_focal_length(df)
    st.altair_chart(chart2.interactive(bind_y=False).properties(width=600))

    chart3 = draw_count_by_date(df)
    st.altair_chart(chart3.interactive(bind_y=False).properties(width=600))

    chart4 = draw_count_by_keyword(
        keywords.loc[(keywords["Lens"].isin(selected_lenses)) & (keywords["Camera"].isin(selected_cameras)), :]
    )
    st.altair_chart(chart4.interactive().properties(width=600))

    # Streamlit widgets automatically run the script from top to bottom. Since
    # this button is not connected to any other logic, it just causes a plain
    # rerun.

    return


# @st.cache
@st.experimental_memo
def build_exposure_library(counter):

    print("loading data", counter)
    dd = {"a": 2}

    return dd


if __name__ == "__main__":

    logger = logging.getLogger("exposurestats")  # package logger shared namespace
    logger.setLevel(logging.DEBUG)  # set logger ouptut level
    ch = logging.StreamHandler()  # get logger streamhandler if we want to format the output
    ch.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))  # format output
    # "%(levelname)s - %(message)s" # minimalist format
    logger.addHandler(ch)  # attach formatting
    logger.propagate = False  # avoids double logging if streamhandler was already attached to another logger elsewhere

    main()
