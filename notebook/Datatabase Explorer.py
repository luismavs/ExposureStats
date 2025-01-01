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
#     display_name: .venv
#     language: python
#     name: python3
# ---

# %%
import duckdb
from exposurestats.db import Database

# %%
with duckdb.connect('../data/database.db') as conn:
    imd = conn.execute('select * from ImageData').fetchall()
    print(imd)
    imd = conn.execute('select * from Manuak').fetchall()
    print(imd)
    imd = conn.execute('select * from Categories').fetchall()
    print(imd)


# %%
with Database('../data/database.db') as db:
    df1 = db.read_table('ImageData')
    print(df1)

    df2 = db.read_table('ManualTaggedImages')
    print(df2)    

# %%
