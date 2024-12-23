# ---
# jupyter:
#   jupytext:
#     formats: py:percent,ipynb
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.6
#   kernelspec:
#     display_name: Python [conda env:py310] *
#     language: python
#     name: conda-env-py310-py
# ---

# %% [markdown]
# # Interactive exploration notebook

# %%
import pandas as pd
from pathlib import Path
import os
import xmltodict
import sys
import seaborn as sns
from tqdm import tqdm
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import ipywidgets as widgets
from typing import List, Optional
from datetime import datetime
import sys

sys.path.append("/Users/luis/code/ExposureStats/exposurestats")
from config import get_config
from exposurestats.data_source import DataSource

cfg = Config.from_yaml("../config.yaml")
cfg

# %% [markdown]
# ## load data

# %%
ds = DataSource(cfg)
df, cameras, lenses, keywords = ds.build_exposure_library()

# %%
keywords.info()

# %%
keywords.loc[keywords["Keywords"]]
