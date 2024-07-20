# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     custom_cell_magics: kql
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.2
#   kernelspec:
#     display_name: py312exp
#     language: python
#     name: python3
# ---

# %%
import polars as pl

# %%
kws = pl.read_parquet('/Users/luis/code/github/ExposureStats/data/keywords.parquet')

# %%
kws

# %%
kws['Keywords'].describe()

# %%
l1 = kws['Keywords'].unique().to_list()

# %%
for sss in l1:
    print(sss)

# %%
## analyse one sidecar

# %%
from exposurestats.data_source import DataSource
from pathlib import Path
from loguru import logger
import sys
logger.remove()
logger.add(sys.stderr,level='TRACE')

# %%
ds = DataSource.from_yaml('/Users/luis/code/github/ExposureStats/config.yaml')
ds.read_one_sidecar(Path('/Users/luis/Pictures/Lisboa 2020-/2022/05/07 Mértola/Exposure Software/Exposure X7/P5080008.ORF.exposurex7'))

# %%
ds.cfg

# %%
