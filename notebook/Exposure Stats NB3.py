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
