# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.6.0
#   kernelspec:
#     display_name: Python [conda env:py38]
#     language: python
#     name: conda-env-py38-py
# ---

# %%
import pandas as pd
from pathlib import Path
import os
import xmltodict
import sys
import seaborn as sns

# %%
FIELDS_TO_READ = {'CreateDate': '@xmp:CreateDate',
                 'FocalLength': '@exif:FocalLength',
                  'FNumber': '@exif:FNumber',
                  'Camera': '@tiff:Model',
                    }
FILE_TYPE =  'exposurex6'
PATH_IN_XML =  ['x:xmpmeta', 'rdf:RDF', 'rdf:Description']

def read_one_image(file_path):
    
    with open(file_path, 'rb') as f:
        d1 = xmltodict.parse(f)

    d2 = d1['x:xmpmeta']['rdf:RDF']['rdf:Description']
    
    d3 = {k : d2[v] for k, v in FIELDS_TO_READ.items()}
    image_name = file_path.name.replace(FILE_TYPE, '')[:-1]
    d3['name'] = image_name

    return d3

def read_dir(path):
    
    imgs = []
    for (dirpath, dirnames, filenames) in os.walk(path):
        files = [f for f in filenames if f.endswith(FILE_TYPE)]
        for f in files:
            fpath = Path(dirpath) / f
            imgs.append(read_one_image(fpath))

    # list of dicts to formatted df
    df = pd.DataFrame(imgs)
    
    df['CreateDate'] = pd.to_datetime(df['CreateDate'])
    df['FocalLength'] = df['FocalLength'].str.replace('/1', 'mm')
    df['FNumber'] = df['FNumber'].str.replace('/1', '')
    df['CropFactor'] = 1
    df.loc[df['Camera'] == 'NIKON D3300', 'CropFactor'] = 1.5
    df['FocalLength_'] = df['FocalLength'].str.replace('mm','').astype(float)
    df['EquivalentFocalLength'] = df['FocalLength_'].mul(df['CropFactor'])
    df['EquivalentFocalLength'] = df['EquivalentFocalLength'].astype(str) + 'mm'
    df = df.drop(columns=['FocalLength_'])
        
    return df

def library_as_df(path):    
    path = Path(path)
    
    df = read_dir(path)
    
    return df


def volume_plot(df, variable):

    sns.catplot(x=variable, kind="count", 
                #palette="ch:.25",
                data=df)

    return


def focal_lengths(df):
    
    volume_plot(df, 'FocalLength')
    
    return





# %%
path = '/Users/luisseabra/Pictures/DevPhotos'
print('path to get stats:', path)
df = library_as_df(path)

focal_lengths(df)

# %%

# %%

# %%
