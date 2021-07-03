# ---
# jupyter:
#   jupytext:
#     formats: py:percent,ipynb
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.3
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
import pandas as pd
from pathlib import Path
import os
import xmltodict
import sys
import seaborn as sns
from tqdm import tqdm
import matplotlib.pyplot as plt
from  matplotlib.ticker import FuncFormatter
import ipywidgets as widgets
from typing import List, Optional
from datetime import datetime


# %%
##TO DO : remove unwanted photos

FIELDS_TO_READ = {'CreateDate': '@xmp:CreateDate',
                 'FocalLength': '@exif:FocalLength',
                  'FNumber': '@exif:FNumber',
                  'Camera': '@tiff:Model',
                  'Lens': '@alienexposure:lens',
                  'Flag': '@alienexposure:pickflag'
                    }

FIELDS_TO_PROCESS = {'Lens':'strip'}

FILE_TYPE =  'exposurex6'
PATH_IN_XML = ['x:xmpmeta', 'rdf:RDF', 'rdf:Description']
DIRS_TO_AVOID = ['recycling']

#
#FILTERS = {'remove__rejected' = {'alienexposure:pickflag' : 2}}
DROP_FILTERS = {'Flag' : [2]}


# %%
def read_one_image(file_path):
    
    with open(file_path, 'rb') as f:
        d1 = xmltodict.parse(f)

    d2 = d1['x:xmpmeta']['rdf:RDF']['rdf:Description']
    
    #
    try:
        d3 = {k : d2[v] for k, v in FIELDS_TO_READ.items()}
        
        for k, v in FIELDS_TO_PROCESS.items():
            if v == 'strip':
                d3[k] = str(d3[k]).strip()

        image_name = file_path.name.replace(FILE_TYPE, '')[:-1]
        d3['name'] = image_name
        
    except KeyError as e:
        print(f'key not in dict: {e}')
        print(f'do some editing in Exposure to register this properly')
        print(file_path)
        print(f'\n')
#        print(FIELDS_TO_READ)
#        for k in d2.keys():
#            print(k,' :: ',d2[k])
        d3 = {}
    
    
    return d3

def read_dir(path):
    
    # recursively find all exposure files
    imgs = []
    files_list = []
    for (dirpath, dirnames, filenames) in os.walk(path):
        if dirpath.split('/')[-1].lower() not in DIRS_TO_AVOID:
            files = [Path(dirpath) / f for f in filenames if f.endswith(FILE_TYPE)]
            files_list.extend(files)
        
    for f in tqdm(files_list):
        img = read_one_image(f)
        if img != {}:
            imgs.append(img)


    # list of dicts to formatted df
    df = pd.DataFrame(imgs)
    
    df['CreateDate'] = pd.to_datetime(df['CreateDate'])
    #df['FocalLength'] = df['FocalLength'].str.replace('/1', 'mm')
    df['FocalLength'] = df['FocalLength'].apply(eval)
    df['FocalLength'] = df['FocalLength'].round(0).astype(int)
    #df['FocalLength'] = df['FocalLength'].astype(str) + 'mm'
    df['FNumber'] = df['FNumber'].str.replace('/1', '').apply(eval)
    df.loc[df['FNumber'] > 90, 'FNumber'] = df.loc[df['FNumber'] > 90, 'FNumber'] / 100. 
    # probably for manual lens
    df.loc[df['FNumber'] > 90, 'FNumber'] = df.loc[df['FNumber'] > 90, 'FNumber'] / 100. 
    df['Flag'] = df['Flag'].astype(int)
    
    df['Camera'] = df['Camera'].str.rstrip()
    #df['CropFactor'] = 2
    #df.loc[df['Camera'] == 'NIKON D3300', 'CropFactor'] = 1.5
    df.loc[df['Camera'] == 'OLYMPUS E-M5 MARK III', 'CropFactor'] = 2
    #df['FocalLength_'] = df['FocalLength'].str.replace('mm','').astype(float) 
    df['FocalLength_'] = df['FocalLength']
    df['EquivalentFocalLength'] = df['FocalLength_'].mul(df['CropFactor'])
    df['EquivalentFocalLength'] = df['EquivalentFocalLength'].astype(str) + 'mm'
    df = df.drop(columns=['FocalLength_'])
    
    # filter df
    for k,v in DROP_FILTERS.items():
        df = df.loc[~df[k].isin(v), :]
        
    print(f'{len(df)} photos in library')
    
    return df

def library_as_df(path):    
    path = Path(path)
    
    df = read_dir(path)
    
    return df


def volume_plot(df:pd.DataFrame, variable:str, xaxis_date=False):

    plt.rcParams["axes.labelsize"] = 30
    
    if xaxis_date is False:
        vals = pd.Series(df[variable].unique()).sort_values(ascending=True)
    else:
        yms = df[variable].unique()
        vals = sorted(yms, key= lambda x:datetime.strptime(x, '%Y - %M')) # assuming it's year month here
            
    p = sns.catplot(x=variable,
                    kind="count", 
                #palette="ch:.25",
                data=df,
                height=6, 
                aspect=4,
                order=vals)
    
    #p.set_yticks(range(len(df))) # <--- set the ticks first
    #p.set_xticklabels(['2011','2012','2013','2014','2015','2016','2017','2018'])

    _, xlabels = plt.xticks()
    _, ylabels = plt.yticks()
    p.set_xticklabels(xlabels, size=20)
    p.set_yticklabels(ylabels, size=20)
    p.set_xticklabels(rotation=45)

    plt.show()

    return


def focal_lengths(df, camera=None, lens=None):
    
    if camera is not None:
        df = df[df['Camera']==camera]

    if lens is not None:
        df = df[df['Lens']==lens]
        
    volume_plot(df, 'FocalLength')
    
    return

def lens(df, camera=None):
    
    if camera is not None:
        df = df[df['Camera']==camera]
    
    volume_plot(df, 'Lens')
        
    return

def plot_by_date(df, lens='all'):

    df['year_month'] = df['CreateDate'].dt.year.astype(str) + " - " + df['CreateDate'].dt.month.astype(str)
    
    if lens != 'all':
        print(f'Filtering to lens {lens}')
        df = df.loc[df['Lens']==lens,:]
        
    volume_plot(df, 'year_month', xaxis_date=True)
    
    return


# %%
path = '/Users/luis/Pictures/Lisboa 2020-'
print('path to get stats:', path)
df = library_as_df(path)

cameras = df['Camera'].unique().tolist()
cameras = sorted(cameras)
lenses = df['Lens'].unique().tolist()
lenses = sorted(lenses)



# %%
w_camera = widgets.Select(
    options=cameras,
    rows=len(cameras),
    description='Cameras:',
    disabled=False
)
w_camera

# %%
lenses = lenses_in_camera = sorted(df.loc[df['Camera']==w_camera.value,'Lens'].unique().tolist())
w_lens = widgets.Select(
    options=lenses,
    rows=len(lenses),
    description='Lenses:',
    disabled=False
)
w_lens

# %%
print(f'{len(df)} photos in library')
focal_lengths(df, camera=w_camera.value)

lens(df, camera=w_camera.value)
print(f'Focal lengths for lens {w_lens.value}')
focal_lengths(df, camera=w_camera.value, lens=w_lens.value)
plot_by_date(df, lens=w_lens.value)


# %% [markdown]
# #### scratch space

# %%
df['Lens'].unique().tolist()

# %%
